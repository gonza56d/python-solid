from http import HTTPStatus
from uuid import uuid4

import responses
from parameterized import parameterized

from users.core.actions import ConfirmIdentity
from users.core.models import SignUp
from users.core.models.states import SignUpStage, UserStatus
from users.tests.mock_factory import identity_factory_mock, user_factory_mock
from users.tests.test_core import CoreTestCase


class TestConfirmUserIdentity(CoreTestCase):

    def setUp(self):
        super().setUp()
        self.identity_validation_url = self.container\
            .config \
            .identity_validation_svc_url() \
            + '/v1/identity-validations'

        self.merlin_api_url = self.container.config \
            .merlin_api_url() \
            + '/v1.5/address/user'

        self.customer_api_url = self.container.config \
            .customer_api_url() \
            + '/v1/customers'

        self.existent_user = user_factory_mock(
            customer_id=None,
            customer=None,
            contact_methods=[],
            status=UserStatus.PENDING_VALIDATION
        )
        self.container.user_repo().save(self.existent_user)

        self.existent_sign_up = SignUp(
            SignUpStage.IDENTITY_VALIDATION,
            user_id=self.existent_user.id
        )
        self.container.sign_up_repo().save(self.existent_sign_up)

        self.address_id = uuid4()
        self.identity_mock = self.IdentityValidationMock(
            self.existent_user.id,
            identity_factory_mock()
        )
        self.merlin_mock = self.MerlinMock(self.existent_user.id, self.address_id)
        self.customer_mock = self.CustomerMock()

    @parameterized.expand([(True,), (False,)])
    @responses.activate
    def test_confirm_identity_success(self, existent_customer: bool):
        """
        Ensure that user can confirm its identity with success.

        - Given a user that has previously validated its identity with success.
        - When the user confirm its identity with an existent address id.
        - Then the customer is associated to the user and advances its sign up stage.
        """
        expected_sig_up_stage = SignUpStage.LEGAL_VALIDATION
        responses.add(
            responses.GET,
            f'{self.identity_validation_url}/{self.existent_user.id}',
            json=self.identity_mock.SUCCESSFUL_GET_RESPONSE
        )
        responses.add(
            responses.GET,
            f'{self.merlin_api_url}/{self.existent_user.id}',
            json=self.merlin_mock.SUCCESSFUL_GET_RESPONSE
        )
        responses.add(
            responses.GET,
            f'{self.customer_api_url}?identity_dni='
            f'{self.identity_mock.SUCCESSFUL_GET_RESPONSE["data"]["dni"]}',
            json=(
                self.customer_mock.SUCCESSFUL_FILTER_RESPONSE
                if existent_customer else self.customer_mock.EMPTY_FILTER_RESPONSE
            )
        )
        responses.add(
            responses.PATCH,
            f'{self.identity_validation_url}/{self.existent_user.id}',
            json=self.identity_mock.SUCCESSFUL_PATCH_RESPONSE
        )
        if not existent_customer:
            responses.add(
                responses.POST,
                self.customer_api_url,
                json=self.customer_mock.SUCCESSFUL_POST_RESPONSE
            )

        action = ConfirmIdentity(
            user_id=self.existent_user.id,
            address_id=self.address_id,
        )
        user_id = self.container.command_bus().handle(action)
        updated_user = self.container.user_repo().get_by_id(self.existent_user.id)
        updated_sign_up = self.container.sign_up_repo()\
            .get_by_user_id(self.existent_user.id)

        assert user_id == self.existent_user.id
        assert updated_sign_up.stage == expected_sig_up_stage
        assert self.address_id in [el.address_id for el in updated_user.user_addresses]
