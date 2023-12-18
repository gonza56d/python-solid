"""Declare the concrete ODM layer of the core.model."""
import re
from typing import (
    Callable,
    Dict,
    List,
    Optional
)

from marshmallow import (
    fields,
    MarshalResult,
    post_dump,
    post_load,
    pre_load,
    Schema,
    validates,
)
from marshmallow.exceptions import ValidationError
from marshmallow_enum import EnumField

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
from users.core.models import (
    Address,
    ContactMethod,
    ContactMethodType,
    Customer,
    Identification,
    Identity,
    PerformIdentityValidationResponse,
    SavePhoneConfirmation,
    SignUp,
    User,
)
from users.core.models import states
from users.core.models.compositions import AuditFields, ContactConfirmation
from users.core.models.locals import ServiceAgreement, UserAddress
from users.core.models.states import (
    BusinessModel,
    ContactConfirmationType,
    SignUpStage,
    UserStatus
)
from users.odm.base import UserAnnotationSchema


class ErrorSchema(Schema):
    """Serialize a raised or collected error inside a api view."""

    code = fields.Str(required=True)
    message = fields.Raw(required=True)


class ResponseErrorSchema(Schema):
    """Serialize the error interface for a 4XX|500 status code response."""

    error = fields.Nested(ErrorSchema, many=False, required=True)


class AuditFieldSchema(UserAnnotationSchema):
    """Schema for AuditField deserialization."""

    class Meta(UserAnnotationSchema.Meta):
        """Configure the Device as the target of the schema."""

        target = AuditFields
        register_as_scheme = True


class AddressSchema(UserAnnotationSchema):
    """Schema to load and dump addresses."""

    class Meta(UserAnnotationSchema.Meta):
        target = Address


class ContactConfirmationSchema(UserAnnotationSchema):
    """Schema for ContactConfirmation deserialization in ContactMethod."""

    type = EnumField(ContactConfirmationType, required=True)

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = ContactConfirmation
        register_as_scheme = True


class GetUserByIdRequest(UserAnnotationSchema):
    """Request schema used when getting a user by its id."""

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = GetUserById
        fields = ('user_id',)


class GetUserContactMethodsRequest(UserAnnotationSchema):
    """Request schema used to get some user's contact methods list."""

    class Meta(UserAnnotationSchema.Meta):
        target = GetUserContactMethods


class ContactMethodTypeResource(UserAnnotationSchema):
    """Resource to represent contact method types."""

    class Meta(UserAnnotationSchema.Meta):
        target = ContactMethodType


class GetUserContactMethodsResponse(UserAnnotationSchema):
    """Response schema used to return a list of user's contact methods."""

    confirmed = fields.Boolean(attribute='is_confirmed')

    class Meta(UserAnnotationSchema.Meta):
        target = ContactMethod
        fields = ('id', 'type', 'value', 'user_id', 'confirmed')

    @post_dump()
    def flatten_type(self, data: dict) -> dict:
        """Get type description value."""
        type_: Optional[dict] = data.get('type')

        if type_ is not None:
            data['type'] = type_.get('description')

        return data


class GetUserByDocumentRequest(UserAnnotationSchema):
    """Request schema used when filtering a user by its document."""

    business_model = EnumField(BusinessModel, required=False)

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = GetUserByDocument

    @pre_load
    def validate_business_model(self, data: dict) -> dict:
        """Validate that the business model is a valid value."""
        if data.get('business_model') is not None:
            try:
                data['business_model'] = BusinessModel(
                    data['business_model']
                ).name
            except ValueError:
                raise ValidationError(f'{data["business_model"]} is not a '
                                      f'valid option for business_model.')
        return data

    @post_load
    def validate_inputs(self, data: dict) -> dict:
        """Validate that only one value is preset at a time."""
        if data.get('business_model') is not None \
                and data.get('service_agr_id') is not None:
            raise ValidationError(
                'Ambiguous input data. Only business_model OR service_agr_id '
                'must be provided. Not both.'
            )
        return data


class UserAddressSchema(UserAnnotationSchema):
    """Represent UserAddress."""

    class Meta(UserAnnotationSchema.Meta):
        target = UserAddress


class IdentificationResource(UserAnnotationSchema):
    """Resource schema used to retrieve a customer identification resource."""

    created_at = fields.DateTime(dump_to='createdAt', load_from='created_date')
    updated_at = fields.DateTime(
        dump_to='updatedAt', load_from='modified_date'
    )
    customer_identification_id = fields.UUID(load_from='id')
    type = fields.String(load_from='document_type')
    number = fields.String(load_from='document_number')

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = Identification
        register_as_scheme = True

    @pre_load()
    def flatten_object(self, data: dict) -> dict:
        """Flatten nested audit fields in data dictionary."""
        for k, v in data.get('audit_fields').items():
            data[k] = v

        return data


class CustomerResource(UserAnnotationSchema):
    """Resource schema used to retrieve a specific customer."""

    identifications = fields.Dict(
        keys=fields.Str(),
        values=IdentificationResource,
        attribute='identifications'
    )
    created_at = fields.DateTime(load_from='created_date')
    updated_at = fields.DateTime(load_from='modified_date')
    document_number = fields.String(attribute='document_number')
    document_type = fields.String(attribute='document_type')

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = Customer
        register_as_scheme = True

    @pre_load
    def flatten_object(self, data: dict) -> dict:
        """Flatten nested fields in the dictionary."""
        if 'audit_fields' in data:
            for k, v in data.get('audit_fields').items():
                data[k] = v

        data['first_name'] = data.get('legal_name').get('first_name')
        data['last_name'] = data.get('legal_name').get('last_name')
        data['id'] = data.get('id') or data.get('customer_id')
        return data


class ContactMethodResource(UserAnnotationSchema):
    """Resource schema used to retrieve a specific contact method."""

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = ContactMethod
        register_as_scheme = True


class UserResourceSchema(UserAnnotationSchema):
    """Single User object resource schema."""

    status = EnumField(UserStatus, required=True)

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = User
        register_as_scheme = True
        fields = (
            'id',
            'service_agr_id',
            'status',
            'customer_id',
            'address_id'
        )


class UserByIdResource(UserAnnotationSchema):
    """Resource schema when getting a specific user by id."""

    status = EnumField(UserStatus, required=True)
    contact_methods = fields.List(fields.Nested(ContactMethodResource))
    email = fields.Email(attribute='email')
    phone_number = fields.String(attribute='phone_number')
    service_agr_id = fields.Int(dump_to='type')

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = User
        register_as_scheme = True

    @post_dump
    def flatten_object(self, data: dict) -> dict:
        """Return this schema data with the expected structure."""
        customer_id = data.get('customer_id')
        identifications = [
            {
                'type': k,
                'number': v['value'],
                'customer_identification_id': customer_id,
                'createdAt': v['audit_fields']['created_date'],
                'updatedAt': v['audit_fields']['modified_date'],
            } for k, v in data.get('customer').get('identifications').items()
        ]
        return {
            'id': data.get('id'),
            'type': data.get('type'),
            'lastName': data.get('customer').get('last_name'),
            'gender': data.get('customer').get('gender'),
            'documentType': data.get('customer').get('document_type'),
            'documentNumber': data.get('customer').get('document_number'),
            'mobileNumber': data.get('phone_number'),
            'birthDate': data.get('customer').get('birth_date'),
            'identifications': identifications,
            'firstName': data.get('customer').get('first_name'),
            'createdAt': data.get('customer').get('created_at'),
            'email': data.get('email'),
            'updatedAt': data.get('customer').get('updated_at'),
            'status': data.get('status'),
            'nationality_id': data.get('customer').get('nationality_id')
        }


class UserByDocumentResource(UserAnnotationSchema):
    """Resource schema when filtering a specific user by document."""

    status = EnumField(UserStatus, required=True)
    contact_methods = fields.List(fields.Nested(ContactMethodResource))
    email = fields.Email(attribute='email')
    phone_number = fields.String(attribute='phone_number')
    service_agr_id = fields.Int(dump_to='type')

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = User
        register_as_scheme = True

    @post_dump
    def flatten_object(self, data: dict) -> dict:
        """Return this schema data with the expected structure."""
        customer_id = data.get('customer_id')
        identifications = [
            {
                'type': k,
                'number': v['value'],
                'customer_identification_id': customer_id,
                'createdAt': v['audit_fields']['created_date'],
                'updatedAt': v['audit_fields']['modified_date'],
            } for k, v in data.get('customer').get('identifications').items()
        ]
        return {
            'type': data.get('type'),
            'status': data.get('status'),
            'customer_status': data.get('customer').get('status'),
            'lastName': data.get('customer').get('last_name'),
            'firstName': data.get('customer').get('first_name'),
            'email': data.get('email'),
            'gender': data.get('customer').get('gender'),
            'documentType': data.get('customer').get('document_type'),
            'documentNumber': data.get('customer').get('document_number'),
            'mobileNumber': data.get('phone_number'),
            'birthDate': data.get('customer').get('birth_date'),
            'identifications': identifications,
            'createdAt': data.get('customer').get('created_at'),
            'updatedAt': data.get('customer').get('updated_at'),
            'nationality_id': data.get('customer').get('nationality_id')
        }


class UserPhoneNumberConfirmationRequest(UserAnnotationSchema):
    """Request schema used to phone number confirmation."""

    PHONE_FORMAT = r"\+54([0-9]{9,13})"

    @validates('phone_number')
    def validate_phone(self, phone):
        """Validate a Phone.

        Raises
        -------
        ValidationError
            If it is invalid.
        """
        if re.fullmatch(self.PHONE_FORMAT, phone) is None:
            raise ValidationError("Invalid field")

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = CreatePhoneConfirmation
        register_as_scheme = True


class ConfirmPhoneNumberRequest(UserAnnotationSchema):
    """Request schema used to confirm otp number."""

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = ConfirmPhoneNumber
        register_as_scheme = True


class CreateSignUpSchema(UserAnnotationSchema):
    """Request schema for email confirmation."""

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = CreateSignUp
        register_as_scheme = True


class SignUpResourceSchema(UserAnnotationSchema):
    """Response schema for email confirmation."""

    stage = EnumField(SignUpStage)

    class Meta(UserAnnotationSchema.Meta):
        target = SignUp


class TokenValidationRequestSchema(UserAnnotationSchema):
    """Request schema for token validation."""

    class Meta(UserAnnotationSchema.Meta):
        """Schema target configurations."""

        target = ValidateEmailConfirmationToken
        register_as_scheme = True


class SavePhoneConfirmationResponse(UserAnnotationSchema):
    """Schema for Phone Number Confirmation deserialization."""

    class Meta(UserAnnotationSchema.Meta):
        target = SavePhoneConfirmation


class IdentitySchema(UserAnnotationSchema):
    """Schema for get identity response."""

    addresses = fields.List(fields.Nested(AddressSchema), required=False)

    class Meta(UserAnnotationSchema.Meta):
        target = Identity

    @post_dump
    def addresses_into_dict(self, data: dict) -> dict:
        """Transform addresses into dict where key=address_id, value=object."""
        addresses = data.get('addresses') or {}
        data['addresses'] = {
            address['address_id']: address
            for address in addresses
        }
        return data


class UserIdentityValidationRequestSchema(UserAnnotationSchema):
    """Schema for users' identity validation request."""

    class Meta(UserAnnotationSchema.Meta):
        target = ValidateUserIdentity


class RequestUserIdentityValidationSchema(UserAnnotationSchema):
    """Schema to request identity validation to external resources."""

    face_id = fields.Str(dump_to='token_face_image')

    class Meta(UserAnnotationSchema.Meta):
        target = RequestUserIdentityValidation


class RequestSignUpStageByUserId(UserAnnotationSchema):
    """Schema to get a sign up stage by its user id."""

    class Meta(UserAnnotationSchema.Meta):
        target = GetSignUpStageByUserId


class GetServiceAgreementRequest(UserAnnotationSchema):
    """Schema for Filter ServiceAgreement deserialization."""

    class Meta(UserAnnotationSchema.Meta):
        """Configure the Device as the target of the schema."""

        target = GetServiceAgreement
        register_as_scheme = True


class ResponseAnnotationSchema(UserAnnotationSchema):
    """Handle the content of a response.

    resolving the hipermedia and the partial content errors list.
    """

    def __init__(
        self,
        *args,
        url_resolver: Optional[Callable] = None,
        **kwargs
    ):
        """Invoke init functionallity."""
        super().__init__(*args, **kwargs)
        self.url_resolver = url_resolver

    def load(self, *args, **kwargs):
        """Not implemented method to this function."""
        raise TypeError('ResponseAnnotationSchema can only dump.')

    def dump(
        self,
        data,
        errors: List[Exception] = [],
        many: bool = False,
        **kwargs
    ) -> dict:
        """Wrap the default behavior of dump to add collected errors list."""
        result = super().dump(data, many, **kwargs)
        content = {
            'data': result.data,
            'hyper': self.hyper(result.data),
        }
        if errors:
            content['errors'] = ErrorSchema(many=True).dump(errors).data
        return MarshalResult(content, result.errors)

    def hyper(self, data) -> dict:
        """Rewrite this method to generate the hyper response attribute.

        hyper is a shorts for hypermedia (HATEOAS).
        """
        return {}


class GetServiceAgreementResponse(UserAnnotationSchema):
    """Schema for Filter ServiceAgreement deserialization."""

    business_model = EnumField(states.BusinessModel, required=True)
    legal_validation_config = fields.List(fields.Str, missing=[], default=[])
    id = fields.Integer(dump_to='service_agreement_id')

    class Meta(UserAnnotationSchema.Meta):
        """Configure the Device as the target of the schema."""

        target = ServiceAgreement


class GetIdentityValidationSchema(UserAnnotationSchema):
    """Schema for requesting the user's identity validation result."""

    class Meta(UserAnnotationSchema.Meta):
        target = GetIdentityValidation


class PostIdentityValidationResponseSchema(UserAnnotationSchema):
    """Schema for identity-validation-svc response after performing a request."""

    class Meta(UserAnnotationSchema.Meta):
        target = PerformIdentityValidationResponse


class UpdateLegalValidationRequest(UserAnnotationSchema):
    """Schema for UpdateLegalValidation deserialization."""

    user_id = fields.UUID(load_only=True)
    pep_data = fields.Dict(required=False)

    class Meta(UserAnnotationSchema.Meta):
        """Configure the Device as the target of the schema."""

        target = UpdateLegalValidation
        register_as_scheme = True

    @post_dump
    def delete_none_fields(self, data: Dict):
        """Delete unused fields."""
        if 'pep_data' in data:
            if data['pep_data'] is None:
                data.pop('pep_data')
        return data


class UpdateLegalValidationResponse(UserAnnotationSchema):
    """Schema for UpdateLegalValidation serialization."""

    user_id = fields.UUID()

    class Meta(UserAnnotationSchema.Meta):
        """Configure the Device as the target of the schema."""

        register_as_scheme = True


class CreateCustomerRequestSchema(Schema):
    """Serialize request to create a customer."""

    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    gender = fields.String(required=True)
    dni = fields.String(required=True)
    cuil = fields.String(required=True)

    @post_dump
    def __nest_identifications(self, data: dict) -> dict:
        data['identifications'] = {
            'dni': data.pop('dni'),
            'cuil': data.pop('cuil'),
        }
        return data

    @post_dump
    def __nest_legal_name(self, data: dict) -> dict:
        data['legal_name'] = {
            'first_name': data.pop('first_name'),
            'last_name': data.pop('last_name'),
        }
        return data


class ConfirmIdentityResponseSchema(Schema):
    """Deserialize the response after confirmation of user's identity."""

    user_id = fields.UUID(required=True)


class CreateCustomerResponseSchema(Schema):
    """Deserialize the response after customer creation."""

    id = fields.UUID(required=True)


class ConfirmIdentitySchema(UserAnnotationSchema):
    """Deserialize the identity confirmation request."""

    class Meta(UserAnnotationSchema.Meta):
        target = ConfirmIdentity
