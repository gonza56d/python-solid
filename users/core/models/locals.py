from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID, uuid4

from users.core.exceptions import EntityNotFound, ResolutionError
from users.core.models import Customer, states
from users.core.models.compositions import AuditFields, ContactConfirmation


@dataclass
class ServiceAgreement:
    """Represent the service agreement model."""

    id: int
    business_model: states.BusinessModel


@dataclass
class ContactMethodType:
    """Represent the possible contact method types collection."""

    id: UUID = field(init=False, default_factory=uuid4)
    description: str


@dataclass
class SignUp:
    """Represent the currect sign up status for a new user."""

    id: UUID = field(init=False, default_factory=uuid4)
    stage: states.SignUpStage
    user_id: Optional[UUID] = None


@dataclass
class User:
    """Represent the base model for user data."""

    id: UUID = field(init=False, default_factory=uuid4)
    service_agr_id: int
    status: states.UserStatus
    contact_methods: List['ContactMethod'] = field(default_factory=list)
    user_addresses: List['UserAddress'] = field(default_factory=list)
    customer_id: Optional[UUID] = None
    terms_and_conditions: UUID = None
    address_id: Optional[UUID] = None
    customer: Optional[Customer] = None
    audit_fields: AuditFields = field(default=AuditFields())

    @property
    def email(self) -> str:
        """Try to return unique user email from its contact methods."""
        email_value = self.__get_contact_method(
            contact_method_type='EMAIL'
        )
        return email_value

    @property
    def phone_number(self) -> str:
        """Try to return unique user phone number from its contact methods."""
        phone_number_value = self.__get_contact_method(
            contact_method_type='PHONE'
        )
        return phone_number_value

    def __get_contact_method(self, contact_method_type: str) -> str:
        """
        Filter by type and try to get one contact method value from instance.

        Raises exceptions if there was more than one unique contact method or
        there was none.
        """
        results = list(filter(
            lambda cm: (
                cm.type.description == contact_method_type and cm.is_confirmed
            ), self.contact_methods
        ))

        if len(results) > 1:
            raise ResolutionError(contact_method_type, self.id)

        if not results:
            raise EntityNotFound(ContactMethod)

        return results[0].value


@dataclass
class ContactMethod:
    """Represent the base model for contact method."""

    id: UUID = field(init=False, default_factory=uuid4)
    type: ContactMethodType
    value: str
    contact_confirmation: ContactConfirmation
    user_id: Optional[UUID] = None
    audit_fields: AuditFields = field(default=AuditFields())

    @property
    def is_confirmed(self) -> bool:
        """Evaluate contact confirmation date.

        Return true if confirmation date is not None.
        """
        return self.contact_confirmation.confirmed_at is not None


@dataclass
class SavePhoneConfirmation:
    """Represent the response for saving phone confirmation."""

    pass


@dataclass
class UserAddress:
    """Collection with user addresses."""

    user_id: UUID
    address_id: UUID
    type: str = 'ONBOARDING'
    priority: Optional[int] = None
    audit_fields: AuditFields = field(default=AuditFields())
