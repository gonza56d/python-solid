from http import HTTPStatus
from os import environ
from uuid import UUID

import responses
from parameterized import parameterized

from users.tests.test_rest_api import ApiLayerTestCase
from users.core.repositories import CustomerRepository
from users.core.models.states import UserStatus
from users.rest_client import CustomerHttpRepository
from users.tests.mock_factory import (
    ccid_provider_mock,
    contact_method_factory_mock,
    user_factory_mock,
)
from users.tests.seeders import seed_user
from users.tests.utils import TestUtils


class TestGetUser(ApiLayerTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.user_id = UUID('194f1762-9ae9-4e41-81db-5ee3848e97bf')
        self.customer_id = UUID('47495f69-0128-4327-8968-88f8aefe6f7c')
        self.user = user_factory_mock(
            id=self.user_id,
            customer_id=self.customer_id,
            status=UserStatus.ACTIVE,
            customer=None
        )

        contact_method_type_repo = self.container.contact_method_type_repo()
        type_email = contact_method_type_repo.get('EMAIL')
        type_phone = contact_method_type_repo.get('PHONE')
        for contact_method in self.user.contact_methods:
            contact_method.type = (
                type_email if '@' in contact_method.value else type_phone
            )

        user_repo = self.container.user_repo()
        user_repo.save(self.user)
        self.customer_url = environ.get(
            'CUSTOMER_API_URL', 'http://customer.api'
        )
        self.customer_repo: CustomerRepository = CustomerHttpRepository(
            self.customer_url,
            self.container.rest_api_ccid_provider()
        )
        self.cuil_number = '25123456785'
        self.dni_number = '12345678'
        self.customer_by_id_response = {
            'data': {
                "status": "ACTIVE",
                "gender": "M",
                "age_group": "ADULT",
                "occupation": {
                    "id": "df01ae0e-52c3-4b06-8255-6283731a6886",
                    "audit_fields": {
                        "created_by": None,
                        "modified_date": "2022-02-02T14:47:05.131559+00:00",
                        "deleted_by": None,
                        "deleted_date": None,
                        "created_date": "2022-02-02T14:47:05.131558+00:00",
                        "modified_by": None
                    },
                    "description": "Comerciante"
                },
                "audit_fields": {
                    "created_by": None,
                    "modified_date": "2022-01-19T00:00:00+00:00",
                    "deleted_by": None,
                    "deleted_date": None,
                    "created_date": "2022-01-19T00:00:00+00:00",
                    "modified_by": None
                },
                "nationality_id": "b0ebd9f8-a81d-4a25-97e5-c854a86e6b17",
                "birth_date": "1996-07-01",
                "relationship": "SINGLE",
                "legal_name": {
                    "first_name": "Guido",
                    "last_name": "Van Rossum"
                },
                "id": "47495f69-0128-4327-8968-88f8aefe6f7c",
                "identifications": {
                    "CUIL": {
                        "id": "d341cd53-f169-4c36-a7d0-82b206ae6f1b",
                        "value": "25123456785",
                        "audit_fields": {
                            "created_by": None,
                            "modified_date": "2022-02-22T22:22:22+00:00",
                            "deleted_by": None,
                            "deleted_date": None,
                            "created_date": "2022-02-22T22:22:22+00:00",
                            "modified_by": None
                        }
                    },
                    "DNI": {
                        "id": "907868d4-66a0-48dd-988e-b65765b556e5",
                        "value": "12345678",
                        "audit_fields": {
                            "created_by": None,
                            "modified_date": "2022-02-22T22:22:22+00:00",
                            "deleted_by": None,
                            "deleted_date": None,
                            "created_date": "2022-02-22T22:22:22+00:00",
                            "modified_by": None
                        }
                    }
                }
            },
            'hyper': {}
        }
        self.customer_filter_response = {
            'data': [{
                "status": "ACTIVE",
                "gender": "M",
                "age_group": "ADULT",
                "audit_fields": {
                    "created_by": None,
                    "modified_date": "2022-01-19T00:00:00+00:00",
                    "deleted_by": None,
                    "deleted_date": None,
                    "created_date": "2022-01-19T00:00:00+00:00",
                    "modified_by": None
                },
                "nationality_id": "b0ebd9f8-a81d-4a25-97e5-c854a86e6b17",
                "birth_date": "1996-07-01",
                "relationship": "SINGLE",
                "legal_name": {
                    "first_name": "Guido",
                    "last_name": "Van Rossum"
                },
                "occupation_id": "df01ae0e-52c3-4b06-8255-6283731a6886",
                "customer_id": "47495f69-0128-4327-8968-88f8aefe6f7c",
                "identifications": {
                    "CUIL": {
                        "id": "d341cd53-f169-4c36-a7d0-82b206ae6f1b",
                        "value": "25123456785",
                        "audit_fields": {
                            "created_by": None,
                            "modified_date": "2022-02-22T22:22:22+00:00",
                            "deleted_by": None,
                            "deleted_date": None,
                            "created_date": "2022-02-22T22:22:22+00:00",
                            "modified_by": None
                        }
                    },
                    "DNI": {
                        "id": "907868d4-66a0-48dd-988e-b65765b556e5",
                        "value": "12345678",
                        "audit_fields": {
                            "created_by": None,
                            "modified_date": "2022-02-22T22:22:22+00:00",
                            "deleted_by": None,
                            "deleted_date": None,
                            "created_date": "2022-02-22T22:22:22+00:00",
                            "modified_by": None
                        }
                    }
                }
            }],
            'hyper': {}
        }

    def test_status_success(self):
        response = self.client.get(f'{self.root_endpoint}/status')
        assert response.status_code == HTTPStatus.OK

    def test_get_user_by_id_bad_request(self):
        response = self.client.get(f'{self.root_endpoint}/byId/123')
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_user_by_id_not_found(self):
        expected_response_content = {
            'error': {
                'code': 'NB-ERROR-00401',
                'message': 'Entity Not Found <User>'
            }
        }
        response = self.client.get(
            f'{self.root_endpoint}/byId/194f1762-9ae9-4e41-81db-5ee3848e97b4'
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == expected_response_content

    @responses.activate
    def test_get_user_by_id_success(self):
        expected_customer_request_headers = {
            'X-Correlation-ID': '47063769-18c0-4601-9ea7-430b932d5565'
        }
        expected_response = {
            'data': {
                "lastName": "Van Rossum",
                "gender": "M",
                "documentType": "CUIL",
                "documentNumber": "25123456785",
                "mobileNumber": "5412345678",
                "type": 0,
                "birthDate": "1996-07-01",
                "identifications": [
                    {
                        'type': 'CUIL',
                        'number': '25123456785',
                        'customer_identification_id': str(self.customer_id),
                        'createdAt': '2022-02-22T22:22:22+00:00',
                        'updatedAt': '2022-02-22T22:22:22+00:00',
                    },
                    {
                        'type': 'DNI',
                        'number': '12345678',
                        'customer_identification_id': str(self.customer_id),
                        'createdAt': '2022-02-22T22:22:22+00:00',
                        'updatedAt': '2022-02-22T22:22:22+00:00',
                    },
                ],
                "firstName": "Guido",
                "createdAt": '2022-01-19T00:00:00+00:00',
                "email": self.user.email,
                "updatedAt": '2022-01-19T00:00:00+00:00',
                "status": "ACTIVE",
                'id': str(self.user_id),
                'nationality_id': 'b0ebd9f8-a81d-4a25-97e5-c854a86e6b17'
            },
            'hyper': {
                f'/v2/users/byId/{self.user_id}': ['GET'],
            }
        }

        responses.add(
            responses.GET,
            f'{self.customer_url}/v1/customers/{str(self.customer_id)}',
            json=self.customer_by_id_response,
            status=200
        )
        response = self.client.get(
            f'{self.root_endpoint}/byId/{str(self.user_id)}',
            headers={'X-Correlation-ID': str(ccid_provider_mock())}
        )
        customer_request_headers = responses.calls[0].request.headers

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_response
        assert customer_request_headers == expected_customer_request_headers

    @parameterized.expand([
        ('DNI', 'identity_dni', 'dni_number', 0),
        ('CUIL', 'identity_cuil', 'cuil_number', 0),
    ])
    @responses.activate
    def test_get_user_by_business_model_success(
        self,
        document_type,
        url_param,
        document_value,
        business_model
    ):
        expected_response = {
            "lastName": "Van Rossum",
            "gender": "M",
            "documentType": "CUIL",
            "documentNumber": "25123456785",
            "mobileNumber": "5412345678",
            "type": 0,
            "birthDate": "1996-07-01",
            "identifications": [
                {
                    'type': 'CUIL',
                    'number': '25123456785',
                    'customer_identification_id': str(self.customer_id),
                    'createdAt': '2022-02-22T22:22:22+00:00',
                    'updatedAt': '2022-02-22T22:22:22+00:00',
                },
                {
                    'type': 'DNI',
                    'number': '12345678',
                    'customer_identification_id': str(self.customer_id),
                    'createdAt': '2022-02-22T22:22:22+00:00',
                    'updatedAt': '2022-02-22T22:22:22+00:00',
                },
            ],
            "firstName": "Guido",
            "createdAt": '2022-01-19T00:00:00+00:00',
            "email": self.user.email,
            "updatedAt": '2022-01-19T00:00:00+00:00',
            "status": "ACTIVE",
            'id': str(self.user_id),
            'nationality_id': 'b0ebd9f8-a81d-4a25-97e5-c854a86e6b17'
        }

        document_values = {
            'dni_number': self.dni_number,
            'cuil_number': self.cuil_number
        }
        responses.add(
            responses.GET,
            f'{self.customer_url}/v1/customers?{url_param}='
            f'{document_values[document_value]}',
            json=self.customer_filter_response,
            status=200
        )
        response = self.client.get(
            f'{self.root_endpoint}/byDocument/{document_type}/'
            f'{document_values[document_value]}/businessModel/{business_model}'
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_response

    @parameterized.expand([
        ('DNI', 'identity_dni', 'dni_number', 1),
        ('CUIL', 'identity_cuil', 'cuil_number', 1),
    ])
    @responses.activate
    def test_get_user_by_business_model_fail_by_business_model(
        self,
        document_type,
        url_param,
        document_value,
        business_model
    ):
        expected_response = {}

        document_values = {
            'dni_number': self.dni_number,
            'cuil_number': self.cuil_number
        }
        responses.add(
            responses.GET,
            f'{self.customer_url}/v1/customers?{url_param}='
            f'{document_values[document_value]}',
            json=self.customer_filter_response,
            status=200
        )
        response = self.client.get(
            f'{self.root_endpoint}/byDocument/{document_type}/'
            f'{document_values[document_value]}/businessModel/{business_model}'
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_response

    @parameterized.expand([
        ('DNI', 'identity_dni', 'dni_number'),
        ('CUIL', 'identity_cuil', 'cuil_number'),
    ])
    @responses.activate
    def test_get_user_by_document_endpoint_success(
        self,
        document_type,
        url_param,
        document_value
    ):
        svc_agr_id = 0
        expected_response = {
            "lastName": "Van Rossum",
            "gender": "M",
            "documentType": "CUIL",
            "documentNumber": "25123456785",
            "mobileNumber": "5412345678",
            "type": 0,
            "birthDate": "1996-07-01",
            "identifications": [
                {
                    'type': 'CUIL',
                    'number': '25123456785',
                    'customer_identification_id': str(self.customer_id),
                    'createdAt': '2022-02-22T22:22:22+00:00',
                    'updatedAt': '2022-02-22T22:22:22+00:00',
                },
                {
                    'type': 'DNI',
                    'number': '12345678',
                    'customer_identification_id': str(self.customer_id),
                    'createdAt': '2022-02-22T22:22:22+00:00',
                    'updatedAt': '2022-02-22T22:22:22+00:00',
                },
            ],
            "firstName": "Guido",
            "createdAt": '2022-01-19T00:00:00+00:00',
            "email": self.user.email,
            "updatedAt": '2022-01-19T00:00:00+00:00',
            "status": "ACTIVE",
            'customer_status': 'ACTIVE',
            'nationality_id': 'b0ebd9f8-a81d-4a25-97e5-c854a86e6b17'
        }

        document_values = {
            'dni_number': self.dni_number,
            'cuil_number': self.cuil_number
        }
        responses.add(
            responses.GET,
            f'{self.customer_url}/v1/customers?{url_param}='
            f'{document_values[document_value]}',
            json=self.customer_filter_response,
            status=200
        )
        response = self.client.get(
            f'{self.root_endpoint}/byDocument/{document_type}/'
            f'{document_values[document_value]}/'
            f'{svc_agr_id}'
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_response

    @parameterized.expand([
        ('DNI', 'identity_dni', 'dni_number'),
        ('CUIL', 'identity_cuil', 'cuil_number'),
    ])
    @responses.activate
    def test_get_user_by_document_user_not_found(
        self,
        document_type,
        url_param,
        document_value
    ):
        wrong_svc_agr_id = 27
        expected_response_content = {}
        document_values = {
            'dni_number': self.dni_number,
            'cuil_number': self.cuil_number
        }

        responses.add(
            responses.GET,
            f'{self.customer_url}/v1/customers?{url_param}='
            f'{document_values[document_value]}',
            json=self.customer_filter_response,
            status=200
        )
        response = self.client.get(
            f'{self.root_endpoint}/byDocument/{document_type}'
            f'/{document_values[document_value]}/{wrong_svc_agr_id}'
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == expected_response_content

    @parameterized.expand([
        ('DNI', 'identity_dni', '34341252'),
        ('CUIL', 'identity_cuil', '27343412521')
    ])
    @responses.activate
    def test_get_user_by_document_customer_not_found(
        self,
        document_type,
        url_param,
        wrong_document_value
    ):
        svc_agr_id = 123456789
        expected_response_content = {
            'error': {
                'code': 'NB-ERROR-00401',
                'message': 'Entity Not Found <Customer>'
            }
        }
        customer_api_response_content = {'data': [], 'hyper': {}}

        responses.add(
            responses.GET,
            f'{self.customer_url}/v1/customers?{url_param}='
            f'{wrong_document_value}',
            json=customer_api_response_content,
            status=200
        )
        response = self.client.get(
            f'{self.root_endpoint}/byDocument/{document_type}'
            f'/{wrong_document_value}/{svc_agr_id}'
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == expected_response_content


class TestGetUserView(ApiLayerTestCase):

    def test_get_user_ok(self):
        user = seed_user(
            customer_id=UUID('84bfe03b-9992-4b62-8f4a-155eaad55479')
        )
        expected_response = {
            'status': HTTPStatus.OK,
            'body': {
                'data': {
                    'id': str(user.id),
                    'service_agr_id': user.service_agr_id,
                    'status': user.status.value,
                    'customer_id': str(user.customer_id),
                    'address_id': None
                },
                'hyper': {}
            },
        }
        response = self.client.get(f'/v2/users/{user.id}')
        result_response = {
            'status': response.status_code,
            'body': response.json()
        }

        assert result_response == expected_response

    def test_get_user_bad_request(self):
        expected_response = {
            'status': HTTPStatus.BAD_REQUEST,
            'body': {
                'error': {
                    'code': 'NB-ERROR-00402',
                    'message': {'user_id': ['Not a valid UUID.']}
                },
            },
        }
        response = self.client.get(
            '/v2/users/8565dd76-5aa6-493e-b2ae-f2719wrongid'
        )
        result_response = {
            'status': response.status_code,
            'body': response.json()
        }

        assert result_response == expected_response

    def test_get_user_not_found(self):
        expected_response = {
            'status': HTTPStatus.NOT_FOUND,
            'body': {
                'error': {
                    'code': 'NB-ERROR-00401',
                    'message': 'Entity Not Found <User>'
                },
            },
        }
        response = self.client.get(
            '/v2/users/8565dd76-5aa6-493e-b2ae-f2719d0d20e9'
        )
        result_response = {
            'status': response.status_code,
            'body': response.json()
        }

        assert result_response == expected_response

    def test_get_user_contact_methods_view(self):
        """
        Ensure that /contact_methods resource can fetch user's contact methods properly.

        - Given an existent user.
        - When /contact_methods resource is called.
        - With the existent user's id.
        - Then a list of user's contact methods is displayed in the response inteface.
        """
        contact_methods = [
            contact_method_factory_mock(type_='EMAIL', confirmed=True),
            contact_method_factory_mock(type_='PHONE', confirmed=True),
        ]
        user = seed_user(contact_methods=contact_methods)
        self.container.user_repo().save(user)
        expected_result = {
            'status_code': HTTPStatus.OK,
            'response_json': {
                'data': [
                    {
                        'id': str(contact_method.id),
                        'type': contact_method.type.description,
                        'value': contact_method.value,
                        'confirmed': contact_method.is_confirmed,
                        'user_id': str(contact_method.user_id),
                    } for contact_method in contact_methods
                ],
                'hyper': {}
            }
        }

        response = self.client.get(f'/v2/users/{user.id}/contact_methods')

        assert response.status_code == expected_result['status_code']
        assert TestUtils.compare_iterables_ignoring_order(
            response.json(), expected_result['response_json']
        )
