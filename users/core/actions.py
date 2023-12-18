"""Microservice's DTOs."""

from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from users.core.models.states import (
    BusinessModel,
)


@dataclass
class ConfirmIdentity:
    """Action when user requests to confirm its identity and address."""

    user_id: UUID
    address_id: UUID


@dataclass
class CreateSignUp:
    """Represent the action of creating a new sign up process."""

    service_agr_id: int
    email: str


@dataclass
class CreateUser:
    """Represent the action of create a user."""

    customer_id: UUID
    service_agr_id: int


@dataclass
class GetUserById:
    """Represent the action of get a user by its id."""

    user_id: UUID
    fetch_customer: bool = True


@dataclass
class GetUserByDocument:
    """Represent the action of get a user by its document."""

    document_type: str
    document_value: str
    service_agr_id: Optional[int] = None
    business_model: Optional[BusinessModel] = None


@dataclass
class CreatePhoneConfirmation:
    """Represent the action to create an OTP code."""

    user_id: UUID
    phone_number: str


@dataclass
class ConfirmPhoneNumber:
    """Represent the action to confirm phone number."""

    user_id: UUID
    otp: str


@dataclass
class ValidateEmailConfirmationToken:
    """Represent the action of validating a email confirmation token."""

    token: str


@dataclass
class ValidateUserIdentity:
    """Users' identity validation request action."""

    user_id: UUID
    ocr: str
    selfie: str
    face_id: str
    base64_front: str
    base64_selfie: str
    base64_back: str


@dataclass
class RequestUserIdentityValidation(ValidateUserIdentity):
    """Model to request an indentity validation to identity validation implementation."""

    service_agreement_id: int


@dataclass
class GetSignUpStageByUserId:
    """Action to get a sign up instance from its user id."""

    user_id: UUID


@dataclass
class GetServiceAgreement:
    """Action to get service agreement."""

    service_agreement_id: int


@dataclass
class GetIdentityValidation:
    """Action to get an identity validation."""

    user_id: UUID


@dataclass
class UpdateLegalValidation:
    """Represent the action of update a legal validation."""

    user_id: UUID
    pep: bool
    so: bool
    facta: bool
    occupation_id: UUID
    relationship: str
    customer_id: Optional[UUID] = None
    pep_data: Optional[Dict] = None


@dataclass
class GetUserContactMethods:
    """Action to get a list with the user's contact methods."""

    user_id: UUID
