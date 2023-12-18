from typing import List
from uuid import UUID

from nwrest import RequestBuilder
from requests import HTTPError, Response

from users.api.providers import RestApiCCIDProvider
from users.core.actions import UpdateLegalValidation
from users.core.exceptions import DependencyError
from users.core.models import Customer, Identity
from users.core.repositories import CustomerRepository
from users.odm.schemas import (
    CreateCustomerRequestSchema,
    CreateCustomerResponseSchema,
    CustomerResource,
    UpdateLegalValidationRequest,
)


class CustomerHttpRepository(CustomerRepository):
    """Access to elements of the external Customer collection.

    Uses http requests.
    """

    def __init__(
        self,
        customer_api_url: str,
        ccid_provider: RestApiCCIDProvider
    ):
        """Initialize this repository with the proper request builder."""
        self.request_builder = RequestBuilder(base_url=customer_api_url)
        self.request_builder\
            .version('v1')\
            .root('customers')\
            .set_ccid_provider(ccid_provider)
        self.schema = CustomerResource

    def __handle_http_error(self, response: Response):
        data = response.json()
        error = data.get('error')
        raise DependencyError(error.get('code'), error.get('message'))

    def get_by_id(self, customer_id: UUID) -> Customer:
        """Get a customer by its id value."""
        with self.request_builder as request:
            response = request.get(f'{str(customer_id)}')

        json_data = response.json()['data']
        deserialized_customer = self.schema().load(json_data).data

        return deserialized_customer

    def list_by_dni(self, dni: str) -> List[Customer]:
        """List customers by its cuil value."""
        with self.request_builder as request:
            response = request.get(params={'identity_dni': dni})

        json_data = response.json()['data']
        deserialized_customer_list = self.schema()\
            .load(json_data, many=True)\
            .data

        return deserialized_customer_list

    def list_by_cuil(self, cuil: str) -> List[Customer]:
        """List customers by its cuil value."""
        with self.request_builder as request:
            response = request.get(params={'identity_cuil': cuil})

        json_data = response.json()['data']
        deserialized_customer_list = self.schema()\
            .load(json_data, many=True)\
            .data

        return deserialized_customer_list

    def update_legal_validation(self, action: UpdateLegalValidation) -> None:
        """Update a legal validation."""
        try:

            payload = UpdateLegalValidationRequest().dump(action).data
            self.request_builder.patch(
                f'{str(action.customer_id)}/legal_validation',
                data=payload
            )
        except HTTPError as err:
            self.__handle_http_error(err.response)

    def create(self, from_identity: Identity) -> UUID:
        """Create a new customer from the obtained identity."""
        request_data = CreateCustomerRequestSchema().dump(from_identity).data
        with self.request_builder as request:
            response = request.post(data=request_data)

        json_data = response.json()['data']
        data = CreateCustomerResponseSchema().load(json_data).data
        return data['id']
