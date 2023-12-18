from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4

from . import ApiLayerTestCase
from users.tests.mock_factory import (
    contact_confirmation_factory_mock,
    contact_method_factory_mock,
    user_factory_mock,
)
from users.core.models import SignUp
from users.core.models.states import SignUpStage


class TestValidateEmailConfirmationViews(ApiLayerTestCase):

    def test_email_confirmation_token_success(self):
        user_id = uuid4()
        expected_result = {
            'status': HTTPStatus.OK,
            'response': {
                'data': {'user_id': str(user_id)},
                'hyper': {
                    f'/v2/users/signup/{user_id}/identity_validation': ['POST']
                }
            }
        }

        existing_user = user_factory_mock(
            id=user_id,
            service_agr_id=0,
            contact_methods=[]
        )
        contact_method_id = uuid4()
        contact_method = contact_method_factory_mock(
            type_='EMAIL',
            value='test6@email.com',
            confirmed=False,
            contact_confirmation=contact_confirmation_factory_mock(
                user_id=str(existing_user.id),
                contact_method_id=str(contact_method_id),
                confirmed=False,
                expire_at=datetime.now() + timedelta(hours=5000)
            )
        )
        existing_user.contact_methods.append(contact_method)

        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.EMAIL_CONFIRMATION, existing_user.id)
        )

        response = self.client.get(
            f'{self.root_endpoint}'
            '/signup/email_confirmation/'
            f'{contact_method.contact_confirmation.value}'
        )

        assert {
            'status': response.status_code,
            'response': response.json()
        } == expected_result
