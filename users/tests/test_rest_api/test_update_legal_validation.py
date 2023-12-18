from http import HTTPStatus

import responses
from users.core.models.locals import SignUp
from users.core.models.states import SignUpStage

from users.tests.mock_factory import CUSTOMER_ID, USER_ID, customer_factory_mock, user_factory_mock
from users.tests.test_rest_api import ApiLayerTestCase


class UpdateLegalValidationIdentity(ApiLayerTestCase):

    def setUp(self):
        super().setUp()
        self.command_bus = self.container.command_bus()
        self.customer = customer_factory_mock()
        self.user = user_factory_mock(
            contact_methods=[]
        )
        self.sign_up_repo = self.container.sign_up_repo()
        self.user_repo = self.container.user_repo()
        self.user_repo.save(self.user)
        self.url = self.container.config.customer_api_url()
        self.customer_id = CUSTOMER_ID
        self.user_id = USER_ID
        self.expected_sign_up = SignUp(
            stage=SignUpStage.IDENTITY_VALIDATION,
            user_id=self.user_id
        )

    @responses.activate
    def test_update_legal_validation_success(self):
        expected_result = {
            'data': {
                'user_id': str(self.user_id)
            },
            'hyper': {
                f'/users/signup/{self.user_id}/legal_validation': ['PATCH']
            }
        }

        request_payload = {
            "pep": False,
            "so": False,
            "facta": False,
            "occupation_id": "55806ed2-a714-493e-9e27-73c409b2b180",
            "relationship": "MARRIED"
        }
        responses.add(
            responses.PATCH,
            f'{self.url}/v1/customers/{str(self.customer_id)}/legal_validation',
            json={
                'data': {
                    'id': f'{self.customer_id}'
                },
            },
            status=HTTPStatus.OK
        )
        self.sign_up_repo.save(self.expected_sign_up)

        response = self.client.patch(
            f'{self.root_endpoint}/signup/{self.user_id}/legal_validation',
            json=request_payload
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_result

    @responses.activate
    def test_update_legal_validation_with_pep_data_success(self):
        expected_result = {
            'data': {
                'user_id': str(self.user_id)
            },
            'hyper': {
                f'/users/signup/{self.user_id}/legal_validation': ['PATCH']
            }
        }

        request_payload = {
            "pep": True,
            "pep_data": {
                "link": False,
                "type": "string",
                "name": "string",
                "start": "1981-01-05"
            },
            "so": False,
            "facta": False,
            "occupation_id": "55806ed2-a714-493e-9e27-73c409b2b180",
            "relationship": "MARRIED"
        }
        responses.add(
            responses.PATCH,
            f'{self.url}/v1/customers/{str(self.customer_id)}/legal_validation',
            json={
                'data': {
                    'id': f'{self.customer_id}'
                },
            },
            status=HTTPStatus.OK
        )
        self.sign_up_repo.save(self.expected_sign_up)

        response = self.client.patch(
            f'{self.root_endpoint}/signup/{self.user_id}/legal_validation',
            json=request_payload
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_result

    @responses.activate
    def test_update_legal_validation_fail_occupation_no_exist(self):
        expected_result = {
            'error': {
                'code': 'NB-ERROR-01001',
                'message': 'Entity not Found <Occupation>'
            }
        }

        request_payload = {
            "pep": True,
            "pep_data": {
                "link": False,
                "type": "string",
                "name": "string",
                "start": "1981-01-05"
            },
            "so": False,
            "facta": False,
            "occupation_id": "55806ed2-a714-493e-9e27-73c409b2b180",
            "relationship": "MARRIED"
        }
        responses.add(
            responses.PATCH,
            f'{self.url}/v1/customers/{str(self.customer_id)}/legal_validation',
            json={
                "error": {
                    "message": "Entity not Found <Occupation>",
                    "code": "NB-ERROR-01001"
                }
            },
            status=HTTPStatus.NOT_FOUND
        )
        response = self.client.patch(
            f'{self.root_endpoint}/signup/{self.user_id}/legal_validation',
            json=request_payload
        )
        assert response.status_code == HTTPStatus.FAILED_DEPENDENCY
        assert response.json() == expected_result

    def test_update_legal_validation_fail_user_no_exist(self):
        expected_result = {'error': {'code': 'NB-ERROR-00401', 'message': 'Entity Not Found <User>'}}
        request_payload = {
            "pep": True,
            "pep_data": {
                "link": False,
                "type": "string",
                "name": "string",
                "start": "1981-01-05"
            },
            "so": False,
            "facta": False,
            "occupation_id": "55806ed2-a714-493e-9e27-73c409b2b180",
            "relationship": "MARRIED"
        }
        response = self.client.patch(
            f'{self.root_endpoint}/signup/05edf610-9a55-42e8-b917-80aa32e6e262/legal_validation',
            json=request_payload
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == expected_result
