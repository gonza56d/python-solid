from http import HTTPStatus
import json
from logging import Logger

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, Request
from fastapi.responses import JSONResponse

from users.api.providers import RestApiCCIDProvider
from users.containers import UserContainer
from users.core import exceptions as e


exception_status_map = {
    e.EntityNotFound: HTTPStatus.OK,
    e.ResolutionError: HTTPStatus.CONFLICT,
    e.DependencyError: HTTPStatus.FAILED_DEPENDENCY,
    e.ValidationError: HTTPStatus.BAD_REQUEST,
    e.StorageReadError: HTTPStatus.INTERNAL_SERVER_ERROR
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
    logger = logger.patch(
        lambda record: record['extra'].update(ccid=str(ccid_provider()))
    )
    payload = await request.body() or '{}'
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
            'content': json.loads(response.body)
        }
    }
    logger.log(level, message)


async def user_error_handler(
    request: Request,
    exception: e.UserError
) -> JSONResponse:
    """Intercept the exception handle a unique json response interface."""
    status_code = exception_status_map.get(
        type(exception),
        HTTPStatus.INTERNAL_SERVER_ERROR
    )
    response = JSONResponse(
        status_code=status_code,
        content={
            'error': {
                'code': exception.code,
                'message': exception.message
            }
        }
    )
    await log_http('DEBUG', request, response)
    return response


@inject
async def unknown_error_handler(
    request: Request,
    exception: Exception,
    logger: Logger = Depends(Provide[UserContainer.logger])
) -> JSONResponse:
    """Intercept the unkown error a unique json response interface."""
    logger.exception(exception)
    response = JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={
            'error': {
                'code': 'NB-ERROR-00400',
                'message': 'unknown error'
            }
        }
    )
    await log_http('DEBUG', request, response)
    return response
