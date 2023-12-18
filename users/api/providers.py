from contextvars import ContextVar
from typing import Optional
from uuid import UUID, uuid4

from fastapi import Request

from users.core.exceptions import WrongCCIDError


class RestApiCCIDProvider:
    """
    Callable Singleton that hold the current request to provide the CCID.

    Whenever that a request I/O happens the ccid will be holded.
    """

    def __init__(self):
        """
        Initialize the optional attributes to the provider.

        This object is injected as a singleton in FastAPI ContextMiddleware,
        latter will provide the request object to the CCID Provider.
        """
        self.request: Optional[Request] = None
        self.context: ContextVar[UUID] = ContextVar('ccid')

    def __call__(self) -> UUID:
        """Provide the setted CCID from the request or from it self."""
        raw_ccid: Optional[str] = None

        if self.request:
            raw_ccid = self.request\
                .headers\
                .get('X-Correlation-ID', None)

        if raw_ccid is not None:
            try:
                self.context.set(UUID(raw_ccid))
            except ValueError as error:
                raise WrongCCIDError(raw_ccid) from error

        return self.context.get(uuid4())
