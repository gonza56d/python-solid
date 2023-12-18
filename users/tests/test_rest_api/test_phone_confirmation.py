from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import uuid4

from users.core.models import SignUp, User
from users.core.models.states import ContactConfirmationType, SignUpStage
from users.tests.mock_factory import (
    contact_confirmation_factory_mock,
    contact_method_factory_mock,
    user_factory_mock
)
from users.tests.test_rest_api import ApiLayerTestCase


class TestPhoneConfirmationView(ApiLayerTestCase):

    def setUp(self):
        super().setUp()
        self.root_endpoint = '/v2/users'

        self.unknown_error_expected = {
            'error': {
                'code': 'NB-ERROR-00400',
                'message': 'unknown error'
            }
        }

    def test_create_phone_confirmation_success(self):
        """First scenary of the creation phone confirmation event."""
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
                confirmed=False,
                expire_at=datetime.now() - timedelta(hours=5000)
            )
        )
        existing_user.contact_methods.append(contact_method)
        self.container.user_repo().save(existing_user)

        self.container.sign_up_repo().save(
            SignUp(SignUpStage.EMAIL_CONFIRMATION, existing_user.id)
        )

        payload = {"phone_number": "+5401164372323"}

        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )

        user: User = self.container.user_repo().get_by_id(existing_user.id)
        json_response = response.json()

        assert response.status_code == HTTPStatus.CREATED
        assert len(user.contact_methods) == 2
        assert json_response['data'] == {}
        assert 'hyper' in json_response

    def test_create_phone_confirmation_less_than_9_digits_bad_request(self):
        """First scenary of the creation phone confirmation event."""
        expected = {
            'error': {
                'code': 'NB-ERROR-00402',
                'message': {
                    'phone_number': ['Invalid field']
                }
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
                confirmed=False,
                expire_at=datetime.now() - timedelta(hours=5000)
            )
        )
        existing_user.contact_methods.append(contact_method)
        self.container.user_repo().save(existing_user)

        self.container.sign_up_repo().save(
            SignUp(SignUpStage.EMAIL_CONFIRMATION, existing_user.id)
        )

        payload = {"phone_number": "+5435132483"}

        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )

        user: User = self.container.user_repo().get_by_id(existing_user.id)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert len(user.contact_methods) == 1
        assert response.json() == expected

    def test_create_phone_confirmation_14_digits_phone_number_bad_request(self):
        """First scenary of the creation phone confirmation event."""
        expected = {
            'error': {
                'code': 'NB-ERROR-00402',
                'message': {
                    'phone_number': ['Invalid field']
                }
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
                confirmed=False,
                expire_at=datetime.now() - timedelta(hours=5000)
            )
        )
        existing_user.contact_methods.append(contact_method)
        self.container.user_repo().save(existing_user)

        self.container.sign_up_repo().save(
            SignUp(SignUpStage.EMAIL_CONFIRMATION, existing_user.id)
        )

        payload = {"phone_number": "+5401164372323123"}

        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )

        user: User = self.container.user_repo().get_by_id(existing_user.id)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert len(user.contact_methods) == 1
        assert response.json() == expected

    def test_create_phone_confirmation_plus54_is_missing_bad_request(self):
        """First scenary of the creation phone confirmation event.
        """
        expected = {
            'error': {
                'code': 'NB-ERROR-00402',
                'message': {
                    'phone_number': ['Invalid field']
                }
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
                confirmed=False,
                expire_at=datetime.now() - timedelta(hours=5000)
            )
        )
        existing_user.contact_methods.append(contact_method)
        self.container.user_repo().save(existing_user)

        self.container.sign_up_repo().save(
            SignUp(SignUpStage.EMAIL_CONFIRMATION, existing_user.id)
        )

        payload = {"phone_number": "011643723231"}

        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )

        user: User = self.container.user_repo().get_by_id(existing_user.id)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert len(user.contact_methods) == 1
        assert response.json() == expected

    def test_renew_phone_confirmation_success(self):
        """First scenary of the creation phone confirmation event.
        """
        existing_user = user_factory_mock(
            service_agr_id=0,
            contact_methods=[]
        )
        contact_method_id = uuid4()
        expire_date_time = datetime.now() + timedelta(hours=1)
        contact_method = contact_method_factory_mock(
            type_='PHONE',
            value='+5412345678945',
            confirmed=True,
            contact_confirmation=contact_confirmation_factory_mock(
                user_id=str(existing_user.id),
                value='1234',
                contact_method_id=str(contact_method_id),
                confirmed=False,
                expire_at=expire_date_time,
                type=ContactConfirmationType.OTP
            )
        )
        existing_user.contact_methods.append(contact_method)
        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.PHONE_CONFIRMATION, existing_user.id)
        )
        payload = {"phone_number": "+5412345678945"}
        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )
        user: User = self.container.user_repo().get_by_id(existing_user.id)

        assert response.status_code == HTTPStatus.CREATED
        assert len(user.contact_methods) == 1
        assert user.contact_methods[0].type.description == 'PHONE'
        assert user.contact_methods[0].contact_confirmation.is_still_pending
        assert not user.contact_methods[0].contact_confirmation.is_expired
        assert user.contact_methods[0].contact_confirmation.value != contact_method.contact_confirmation.value

    def test_renew_phone_confirmation_expired_and_update_expired_time(self):
        """First scenary of the creation phone confirmation event.
        """
        existing_user = user_factory_mock(
            service_agr_id=0,
            contact_methods=[]
        )
        contact_method_id = uuid4()
        expire_date_time = datetime.now() - timedelta(hours=1)
        contact_method = contact_method_factory_mock(
            type_='PHONE',
            value='+5412345678945',
            confirmed=True,
            contact_confirmation=contact_confirmation_factory_mock(
                user_id=str(existing_user.id),
                value='1234',
                contact_method_id=str(contact_method_id),
                confirmed=False,
                expire_at=expire_date_time,
                type=ContactConfirmationType.OTP
            )
        )
        existing_user.contact_methods.append(contact_method)
        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.PHONE_CONFIRMATION, existing_user.id)
        )
        payload = {"phone_number": "+5412345678945"}
        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )
        user: User = self.container.user_repo().get_by_id(existing_user.id)

        assert response.status_code == HTTPStatus.CREATED
        assert len(user.contact_methods) == 1
        assert user.contact_methods[0].type.description == 'PHONE'
        assert user.contact_methods[0].contact_confirmation.is_still_pending
        assert not user.contact_methods[0].contact_confirmation.is_expired
        assert user.contact_methods[0].contact_confirmation.value != contact_method.contact_confirmation.value

    def test_phone_number_has_been_confirmed_badrequest(self):
        """First scenary of the creation phone confirmation event.
        """
        existing_user = user_factory_mock(
            service_agr_id=0,
            contact_methods=[]
        )
        contact_method_id = uuid4()
        contact_method = contact_method_factory_mock(
            type_='PHONE',
            value='+5412345678945',
            confirmed=True,
            contact_confirmation=contact_confirmation_factory_mock(
                user_id=str(existing_user.id),
                value='1234',
                contact_method_id=str(contact_method_id),
                confirmed=True,
                expire_at=datetime.now() + timedelta(hours=1),
                type=ContactConfirmationType.OTP
            )
        )
        existing_user.contact_methods.append(contact_method)

        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.PHONE_CONFIRMATION, existing_user.id)
        )
        payload = {"phone_number": "+5401145452323"}
        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )
        user: User = self.container.user_repo().get_by_id(existing_user.id)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert len(user.contact_methods) == 1
        assert user.contact_methods[0].type.description == 'PHONE'
        assert not user.contact_methods[0].contact_confirmation.is_still_pending
        assert not user.contact_methods[0].contact_confirmation.is_expired
        assert user.contact_methods[0] == contact_method

    def test_create_phone_number_notfound_error(self):
        """First scenary of the creation phone confirmation event."""
        user_id = ''

        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(user_id)}/phone_confirmation'
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_create_phone_number_badrequest_error(self):
        """First scenary of the creation phone confirmation event."""
        user_id = 'algo'
        payload = {}

        response = self.client.post(
            f'{self.root_endpoint}/signup/{str(user_id)}/phone_confirmation',
            json=payload
        )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == self.unknown_error_expected

    def test_confirm_phone_number_otp_not_send_error(self):
        """That happens when the otp phone number is not correct."""
        payload = {}
        response = self.client.patch(
            f'{self.root_endpoint}/signup/{str(uuid4())}/phone_confirmation',
            json=payload
        )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == self.unknown_error_expected

    def test_confirm_phone_number_user_id_not_send_error(self):
        """Raise when the user_id parameter is not in the correct format."""
        expected = {
            'error': {
                'code': 'NB-ERROR-00402',
                'message': {
                    'user_id': ['Not a valid UUID.']
                }
            }
        }
        payload = {'otp': '1234'}
        response = self.client.patch(
            f'{self.root_endpoint}/signup/{str(1234)}/phone_confirmation',
            json=payload
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == expected

    def test_confirm_phone_number_otp_is_invalid_error(self):
        """That happens when the otp phone number is not correct."""
        expected = {
            'error': {
                'code': 'NB-ERROR-00402',
                'message': 'The phone number has been confirmed.'
            }
        }

        existing_user = user_factory_mock(
            service_agr_id=0,
            contact_methods=[]
        )
        contact_method_id = uuid4()
        contact_method = contact_method_factory_mock(
            type_='PHONE',
            value='+5412345678945',
            confirmed=True,
            contact_confirmation=contact_confirmation_factory_mock(
                user_id=str(existing_user.id),
                value='1234',
                contact_method_id=str(contact_method_id),
                confirmed=True,
                expire_at=datetime.now() + timedelta(hours=1),
                type=ContactConfirmationType.OTP
            )
        )
        existing_user.contact_methods.append(contact_method)

        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.PHONE_CONFIRMATION, existing_user.id)
        )
        payload = {"otp": "0000"}
        response = self.client.patch(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == expected

    def test_confirm_phone_number_otp_is_successful(self):
        """That happens when the otp phone number is not correct."""
        existing_user = user_factory_mock(
            service_agr_id=0,
            contact_methods=[]
        )
        contact_method_id = uuid4()
        contact_method = contact_method_factory_mock(
            type_='PHONE',
            value='+543513299314',
            confirmed=True,
            contact_confirmation=contact_confirmation_factory_mock(
                user_id=str(existing_user.id),
                value='8432',
                contact_method_id=str(contact_method_id),
                confirmed=False,
                expire_at=datetime.now() + timedelta(hours=1),
                type=ContactConfirmationType.OTP
            )
        )
        existing_user.contact_methods.append(contact_method)

        self.container.user_repo().save(existing_user)
        self.container.sign_up_repo().save(
            SignUp(SignUpStage.PHONE_CONFIRMATION, existing_user.id)
        )
        payload = {"otp": "8432"}
        response = self.client.patch(
            f'{self.root_endpoint}/signup/{str(existing_user.id)}/phone_confirmation',
            json=payload
        )

        existing_user = self.container.user_repo().get_by_id(existing_user.id)
        json_response = response.json()

        assert response.status_code == HTTPStatus.OK
        assert json_response['data'] == {}
        assert 'hyper' in json_response
        assert not existing_user.contact_methods[0].contact_confirmation.is_still_pending
