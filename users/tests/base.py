from unittest import TestCase
from uuid import UUID, uuid4

from users.core.models import Identity


class BaseTestCase(TestCase):
    """Inherit to provide mock utilities."""

    class CustomerMock:

        def __init__(self):
            self.SUCCESSFUL_POST_RESPONSE = {
                "data": {
                    "id": "00ba171d-038f-4be0-bd27-d63d39851f16"
                },
                "hyper": {
                    "/v1/customers/3264113-23e2-4fd0-bc90-b4dc548b2473": [
                        "GET",
                        "PATCH"
                    ]
                }
            }

            self.EMPTY_FILTER_RESPONSE = {
                "data": [],
                "hyper": {}
            }

            self.SUCCESSFUL_FILTER_RESPONSE = {
                "data": [{
                    "id": "dbf4be34-8988-49b0-b8ea-3c3e08c9d844",
                    "status": "ACTIVE",
                    "age_group": "TEEN",
                    "legal_name": {
                        "first_name": "Jhon",
                        "last_name": "Doe"
                    },
                    "gender": "F",
                    "birth_date": "1996-07-01",
                    "relationship": "MARRIED",
                    "occupation_id": "91a339c8-0ba9-471f-9e9d-86f416788d53",
                    "nationality_id": "2b09f404-9699-49ac-b92d-3aab9eeb8bc6",
                    "identifications": {
                        "CUIL": {
                            "id": "e01dff10-123e-458c-a975-f1ec86d559f7",
                            "value": "20282582582",
                            "audit_fields": {
                                "created_date": "2022-04-13T20:29:56.490577+00:00",
                                "deleted_by": None,
                                "modified_date": "2022-04-13T20:29:56.490584+00:00",
                                "deleted_date": None,
                                "created_by": None,
                                "modified_by": None
                            }
                        },
                        "DNI": {
                            "id": "e01dff10-123e-458c-a975-f1ec86d559f7",
                            "value": "28258258",
                            "audit_fields": {
                                "created_date": "2022-04-13T20:29:56.490577+00:00",
                                "deleted_by": None,
                                "modified_date": "2022-04-13T20:29:56.490584+00:00",
                                "deleted_date": None,
                                "created_by": None,
                                "modified_by": None
                            }
                        }
                    },
                    "audit_fields": {
                        "created_date": "2022-04-13T20:29:56.490577+00:00",
                        "deleted_by": None,
                        "modified_date": "2022-04-13T20:29:56.490584+00:00",
                        "deleted_date": None,
                        "created_by": None,
                        "modified_by": None
                    }
                }],
                "hyper": {}
            }

    class MerlinMock:

        def __init__(self, user_id: UUID, address_id: UUID = None):
            self.SUCCESSFUL_GET_RESPONSE = [
                {
                    "address_id": str(address_id or uuid4()),
                    "user_id": str(user_id),
                    "status": "SOME_STATUS",
                    "source": "SOME_SOURCE",
                    "street_name": "string",
                    "street_no": "string",
                    "street_intersection": "string",
                    "floor_no": "string",
                    "apartment_no": "string",
                    "city": "string",
                    "zip_code": "string",
                    "exteded_zip_code": "string",
                    "province_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "country_id": "0f1bfb04-6c2f-4834-a55c-d31853506ae9"
                },
                {
                    "address_id": str(uuid4()),
                    "user_id": str(user_id),
                    "status": "SOME_STATUS",
                    "source": "SOME_SOURCE",
                    "street_name": "string",
                    "street_no": "string",
                    "street_intersection": "string",
                    "floor_no": "string",
                    "apartment_no": "string",
                    "city": "string",
                    "zip_code": "string",
                    "exteded_zip_code": "string",
                    "province_id": "c81e15cd-9ee3-4412-a97f-211172513cca",
                    "country_id": "0f1bfb04-6c2f-4834-a55c-d31853506ae9"
                }
            ]

    class IdentityValidationMock:

        def __init__(self, user_id: UUID, expected_identity: Identity):
            self.SUCCESSFUL_PATCH_RESPONSE = {
                'data': {
                    'user_id': str(user_id)
                },
                "hyper": {
                    f"/identity-validations/{user_id}": ["GET", "PATCH"]
                }
            }

            self.SUCCESSFUL_GET_RESPONSE = {
                'data': {
                    'nationality': expected_identity.nationality,
                    'last_name': expected_identity.last_name,
                    'gender': expected_identity.gender,
                    'cuil': expected_identity.cuil,
                    'dni': expected_identity.dni,
                    'first_name': expected_identity.first_name,
                    'birth_date': str(expected_identity.birth_date)
                },
                "hyper": {
                    f"/identity-validations/{user_id}": ["GET"]
                }
            }

            self.SUCCESSFUL_POST_RESPONSE = {
                'data': {'user_id': str(user_id)},
                "hyper": {
                    f"/identity-validations/{user_id}": ["GET"]
                }
            }

            self.NO_MATCH_POST_RESPONSE = {}

            self.EXCEEDED_ATTEMPTS_TICKET_NOT_SENT = {
                "error": {
                    "message": "Number of identity validation attempts exceeded. "
                               "Ticket sent: False.",
                    "code": "NB-ERROR-00850"
                }
            }

            self.EXCEEDED_ATTEMPTS_TICKET_SENT = {
                "error": {
                    "message": "Number of identity validation attempts exceeded. "
                               "Ticket sent: True.",
                    "code": "NB-ERROR-00851"
                }
            }

            self.USER_MINOR_ERROR = {
                "error": {
                    "message": "The person is a minor.",
                    "code": "NB-ERROR-00802"
                }
            }

            self.USER_TEEN_PARTIAL_RESPONSE = {
                "data": {
                    "user_id": str(user_id),
                    "hyper": {
                        f"/v1/identity-validations/{user_id}":
                            ["GET, PATCH"]
                    },
                },
                "errors": [{
                    "message": "Person is a teen. Pending parental authorization.",
                    "code": "NB-ERROR-00852"
                }]
            }

