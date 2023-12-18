from typing import Callable
from uuid import uuid4

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, Request

from users.api.providers import RestApiCCIDProvider
from users.containers import UserContainer


@inject
async def rest_api_ccid_provider_middleware(
    request: Request,
    next_call: Callable,
    ccid_provider: RestApiCCIDProvider = Depends(
        Provide[UserContainer.rest_api_ccid_provider]
    )
):
    """Intercept a incoming request and set it to the ccid provider."""
    ccid = ccid_provider.context.set(uuid4())
    ccid_provider.request = request
    response = await next_call(request)
    ccid_provider.context.reset(ccid)
    return response
