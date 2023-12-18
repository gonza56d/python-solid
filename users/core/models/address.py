from dataclasses import dataclass
from uuid import UUID


@dataclass
class Address:
    """Represent address entity."""

    address_id: UUID
    user_id: UUID
    status: str
    source: str
    street_name: str
    street_no: str
    street_intersection: str
    floor_no: str
    apartment_no: str
    city: str
    zip_code: str
    exteded_zip_code: str
    province_id: UUID
    country_id: UUID
