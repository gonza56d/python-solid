import os

from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from dependency_injector.wiring import inject, Provide
import jwt

from users.core.models import (
    ContactMethod,
    Customer,
    Identification,
    ServiceAgreement,
    User, Identity,
)
from users.core.models.compositions import AuditFields, ContactConfirmation
from users.containers import UserContainer
from users.core.repositories import ContactMethodTypeRepository
from users.core.models.states import (
    BusinessModel,
    ContactConfirmationType,
    UserStatus
)


USER_ID = UUID('0ab11811-e787-4d38-87cf-133db12172ea')
CUSTOMER_ID = UUID('c2a153a6-4a1b-4447-92c2-d89d81f13e8e')
CUSTOMER_NATIONALITY_ID = UUID('b0ebd9f8-a81d-4a25-97e5-c854a86e6b17')
TEST_ENV_VARS = {
    'db_uri': os.environ.get('DB_URI'),
    'customer_api_url': os.environ.get('CUSTOMER_API_URL'),
    'broker_url': os.environ.get('BROKER_URL'),
    'jwt_secret': os.environ.get('JWT_SECRET'),
    'contact_confirmation_expiration_timedelta': os.environ.get(
        'CONTACT_CONFIRMATION_EXPIRATION_TIMEDELTA'
    ),
    'identity_validation_svc_url': os.environ.get('IDENTITY_VALIDATION_SVC_URL'),
    'merlin_api_url': os.environ.get('MERLIN_API_URL'),
}


def audit_fields_factory_mock(**kwargs) -> AuditFields:
    default_kwargs = {
        'created_by': None,
        'created_date': datetime(2022, 2, 22, 22, 22, 22),
        'modified_by': None,
        'modified_date': datetime(2022, 2, 22, 22, 22, 22),
        'deleted_by': None,
        'deleted_date': None
    }
    default_kwargs.update(kwargs)
    return AuditFields(**default_kwargs)


def ccid_provider_mock() -> UUID:
    return UUID('47063769-18c0-4601-9ea7-430b932d5565')


def contact_confirmation_factory_mock(
    user_id: str,
    contact_method_id: str,
    confirmed: bool,
    **kwargs
) -> ContactConfirmation:
    encoded_jwt = jwt.encode(
        {
            'user_id': str(user_id),
            'contact_method_id': str(contact_method_id)
        },
        os.environ.get('JWT_SECRET'),
        algorithm='HS256'
    )
    default_kwargs = {
        'type': ContactConfirmationType.TOKEN,
        'value': encoded_jwt,
        'created_at': datetime.now(),
        'expire_at': datetime.now() + timedelta(
            hours=int(
                os.environ.get('CONTACT_CONFIRMATION_EXPIRATION_TIMEDELTA')
            )
        ),
        'confirmed_at': datetime.now() if confirmed else None,
    }
    default_kwargs.update(kwargs)
    return ContactConfirmation(**default_kwargs)


def identification_factory_mock(type_: str, **kwargs) -> Identification:
    if type_ == 'DNI':
        default_kwargs = {
            'customer_identification_id': str(CUSTOMER_ID),
            'number': '12345678',
            'type': 'DNI',
            'created_at': datetime(2022, 2, 22, 22, 22, 22),
            'updated_at': datetime(2022, 2, 22, 22, 22, 22)
        }
    elif type_ == 'CUIL':
        default_kwargs = {
            'customer_identification_id': str(CUSTOMER_ID),
            'number': '20123456785',
            'type': 'CUIL',
            'created_at': datetime(2022, 2, 22, 22, 22, 22),
            'updated_at': datetime(2022, 2, 22, 22, 22, 22)
        }
    else:
        raise ValueError('type_ parameter must be CUIL or DNI')
    default_kwargs.update(kwargs)
    return Identification(**default_kwargs)


def customer_factory_mock(**kwargs) -> Customer:
    default_kwargs = {
        'id': CUSTOMER_ID,
        'last_name': 'SAVINO',
        'gender': 'F',
        'birth_date': str(date(1900, 1, 1)),
        'identifications': {
            'DNI': identification_factory_mock(type_='DNI'),
            'CUIL': identification_factory_mock(type_='CUIL')
        },
        'first_name': 'SILVANA DEL CARMEN',
        'created_at': datetime(2022, 2, 22, 22, 22, 22),
        'updated_at': datetime(2022, 2, 22, 22, 22, 22),
        'status': 'ACTIVE',
        'nationality_id': CUSTOMER_NATIONALITY_ID
    }
    default_kwargs.update(kwargs)
    return Customer(**default_kwargs)


def identity_factory_mock(**kwargs) -> Identity:
    return Identity(
        first_name=kwargs.get('first_name', 'Cacho'),
        last_name=kwargs.get('last_name', 'De Codigo'),
        nationality=kwargs.get('nationality', 'Argentina'),
        gender=kwargs.get('gender', 'M'),
        dni=kwargs.get('dni', '12345678'),
        cuil=kwargs.get('cuil', '20123456785'),
        addresses=kwargs.get('addresses', []),
        birth_date=kwargs.get('birth_date', date(1996, 7, 1))
    )


def user_factory_mock(**kwargs) -> User:
    user_id = kwargs.pop('id', USER_ID)
    default_kwargs = {
        'customer_id': CUSTOMER_ID,
        'service_agr_id': 0,
        'status': UserStatus.ACTIVE,
        'customer': customer_factory_mock(),
        'contact_methods': [
            contact_method_factory_mock(type_='EMAIL', confirmed=True),
            contact_method_factory_mock(
                type_='EMAIL',
                value='mock2@email.com',
                confirmed=False
            ),
            contact_method_factory_mock(type_='PHONE', confirmed=True),
            contact_method_factory_mock(
                type_='PHONE',
                value='5412345670',
                confirmed=False
            ),
        ],
        'audit_fields': audit_fields_factory_mock()
    }
    default_kwargs.update(kwargs)
    user = User(**default_kwargs)
    user.id = user_id
    user.contact_methods.sort(key=lambda cm: str(cm.id))
    return user


@inject
def contact_method_factory_mock(
    type_: str,
    confirmed: bool,
    contact_method_type_repo: ContactMethodTypeRepository =
    Provide[UserContainer.contact_method_type_repo],
    **kwargs
) -> ContactMethod:
    contact_method_id = kwargs.pop('id', uuid4())
    user_id = kwargs.pop('user_id', USER_ID)
    contact_method_type = contact_method_type_repo.get(type_)
    if type_ == 'EMAIL':
        default_kwargs = {
            'user_id': user_id,
            'type': contact_method_type,
            'value': 'mock@email.com',
            'contact_confirmation': contact_confirmation_factory_mock(
                user_id=user_id,
                contact_method_id=contact_method_id,
                confirmed=confirmed,
            ),
            'audit_fields': audit_fields_factory_mock()
        }
    elif type_ == 'PHONE':
        default_kwargs = {
            'user_id': user_id,
            'type': contact_method_type,
            'value': '5412345678',
            'contact_confirmation': contact_confirmation_factory_mock(
                user_id=user_id,
                contact_method_id=contact_method_id,
                confirmed=confirmed,
            ),
            'audit_fields': audit_fields_factory_mock()
        }
    else:
        raise ValueError(
            'type_ argument must be a ContactMethodType description'
        )
    default_kwargs.update(kwargs)
    contact_method = ContactMethod(**default_kwargs)
    contact_method.id = contact_method_id
    return contact_method


def service_agreement_factory_mock(**kwargs) -> ServiceAgreement:
    id_ = kwargs.get('id', 0)
    business_model_ = kwargs.get('business_model', BusinessModel.NUBI)
    default_kwargs = {'id': id_, 'business_model': business_model_}
    default_kwargs.update(kwargs)
    return ServiceAgreement(**default_kwargs)
