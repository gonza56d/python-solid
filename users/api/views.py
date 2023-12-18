from http import HTTPStatus
from typing import Optional
from uuid import UUID

from dependency_injector.wiring import (
    inject,
    Provide,
)
from fastapi import Depends
from fastapi.responses import FileResponse, JSONResponse
from nwkcorelib import CommandBus

from users.api.routers import apidoc, routes, v2
from users.containers import UserContainer
from users.core.actions import GetUserContactMethods
from users.core.models import Identity, SignUp
from users.core.models.states import SignUpStage
from users.odm.schemas import (
    ConfirmIdentityResponseSchema,
    ConfirmIdentitySchema,
    ConfirmPhoneNumberRequest,
    CreateSignUpSchema,
    ErrorSchema,
    GetIdentityValidationSchema,
    GetServiceAgreementRequest,
    GetServiceAgreementResponse,
    GetUserByDocumentRequest,
    GetUserByIdRequest,
    GetUserContactMethodsRequest,
    GetUserContactMethodsResponse,
    IdentitySchema,
    RequestSignUpStageByUserId,
    SavePhoneConfirmationResponse,
    SignUpResourceSchema,
    TokenValidationRequestSchema,
    UpdateLegalValidationRequest,
    UpdateLegalValidationResponse,
    UserByDocumentResource,
    UserByIdResource,
    UserIdentityValidationRequestSchema,
    UserPhoneNumberConfirmationRequest,
    UserResourceSchema,
)
from users.orm import Database


@routes.get("/status")
@v2
@inject
def status(database: Database = Depends(Provide[UserContainer.database])):
    """Check the status of the private resource of the service."""
    with database.session() as session:
        session.execute("SELECT 1")

    return JSONResponse(status_code=HTTPStatus.OK)


@apidoc.get('/swagger.yml')
@v2
def docs() -> FileResponse:
    """Get the swagger yml file."""
    yml_path = '/app/users/api/docs/v2.yml'
    return FileResponse(
        status_code=HTTPStatus.OK,
        path=yml_path,
        filename='swagger.yml'
    )


@routes.get('/byId/{user_id}')
@v2
@inject
def get_user_by_id(
    user_id: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """
    Get a specific user by its ID.

    Parameters
    ----------
    user_id: uuid
        ID to match the user to get.

    command_bus: CommandBus

    Returns
    -------
    JSONResponse
        A single user with its customer data.
    """
    request_schema = GetUserByIdRequest()
    response_schema = UserByIdResource(
        url_resolver=routes.url_path_for,
        view_to_resolve='get_user_by_id',
        api_version=2,
        view_kwargs={'user_id': user_id},
        http_methods=['GET']
    )

    loaded_request_schema = request_schema.load({'user_id': user_id})

    user = command_bus.handle(loaded_request_schema.data)

    response_schema.dump(user)

    return JSONResponse(
        content=response_schema.data_with_hypermedia,
        status_code=HTTPStatus.OK
    )


@routes.get('/{user_id}')
@v2
@inject
def get_user(
    user_id: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """
    Get a specific user by its ID.

    Parameters
    ----------
    user_id: uuid
        ID to match the user to get.

    command_bus: CommandBus

    Returns
    -------
    JSONResponse
        A single user with its customer data.
    """
    request_schema = GetUserByIdRequest()
    response_schema = UserResourceSchema()

    get_user_action = request_schema.load({'user_id': user_id}).data
    get_user_action.fetch_customer = False
    user = command_bus.handle(get_user_action)

    response_content = {
        'data': response_schema.dump(user).data,
        'hyper': {}
    }

    return JSONResponse(
        content=response_content,
        status_code=HTTPStatus.OK
    )


@routes.get('/{user_id}/contact_methods')
@v2
@inject
def get_user_contact_methods(
    user_id: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """
    Get some user's list of contact methods.

    Parameters
    ----------
    user_id: uuid
        ID to match the user to get contact methods from.

    command_bus: CommandBus

    Returns
    -------
    JSONResponse
        A list with all the contact methods of the user found.
    """
    request_schema = GetUserContactMethodsRequest()
    response_schema = GetUserContactMethodsResponse()

    action: GetUserContactMethods = request_schema.load({'user_id': user_id}).data

    result = command_bus.handle(action)

    serialized_data = response_schema.dump(result, many=True).data

    return JSONResponse(
        content={
            'data': serialized_data,
            'hyper': {},
        },
        status_code=HTTPStatus.OK
    )


@routes.get(
    '/byDocument/{document_type}/{document_value}'
    '/businessModel/{business_model}'
)
@v2
@inject
def get_user_by_business_model(
    document_type: str,
    document_value: str,
    business_model: int,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Retrieve a specific user by its document and business model."""
    request_schema = GetUserByDocumentRequest()
    response_schema = UserByIdResource()
    loaded_request_schema = request_schema.load({
        'document_type': document_type,
        'document_value': document_value,
        'business_model': business_model
    })

    user = command_bus.handle(loaded_request_schema.data)

    if user is not None:
        response = response_schema.dump(user)
        return JSONResponse(
            content=response.data,
            status_code=HTTPStatus.OK
        )
    else:
        return JSONResponse(
            content={},
            status_code=HTTPStatus.OK
        )


@routes.get(
    '/byDocument/{document_type}/{document_value}/{service_agreement_id}'
)
@v2
@inject
def get_user_by_service_agreement_id(
    document_type: str,
    document_value: str,
    service_agreement_id: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Retrieve a specific user by its document and service agreement id.

    Parameters
    ----------
    document_type : str
        Type of document to search by.

    document_value : str
        Value of the specified document to search by.

    service_agreement_id : int
        Value of the service agreement id to search by.

    command_bus : CommandBus
        Injected command bus to handle request data.

    Returns
    -------
    JSONResponse
        A single user with its customer and service agreement data
    """
    request_schema = GetUserByDocumentRequest()
    response_schema = UserByDocumentResource()
    loaded_request_schema = request_schema.load({
        'document_type': document_type,
        'document_value': document_value,
        'service_agr_id': service_agreement_id
    })

    user = command_bus.handle(loaded_request_schema.data)

    if user is not None:
        response = response_schema.dump(user)
        return JSONResponse(
            content=response.data,
            status_code=HTTPStatus.OK
        )
    else:
        return JSONResponse(
            content={},
            status_code=HTTPStatus.OK
        )


@routes.post(
    '/signup/{user_id}/phone_confirmation'
)
@v2
@inject
def create_phone_confirmation(
    user_id: str,
    payload: dict,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Send a message with a OTP number verification message.

    Parameters
    ----------
    user_id : str
        User id to send message phone confirm.

    command_bus : CommandBus
        Injected command bus to handle request data.

    Returns
    -------
    JSONResponse
        Retrieve a empty message
    """
    request_schema = UserPhoneNumberConfirmationRequest()
    response_schema = SavePhoneConfirmationResponse(
        url_resolver=routes.url_path_for,
        view_to_resolve='create_phone_confirmation',
        view_kwargs={'user_id': user_id},
        http_methods=['GET', 'PATCH']
    )

    loaded_request_schema = request_schema.load({
        'user_id': user_id,
        'phone_number': payload['phone_number']
    })

    command_bus.handle(loaded_request_schema.data)

    response_schema.dump({
        'id': user_id
    })

    return JSONResponse(
        content=response_schema.data_with_hypermedia,
        status_code=HTTPStatus.CREATED
    )


@routes.patch(
    '/signup/{user_id}/phone_confirmation'
)
@v2
@inject
def confirm_phone_number(
    user_id: str,
    payload: dict,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Send a message with a OTP code verification.

    Parameters
    ----------
    user_id : str
        User id to send message phone confirm.

    command_bus : CommandBus
        Injected command bus to handle request data.

    Returns
    -------
    JSONResponse
        Retrieve a empty message
    """
    request_schema = ConfirmPhoneNumberRequest()
    response_schema = SavePhoneConfirmationResponse(
        url_resolver=routes.url_path_for,
        view_to_resolve='create_phone_confirmation',
        view_kwargs={'user_id': user_id},
        http_methods=['GET', 'PATCH']
    )

    loaded_request_schema = request_schema.load({
        'user_id': user_id,
        'otp': payload['otp']
    })

    command_bus.handle(loaded_request_schema.data)

    response_schema.dump({'id': user_id})

    return JSONResponse(
        content=response_schema.data_with_hypermedia,
        status_code=HTTPStatus.OK
    )


@routes.post('/signup/email_confirmation')
@v2
@inject
def post_email_confirmation(
    request_payload: dict,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Create a new sign up process."""
    request_schema = CreateSignUpSchema()
    response_schema = SignUpResourceSchema(only=('user_id',))

    loaded_request_schema = request_schema.load(request_payload)

    sign_up = command_bus.handle(loaded_request_schema.data)

    response_content = response_schema.dump(sign_up)

    return JSONResponse(
        content=response_content.data,
        status_code=HTTPStatus.OK
    )


@routes.get('/signup/email_confirmation/{token}')
@v2
@inject
def post_email_confirmation_token(
    token: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """
    Perform email confirmation token validation.

    Set contact method as confirmed and sign up stage to IDENTITY_VALIDATION
    if the token validation succeed.
    """
    request_schema = TokenValidationRequestSchema()
    response_schema = SignUpResourceSchema(only=('user_id',))

    loaded_request_schema = request_schema.load({'token': token})
    token_validation: SignUp = command_bus.handle(loaded_request_schema.data)
    response_content = response_schema.dump(token_validation)

    return JSONResponse(
        content={
            'data': response_content.data,
            'hyper': {
                f'/v2/users/signup/{token_validation.user_id}/identity_validation': [
                    'POST'
                ]
            }
        },
        status_code=HTTPStatus.OK
    )


@routes.post('/signup/{user_id}/identity_validation')
@v2
@inject
def validate_user_identity(
    user_id: str,
    payload: dict,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Get user ID and request user's identity validation."""
    request_schema = UserIdentityValidationRequestSchema()

    payload.update({'user_id': user_id})
    loaded_request = request_schema.load(payload)

    user_id: Optional[UUID] = command_bus.handle(loaded_request.data)

    return JSONResponse(
        content={
            'data': {
                'user_id': str(user_id)
            },
            'hyper': {
                f'/v2/users/signup/{user_id}/identity_validation': ['GET']
            }
        } if user_id is not None else {},
        status_code=(
            HTTPStatus.CREATED if user_id is not None
            else HTTPStatus.PARTIAL_CONTENT
        )
    )


@routes.get('/signup/{user_id}/identity_validation')
@v2
@inject
def get_user_identity_validation(
    user_id: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Get user identity validation result."""
    request_schema = GetIdentityValidationSchema()
    response_schema = IdentitySchema(
        url_resolver=routes.url_path_for,
        view_to_resolve='get_user_identity_validation',
        api_version=2,
        view_kwargs={'user_id': user_id},
        http_methods=['GET'],
    )

    loaded_request = request_schema.load({'user_id': user_id})

    identity: Identity = command_bus.handle(loaded_request.data)

    response_schema.dump(identity)
    response_content = response_schema.data_with_hypermedia

    if command_bus.errors:
        response_content['errors'] = [
            ErrorSchema().dump(error).data for error in command_bus.errors
        ]

    return JSONResponse(
        content=response_content,
        status_code=(
            HTTPStatus.OK if not command_bus.errors else HTTPStatus.PARTIAL_CONTENT
        )
    )


@routes.patch('/signup/{user_id}/identity_validation')
@v2
@inject
def confirm_user_identity(
    user_id: str,
    payload: dict,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Confirm user identity. Assign address and customer."""
    request_schema = ConfirmIdentitySchema()
    response_schema = ConfirmIdentityResponseSchema()

    loaded_request = request_schema.load({'user_id': user_id, **payload})

    _user_id: UUID = command_bus.handle(loaded_request.data)
    response_data: dict = response_schema.dump({'user_id': _user_id}).data

    return JSONResponse(
        content={
            'data': response_data,
            'hyper': {
                f'/v2/users/signup/{_user_id}/legal_validation': ['PATCH'],
                f'/v2/users/byId/{_user_id}': ['GET']
            }
        },
        status_code=HTTPStatus.OK
    )


@routes.get('/signup/{user_id}')
@v2
@inject
def get_sign_up_stage(
    user_id: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Get sign up stage by its user id."""
    request_schema = RequestSignUpStageByUserId()
    response_schema = SignUpResourceSchema(
        url_resolver=routes.url_path_for,
        view_to_resolve='get_sign_up_stage',
        view_kwargs={'user_id': user_id},
        http_methods=['GET', 'PATCH', 'POST'],
        only=('stage',)
    )

    loaded_request = request_schema.load({'user_id': user_id})

    stage: SignUpStage = command_bus.handle(loaded_request.data)

    response_schema.dump({'stage': stage})

    return JSONResponse(
        content=response_schema.data_with_hypermedia,
        status_code=HTTPStatus.OK
    )


@routes.get("/service-agreements/{service_agreement_id}")
@v2
@inject
def get_service_agreement(
    service_agreement_id: str,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Retrieve any Service Agreement by ID."""
    request_schema = GetServiceAgreementRequest()
    response_schema = GetServiceAgreementResponse(
        only=('id', 'legal_validation_config',)
    )

    action = request_schema.load({'service_agreement_id': service_agreement_id}).data
    service_agr = command_bus.handle(action)
    response_schema.dump(service_agr).data
    return JSONResponse(
        content=response_schema.data_with_hypermedia,
        status_code=HTTPStatus.OK
    )


@routes.patch("/signup/{user_id}/legal_validation")
@v2
@inject
def update_legal_validation(
    user_id: str,
    payload: dict,
    command_bus: CommandBus = Depends(Provide[UserContainer.command_bus])
) -> JSONResponse:
    """Update a Legal Validation."""
    request_schema = UpdateLegalValidationRequest()
    response_schema = UpdateLegalValidationResponse(
        url_resolver=routes.url_path_for,
        view_to_resolve='update_legal_validation',
        view_kwargs={'user_id': user_id},
        http_methods=['PATCH']
    )
    payload.update({'user_id': user_id})
    action = request_schema.load(payload).data
    command_bus.handle(action)
    response_schema.dump({'user_id': user_id}).data
    return JSONResponse(
        content=response_schema.data_with_hypermedia,
        status_code=HTTPStatus.OK
    )
