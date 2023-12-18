from http import HTTPStatus
from unittest.mock import MagicMock

from users.tests.test_rest_api import ApiLayerTestCase


class TestGetUser(ApiLayerTestCase):

    def setUp(self) -> None:
        super().setUp()

    def test_get_service_agreement_by_id_success(self):
        response = self.client.get(
            f'{self.root_endpoint}/service-agreements/1'
        )
        expected_response = {
            "data": {
                "service_agreement_id": 1,
                "legal_validation_config": []
            }
            ,
            "hyper": {"": []}
        }
        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_response

    def test_get_service_agreement_by_id_error_invalid_type(self):
        response = self.client.get(
            f'{self.root_endpoint}/service-agreements/nubi'
        )
        expected_response = {
            "error": {
                "code": "NB-ERROR-00402",
                "message": {"service_agreement_id": ["Not a valid integer."]}
            }
        }
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == expected_response

    def test_get_service_agreement_no_exist(self):
        response = self.client.get(
            f'{self.root_endpoint}/service-agreements/11234'
        )
        expected_response = {
            'error': {'message': 'Entity Not Found <ServiceAgreement>', 'code': 'NB-ERROR-00401'}
        }
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == expected_response

    def test_get_service_agreement_fail_to_read(self):
        service_agreement_repo_mock = self.container.service_agreement_repo()
        service_agreement_repo_mock.session_factory = MagicMock()
        service_agreement_repo_mock.session_factory.side_effect = Exception()
        self.container.service_agreement_repo.override(
            service_agreement_repo_mock
        )
        response = self.client.get(
            f'{self.root_endpoint}/service-agreements/1'
        )
        expected_response = {
            "error": {
                "code": "NB-ERROR-00403",
                "message": "Storage Error"
            }
        }
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == expected_response
