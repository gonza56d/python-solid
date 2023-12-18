import os

from alembic.command import downgrade, upgrade
from alembic.config import Config
from starlette.testclient import TestClient

from users.api.run import app
from users.containers import UserContainer
from users.tests.base import BaseTestCase
from users.tests.mock_factory import TEST_ENV_VARS


class ApiLayerTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.root_endpoint = '/v2/users'
        self.container = UserContainer()
        self.container.config.from_dict(TEST_ENV_VARS)
        self.container.wire(modules=['users.tests.mock_factory'])
        self.jwt_secret = 'ADIVINAME'
        self.client = TestClient(app)
        self.alembic_cfg = Config(os.environ.get('ALEMBIC_CONFIG'))
        upgrade(self.alembic_cfg, 'head')

    def tearDown(self):
        super().tearDown()
        downgrade(self.alembic_cfg, 'base')
