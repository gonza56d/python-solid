from xml.dom import NotFoundErr
from users.core.actions import GetServiceAgreement
from users.core.exceptions import EntityNotFound
from users.core.models import states
from users.tests.mock_factory import service_agreement_factory_mock
from users.tests.test_core import CoreTestCase


class TestGetServiceAgreement(CoreTestCase):

    def setUp(self):
        super().setUp()
        self.service_agr_repo = self.container.service_agreement_repo()
        self.command_bus = self.container.command_bus()

    def test_get_service_agr_action_success(self):
        action = GetServiceAgreement(0)
        obtained_service_agr = self.command_bus.handle(action)

        service_agr_object = service_agreement_factory_mock(
            id=0,
            business_model=states.BusinessModel.NUBI
        )
        assert obtained_service_agr == service_agr_object

    def test_get_service_agr_error_not_found(self):
        action = GetServiceAgreement(654)
        with self.assertRaises(EntityNotFound):
            self.command_bus.handle(action)
