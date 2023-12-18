from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

from . import states


@dataclass(frozen=True)
class CompositeType:
    """Base class for all the classes that declare a composite type."""

    def __new__(cls, *args, **kwargs):
        """
        Prevent this class to be instantiated by itself.

        Only classes inheriting CompositeType can be instantiated.
        """
        if cls is CompositeType:
            raise TypeError('This class cannot instantiate by itself.')
        return super().__new__(cls)

    def recreate(self, **new_attributes) -> 'CompositeType':
        """
        Recreate a new instance of the prototype with the updated state.

        Parameters
        ----------
        new_attributes: kwargs
            The attributes of the original instance that have changed values.

        Returns
        -------
        CompositeType:
            A new instance of the same object with the updated attr values.
        """
        attributes = asdict(self)
        attributes.update(new_attributes)

        return self.__class__(**attributes)


@dataclass(frozen=True)
class AuditFields(CompositeType):
    """Represent the base model for audit fields."""

    created_by: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    modified_by: Optional[str] = None
    modified_date: datetime = field(default_factory=datetime.now)
    deleted_by: Optional[str] = None
    deleted_date: Optional[datetime] = None

    def __composite_values__(self) -> tuple:
        """Return the state of the object as a tuple."""
        return (
            self.created_by, self.created_date, self.modified_by,
            self.modified_date, self.deleted_by, self.deleted_date
        )


@dataclass(frozen=True)
class ContactConfirmation(CompositeType):
    """Represent how a new user will confirm its provided contact method."""

    type: states.ContactConfirmationType
    value: str
    created_at: datetime
    expire_at: datetime
    confirmed_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Return true if the expired date is before today."""
        return self.expire_at < datetime.today() and self.confirmed_at is None

    @property
    def is_still_pending(self) -> bool:
        """
        Return true if the confirmation is still pending.

        Check that the confirmation date is None and it's not expired yet.
        """
        return self.expire_at >= datetime.today() and self.confirmed_at is None

    def __composite_values__(self) -> tuple:
        """Return the state of the object as a tuple."""
        return (
            self.type, self.value, self.created_at, self.expire_at,
            self.confirmed_at
        )
