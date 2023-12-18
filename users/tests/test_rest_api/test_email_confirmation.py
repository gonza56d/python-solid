from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4

from users.core.models.states import SignUpStage
from users.tests.test_rest_api import ApiLayerTestCase
from users.core.models import SignUp, User
from users.tests.mock_factory import (
    contact_confirmation_factory_mock,
    contact_method_factory_mock,
    user_factory_mock,
)


class TestEmailConfirmation(ApiLayerTestCase):

    def test_email_confirmation_success(self):
        """Most common happy path for users' sign up.

        Ensure that the email confirmation is working without any conflict as
        expected.
        """
        request_payload = {
            'service_agr_id': 0,
            'email': 'test6@email.com'
        }

        response = self.client.post(
            f'{self.root_endpoint}/signup/email_confirmation',
            json=request_payload
        )
        user_id = response.json()['user_id']
        user: User = self.container.user_repo().get_by_id(user_id)

        assert response.status_code == HTTPStatus.OK
        assert user.service_agr_id == request_payload['service_agr_id']
        assert len(user.contact_methods) == 1
        assert user.contact_methods[0].type.description == 'EMAIL'
        assert request_payload['email']\
               in [email.value for email in user.contact_methods]

    def test_email_confirmation_success_by_renewing_contact_confirmation(self):
        """Alternative happy path for users' sign up when confirmation expired.

        Insert user data with an expired contact confirmation, so that it is
        expected that the user and contact method creation will be skipped
        while the contact confirmation expiration date will be refreshed in
        order to be ready and pending for users' confirmation again.
        """
        request_payload = {
            'service_agr_id': 0,
            'email': 'test6@email.com'
        }
        existing_user = user_factory_mock(
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
                expire_at=datetime.now() - timedelta(hours=5000)
            )
        )
        existing_user.contact_methods.append(contact_method)

        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.EMAIL_CONFIRMATION, existing_user.id)
        )
        response = self.client.post(
            f'{self.root_endpoint}/signup/email_confirmation',
            json=request_payload
        )
        user_id = response.json()['user_id']
        user: User = self.container.user_repo().get_by_id(user_id)

        assert response.status_code == HTTPStatus.OK
        assert user.service_agr_id == request_payload['service_agr_id']
        assert len(user.contact_methods) == 1
        assert user.contact_methods[0].type.description == 'EMAIL'
        assert request_payload['email'] \
               in [email.value for email in user.contact_methods]

    def test_email_confirmation_fail_by_pending_contact_confirmation(self):
        """Alternative path when the contact confirmation is still pending.

        The first post request is expected to be successful, while the second
        one is expected to response a bad request, telling that the email
        confirmation is active and still in progress.
        """
        request_payload = {
            'service_agr_id': 0,
            'email': 'test6@email.com'
        }
        bad_request_response_payload = {
            'error': {
                'code': 'NB-ERROR-00402',
                'message': 'Contact confirmation for the submitted email is '
                           'still active and pending.'
            }
        }

        first_response = self.client.post(
            f'{self.root_endpoint}/signup/email_confirmation',
            json=request_payload
        )
        second_response = self.client.post(
            f'{self.root_endpoint}/signup/email_confirmation',
            json=request_payload
        )

        assert first_response.status_code == HTTPStatus.OK
        assert second_response.status_code == HTTPStatus.BAD_REQUEST
        assert second_response.json() == bad_request_response_payload

    def test_email_confirmation_fail_by_email_taken(self):
        """Alternative path when the submitted email is already taken.

        Insert user data with a confirmed email and ensure that user receives a
        bad request response after making a request with the same previous
        email.
        """
        request_payload = {
            'service_agr_id': 0,
            'email': 'test6@email.com'
        }
        bad_request_response_payload = {
            'error': {
                'code': 'NB-ERROR-00402',
                'message': 'Email already taken.'
            }
        }
        existing_user = user_factory_mock(
            service_agr_id=0,
            contact_methods=[]
        )
        contact_method_id = uuid4()
        contact_method = contact_method_factory_mock(
            type_='EMAIL',
            value='test6@email.com',
            confirmed=True,
            contact_confirmation=contact_confirmation_factory_mock(
                user_id=str(existing_user.id),
                contact_method_id=str(contact_method_id),
                expire_at=datetime.now() - timedelta(hours=5000),
                confirmed=True,
                confirmed_at=datetime.now() - timedelta(hours=3)
            )
        )
        existing_user.contact_methods.append(contact_method)

        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.EMAIL_CONFIRMATION, existing_user.id)
        )
        response = self.client.post(
            f'{self.root_endpoint}/signup/email_confirmation',
            json=request_payload
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == bad_request_response_payload
