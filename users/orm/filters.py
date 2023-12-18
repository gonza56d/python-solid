from abc import ABC, abstractclassmethod
from typing import Optional

from sqlalchemy.orm import Query


class BaseFilter(ABC):
    """Filters base clase."""

    @abstractclassmethod
    def apply(self, query: Query):
        """Filter applying method."""
        raise NotImplementedError()


class FilterByInt(BaseFilter):
    """Filter by Int."""

    def __init__(self, property_name: int, value: Optional[int]):
        """Start with specific parameters."""
        self.property_name = property_name
        self.value = value

    def apply(self, query: Query):
        """Filter applying method."""
        if self.value is not None:
            query = query.filter(self.property_name == self.value)
        return query
