from contextlib import contextmanager
from unittest.mock import MagicMock
from uuid import uuid4

from pymessagebus import CommandBus

from users.core.actions import ConfirmPhoneNumber
from users.core.exceptions import (
    EntityNotFound,
    ValidationError,
)
from users.core.handlers import ConfirmPhoneNumberHandler
from users.core.models import (
    ContactMethodType,
    SignUp
)
from users.core.models.states import (
    ContactConfirmationType,
    SignUpStage
)
from users.tests.mock_factory import (
    contact_confirmation_factory_mock,
    contact_method_factory_mock,
    user_factory_mock,
)
from users.tests.test_core import CoreTestCase


class TestConfirmPhoneNumber(CoreTestCase):
    """Unit tests cases for CreatePhoneNumber action"""

    def setUp(self):
        super().setUp()
        self.sign_up_repo = self.container.sign_up_repo()
        self.user_repo = self.container.user_repo()
        self.contact_method_type_repo = self.container.contact_method_type_repo()
        self.command_bus = self.container.command_bus()

        self.returned_user = user_factory_mock(
            contact_methods=[
                contact_method_factory_mock('PHONE', confirmed=False)
            ]
        )
        self.returned_user.contact_methods[0]\
        .contact_confirmation = contact_confirmation_factory_mock(
        user_id=str(self.returned_user.id),
        contact_method_id=str(self.returned_user.contact_methods[0].id),
        confirmed=False,
        type=ContactConfirmationType.OTP,
        value='1234'
)
        self.expected_sign_up = SignUp(
            stage=SignUpStage.PHONE_CONFIRMATION,
            user_id=self.returned_user.id
        )

    @contextmanager
    def assertNotRaises(self, exc_type):
        try:
            yield None
        except exc_type:
            raise self.failureException('{} raised'.format(exc_type.__name__))

    def test_confirm_phone_number_given_user_and_signup_success(self):
        """Given user and signup 
        When otp equals that used at the time of user creation
        Then ConfirPhoneNumber action executes succesfully"""

        self.user_repo.save(self.returned_user)

        self.sign_up_repo.save(self.expected_sign_up)

        action = ConfirmPhoneNumber(user_id=self.returned_user.id, otp='1234')
        
        with self.assertNotRaises(ValidationError):
            self.command_bus.handle(action)

    def test_confirm_phone_number_given_user_and_signup_with_different_otp_fails(self):
        """Given user and signup 
        When otp differs from that used at the time of user creation
        Then ConfirPhoneNumber action fails"""


        self.user_repo.save(self.returned_user)

        self.sign_up_repo.save(self.expected_sign_up)

        action = ConfirmPhoneNumber(user_id=self.returned_user.id, otp='0000')

        with self.assertRaises(ValidationError):
            self.command_bus.handle(action)

    def test_confirm_phone_number_given_nothing_EntityNoTFound(self):
        """Given nothing
        When ConfirmPhoneNumberHandler is called
        Then ConfirPhoneNumber action fails"""

        action = ConfirmPhoneNumber(user_id=uuid4(), otp='1234')

        with self.assertRaises(EntityNotFound):
            self.command_bus.handle(action)

    def test_confirm_phone_number_given_signup_EntityNoTFound(self):
        """Given signup 
        When ConfirmPhoneNumberHandler is called
        Then ConfirPhoneNumber action fails"""

        self.user_repo.save(self.returned_user)

        action = ConfirmPhoneNumber(user_id=uuid4(), otp='1234')

        with self.assertRaises(EntityNotFound):
            self.command_bus.handle(action)