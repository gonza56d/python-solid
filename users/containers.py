"""Declare the IoC layer between the core and application layer."""
from logging import Logger

from dependency_injector.containers import (
    DeclarativeContainer,
    WiringConfiguration
)
from dependency_injector.providers import (
    Configuration,
    Factory,
    Object,
    Singleton
)
from nwevents import BrokerConnector, EventManager
from nwkcorelib import CommandBus, CommandBusFactory
from nwloggers import make_logger
from sqlalchemy import MetaData

from users.api.providers import RestApiCCIDProvider
from users.core.actions import (
    ConfirmIdentity,
    ConfirmPhoneNumber,
    CreatePhoneConfirmation,
    CreateSignUp,
    GetIdentityValidation,
    GetServiceAgreement,
    GetSignUpStageByUserId,
    GetUserByDocument,
    GetUserById,
    GetUserContactMethods,
    UpdateLegalValidation,
    ValidateEmailConfirmationToken,
    ValidateUserIdentity,
)
from users.core.handlers import (
    ConfirmIdentityHandler,
    ConfirmPhoneNumberHandler,
    CreatePhoneConfirmationHandler,
    CreateSignUpHandler,
    GetIdentityHandler,
    GetServiceAgreementByIDHandler,
    GetSignUpStageByUserIdHandler,
    GetUserByDocumentHandler,
    GetUserByIdHandler,
    GetUserContactMethodsHandler,
    TokenValidationHandler,
    UpdateLegalValidationHandler,
    ValidateUserIdentityHandler,
)
from users.core.repositories import (
    AddressRepository,
    ContactMethodRepository,
    ContactMethodTypeRepository,
    CustomerRepository,
    IdentityValidationRepository,
    ServiceAgreementRepository,
    SignUpRepository,
    UserRepository,
)
from users.orm import Database
from users.orm.mappings import metadata_obj
from users.orm.repositories import (
    ContactMethodDbRepository,
    ContactMethodTypeDbRepository,
    ServiceAgreementDbRepository,
    SignUpDbRepository,
    UserDbRepository,
)
from users.rest_client import (
    CustomerHttpRepository,
    IdentityValidationHttpRepository,
    MerlinHttpRepository,
)


class UserContainer(DeclarativeContainer):
    """Dependency container for the Users consumer."""

    wiring_config = WiringConfiguration(modules=[
        "users.api.views",
        "users.api.routers",
        "users.api.exceptions",
        "users.api.middlewares",
        "users.tests.seeders"
    ])
    config = Configuration()
    rest_api_ccid_provider: Singleton[RestApiCCIDProvider] = Singleton(
        RestApiCCIDProvider
    )
    logger: Object[Logger] = Object(make_logger('users-svc'))
    metadata: Object[MetaData] = Object(metadata_obj)
    database: Singleton[Database] = Singleton(
        Database,
        config.db_uri,
        logger
    )
    broker_connector: Singleton[BrokerConnector] = Singleton(
        BrokerConnector,
        broker_url=config.broker_url
    )
    event_manager: Factory[EventManager] = Factory(
        EventManager,
        connector=broker_connector
    )
    contact_method_type_repo: Factory[ContactMethodTypeRepository] = \
        Factory(ContactMethodTypeDbRepository, database.provided.session)
    user_repo: Factory[UserRepository] = Factory(
        UserDbRepository,
        session_factory=database.provided.session
    )
    contact_method_repo: Factory[ContactMethodRepository] = Factory(
        ContactMethodDbRepository,
        session_factory=database.provided.session
    )
    sign_up_repo: Factory[SignUpRepository] = Factory(
        SignUpDbRepository,
        session_factory=database.provided.session
    )
    customer_repo: Factory[CustomerRepository] = Factory(
        CustomerHttpRepository,
        customer_api_url=config.customer_api_url,
        ccid_provider=rest_api_ccid_provider
    )
    service_agreement_repo: Factory[ServiceAgreementRepository] = Factory(
        ServiceAgreementDbRepository,
        session_factory=database.provided.session
    )
    identity_validation_repo: Factory[IdentityValidationRepository] = Factory(
        IdentityValidationHttpRepository,
        identity_validation_svc_url=config.identity_validation_svc_url,
        ccid_provider=rest_api_ccid_provider
    )
    merlin_repo: Factory[AddressRepository] = Factory(
        MerlinHttpRepository,
        address_url=config.merlin_api_url,
        ccid_provider=rest_api_ccid_provider,
    )

    command_bus: CommandBusFactory[CommandBus] = CommandBusFactory({
        GetUserById: Factory(
            GetUserByIdHandler,
            user_repo=user_repo,
            customer_repo=customer_repo
        ),
        GetUserByDocument: Factory(
            GetUserByDocumentHandler,
            user_repo=user_repo,
            customer_repo=customer_repo
        ),
        CreateSignUp: Factory(
            CreateSignUpHandler,
            sign_up_repo=sign_up_repo,
            user_repo=user_repo,
            contact_method_repo=contact_method_repo,
            contact_method_type_repo=contact_method_type_repo,
            jwt_secret=config.jwt_secret,
            event_manager=event_manager,
            contact_confirmation_expiration_timedelta=config.
            contact_confirmation_expiration_timedelta
        ),
        CreatePhoneConfirmation: Factory(
            CreatePhoneConfirmationHandler,
            user_repo=user_repo,
            contact_method_type_repo=contact_method_type_repo,
            event_manager=event_manager
        ),
        ConfirmPhoneNumber: Factory(
            ConfirmPhoneNumberHandler,
            sign_up_repo=sign_up_repo,
            user_repo=user_repo,
            contact_method_type_repo=contact_method_type_repo
        ),
        ValidateEmailConfirmationToken: Factory(
            TokenValidationHandler,
            contact_method_repo=contact_method_repo,
            sign_up_repo=sign_up_repo
        ),
        ValidateUserIdentity: Factory(
            ValidateUserIdentityHandler,
            user_repo=user_repo,
            sign_up_repo=sign_up_repo,
            identity_validation_repo=identity_validation_repo,
        ),
        GetSignUpStageByUserId: Factory(
            GetSignUpStageByUserIdHandler,
            sign_up_repo=sign_up_repo
        ),
        GetServiceAgreement: Factory(
            GetServiceAgreementByIDHandler,
            service_agr_repo=service_agreement_repo
        ),
        GetIdentityValidation: Factory(
            GetIdentityHandler,
            user_repo=user_repo,
            sign_up_repo=sign_up_repo,
            identity_validation_repo=identity_validation_repo,
            address_repo=merlin_repo,
        ),
        UpdateLegalValidation: Factory(
            UpdateLegalValidationHandler,
            user_repo=user_repo,
            customer_repo=customer_repo,
            sign_up_repo=sign_up_repo
        ),
        GetUserContactMethods: Factory(
            GetUserContactMethodsHandler,
            user_repo=user_repo,
        ),
        ConfirmIdentity: Factory(
            ConfirmIdentityHandler,
            user_repo=user_repo,
            identity_validation_repo=identity_validation_repo,
            address_repo=merlin_repo,
            customer_repo=customer_repo,
            sign_up_repo=sign_up_repo,
        ),
    })
