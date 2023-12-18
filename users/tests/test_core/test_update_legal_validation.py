from http import HTTPStatus
from uuid import UUID

import responses
from users.core.exceptions import (
    DependencyError,
    EntityNotFound
)

from users.core.actions import UpdateLegalValidation
from users.core.models.locals import SignUp
from users.core.models.states import SignUpStage
from users.tests.mock_factory import (
    CUSTOMER_ID,
    customer_factory_mock,
    user_factory_mock,
    USER_ID,
)
from users.tests.test_core import CoreTestCase


class TestUpdateLegalValidation(CoreTestCase):

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
    def test_update_legal_validation_action_success(self):
        responses.add(
            responses.PATCH,
            f'{self.url}/v1/customers/{str(self.customer_id)}/legal_validation',
            json={
                'data': {
                    'id': f'{self.customer_id}'
                },
            },
            status=200
        )
        self.sign_up_repo.save(self.expected_sign_up)
        action = UpdateLegalValidation(
            user_id=self.user_id,
            pep=False,
            so=False,
            facta=False,
            occupation_id=UUID('14e56e54-3e0e-4b7c-87f7-38bb219772d0'),
            relationship='MARRIED',
            customer_id=self.customer_id
        )
        self.command_bus.handle(action)
        sign_up: SignUp = self.sign_up_repo.get_by_user_id(self.user_id)
        assert sign_up.stage == SignUpStage.LEGAL_VALIDATION

    @responses.activate
    def test_update_legal_validation_action_fail_occupation_not_found(self):
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
        self.sign_up_repo.save(self.expected_sign_up)
        action = UpdateLegalValidation(
            user_id=self.user_id,
            pep=False,
            so=False,
            facta=False,
            occupation_id=UUID('14e56e54-3e0e-4b7c-87f7-38bb219772d0'),
            relationship='MARRIED',
            customer_id=self.customer_id
        )
        with self.assertRaises(DependencyError):
            self.command_bus.handle(action)
        sign_up: SignUp = self.sign_up_repo.get_by_user_id(self.user_id)
        assert sign_up.stage == SignUpStage.IDENTITY_VALIDATION

    def test_update_legal_validation_action_fail_user_not_found(self):
        action = UpdateLegalValidation(
            user_id=UUID('0da2ffef-1a72-47e7-aba7-55d85f14e791'),
            pep=False,
            so=False,
            facta=False,
            occupation_id=UUID('14e56e54-3e0e-4b7c-87f7-38bb219772d0'),
            relationship='MARRIED',
            customer_id=self.customer_id
        )
        self.sign_up_repo.save(self.expected_sign_up)
        with self.assertRaises(EntityNotFound):
            self.command_bus.handle(action)
        sign_up: SignUp = self.sign_up_repo.get_by_user_id(self.user_id)
        assert sign_up.stage == SignUpStage.IDENTITY_VALIDATION
