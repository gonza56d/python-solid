from http import HTTPStatus

import responses
from parameterized import parameterized

from users.core.actions import ValidateUserIdentity
from users.core.exceptions import (
    AttemptsExceededError,
    ValidationError,
    UserIdentityMinorError,
)
from users.core.models import SignUp
from users.core.models.states import SignUpStage, UserStatus
from users.tests.mock_factory import user_factory_mock, identity_factory_mock
from users.tests.test_core import CoreTestCase


class TestValidateUserIdentity(CoreTestCase):

    def setUp(self):
        super().setUp()
        self.command_bus = self.container.command_bus()
        self.identity_validation_url = self.container\
           .config\
           .identity_validation_svc_url()\
            + '/v1/identity-validations'
        self.user = user_factory_mock(
            status=UserStatus.PENDING_VALIDATION,
            contact_methods=[],
        )
        self.user_repo = self.container.user_repo()
        self.user_repo.save(self.user)
        self.sign_up = SignUp(
            user_id=self.user.id,
            stage=SignUpStage.IDENTITY_VALIDATION
        )
        self.sign_up_repo = self.container.sign_up_repo()
        self.sign_up_repo.save(self.sign_up)

    @responses.activate
    def test_perform_identity_validation_success(self):
        """
        Ensure that identity validation can be performed correctly.

        Given a valid identity validation request.
        When the identity validation service response is satisfactory.
        Then the user id is returned and sign up stage is updated.
        """
        expected_result = {
            'user_id': self.user.id,
            'user_status': UserStatus.VALIDATED,
        }

        action = ValidateUserIdentity(
            user_id=self.user.id,
            ocr='some tokenized ocr',
            selfie='some selfie data',
            face_id='some face data',
            base64_front='some picture data',
            base64_selfie='some other picture data',
            base64_back='some other and another picture data',
        )
        mock = self.IdentityValidationMock(
            self.user.id,
            identity_factory_mock()
        )
        responses.add(
            responses.POST,
            self.identity_validation_url,
            json=mock.SUCCESSFUL_POST_RESPONSE
        )
        user_id = self.command_bus.handle(action)
        updated_user = self.user_repo.get_by_id(self.user.id)

        assert {
            'user_id':  user_id,
            'user_status': updated_user.status,
        } == expected_result

    @responses.activate
    def test_perform_identity_validation_wrong_sign_up_stage(self):
        """
        Ensure that identity validation validates sign up stage before performing.

        Given a valid identity validation request.
        When the sign up stage is not IDENTITY_VALIDATION.
        Then ValidationError is raised.
        """
        self.sign_up.stage = SignUpStage.EMAIL_CONFIRMATION

        self.sign_up_repo.save(self.sign_up)
        action = ValidateUserIdentity(
            user_id=self.user.id,
            ocr='some tokenized ocr',
            selfie='some selfie data',
            face_id='some face data',
            base64_front='some picture data',
            base64_selfie='some other picture data',
            base64_back='some other and another picture data',
        )
        mock = self.IdentityValidationMock(
            self.user.id,
            identity_factory_mock()
        )
        responses.add(
            responses.POST,
            self.identity_validation_url,
            json=mock.SUCCESSFUL_POST_RESPONSE
        )

        self.assertRaises(ValidationError, self.command_bus.handle, action)

    @parameterized.expand([('sent',), ('not_sent',)])
    @responses.activate
    def test_perform_identity_validation_exceeded_attempts(self, ticket_result: str):
        """
        Ensure that identity validation can be performed correctly.

        Given a valid identity validation request.
        When the identity validation service response is not satisfactory.
        With exceeded attempts.
        Then sign up stage is not updated and user status is BANNED/BANNED_NOTIFIED.
        """
        mock = self.IdentityValidationMock(
            self.user.id,
            identity_factory_mock()
        )
        zendesk_ticket = {
            'sent': {
                'error_code': 'NB-ERROR-00851',
                'user_status': UserStatus.BANNED_NOTIFIED,
                'mock': mock.EXCEEDED_ATTEMPTS_TICKET_SENT,
            },
            'not_sent': {
                'error_code': 'NB-ERROR-00850',
                'user_status': UserStatus.BANNED,
                'mock': mock.EXCEEDED_ATTEMPTS_TICKET_NOT_SENT,
            },
        }
        expected_result = {
            'sign_up_stage': SignUpStage.IDENTITY_VALIDATION,
            'user_status': zendesk_ticket[ticket_result]['user_status']
        }

        action = ValidateUserIdentity(
            user_id=self.user.id,
            ocr='some tokenized ocr',
            selfie='some selfie data',
            face_id='some face data',
            base64_front='some picture data',
            base64_selfie='some other picture data',
            base64_back='some other and another picture data',
        )
        responses.add(
            responses.POST,
            self.identity_validation_url,
            json=zendesk_ticket[ticket_result]['mock'],
            status=HTTPStatus.BAD_REQUEST
        )

        self.assertRaises(AttemptsExceededError, self.command_bus.handle, action)
        updated_sign_up = self.sign_up_repo.get_by_user_id(self.user.id)
        updated_user = self.user_repo.get_by_id(self.user.id)
        assert {
            'sign_up_stage': updated_sign_up.stage,
            'user_status': updated_user.status
        } == expected_result

    @parameterized.expand([('minor',), ('teen',)])
    @responses.activate
    def test_validate_user_identity_under_age(self, under_age_option):
        """
        Ensure that validation process updates signup_stage/user_status on under age.

        - Given an proper identity validation request.
        - When the result indicates that person is minor/teen.
        - Then:
            - Minor: User's sign up stage is updated to SIGNUP_BLOCKED.
            - Teen: User's status is updated to PENDING_AUTHORIZATION.
        """
        mock = self.IdentityValidationMock(
            self.user.id,
            identity_factory_mock()
        )
        under_age = {
            'minor': {
                'user_status': self.user.status,
                'sign_up_stage': SignUpStage.SIGN_UP_BLOCKED,
                'response': mock.USER_MINOR_ERROR,
                'status': HTTPStatus.BAD_REQUEST,
            },
            'teen': {
                'user_status': UserStatus.PENDING_AUTHORIZATION,
                'sign_up_stage': SignUpStage.IDENTITY_VALIDATION,
                'response': mock.USER_TEEN_PARTIAL_RESPONSE,
                'status': HTTPStatus.PARTIAL_CONTENT
            },
        }
        expected_result = {
            'user_status': under_age[under_age_option]['user_status'],
            'sign_up_stage': under_age[under_age_option]['sign_up_stage'],
        }

        action = ValidateUserIdentity(
            user_id=self.user.id,
            ocr='some tokenized ocr',
            selfie='some selfie data',
            face_id='some face data',
            base64_front='some picture data',
            base64_selfie='some other picture data',
            base64_back='some other and another picture data',
        )
        responses.add(
            responses.POST,
            self.identity_validation_url,
            json=under_age[under_age_option]['response'],
            status=under_age[under_age_option]['status']
        )

        if under_age_option == 'minor':
            self.assertRaises(UserIdentityMinorError, self.command_bus.handle, action)
        elif under_age_option == 'teen':
            self.command_bus.handle(action)
        updated_sign_up = self.sign_up_repo.get_by_user_id(self.user.id)
        updated_user = self.user_repo.get_by_id(self.user.id)
        assert {
            'user_status': updated_user.status,
            'sign_up_stage': updated_sign_up.stage,
        } == expected_result
