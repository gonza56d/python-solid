from enum import Enum


class BusinessModel(Enum):
    """Possible states for business model."""

    NUBI = 0
    NUBIZ = 1


class ContactConfirmationType(Enum):
    """Represent possible states for 'type' in ContactConfirmation model."""

    TOKEN = 'TOKEN'
    OTP = 'OTP'


class SignUpStage(Enum):
    """Represent possible states for 'stage' in SignUp model."""

    EMAIL_CONFIRMATION = 'EMAIL_CONFIRMATION'
    IDENTITY_VALIDATION = 'IDENTITY_VALIDATION'
    LEGAL_VALIDATION = 'LEGAL_VALIDATION'
    PHONE_CONFIRMATION = 'PHONE_CONFIRMATION'
    GENERATE_CREDENTIALS = 'GENERATE_CREDENTIALS'
    SIGN_UP_BLOCKED = 'SIGN_UP_BLOCKED'


class UserStatus(Enum):
    """Represent possible status types for a user."""

    PENDING_VALIDATION = 'PENDING_VALIDATION'
    VALIDATION_REJECTED = 'VALIDATION_REJECTED'
    BANNED = 'BANNED'
    BANNED_NOTIFIED = 'BANNED_NOTIFIED'
    VALIDATED = 'VALIDATED'
    ACTIVE = 'ACTIVE'
    BLOCKED = 'BLOCKED'
    PENDING_AUTHORIZATION = 'PENDING_AUTHORIZATION'
