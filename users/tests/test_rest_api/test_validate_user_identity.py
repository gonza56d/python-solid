from http import HTTPStatus
from uuid import uuid4

import responses
from parameterized import parameterized

from users.core.models import SignUp
from users.core.models.states import SignUpStage, UserStatus
from users.tests.mock_factory import user_factory_mock
from users.tests.test_rest_api import ApiLayerTestCase


class ValidateUserIdentity(ApiLayerTestCase):

    def setUp(self):
        super().setUp()
        self.container = self.container
        self.identity_validation_ep = self.container.config.identity_validation_svc_url()
        self.user = user_factory_mock(
            status=UserStatus.PENDING_VALIDATION,
            contact_methods=[]
        )
        user_repo = self.container.user_repo()
        user_repo.save(self.user)
        sign_up = SignUp(
            stage=SignUpStage.IDENTITY_VALIDATION,
            user_id=self.user.id
        )
        self.container.sign_up_repo().save(sign_up)

    @responses.activate
    def test_validate_user_identity_sucess(self):
        user_id = self.user.id
        expected_result = {
            'response': {
                'data': {
                    'user_id': str(user_id)
                },
                'hyper': {
                    f'/v2/users/signup/{user_id}/identity_validation': ['GET']
                }
            },
            'status': HTTPStatus.CREATED
        }

        request_payload = {
            'ocr': 'some tokenized ocr',
            'selfie': 'some selfie data',
            'face_id': 'some face_id data',
            'base64_front': 'random',
            'base64_selfie': 'data',
            'base64_back': 'here',
        }
        responses.add(
            responses.POST,
            f'{self.identity_validation_ep}/v1/identity-validations',
            json={
                'data': {'user_id': str(user_id)},
                'hyper': {
                    f'/v1/identity-validations/{user_id}/': ['GET']
                }
            }
        )
        response = self.client.post(
            f'{self.root_endpoint}/signup/{user_id}/identity_validation',
            json=request_payload
        )

        assert {
            'response': response.json(),
            'status': response.status_code
        } == expected_result

    @responses.activate
    def test_validate_user_identity_error(self):
        expected_result = {
            'response': {},
            'status_code': HTTPStatus.PARTIAL_CONTENT
        }

        user_id = self.user.id
        request_payload = {
            'ocr': 'some tokenized ocr',
            'selfie': 'some selfie data',
            'face_id': 'some face_id data',
            'base64_front': 'random',
            'base64_selfie': 'data',
            'base64_back': 'here',
        }
        responses.add(
            responses.POST,
            f'{self.identity_validation_ep}/v1/identity-validations',
            json={},
            status=HTTPStatus.PARTIAL_CONTENT
        )
        response = self.client.post(
            f'{self.root_endpoint}/signup/{user_id}/identity_validation',
            json=request_payload
        )

        assert {
            'response': response.json(),
            'status_code': response.status_code,
        } == expected_result

    @parameterized.expand([('sent',), ('not_sent',)])
    @responses.activate
    def test_perform_identity_validation_exceeded_attempts_view(
        self,
        ticket_result: str
    ):
        possible_results = {
            'sent': {
                'response': {
                    "error": {
                        "message": "Number of identity validation attempts exceeded. "
                                   "Ticket sent: True.",
                        "code": "NB-ERROR-00851"
                    }
                },
                'status': HTTPStatus.BAD_REQUEST
            },
            'not_sent': {
                'response': {
                    "error": {
                        "message": "Number of identity validation attempts exceeded. "
                                   "Ticket sent: False.",
                        "code": "NB-ERROR-00850"
                    }
                },
                'status': HTTPStatus.BAD_REQUEST
            }
        }
        expected_result = possible_results[ticket_result]

        responses.add(
            responses.POST,
            f'{self.identity_validation_ep}/v1/identity-validations',
            json=expected_result['response'],
            status=expected_result['status'],
        )
        request_payload = {
            'ocr': 'some tokenized ocr',
            'selfie': 'some selfie data',
            'face_id': 'some face_id data',
            'base64_front': 'random',
            'base64_selfie': 'data',
            'base64_back': 'here',
        }
        response = self.client.post(
            f'{self.root_endpoint}/signup/{self.user.id}/identity_validation',
            json=request_payload
        )

        assert {
            'response': response.json(),
            'status': response.status_code,
        } == expected_result
