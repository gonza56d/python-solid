from http import HTTPStatus
from typing import Optional
from uuid import UUID

from nwrest import RequestBuilder
from nwrest.exceptions import PropagableHttpError
from requests import HTTPError

from users.api.providers import RestApiCCIDProvider
from users.core.actions import RequestUserIdentityValidation
from users.core.exceptions import (
    AttemptsExceededError,
    IdentityDataError,
    UserIdentityMinorError,
    UserIdentityTeenPartialError,
)
from users.core.models import (
    Identity,
    PerformIdentityValidationResponse
)
from users.core.repositories import IdentityValidationRepository
from users.odm.schemas import (
    ConfirmIdentityResponseSchema,
    IdentitySchema,
    PostIdentityValidationResponseSchema,
    RequestUserIdentityValidationSchema,
)


class IdentityValidationHttpRepository(IdentityValidationRepository):
    """Access to identity validation operations by HTTP.

    Connect with Nubi's identity validation microservice.
    """

    def __init__(
        self,
        identity_validation_svc_url: str,
        ccid_provider: RestApiCCIDProvider
    ):
        """Initialize repo with request builder."""
        self.request_builder = RequestBuilder(base_url=identity_validation_svc_url)
        self.request_builder\
            .version('v1')\
            .root('identity-validations')\
            .set_ccid_provider(ccid_provider)\
            .set_error_handler(self.__identity_validation_error_handler)

    def __identity_validation_error_handler(
        self,
        error: HTTPError,
        propagable_error: Optional[PropagableHttpError] = None
    ):
        if propagable_error is not None:

            code = propagable_error.code
            message = propagable_error.message
            status_code = propagable_error.status_code

            if code == 'NB-ERROR-00850' or code == 'NB-ERROR-00851':
                raise AttemptsExceededError(code, message, status_code)

            if code == 'NB-ERROR-00860' or code == 'NB-ERROR-00861':
                raise IdentityDataError(code, message, status_code)

            if code == 'NB-ERROR-00802' and 'minor' in message:
                raise UserIdentityMinorError(code, message, status_code)

            raise propagable_error

        raise error

    def confirm_identity(self, user_id: UUID) -> UUID:
        """Handle identity confirmation with identity-validation-svc."""
        with self.request_builder as request:
            response = request.patch(f'{user_id}')

        json_data = response.json()['data']
        data = ConfirmIdentityResponseSchema().load(json_data).data
        return data['user_id']

    def validate_identity(
        self,
        data: RequestUserIdentityValidation
    ) -> Optional[UUID]:
        """Perform identity validation request and return result data."""
        serialized_data = RequestUserIdentityValidationSchema().dump(data).data

        with self.request_builder as request:
            response = request.post(data=serialized_data)

        errors = response.json().get('errors')
        if response.status_code == HTTPStatus.PARTIAL_CONTENT and not errors:
            return None

        json_data = response.json()['data']
        perform_identity_validation: PerformIdentityValidationResponse = \
            PostIdentityValidationResponseSchema()\
            .load(json_data)\
            .data

        if errors:
            if 'NB-ERROR-00852' in [error['code'] for error in errors]:
                raise UserIdentityTeenPartialError(perform_identity_validation.user_id)

        return perform_identity_validation.user_id

    def get_identity_by_user_id(
        self,
        user_id: UUID
    ) -> Optional[Identity]:
        """Get an identity by its user ID."""
        with self.request_builder as request:
            response = request.get(f'{user_id}')

        json_data = response.json()['data']
        deserialized_identity: Identity = IdentitySchema().load(json_data).data

        return deserialized_identity
