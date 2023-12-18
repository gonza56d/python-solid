from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from random import randrange
from typing import List, Optional, Union
from uuid import UUID

import jwt
from nwevents import EventManager
from nwkcorelib import CommandHandler

from users.core.actions import (
    ConfirmIdentity,
    ConfirmPhoneNumber,
    CreatePhoneConfirmation,
    CreateSignUp,
    GetIdentityValidation,
    GetServiceAgreement,
    GetSignUpStageByUserId,
    GetUserByDocument,
    GetUserById,
    GetUserContactMethods,
    RequestUserIdentityValidation,
    UpdateLegalValidation,
    ValidateEmailConfirmationToken,
    ValidateUserIdentity,
)
from users.core.exceptions import (
    AttemptsExceededError,
    DuplicatedResourceError,
    EntityNotFound,
    IdentityDataError,
    IdentityValidationError,
    MissingAddressError,
    UserIdentityMinorError,
    UserIdentityTeenPartialError,
    ValidationError,
)
from users.core.models import (
    Address,
    ContactMethod,
    ContactMethodType,
    Customer,
    Identity,
    ServiceAgreement,
    SignUp,
    User,
    UserAddress,
)
from users.core.models import states
from users.core.models.compositions import ContactConfirmation
from users.core.models.states import (
    ContactConfirmationType,
    SignUpStage,
    UserStatus
)
from users.core.repositories import (
    AddressRepository,
    ContactMethodRepository,
    ContactMethodTypeRepository,
    CustomerRepository,
    IdentityValidationRepository,
    SignUpRepository,
    UserRepository,
)
from users.events import SavedContactMethod, SavedSignUp
from users.orm.repositories import ServiceAgreementDbRepository


@dataclass
class CreateSignUpHandler(CommandHandler):
    """Handler of the CreateSignUp action."""

    sign_up_repo: SignUpRepository
    user_repo: UserRepository
    contact_method_repo: ContactMethodRepository
    contact_method_type_repo: ContactMethodTypeRepository
    jwt_secret: str
    event_manager: EventManager
    contact_confirmation_expiration_timedelta: str

    def __call__(self, create_sign_up: CreateSignUp) -> SignUp:
        """
        Handle user sign up creation.

        If User and ContactMethod exist, renew the ContactConfirmation in
        case it has expired, or return an exception if it has not expired and
        is still pending to be confirmed.
        If User and ContactMethod exist but the ContactConfirmation is already
        confirmed, return a SignUpError (email is already taken).
        """
        user = self.user_repo.get_by_service_agr_id_and_email(
            service_agr_id=create_sign_up.service_agr_id,
            email=create_sign_up.email
        )

        if user is not None:
            contact_method = list(filter(
                lambda cm: cm.value == create_sign_up.email,
                user.contact_methods
            ))[0]

            contact_confirmation = contact_method.contact_confirmation

            if contact_confirmation.is_expired:
                return self.__renew_contact_confirmation(
                    user,
                    contact_method
                )

            elif contact_confirmation.is_still_pending:
                raise ValidationError(
                    'Contact confirmation for the submitted email '
                    'is still active and pending.'
                )
            raise ValidationError(
                'Email already taken.'
            )

        return self.__perform_sign_up(create_sign_up)

    def __renew_contact_confirmation(
        self,
        user: User,
        contact_method: ContactMethod
    ) -> SignUp:
        """
        Generate a ContactConfirmation for Users' ContactMethod again.

        Called when the ContactMethod's ContactConfirmation has expired.
        """
        contact_method.confirmation_expire_at = (
            datetime.now() + timedelta(
                hours=int(self.contact_confirmation_expiration_timedelta)
            )
        )

        self.contact_method_repo.save(contact_method)

        sign_up = self.sign_up_repo.get_by_user_id(user.id)

        self.__emit_saved_sign_up(sign_up, user, contact_method)

        return sign_up

    def __emit_saved_sign_up(
        self,
        sign_up: SignUp,
        user: User,
        contact_method: ContactMethod
    ):
        """Emit event telling that a sign up has been created or updated."""
        self.event_manager.emit(SavedSignUp(
            sign_up=sign_up,
            user=user,
            contact_method=contact_method
        ))

    def __generate_jwt(self, contact_method_id: UUID) -> str:
        encoded_jwt_value = jwt.encode(
            {
                'contact_method_id': str(contact_method_id)
            },
            self.jwt_secret,
            algorithm='HS256'
        )
        return encoded_jwt_value

    def __perform_sign_up(self, create_sign_up: CreateSignUp) -> SignUp:
        """Proceed with the sign up process."""
        user = User(
            service_agr_id=create_sign_up.service_agr_id,
            status=UserStatus.PENDING_VALIDATION,
        )

        contact_method_type = self.contact_method_type_repo.get('EMAIL')

        contact_method = ContactMethod(
            type=contact_method_type,
            value=create_sign_up.email,
            contact_confirmation=None
        )
        contact_confirmation = ContactConfirmation(
            type=ContactConfirmationType.TOKEN,
            value=self.__generate_jwt(
                contact_method.id
            ),
            created_at=datetime.now(),
            expire_at=datetime.now() + timedelta(
                hours=int(self.contact_confirmation_expiration_timedelta)
            )
        )
        contact_method.contact_confirmation = contact_confirmation

        user.contact_methods.append(contact_method)

        sign_up = SignUp(stage=SignUpStage.EMAIL_CONFIRMATION)
        sign_up.user_id = user.id

        self.user_repo.save(user)

        self.sign_up_repo.save(sign_up)

        self.__emit_saved_sign_up(sign_up, user, contact_method)

        return sign_up


@dataclass
class GetUserByIdHandler(CommandHandler):
    """Handler of the GetUserById action."""

    user_repo: UserRepository
    customer_repo: CustomerRepository

    def __call__(self, get_user: GetUserById) -> User:
        """Make the object callable to handle GetUserById."""
        user: User = self.user_repo.get_by_id(get_user.user_id)
        if user is None:
            raise EntityNotFound(User)

        if get_user.fetch_customer:
            user.customer = self.customer_repo.get_by_id(user.customer_id)

        return user


@dataclass
class GetUserByDocumentHandler(CommandHandler):
    """Handler of the GetUserByDocument action."""

    user_repo: UserRepository
    customer_repo: CustomerRepository

    def __get_customers(
        self,
        document_type: str,
        document_value: str
    ) -> List[Customer]:
        if document_type == 'DNI':
            customers: List[Customer] = self.customer_repo.list_by_dni(
                document_value
            )

        elif document_type == 'CUIL':
            customers: List[Customer] = self.customer_repo.list_by_cuil(
                document_value
            )

        else:
            raise ValidationError(
                f'{document_type} is not a valid value for '
                'document_type'
            )

        return customers

    def __get_user(
        self,
        business_model: states.BusinessModel,
        service_agr_id: int,
        customer_id: UUID,
    ) -> User:
        if service_agr_id is not None:
            return self.user_repo.get_by_customer_and_service_agr_id(
                customer_id=customer_id,
                service_agr_id=service_agr_id
            )
        elif business_model is not None:
            return self.user_repo.get_by_customer_and_business_model(
                customer_id=customer_id,
                business_model=business_model
            )

    def __call__(self, get_user: GetUserByDocument) -> Optional[User]:
        """Make the object callable to handle GetUserByDocument."""
        customers = self.__get_customers(
            get_user.document_type,
            get_user.document_value
        )
        if not customers:
            raise EntityNotFound(Customer)

        user = self.__get_user(
            get_user.business_model,
            get_user.service_agr_id,
            customers[0].id
        )
        if user is None:
            return None
        user.customer = customers[0]

        return user


@dataclass
class CreatePhoneConfirmationHandler(CommandHandler):
    """Handler of create phone confirmation action."""

    user_repo: UserRepository
    contact_method_type_repo: ContactMethodTypeRepository
    event_manager: EventManager
    PHONE_TYPE_DESCRIPTION = 'PHONE'

    def __call__(self, action: CreatePhoneConfirmation) -> str:
        """Handle create phone confirmatión."""
        user = self.user_repo.get_by_id(
            user_id=action.user_id
        )

        # Find if there is a contact method such as the user's phone.
        confirmation_phone = \
            self.__get_current_contact_confirmation_phone(user)
        otp_result = None
        if confirmation_phone is None:
            # Search contact method type = PHONE
            contact_method_type_phone = \
                self.contact_method_type_repo.get(self.PHONE_TYPE_DESCRIPTION)
            if contact_method_type_phone is None:
                raise EntityNotFound(ContactMethod)
            contact_method_created = \
                self.__create_contact_method_confirmation_phone(
                    user,
                    contact_method_type_phone,
                    action.phone_number
                )
            user.contact_methods.append(contact_method_created)
            otp_result = contact_method_created.contact_confirmation.value
        else:
            self.__update_contact_method_confirmation_phone(
                confirmation_phone,
                action.phone_number
            )
            otp_result = confirmation_phone.contact_confirmation.value

        self.user_repo.save(user)
        self.__emit_saved_contact_method(action.phone_number, otp_result)
        return otp_result

    def __emit_saved_contact_method(
        self,
        phone_number: str,
        otp: str
    ):
        """Emit an event.

        Indicating that a create phone confirmation has been created.
        """
        self.event_manager.emit(
            SavedContactMethod(
                phone_number,
                otp
            )
        )

    def __generate_otp(self):
        """Generate a random 4 digit confirmation code.

        Returns
        -------
        str
            confirmation code.
        """
        SMS_CODE_MIN_VALUE = 1000
        SMS_CODE_MAX_VALUE = 9999

        return str(randrange(SMS_CODE_MIN_VALUE, SMS_CODE_MAX_VALUE))

    def __generate_otp_expiration_date(self):
        """Generate the code expiration datetime.

        Returns
        -------
        datetime
            code expiration date.
        """
        SMS_CODE_EXPIRATION_HOURS = 1

        return datetime.now(timezone.utc) + \
            timedelta(hours=SMS_CODE_EXPIRATION_HOURS)

    def __create_contact_method_confirmation_phone(
        self,
        user: User,
        contact_method_type_phone: ContactMethodType,
        phone_number: str
    ) -> ContactMethod:
        """Build scenary a new contact."""
        contact_confirmation = ContactConfirmation(
            ContactConfirmationType.OTP,
            self.__generate_otp(),
            datetime.today(),
            self.__generate_otp_expiration_date(),
            None
        )

        contact_method_created = ContactMethod(
            contact_method_type_phone,
            phone_number,
            contact_confirmation,
            user.id
        )

        return contact_method_created

    def __update_contact_method_confirmation_phone(
        self,
        contact_method_phone: ContactMethod,
        phone_number: str
    ):
        """Build scenary contact confirmation update."""
        contact_confirmation_updated = ContactConfirmation(
            ContactConfirmationType.OTP,
            self.__generate_otp(),
            datetime.today(),
            self.__generate_otp_expiration_date(),
            None
        )
        contact_method_phone.contact_confirmation = \
            contact_confirmation_updated

        contact_method_phone.value = phone_number

        return

    def __get_current_contact_confirmation_phone(
        self,
        user: User
    ) -> Optional[ContactMethod]:
        """Get current contact confirmation phone assigned to user."""
        for contact_method in user.contact_methods:

            is_phone_type = (
                contact_method.type.description == self.PHONE_TYPE_DESCRIPTION
            )

            is_confirmed = (
                contact_method.contact_confirmation.confirmed_at is not None
            )

            if is_phone_type and not is_confirmed:
                return contact_method
            elif is_phone_type and is_confirmed:
                raise ValidationError("The phone number has been confirmed.")


@dataclass
class ConfirmPhoneNumberHandler(CommandHandler):
    """Handler of confirm phone number action."""

    sign_up_repo: SignUpRepository
    user_repo: UserRepository
    contact_method_type_repo: ContactMethodTypeRepository

    PHONE_TYPE_DESCRIPTION = 'PHONE'

    def __call__(self, action: ConfirmPhoneNumber):
        """Handle create phone confirmation."""
        user = self.user_repo.get_by_id(
            user_id=action.user_id
        )

        signup = self.sign_up_repo.get_by_user_id(action.user_id)

        # Search contact method type = PHONE
        self.contact_method_type_repo.get(self.PHONE_TYPE_DESCRIPTION)

        # Find if there is a contact method such as the user's phone.
        confirmation_phone = \
            self.__get_current_contact_confirmation_phone(user)

        signup.stage = states.SignUpStage.PHONE_CONFIRMATION
        if confirmation_phone.contact_confirmation.value == action.otp:
            confirmation_phone.contact_confirmation = \
                confirmation_phone.contact_confirmation.recreate(
                    confirmed_at=datetime.now()
                )
            self.user_repo.save(user)
            self.sign_up_repo.save(signup)
        else:
            raise ValidationError("OTP code is invalid.")

    def __get_current_contact_confirmation_phone(
        self,
        user: User
    ) -> Optional[ContactMethod]:
        """Get current contact confirmation phone assigned to user."""
        for contact_method in user.contact_methods:
            is_pending = (
                contact_method.contact_confirmation.is_still_pending
            )

            is_phone_type = (
                contact_method.type.description == self.PHONE_TYPE_DESCRIPTION
            )

            is_confirmed = (
                contact_method.contact_confirmation.confirmed_at is not None
            )

            if is_phone_type and is_pending:
                return contact_method
            elif is_phone_type and is_confirmed:
                raise ValidationError("The phone number has been confirmed.")


@dataclass
class TokenValidationHandler(CommandHandler):
    """Business logic for email confirmation token."""

    contact_method_repo: ContactMethodRepository
    sign_up_repo: SignUpRepository

    def __call__(self, validation: ValidateEmailConfirmationToken) -> SignUp:
        """
        Perform the token validation by calling this object.

        If token is valid, set the contact method confirmation date to
        datetime.now() and set the sign up stage to IDENTITY_VALIDATION.
        """
        email: Optional[ContactMethod] = self.\
            contact_method_repo.\
            get_by_token(validation.token)

        if email is None or \
                email.contact_confirmation.confirmed_at is not None or \
                email.contact_confirmation.expire_at < datetime.now():
            raise ValidationError('Invalid confirmation token')

        sign_up: SignUp = self.sign_up_repo.get_by_user_id(email.user_id)
        sign_up.stage = SignUpStage.IDENTITY_VALIDATION

        email.contact_confirmation = email.contact_confirmation.recreate(
            confirmed_at=datetime.now()
        )

        self.contact_method_repo.save(email)
        self.sign_up_repo.save(sign_up)

        return sign_up


@dataclass
class ValidateUserIdentityHandler(CommandHandler):
    """Business logic for users' identity validations."""

    user_repo: UserRepository
    identity_validation_repo: IdentityValidationRepository
    sign_up_repo: SignUpRepository

    def __call__(self, validation_data: ValidateUserIdentity) -> Optional[UUID]:
        """
        Perform external identity validation request.

        Return identity validation id if validation was successful and identity was
        confirmed.
        """
        user = self.user_repo.get_by_id(validation_data.user_id)

        if user.status is not UserStatus.PENDING_VALIDATION:
            raise ValidationError(
                'User status is not PENDING_VALIDATION. '
                f'(Current status: {user.status.value})'
            )

        sign_up = self.sign_up_repo.get_by_user_id(validation_data.user_id)

        if sign_up.stage is not SignUpStage.IDENTITY_VALIDATION:
            raise ValidationError(
                'Sign up stage is not IDENTITY_VALIDATION. '
                f'(Current sign up stage: {sign_up.stage.value}).'
            )

        request_id_validation = RequestUserIdentityValidation(
            service_agreement_id=user.service_agr_id,
            **asdict(validation_data)
        )

        try:
            user_id = self.identity_validation_repo\
                .validate_identity(request_id_validation)
        except (AttemptsExceededError, IdentityDataError) as err:
            self.__update_on_attempts_exceed_or_data_error(user, err)
            raise err
        except UserIdentityMinorError as err:
            self.__update_on_validation_minor(sign_up)
            raise err
        except UserIdentityTeenPartialError as err:
            self.__update_on_validation_teen(user)
            user_id = err.user_id
        else:
            if user_id is not None:
                self.__update_on_validation_success(user)
        return user_id

    def __update_on_validation_success(self, user: User) -> None:
        user.status = UserStatus.VALIDATED
        self.user_repo.save(user)

    def __update_on_attempts_exceed_or_data_error(
            self,
            user: User,
            err: Union[AttemptsExceededError, IdentityDataError]
    ):
        user.status = (
            UserStatus.BANNED_NOTIFIED if err.banned_notified else UserStatus.BANNED
        )
        self.user_repo.save(user)

    def __update_on_validation_teen(self, user: User) -> None:
        user.status = UserStatus.PENDING_AUTHORIZATION
        self.user_repo.save(user)

    def __update_on_validation_minor(self, sign_up: SignUp) -> None:
        sign_up.stage = SignUpStage.SIGN_UP_BLOCKED
        self.sign_up_repo.save(sign_up)


@dataclass
class GetSignUpStageByUserIdHandler(CommandHandler):
    """Business logic for getting sign up instances from its user's ID."""

    sign_up_repo: SignUpRepository

    def __call__(self, get_sign_up: GetSignUpStageByUserId) -> SignUpStage:
        """Get a sign up instance stage by its user id."""
        sign_up: SignUp = self.sign_up_repo.get_by_user_id(get_sign_up.user_id)

        return sign_up.stage


@dataclass
class GetServiceAgreementByIDHandler(CommandHandler):
    """Business logic for getting service agreement instances by ID."""

    service_agr_repo: ServiceAgreementDbRepository

    def __call__(
        self,
        action: GetServiceAgreement
    ) -> ServiceAgreement:
        """Get a service agreement instance by ID."""
        service_agr: ServiceAgreement = self.service_agr_repo.get(
            action.service_agreement_id
        )
        return service_agr


@dataclass
class GetIdentityHandler(CommandHandler):
    """Business logic for getting a user's identity validation."""

    user_repo: UserRepository
    sign_up_repo: SignUpRepository
    identity_validation_repo: IdentityValidationRepository
    address_repo: AddressRepository

    def __call__(self, action: GetIdentityValidation) -> Identity:
        """Get a user's identity validation."""
        user = self.user_repo.get_by_id(action.user_id)

        sign_up = self.sign_up_repo.get_by_user_id(user.id)

        identity = self.identity_validation_repo.get_identity_by_user_id(user.id)

        if sign_up.stage is not SignUpStage.IDENTITY_VALIDATION:
            raise IdentityValidationError(sign_up.stage)

        try:
            identity.addresses = self.address_repo.list(action.user_id)
        except MissingAddressError as err:
            self.errors.append(err)

        return identity


@dataclass
class UpdateLegalValidationHandler(CommandHandler):
    """Business logic for update a legal validation."""

    user_repo: UserRepository
    customer_repo: CustomerRepository
    sign_up_repo: SignUpRepository

    def __call__(self, action: UpdateLegalValidation) -> User:
        """Update a user's legal validation."""
        user = self.user_repo.get_by_id(action.user_id)
        action.customer_id = user.customer_id
        self.customer_repo.update_legal_validation(action)
        sign_up: SignUp = self.sign_up_repo.get_by_user_id(user.id)
        sign_up.stage = SignUpStage.LEGAL_VALIDATION
        self.sign_up_repo.save(sign_up)


@dataclass
class GetUserContactMethodsHandler(CommandHandler):
    """Business logic to fetch some user's contact methods."""

    user_repo: UserRepository

    def __call__(self, action: GetUserContactMethods) -> List[ContactMethod]:
        """Get a user or raise entity not found and fetch its contact methods list."""
        user = self.user_repo.get_by_id(action.user_id)
        return user.contact_methods


@dataclass
class ConfirmIdentityHandler(CommandHandler):
    """Business logic for users' identity and address confirmation."""

    user_repo: UserRepository
    identity_validation_repo: IdentityValidationRepository
    address_repo: AddressRepository
    customer_repo: CustomerRepository
    sign_up_repo: SignUpRepository

    def __call__(self, action: ConfirmIdentity) -> UUID:
        """
        Handle identity and address confirmation.

        Associate user to existent customer or request a new one.
        """
        user = self.__get_user(action.user_id)

        sign_up = self.__get_sign_up(action.user_id)

        user_id = self.identity_validation_repo.confirm_identity(action.user_id)
        identity = self.identity_validation_repo.get_identity_by_user_id(action.user_id)

        self.__associate_address(user, action.user_id, action.address_id)
        self.__associate_customer(user, identity)

        self.user_repo.save(user)

        sign_up.stage = SignUpStage.LEGAL_VALIDATION
        self.sign_up_repo.save(sign_up)

        return user_id

    def __get_user(self, user_id: UUID) -> User:
        user = self.user_repo.get_by_id(user_id)
        if user.status is not UserStatus.PENDING_VALIDATION:
            raise ValidationError(
                'User status is not PENDING_VALIDATION. '
                f'(Current status: {user.status.value}).'
            )

        return user

    def __get_sign_up(self, user_id: UUID) -> SignUp:
        sign_up = self.sign_up_repo.get_by_user_id(user_id)
        if sign_up.stage is not SignUpStage.IDENTITY_VALIDATION:
            raise ValidationError(
                'Sign up stage is not IDENTITY_VALIDATION. '
                f'(Current sign up stage: {sign_up.stage.value}).'
            )

        return sign_up

    def __associate_customer(self, user: User, identity: Identity):
        customers = self.customer_repo.list_by_dni(identity.dni)
        if len(customers) > 1:
            raise DuplicatedResourceError(Customer)

        if customers:
            customer_id = customers[0].id
        else:
            customer_id = self.customer_repo.create(identity)

        user.customer_id = customer_id

    def __associate_address(self, user: User, user_id: UUID, address_id: UUID):
        addresses = self.address_repo.list(user_id)

        if address_id not in [address.address_id for address in addresses]:
            raise EntityNotFound(Address)

        user_adress = UserAddress(user_id, address_id)
        user.user_addresses.append(user_adress)
