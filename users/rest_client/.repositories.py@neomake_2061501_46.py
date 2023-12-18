from typing import List
from uuid import UUID

from nwrest import RequestBuilder

from users.core.model import Customer
from users.core.repositories import CustomerRepository
from users.odm.schemas import CustomerResource


class CustomerHttpRepository(CustomerRepository):
    """Access to elements of the external Customer collection.

    Uses http requests.
    """

    def __init__(self, customer_api_url: str):
        """Initialize this repository with the proper request builder."""
        self.request_builder = RequestBuilder(base_url=customer_api_url)
        self.request_builder.version('v1').root('customers')
        self.customer_resource = CustomerResource()

    def get_by_id(self, customer_id: UUID) -> Customer:
        """Get a customer by its id value."""
        response = self.request_builder.get(
            f'{str(customer_id)}'
        )
        customer = self.customer_resource.load(response.json()).data
        return customer

    def list_by_dni(self, dni: str) -> List[Customer]:
        """List customers by its cuil value."""
        response = self.request_builder.get(f'?identity_dni={dni}')
        customer = self.customer_resource.load(
            response.json().get('data', []), many=True
        ).data
        return customer

    def list_by_cuil(self, cuil: str) -> List[Customer]:
        """List customers by its cuil value."""
        response = self.request_builder.get(f'?identity_cuil={cuil}')
        customer = self.customer_resource.load(
            response.json().get('data', []), many=True
        ).data
        return customer
