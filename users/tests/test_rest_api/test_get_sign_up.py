from http import HTTPStatus
from uuid import uuid4

from users.core.models import SignUp
from users.core.models.states import SignUpStage
from users.tests.mock_factory import user_factory_mock
from users.tests.test_rest_api import ApiLayerTestCase


class TestGetSignUpStageView(ApiLayerTestCase):

    def setUp(self):
        super().setUp()
        self.user = user_factory_mock(contact_methods=[])
        self.sign_up = SignUp(
            stage=SignUpStage.IDENTITY_VALIDATION,
            user_id=self.user.id
        )
        self.container.user_repo().save(self.user)
        self.container.sign_up_repo().save(self.sign_up)

    def test_get_sign_up_stage_by_user_id_view_success(self):
        expected_response_data = {
            'stage': self.sign_up.stage.value
        }

        response = self.client.get(f'{self.root_endpoint}/signup/{self.user.id}')

        assert response.status_code == 200
        assert response.json()['data'] == expected_response_data
        assert 'hyper' in response.json()

    def test_get_sign_up_stage_by_user_id_view_not_found(self):
        expected_response = {
            'error': {
                'code': 'NB-ERROR-00401',
                'message': 'Entity Not Found <SignUp>'
            }
        }

        response = self.client.get(f'{self.root_endpoint}/signup/{uuid4()}')

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == expected_response
