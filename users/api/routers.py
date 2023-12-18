from typing import Callable

from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute
from fastapi_versioning import version

from users.api.exceptions import (
    log_http,
    user_error_handler
)


class UsersRouteHandler(APIRoute):
    """Catch and handle exceptions when a view method is called."""

    def get_route_handler(self) -> Callable:
        """Intercept all calls to an endpoint."""
        original_route_handler = super().get_route_handler()

        async def users_route_handler(request: Request) -> Response:
            try:
                response = await original_route_handler(request)
                await log_http('INFO', request, response)
            except Exception as error:
                response = await user_error_handler(request, error)
            return response

        return users_route_handler


routes = APIRouter(
    prefix="/users",
    tags=["users"],
    route_class=UsersRouteHandler
)
apidoc = APIRouter(
    prefix="/api/docs",
    tags=["api-docs"]
)
v2 = version(2)
