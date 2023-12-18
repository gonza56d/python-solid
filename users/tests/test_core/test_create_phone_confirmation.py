from contextlib import contextmanager
from unittest.mock import MagicMock
from uuid import UUID

from pymessagebus import CommandBus

from users.core.actions import CreatePhoneConfirmation
from users.core.exceptions import ValidationError
from users.core.handlers import CreatePhoneConfirmationHandler
from users.core.models import ContactMethodType
from users.core.models.states import ContactConfirmationType
from users.tests.mock_factory import (
    contact_confirmation_factory_mock,
    contact_method_factory_mock,
    user_factory_mock,
)
from users.tests.test_core import CoreTestCase


class TestCreatePhoneConfirmation(CoreTestCase):
    """Unit tests cases for Create Phone Number Confirmation business logic."""

    def setUp(self):
        super().setUp()
        self.sign_up_repo = self.container.sign_up_repo()
        self.user_repo = self.container.user_repo()
        self.contact_method_type_repo = self.container.contact_method_type_repo()
        self.command_bus = self.container.command_bus()

    def test_create_phone_number_confirmation_otp_success(self):
        """Given user with contact method of type that is NOT PHONE
        When phone number is provided to CreatePhoneConfirmation action
        Then CreatePhoneConfirmation action succeeds"""

        self.returned_user = user_factory_mock(
            contact_methods=[
                contact_method_factory_mock('EMAIL', confirmed=False)
            ]
        )

        self.returned_user.contact_methods[0]\
            .contact_confirmation = contact_confirmation_factory_mock(
            user_id=str(self.returned_user.id),
            contact_method_id=str(self.returned_user.contact_methods[0].id),
            confirmed=False,
            type=ContactConfirmationType.OTP
        )

        self.user_repo.save(self.returned_user)

        action = CreatePhoneConfirmation(user_id=self.returned_user.id, phone_number='+5412345678945')
        
        otp_created = self.command_bus.handle(action)

        assert len(otp_created) == 4

    def test_renew_phone_number_confirmation_otp_success(self):
        """Given user with contact method of type PHONE
        When phone number is provided to CreatePhoneConfirmation action
        Then CreatePhoneConfirmation action succeeds"""

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
            type=ContactConfirmationType.OTP
        )

        self.user_repo.save(self.returned_user)

        action = CreatePhoneConfirmation(user_id=self.returned_user.id, phone_number='+5412345678945')
        
        otp_created = self.command_bus.handle(action)

        assert len(otp_created) == 4

    def test_create_phone_number_confirmed_error(self):
        """Given user with contact method of type PHONE that has already been confirmed
        When phone number is provided to CreatePhoneConfirmation action
        Then throw exception that phone number has been confirmed"""

        self.returned_user = user_factory_mock(
            contact_methods=[
                contact_method_factory_mock('PHONE', confirmed=False)
            ]
        )

        self.returned_user.contact_methods[0]\
            .contact_confirmation = contact_confirmation_factory_mock(
            user_id=str(self.returned_user.id),
            contact_method_id=str(self.returned_user.contact_methods[0].id),
            confirmed=True,
            type=ContactConfirmationType.OTP
        )

        self.user_repo.save(self.returned_user)

        action = CreatePhoneConfirmation(
            user_id=self.returned_user.id,
            phone_number='+5412345678945'
        )
        
        with self.assertRaises(ValidationError):
            self.command_bus.handle(action)
