from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from users.core.actions import RequestUserIdentityValidation
from users.core.models import (
    Address,
    ContactMethod,
    ContactMethodType,
    Customer,
    Identity,
    ServiceAgreement,
    SignUp,
    User,
)
from users.core.models.states import BusinessModel


@dataclass
class UserRepository(ABC):
    """Represent an abstraction of the user repository."""

    @abstractmethod
    def save(self, user: User) -> None:
        """Persist a user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User:
        """Get a user by its id."""
        pass

    @abstractmethod
    def get_by_customer_and_business_model(
        self,
        customer_id: UUID,
        business_model: BusinessModel,
    ) -> Optional[User]:
        """Get a user by its business model."""
        pass

    @abstractmethod
    def get_by_customer_and_service_agr_id(
        self,
        customer_id: UUID,
        service_agr_id: int
    ) -> Optional[User]:
        """Get a user by its service agreement id."""
        pass

    @abstractmethod
    def get_by_service_agr_id_and_email(
        self,
        service_agr_id: int,
        email: str
    ) -> Optional[User]:
        """Get a user or none by its svc agreement id and email."""
        pass


@dataclass
class ContactMethodTypeRepository(ABC):
    """Represent an abstraction of the contact method types repository."""

    @abstractmethod
    def get(self, description: str) -> ContactMethodType:
        """Get a contact method type by its description."""
        pass


@dataclass
class SignUpRepository(ABC):
    """Represent an abstraction of the sign up repository."""

    @abstractmethod
    def get(self, sign_up_id: UUID) -> SignUp:
        """Get a sign up object by its primary key."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: UUID) -> SignUp:
        """Get a sign up object by its user id."""
        pass

    @abstractmethod
    def save(self, sign_up: SignUp) -> None:
        """Persist a SignUp object."""
        pass


@dataclass
class CustomerRepository(ABC):
    """Represent an abstraction of the customer repository."""

    @abstractmethod
    def get_by_id(self, customer_id: UUID) -> Customer:
        """Get a customer by its id."""
        pass

    @abstractmethod
    def list_by_dni(self, dni: str) -> List[Customer]:
        """List customers by their dni."""
        pass

    @abstractmethod
    def list_by_cuil(self, cuil: str) -> List[Customer]:
        """List customers by their cuil."""
        pass

    @abstractmethod
    def update_legal_validation(self, customer_id: UUID) -> None:
        """Update a legal validation."""
        pass

    @abstractmethod
    def create(self, from_identity: Identity) -> UUID:
        """Create a customer and return its ID."""


@dataclass
class ContactMethodRepository(ABC):
    """Represent an abstraction of the contact method repository."""

    @abstractmethod
    def get_by_type_and_value(
        self,
        type_: str,
        value: str,
        user_id: UUID,
    ) -> Optional[ContactMethod]:
        """Get a contact method or none by its value, type and user_id."""
        pass

    @abstractmethod
    def get(self, contact_method_id: UUID) -> ContactMethod:
        """Retrieve a contact method object by its primary key."""
        pass

    @abstractmethod
    def save(self, contact_method: ContactMethod) -> None:
        """Create a contact method."""
        pass

    @abstractmethod
    def get_by_token(self, token: str) -> Optional[ContactMethod]:
        """Get a contact method or none by its validation token value."""
        pass


@dataclass
class ServiceAgreementRepository(ABC):
    """Represent a contract interface for the service agreement repository."""

    @abstractmethod
    def save(self, service_agreement: ServiceAgreement) -> None:
        """Save a new service agreement instance."""
        pass

    @abstractmethod
    def get(self, id: int) -> ServiceAgreement:
        """Retrieve a service agreement object by its primary key."""
        pass


class IdentityValidationRepository(ABC):
    """Represent an interface for identity validation operations."""

    @abstractmethod
    def validate_identity(
        self,
        data: RequestUserIdentityValidation
    ) -> Optional[UUID]:
        """Perform identity validation."""

    @abstractmethod
    def get_identity_by_user_id(
        self,
        user_id: UUID
    ) -> Optional[Identity]:
        """Get an identity by its user ID."""

    @abstractmethod
    def confirm_identity(self, user_id: UUID) -> UUID:
        """Confirm user's identity."""


class AddressRepository(ABC):
    """Represent a contract to interact with address operations."""

    @abstractmethod
    def list(self, user_id: UUID) -> List[Address]:
        """Get user addresses."""
