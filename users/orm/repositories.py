from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Callable
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from users.core.exceptions import (
    EntityNotFound,
    StorageReadError
)
from users.core.models import (
    ContactMethod,
    ContactMethodType,
    ServiceAgreement,
    SignUp,
    User,
)
from users.core.models.states import BusinessModel
from users.core.repositories import (
    ContactMethodRepository,
    ContactMethodTypeRepository,
    ServiceAgreementRepository,
    SignUpRepository,
    UserRepository,
)


class DatabaseRepository:
    """Superclass of all *DBRepository objects."""

    def __init__(
            self,
            session_factory: Callable[
                ...,
                AbstractAsyncContextManager[Session]
            ]
    ):
        """Initialize the session_factory for the subclasses."""
        self.session_factory = session_factory


class UserDbRepository(DatabaseRepository, UserRepository):
    """Access to elements of the User collection."""

    def save(self, user: User) -> None:
        """Persist a User object."""
        with self.session_factory() as session:
            session.add(user)
            session.commit()

    def get_by_id(self, user_id: UUID) -> User:
        """Retrieve a User object by user id."""
        with self.session_factory() as session:
            user = session.get(User, user_id)

        if user is None:
            raise EntityNotFound(User)

        return user

    def get_by_customer_and_business_model(
        self,
        customer_id: UUID,
        business_model: BusinessModel,
    ) -> Optional[User]:
        """Get a user by its business model."""
        with self.session_factory() as session:
            return session\
                .query(User)\
                .join(ServiceAgreement)\
                .filter(
                    ServiceAgreement.business_model == business_model,
                    User.customer_id == customer_id)\
                .one_or_none()

    def get_by_customer_and_service_agr_id(
        self,
        customer_id: UUID,
        service_agr_id: int
    ) -> Optional[User]:
        """Retrieve a User object by service agreement id."""
        with self.session_factory() as session:
            return session\
                .query(User)\
                .filter(
                    User.service_agr_id == service_agr_id,
                    User.customer_id == customer_id)\
                .one_or_none()

    def get_by_service_agr_id_and_email(
        self,
        service_agr_id: int,
        email: str
    ) -> Optional[User]:
        """Get a user or none by its svc agreement id and email."""
        with self.session_factory() as session:
            obtained_user: Optional[User] = session\
                .query(User)\
                .join(ContactMethod)\
                .join(ContactMethodType)\
                .filter(
                    User.service_agr_id == service_agr_id,
                    ContactMethodType.description == 'EMAIL',
                    ContactMethod.value == email
            ).one_or_none()
            return obtained_user


class ContactMethodTypeDbRepository(
        DatabaseRepository,
        ContactMethodTypeRepository
):
    """Access to elements of the ContactMethodType collection."""

    def get(self, description: str) -> ContactMethodType:
        """Retrieve a contact method type by its description."""
        with self.session_factory() as session:
            contact_method_type = session.query(ContactMethodType).filter(
                ContactMethodType.description == description
            ).one_or_none()
            return contact_method_type


class SignUpDbRepository(DatabaseRepository, SignUpRepository):
    """Access to elements of the SignUp collection."""

    def get(self, sign_up_id: UUID) -> SignUp:
        """Get a sign up object by its primary key."""
        with self.session_factory() as session:
            sign_up: SignUp = session.get(SignUp, sign_up_id)

        if sign_up is None:
            raise EntityNotFound(SignUp)

        return sign_up

    def get_by_user_id(self, user_id: UUID) -> SignUp:
        """Get a sign up object by its user id."""
        with self.session_factory() as session:
            try:
                return session.query(SignUp)\
                    .filter(SignUp.user_id == user_id)\
                    .one()
            except NoResultFound as err:
                raise EntityNotFound(SignUp) from err

    def save(self, sign_up: SignUp) -> None:
        """Persist a SignUp object."""
        with self.session_factory() as session:
            session.add(sign_up)
            session.commit()


class ContactMethodDbRepository(DatabaseRepository, ContactMethodRepository):
    """Access to elements of the ContactMethod collection."""

    def get(self, contact_method_id: UUID) -> ContactMethod:
        """Retrieve a contact method object by its ID."""
        with self.session_factory() as session:
            contact_method: ContactMethod = session.get(
                ContactMethod,
                contact_method_id
            )

        if contact_method is None:
            raise EntityNotFound(ContactMethod)

        return contact_method

    def save(self, contact_method: ContactMethod) -> None:
        """Persist a ContactMethod object."""
        with self.session_factory() as session:
            session.add(contact_method)
            session.commit()

    def get_by_type_and_value(
        self,
        type_: str,
        value: str,
        user_id: UUID
    ) -> Optional[ContactMethod]:
        """Get a contact method or none by its value, type and user_id."""
        with self.session_factory() as session:
            contact_method: Optional[ContactMethod] = session\
                .query(ContactMethod)\
                .join(ContactMethodType)\
                .filter(
                    ContactMethod.type.description == type_,
                    ContactMethod.value == value,
                    ContactMethod.user_id == user_id
            ).one_or_none()
            return contact_method

    def get_by_token(self, token: str) -> Optional[ContactMethod]:
        """Get the contact method or none by its validation token value."""
        with self.session_factory() as session:
            contact_method: Optional[ContactMethod] = session\
                .query(ContactMethod)\
                .filter(ContactMethod.confirmation_value == token)\
                .one_or_none()
            return contact_method


class ServiceAgreementDbRepository(
    DatabaseRepository,
    ServiceAgreementRepository
):
    """Access to elements of the service_agreement collection."""

    def save(self, service_agreement: ServiceAgreement) -> None:
        """Insert a service agreement in the database."""
        with self.session_factory() as session:
            session.add(service_agreement)
            session.commit()

    def get(self, service_agreement_id: int) -> ServiceAgreement:
        """Retrieve a contact method object by its ID."""
        try:
            with self.session_factory() as session:
                service_agreement: ServiceAgreement = session.get(
                    ServiceAgreement,
                    service_agreement_id
                )
        except Exception as error:
            raise StorageReadError(
                "Tried to retrieve service agreements."
            ) from error
        if service_agreement is None:
            raise EntityNotFound(ServiceAgreement)

        return service_agreement
