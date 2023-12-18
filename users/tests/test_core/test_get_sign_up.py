from uuid import uuid4

from users.core.actions import GetSignUpStageByUserId
from users.core.exceptions import EntityNotFound
from users.core.handlers import GetSignUpStageByUserIdHandler
from users.core.models import SignUp
from users.core.models.states import SignUpStage
from users.tests.mock_factory import user_factory_mock
from users.tests.test_core import CoreTestCase


class TestGetSignUpStage(CoreTestCase):

    def setUp(self):
        super().setUp()
        self.user = user_factory_mock(contact_methods=[])
        self.sign_up = SignUp(
            stage=SignUpStage.IDENTITY_VALIDATION,
            user_id=self.user.id
        )
        self.get_sign_up_stage_by_user_id_handler = GetSignUpStageByUserIdHandler(
            sign_up_repo=self.container.sign_up_repo()
        )
        self.command_bus.add_handler(
            GetSignUpStageByUserId,
            self.get_sign_up_stage_by_user_id_handler
        )
        self.container.user_repo().save(self.user)
        self.container.sign_up_repo().save(self.sign_up)

    def test_get_sign_up_stage_by_user_id_success(self):
        expected_sign_up_stage = self.sign_up.stage

        action = GetSignUpStageByUserId(self.user.id)
        obtained_sign_up_stage = self.command_bus.handle(action)

        assert obtained_sign_up_stage == expected_sign_up_stage

    def test_get_sign_up_stage_by_user_id_fail(self):
        expected_exception = EntityNotFound

        action = GetSignUpStageByUserId(uuid4())

        self.assertRaises(
            expected_exception,
            self.command_bus.handle,
            action
        )
