from unittest.mock import MagicMock

from users.core.actions import CreateSignUp
from users.core.exceptions import ValidationError
from users.core.models import SignUp
from users.core.repositories import (
    ContactMethodRepository,
    SignUpRepository,
    UserRepository
)
from users.core.models.states import SignUpStage
from users.tests.mock_factory import (
    contact_confirmation_factory_mock,
    contact_method_factory_mock,
    user_factory_mock,
)
from users.tests.test_core import CoreTestCase


class TestCreateSignUp(CoreTestCase):
    """Unit tests cases for CreateSignUpHandler business logic."""

    def setUp(self):
        super().setUp()
        self.sign_up_repo = self.container.sign_up_repo()
        self.user_repo = self.container.user_repo()
        self.contact_method_type_repo = self.container.contact_method_type_repo()
        self.command_bus = self.container.command_bus()

    def test_create_sign_up_success(self):
        """
        GIVEN no user registered
        WHEN CreateSignUpHandler is called with new svcagr_id and email
        THEN Create SignUp succeeds
        """

        action = CreateSignUp(service_agr_id=0, email='some@email.com')

        created_sign_up = self.command_bus.handle(action)

        assert created_sign_up is not None
        assert created_sign_up.stage == SignUpStage.EMAIL_CONFIRMATION

    def test_create_sign_up_fail_by_existing_active_user(self):
        """
        GIVEN a confirmed user in user repo
        WHEN CreateSignUp action is called with the user's email and svcagr_id
        THEN CreateSignUp action fails
        """
        returned_user = user_factory_mock(
            contact_methods=[
                contact_method_factory_mock('EMAIL', confirmed=True)
            ]
        )
        returned_user.contact_methods[0]\
            .contact_confirmation = contact_confirmation_factory_mock(
            user_id=str(returned_user.id),
            contact_method_id=str(returned_user.contact_methods[0].id),
            confirmed=True)

        self.user_repo.save(returned_user)

        action = CreateSignUp(
            service_agr_id=0,
            email=returned_user.email
        )
        create_sign_up = self.command_bus.handle

        self.assertRaises(ValidationError, create_sign_up, action)
