import os

from alembic.command import downgrade, upgrade
from alembic.config import Config
from pymessagebus import CommandBus

from users.containers import UserContainer
from users.tests.base import BaseTestCase
from users.tests.mock_factory import TEST_ENV_VARS


class CoreTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.container = UserContainer()
        self.container.config.from_dict(TEST_ENV_VARS)
        self.container.wire(modules=['users.tests.mock_factory'])
        self.command_bus = CommandBus()
        self.jwt_secret = 'ADIVINAME'
        self.contact_confirmation_expiration_timedelta = os.environ.get(
            'CONTACT_CONFIRMATION_EXPIRATION_TIMEDELTA'
        )
        self.alembic_cfg = Config(os.environ.get('ALEMBIC_CONFIG'))
        upgrade(self.alembic_cfg, 'head')

    def tearDown(self):
        super().tearDown()
        downgrade(self.alembic_cfg, 'base')
