from fastapi import FastAPI
from fastapi_versioning import VersionedFastAPI

from users.api import views
from users.api.middlewares import rest_api_ccid_provider_middleware
from users.containers import UserContainer


def create_app() -> FastAPI:
    """Configure the application container and start event loop listening."""
    container = UserContainer()
    container.config.db_uri.from_env('DB_URI')
    container.config.customer_api_url.from_env('CUSTOMER_API_URL')
    container.config.jwt_secret.from_env('JWT_SECRET')
    container.config.broker_url.from_env('BROKER_URL')
    container.config.contact_confirmation_expiration_timedelta.from_env(
        'CONTACT_CONFIRMATION_EXPIRATION_TIMEDELTA'
    )
    container.config.identity_validation_svc_url.from_env('IDENTITY_VALIDATION_SVC_URL')
    container.config.merlin_api_url.from_env('MERLIN_API_URL')

    app = FastAPI()
    app.container = container
    app.include_router(views.routes)
    app.include_router(views.apidoc)
    app = VersionedFastAPI(
        app,
        version_format="{major}",
        prefix_format="/v{major}"
    )
    app.middleware('http')(rest_api_ccid_provider_middleware)

    return app


app = create_app()
