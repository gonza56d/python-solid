from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from uuid import UUID

from users.core.models import Address


@dataclass
class Identity:
    """Represent external identity model."""

    first_name: str
    last_name: str
    nationality: str
    gender: str
    dni: str
    cuil: str
    birth_date: date
    addresses: Optional[List[Address]] = field(default_factory=list)


@dataclass
class PerformIdentityValidationResponse:
    """IdentityValidation microservice response after performing a request."""

    user_id: UUID
