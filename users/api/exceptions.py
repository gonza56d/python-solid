from http import HTTPStatus
import json
from logging import Logger

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from nwodm.schemas import exceptions as odmexceptions
from nwrest.exceptions import PropagableHttpError

from users.api.providers import RestApiCCIDProvider
from users.containers import UserContainer
from users.core import exceptions as e
from users.odm.schemas import ResponseErrorSchema


exception_status_map = {
    e.EntityNotFound: HTTPStatus.NOT_FOUND,
    e.ResolutionError: HTTPStatus.CONFLICT,
    e.DependencyError: HTTPStatus.FAILED_DEPENDENCY,
    odmexceptions.ValidationError: HTTPStatus.BAD_REQUEST,
    e.ValidationError: HTTPStatus.BAD_REQUEST,
    e.StorageReadError: HTTPStatus.INTERNAL_SERVER_ERROR,
    e.IdentityValidationError: HTTPStatus.BAD_REQUEST,
    e.EntityGoneError: HTTPStatus.GONE,
}


@inject
async def log_http(
    level: str,
    request: Request,
    response: JSONResponse,
    logger: Logger = Depends(Provide[UserContainer.logger]),
    ccid_provider: RestApiCCIDProvider = Depends(
        Provide[UserContainer.rest_api_ccid_provider]
    )
):
    """Log the request and response data with a level option."""
    payload = await request.body() or '{}'
    response_content = json.loads(response.body) if hasattr(response, 'body') \
        else None
    logger = logger.bind(
        ccid=str(ccid_provider()),
        http={
            'status_code': response.status_code.value,
            'url': str(request.url)
        }
    )

    message = {
        'request': {
            'url': str(request.url),
            'headers': dict(request.headers.items()),
            'method': request.method,
            'payload': json.loads(payload)
        },
        'response': {
            'status_code': response.status_code.value,
            'headers': dict(response.headers.items()),
            'content': response_content
        }
    }
    logger.log(level, message)

    return logger


async def user_error_handler(
    request: Request,
    exception: Exception
) -> JSONResponse:
    """Intercept the exception handle a unique json response interface."""
    if isinstance(exception, PropagableHttpError):
        status_code = exception.status_code
    else:
        status_code = exception_status_map.get(type(exception))
    if status_code is None:
        return await unknown_error_handler(request, exception)

    error_schema = ResponseErrorSchema()

    response = JSONResponse(
        status_code=status_code,
        content=error_schema.dump({
            'error': {
                'code': exception.code,
                'message': exception.message
            }
        }).data
    )

    await log_http('DEBUG', request, response)
    return response


@inject
async def unknown_error_handler(
    request: Request,
    exception: Exception
) -> JSONResponse:
    """Intercept the unkown error a unique json response interface."""
    error_schema = ResponseErrorSchema()
    response = JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=error_schema.dump({
            'error': {
                'code': 'NB-ERROR-00400',
                'message': 'unknown error'
            }
        }).data
    )
    logger = await log_http('DEBUG', request, response)
    logger.exception(exception)
    return response
