from dataclasses import asdict
from http import HTTPStatus
from uuid import uuid4

import responses

from users.core.models import SignUp
from users.core.models.states import UserStatus, SignUpStage
from users.odm.schemas import AddressSchema
from users.tests.mock_factory import identity_factory_mock, user_factory_mock
from users.tests.test_rest_api import ApiLayerTestCase


class TestGetIdentityValidationViews(ApiLayerTestCase):

    def setUp(self):
        super().setUp()
        self.identity_validation_url = self.container\
            .config\
            .identity_validation_svc_url()\
            + '/v1/identity-validations'
        self.merlin_api_url = self.container\
            .config\
            .merlin_api_url()\
            + '/v1.5/address/user'
        user_id = uuid4()
        self.merlin_mock = self.MerlinMock(user_id)
        self.identity_validation_id = uuid4()
        self.existent_identity = identity_factory_mock()
        self.user = user_factory_mock(
            id=user_id,
            status=UserStatus.PENDING_VALIDATION,
            contact_methods=[]
        )
        self.get_identity_validation_url = (
            f'{self.identity_validation_url}/{self.user.id}'
        )
        self.container.user_repo().save(self.user)
        self.sign_up = SignUp(
            stage=SignUpStage.IDENTITY_VALIDATION, user_id=self.user.id
        )
        self.container.sign_up_repo().save(self.sign_up)

    @responses.activate
    def test_get_identity_validation_view_success(self):
        identity = asdict(self.existent_identity)
        identity['birth_date'] = str(identity['birth_date'])
        expected_response = {
            'data': {
                **identity,
                'addresses': {
                    element['address_id']: element
                    for element in self.merlin_mock.SUCCESSFUL_GET_RESPONSE
                }
            },
            'hyper': {
                f'/v2/users/signup/{self.user.id}/identity_validation': ['GET']
            }
        }
        expected_result = {
            'response': expected_response,
            'status': HTTPStatus.OK
        }

        responses.add(
            responses.GET,
            self.get_identity_validation_url,
            json={
                'data': identity,
                'hyper': {
                    "/v1/identity-validations"
                    f"/{self.identity_validation_id}": ["GET"]
                }
            }
        )
        responses.add(
            responses.GET,
            f'{self.merlin_api_url}/{self.user.id}',
            json=self.merlin_mock.SUCCESSFUL_GET_RESPONSE
        )

        response = self.client.get(
            f'{self.root_endpoint}/signup/{self.user.id}/identity_validation'
        )

        assert {
            'response': response.json(),
            'status': response.status_code
        } == expected_result

    @responses.activate
    def test_get_identity_validation_view_missing_addresses_partial_content(self):
        """
        Ensure that partial error response is returned when no addresses.

        - Given a get identity request.
        - When the address service doesn't find any address for the requested user.
        - Then a partial content response is returned.
        """
        identity = asdict(self.existent_identity)
        identity['birth_date'] = str(identity['birth_date'])
        expected_response = {
            'data': {
                **identity,
                'addresses': {}
            },
            'hyper': {
                f'/v2/users/signup/{self.user.id}/identity_validation': ['GET']
            },
            'errors': [{
                'code': 'NB-ERROR-00451',
                'message': 'Missing addresses. Must add a new address.'
            }]
        }
        expected_result = {
            'response': expected_response,
            'status': HTTPStatus.PARTIAL_CONTENT
        }

        responses.add(
            responses.GET,
            self.get_identity_validation_url,
            json={
                'data': identity,
                'hyper': {
                    "/v1/identity-validations"
                    f"/{self.identity_validation_id}": ["GET"]
                }
            }
        )
        responses.add(
            responses.GET,
            f'{self.merlin_api_url}/{self.user.id}',
            json={
                'message': 'Entity Not Found',
                'code': 'NB-ERROR-00401',
                'error': 'HTTP error'
            },
            status=HTTPStatus.NOT_FOUND
        )
        response = self.client.get(
            f'{self.root_endpoint}/signup/{self.user.id}/identity_validation'
        )

        assert {
            'response': response.json(),
            'status': response.status_code
        } == expected_result
