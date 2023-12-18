from unittest.mock import MagicMock

from parameterized import parameterized

from users.core.actions import GetUserByDocument, GetUserById, GetUserContactMethods
from users.core.exceptions import EntityNotFound
from users.core.handlers import GetUserByDocumentHandler, GetUserByIdHandler
from users.core.repositories import CustomerRepository
from users.tests.mock_factory import customer_factory_mock, user_factory_mock, contact_method_factory_mock
from users.tests.test_core import CoreTestCase
from users.tests.utils import TestUtils


class TestGetUser(CoreTestCase):

    def setUp(self):
        super().setUp()
        self.customer = customer_factory_mock()
        self.customer_repo_mock = MagicMock(spec=CustomerRepository)
        self.customer_repo_mock.get_by_id.return_value = self.customer
        self.customer_repo_mock.list_by_dni.return_value = [self.customer]
        self.customer_repo_mock.list_by_cuil.return_value = [self.customer]

        self.user_repo = self.container.user_repo()
        self.contact_method_type_repo = self.container.contact_method_type_repo()

        self.get_user_by_id_handler = GetUserByIdHandler(
            user_repo=self.user_repo,
            customer_repo=self.customer_repo_mock,
        )
        self.get_user_by_document_handler = GetUserByDocumentHandler(
            user_repo=self.user_repo,
            customer_repo=self.customer_repo_mock
        )

        self.command_bus.add_handler(GetUserById, self.get_user_by_id_handler)
        self.command_bus.add_handler(
            GetUserByDocument, self.get_user_by_document_handler
        )
        self.document_number = '12345678'

        self.user = user_factory_mock(customer=self.customer, contact_methods=
        [
                contact_method_factory_mock('PHONE', confirmed=False)
        ])

   
    def test_get_user_by_id_action_success(self):
        """
        GIVEN a user in the user database
        WHEN GetUserByIdHandler is called with user.id
        THEN GetUserById succeeds
        """
        self.user_repo.save(self.user)
        action = GetUserById(self.user.id)
        obtained_user = self.command_bus.handle(action)
        assert obtained_user == self.user

    def test_get_user_by_id_fail_by_user_repo(self):
        """
        GIVEN no user in the user database
        WHEN GetUserByIdHandler is called with user.id
        THEN GetUserById fails
        """
        action = GetUserById(self.user.id)
        self.assertRaises(
            EntityNotFound,
            self.command_bus.handle,
            action
        )

    @parameterized.expand([('DNI',), ('CUIL',)])
    def test_get_user_by_document_success(self, document_type):
        """
        GIVEN a document type, document value and svcagr_id, and both customer and user
        WHEN GetUserByDocumentHandler is called
        THEN GetUserByDocument succeeds
        """
        self.user_repo.save(self.user)
        action = GetUserByDocument(
            document_type=document_type,
            document_value=self.document_number,
            service_agr_id=self.user.service_agr_id
        )
        obtained_user = self.command_bus.handle(action)
        assert obtained_user == self.user

    @parameterized.expand([('DNI',), ('CUIL',)])
    def test_get_user_by_document_fail_by_user_repo(self, document_type: str):
        """
        GIVEN a document type, documenrtvalue and svcagr_id, and no customer associated
        WHEN GetUserByDocumentHandler is called
        THEN GetUserByDocument fails
        """
        action = GetUserByDocument(
            document_type=document_type,
            document_value=self.document_number,
            service_agr_id=self.user.service_agr_id
        )
        self.customer_repo_mock.list_by_dni.return_value = []
        self.customer_repo_mock.list_by_cuil.return_value = []

        self.assertRaises(EntityNotFound, self.command_bus.handle, action)

    def test_get_user_contact_methods(self):
        """
        Ensure that GetUserContactMethods action can fetch contact methods properly.

        - Given an existent user.
        - When GetUserContactMethods action is called.
        - With the existent user's id.
        - Then the list of contact methods of that user is returned.
        """
        expected_result = [
            contact_method_factory_mock(type_='PHONE', confirmed=True),
            contact_method_factory_mock(type_='EMAIL', confirmed=True)
        ]

        user = user_factory_mock(
            customer=self.customer,
            contact_methods=expected_result
        )
        self.container.user_repo().save(user)
        action = GetUserContactMethods(user.id)
        result = self.container.command_bus().handle(action)

        assert TestUtils.compare_iterables_ignoring_order(result, expected_result)
