from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple
from uuid import UUID


@dataclass
class Identification:
    """Represent the base model for identification data."""

    number: str
    created_at: datetime
    customer_identification_id: UUID
    type: str
    updated_at: datetime


@dataclass
class Customer:
    """Represent the base model for customer data."""

    id: UUID
    last_name: str
    gender: str
    birth_date: str
    identifications: Dict[str, Identification]
    first_name: str
    created_at: datetime
    updated_at: datetime
    nationality_id: UUID
    status: Optional[str]

    @property
    def document_type(self) -> str:
        """Documentation type for the highest priority documentation."""
        ui = self.__get_unique_identification()
        return ui[0] if ui else None

    @property
    def document_number(self) -> str:
        """Documentation value for the highest priority documentation."""
        ui = self.__get_unique_identification()
        return ui[1].get('value') if ui else None

    def __get_unique_identification(self) -> Tuple[str, Dict[str, str]]:
        """Return the documentation object with highest priority found."""
        if 'CUIL' in self.identifications:
            return 'CUIL', self.identifications['CUIL']

        if 'DNI' in self.identifications:
            return 'DNI', self.identifications['DNI']
