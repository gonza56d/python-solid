from copy import deepcopy

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    composite,
    registry,
    relationship,
)

from users.core.models import (
    ContactMethod,
    ContactMethodType,
    ServiceAgreement,
    SignUp,
    User,
    UserAddress,
)
from users.core.models import states
from users.core.models.compositions import AuditFields, ContactConfirmation

metadata_obj = MetaData()

mapper_registry = registry(metadata_obj)


audit_fields = [
    Column('created_by', String(20)),
    Column('created_date', DateTime, nullable=False),
    Column('modified_by', String(20)),
    Column('modified_date', DateTime, nullable=False),
    Column('deleted_by', String(20)),
    Column('deleted_date', DateTime)
]

contact_confirmation = [
    Column(
        'confirmation_type',
        Enum(states.ContactConfirmationType),
        nullable=False
    ),
    Column('confirmation_value', String(), nullable=False),
    Column('confirmation_created_at', DateTime, nullable=False),
    Column('confirmation_expire_at', DateTime, nullable=False),
    Column('confirmation_confirmed_at', DateTime, nullable=True),
]


service_agreement_table = Table(
    'service_agreements',
    metadata_obj,
    Column('id', Integer(), nullable=False, primary_key=True),
    Column('business_model', Enum(states.BusinessModel), nullable=False)
)


sign_up_table = Table(
    'sign_ups',
    metadata_obj,
    Column('id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id')),
    Column('stage', Enum(states.SignUpStage), nullable=False),
    UniqueConstraint('user_id', name='u_sign_ups_user_id'),
)

user_table = Table(
    'users',
    metadata_obj,
    Column('id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('customer_id', UUID(as_uuid=True), nullable=True),
    Column(
        'service_agr_id',
        Integer(),
        ForeignKey('service_agreements.id'),
        nullable=False
    ),
    Column('status', Enum(states.UserStatus), nullable=False),
    Column('terms_and_conditions', UUID(as_uuid=True), nullable=True),
    Column('address_id', UUID(as_uuid=True), nullable=True),
    *deepcopy(audit_fields)
)

user_address_table = Table(
    'user_address',
    metadata_obj,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), nullable=False,
           primary_key=True),
    Column('address_id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('type', String(), nullable=False),
    Column('priority', Integer(), nullable=True),
    *deepcopy(audit_fields),
    UniqueConstraint('user_id', 'address_id', name='uc_user_addres'),
)

contact_method_type_table = Table(
    'contact_method_types',
    metadata_obj,
    Column('id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('description', String(), nullable=False),
    UniqueConstraint('description', name='u_contact_method_types_description'),
)

contact_method_table = Table(
    'contact_methods',
    metadata_obj,
    Column('id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id')),
    Column(
        'contact_method_type_id',
        UUID(as_uuid=True),
        ForeignKey('contact_method_types.id')
    ),
    Column('value', String(), nullable=False),
    UniqueConstraint(
        'user_id', 'contact_method_type_id', 'value', name='uix_1'
    ),
    *deepcopy(contact_confirmation),
    *deepcopy(audit_fields)
)

mapper_registry.map_imperatively(
    User,
    user_table,
    properties={
        'contact_methods': relationship(
            ContactMethod,
            lazy='joined',
            order_by='asc(ContactMethod.id)'
        ),
        'user_addresses': relationship(
            UserAddress,
            lazy='joined'
        ),
        'audit_fields': composite(
            AuditFields,
            user_table.c.created_by,
            user_table.c.created_date,
            user_table.c.modified_by,
            user_table.c.modified_date,
            user_table.c.deleted_by,
            user_table.c.deleted_date,
        )
    }
)

mapper_registry.map_imperatively(
    UserAddress,
    user_address_table,
    properties={
        'audit_fields': composite(
            AuditFields,
            user_address_table.c.created_by,
            user_address_table.c.created_date,
            user_address_table.c.modified_by,
            user_address_table.c.modified_date,
            user_address_table.c.deleted_by,
            user_address_table.c.deleted_date,
        )
    }
)

mapper_registry.map_imperatively(
    ServiceAgreement,
    service_agreement_table
)

mapper_registry.map_imperatively(
    ContactMethodType,
    contact_method_type_table
)

mapper_registry.map_imperatively(
    ContactMethod,
    contact_method_table,
    properties={
        'type': relationship(ContactMethodType, lazy='joined'),
        'contact_confirmation': composite(
            ContactConfirmation,
            contact_method_table.c.confirmation_type,
            contact_method_table.c.confirmation_value,
            contact_method_table.c.confirmation_created_at,
            contact_method_table.c.confirmation_expire_at,
            contact_method_table.c.confirmation_confirmed_at,
        ),
        'audit_fields': composite(
            AuditFields,
            contact_method_table.c.created_by,
            contact_method_table.c.created_date,
            contact_method_table.c.modified_by,
            contact_method_table.c.modified_date,
            contact_method_table.c.deleted_by,
            contact_method_table.c.deleted_date,
        )
    }
)

mapper_registry.map_imperatively(
    SignUp,
    sign_up_table
)
