from http import HTTPStatus
from uuid import uuid4

import responses
from nwrest.exceptions import PropagableHttpError

from users.core.actions import GetIdentityValidation
from users.core.exceptions import IdentityValidationError
from users.core.models import SignUp
from users.core.models.states import SignUpStage
from users.odm.schemas import AddressSchema
from users.tests.mock_factory import user_factory_mock, identity_factory_mock
from users.tests.test_core import CoreTestCase


class TestGetIdentityValidationActions(CoreTestCase):

    def setUp(self):
        super().setUp()
        self.command_bus = self.container.command_bus()
        self.identity_validation_url = self.container\
            .config\
            .identity_validation_svc_url()\
            + '/v1/identity-validations'
        self.merlin_api_url = self.container.config\
            .merlin_api_url()\
            + '/v1.5/address/user'

        user_id = uuid4()
        self.identity_validation_id = uuid4()
        self.existent_identity = identity_factory_mock()
        self.user = user_factory_mock(
            id=user_id,
            contact_methods=[]
        )
        self.container.user_repo().save(self.user)
        self.sign_up = SignUp(stage=SignUpStage.IDENTITY_VALIDATION, user_id=user_id)
        self.container.sign_up_repo().save(self.sign_up)

    @responses.activate
    def test_get_identity_success(self):
        """
        Ensure that identity objects are properly returned.

        - Given an existent identity validation ID.
        - When the action of getting an identity validation is performed.
        - Then the identity validation with the requested ID is returned.
        """
        identity_validation_mock = self.IdentityValidationMock(
            self.user.id,
            identity_factory_mock()
        )
        merlin_mock = self.MerlinMock(self.user.id)
        expected_identity = identity_factory_mock(
            addresses=[
                AddressSchema().load(kwargs).data
                for kwargs in merlin_mock.SUCCESSFUL_GET_RESPONSE
            ]
        )

        responses.add(
            responses.GET,
            f'{self.identity_validation_url}/{self.user.id}',
            json=identity_validation_mock.SUCCESSFUL_GET_RESPONSE
        )
        responses.add(
            responses.GET,
            f'{self.merlin_api_url}/{self.user.id}',
            json=merlin_mock.SUCCESSFUL_GET_RESPONSE
        )
        result = self.command_bus.handle(
            GetIdentityValidation(self.user.id)
        )

        assert result == expected_identity

    @responses.activate
    def test_get_identity_validation_404(self):
        """
        Ensure that the proper exception is raised on unexistent ID Validation request.

        - Given a non existent identity validation id.
        - When the action of getting that identity validation is performed.
        - Then the proper IdentityValidationError exception is raised.
        """
        self.user.identity_validation_id = uuid4()
        self.container.user_repo().save(self.user)
        responses.add(
            responses.GET,
            f'{self.identity_validation_url}/{self.user.id}',
            status=HTTPStatus.NOT_FOUND,
            json={
                'error': {
                    'code': 'NB-ERROR-00801',
                    'message': 'Entity Not Found: Identity by user_id: '
                               f'{self.user.id}'
                }
            }
        )
        action = GetIdentityValidation(self.user.id)

        self.assertRaises(PropagableHttpError, self.command_bus.handle, action)

    @responses.activate
    def test_get_identity_validation_wrong_signup_stage(self):
        """
        Ensure that proper exception is raised when signup stage != IDENTITY_VALIDATION.

        - Given a user with current signup stage different from IDENTITY_VALIDATION.
        - When the identity validation is requested.
        - Then IdentityValidationError is raised.
        """
        expected_exception = IdentityValidationError

        self.sign_up.stage = SignUpStage.LEGAL_VALIDATION
        self.container.sign_up_repo().save(self.sign_up)
        mock = self.IdentityValidationMock(
            self.identity_validation_id,
            identity_factory_mock()
        )
        responses.add(
            responses.GET,
            f'{self.identity_validation_url}/{self.user.id}',
            json=mock.SUCCESSFUL_GET_RESPONSE
        )
        action = GetIdentityValidation(self.user.id)

        self.assertRaises(expected_exception, self.command_bus.handle, action)
