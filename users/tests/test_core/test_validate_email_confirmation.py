from datetime import datetime, timedelta

from users.core.exceptions import ValidationError
from users.core.models import SignUp
from users.core.models.states import SignUpStage
from users.tests.test_core import CoreTestCase
from users.core.actions import ValidateEmailConfirmationToken
from users.tests.mock_factory import (
    contact_method_factory_mock,
    user_factory_mock,
)


class TestValidateEmailConfirmation(CoreTestCase):

    def setUp(self):
        super().setUp()
        self.user_repo = self.container.sign_up_repo()
        self.contact_method_repo = self.container.contact_method_repo()
        self.sign_up_repo = self.container.sign_up_repo()
        self.command_bus = self.container.command_bus()
        self.contact_method_repo = self.container.contact_method_repo()
        self.user = user_factory_mock(
            contact_methods=[
                contact_method_factory_mock('PHONE', confirmed=False)
            ]
        )
        self.unconfirmed_email = contact_method_factory_mock(
            type_='EMAIL',
            confirmed=False,
            user_id=self.user.id,
        )
        self.confirmed_email = contact_method_factory_mock(
            type_='EMAIL',
            confirmed=True,
            user_id=self.user.id,
        )

        self.user_repo.save(self.user)

        self.expected_sign_up = SignUp(
            stage=SignUpStage.EMAIL_CONFIRMATION,
            user_id=self.user.id
        )

        self.sign_up_repo.save(self.expected_sign_up)

    def test_validate_email_success(self):
        """
        GIVEN a user, signup and contact method unconfirmed in database
        WHEN ValidateEmailConfirmationHandler is called with contact_method.token
        THEN ValidateEmailConfirmationToken succeeds
        """
        self.contact_method_repo.save(self.unconfirmed_email)

        action = ValidateEmailConfirmationToken(
            self.unconfirmed_email.contact_confirmation.value
        )
        expected_user_id = self.unconfirmed_email.user_id

        token_validation_result: SignUp = self.command_bus.handle(action)

        obtained_user_id = token_validation_result.user_id

        assert obtained_user_id == expected_user_id
        assert self.unconfirmed_email\
                   .contact_confirmation.value == action.token
        assert self.sign_up_repo.get_by_user_id(self.user.id).stage == SignUpStage.IDENTITY_VALIDATION

    def test_validate_email_fail_by_already_confirmed(self):
        """
        GIVEN a user, signup and contact method confirmed in database
        WHEN ValidateEmailConfirmationHandler is called with contact_method.token
        THEN ValidateEmailConfirmationToken fails
        """
        self.contact_method_repo.save(self.confirmed_email)
        
        action = ValidateEmailConfirmationToken(
            self.confirmed_email.contact_confirmation.value
        )

        self.assertRaises(ValidationError, self.command_bus.handle, action)

    def test_validate_email_fail_by_expired_token(self):
        """
        GIVEN a user, signup and contact method in database
        WHEN ValidateEmailConfirmationHandler is called with expired contact_method.token
        THEN ValidateEmailConfirmationToken fails
        """
        self.unconfirmed_email.contact_confirmation = self.unconfirmed_email\
            .contact_confirmation\
            .recreate(expire_at=datetime.now() - timedelta(minutes=5))
         
        self.contact_method_repo.save(self.unconfirmed_email)

        action = ValidateEmailConfirmationToken(
            self.confirmed_email.contact_confirmation.value
        )
        self.assertRaises(ValidationError, self.command_bus.handle, action)
