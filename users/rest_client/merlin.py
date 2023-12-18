from http import HTTPStatus
from typing import List, Optional
from uuid import UUID

from nwrest import RequestBuilder
from nwrest.exceptions import PropagableHttpError
from requests import HTTPError

from users.api.providers import RestApiCCIDProvider
from users.core.exceptions import MissingAddressError
from users.core.models import Address
from users.core.repositories import AddressRepository
from users.odm.schemas import AddressSchema


class MerlinHttpRepository(AddressRepository):
    """Repository to interact with merlin-api under address contract."""

    def __init__(
        self,
        address_url: str,
        ccid_provider: RestApiCCIDProvider
    ):
        """Provide url to perform requests."""
        self.request_builder = RequestBuilder(base_url=address_url, version='v1.5')\
            .root('address')\
            .set_ccid_provider(ccid_provider)\
            .set_error_handler(self.__merlin_error_handler)
        self.schema = AddressSchema()

    def __merlin_error_handler(
            self,
            error: HTTPError,
            propagable_error: Optional[PropagableHttpError] = None
    ):
        json = error.response.json()
        status = error.response.status_code

        if json.get('code') == 'NB-ERROR-00401' and status == HTTPStatus.NOT_FOUND:
            raise MissingAddressError()

        raise error

    def list(self, user_id: UUID) -> List[Address]:
        """Retrieve a list of user's addresses from merlin-api."""
        with self.request_builder as request:
            response = request.get(f'user/{user_id}')

        addresses = self.schema.load(response.json(), many=True).data
        return addresses
