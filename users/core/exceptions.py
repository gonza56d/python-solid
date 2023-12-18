from abc import ABC, abstractmethod
from typing import Type, Union
from uuid import UUID

from nwrest.exceptions import PropagableHttpError


class UserError(ABC, Exception):
    """Abstraction and superclass of all errors, works as a interface."""

    @property
    @abstractmethod
    def message(self) -> str:
        """Retrive the exception message."""
        pass

    @property
    @abstractmethod
    def code(self) -> str:
        """Retrive the validation error code."""
        pass


class EntityNotFound(UserError):
    """When a Entity of the model could not be retrived from the datasource."""

    def __init__(self, entity_type: Type = None) -> None:
        """Initialize the name of entity type that not found."""
        self.__message = "Entity Not Found"

        if entity_type is not None:
            self.__message = f"Entity Not Found <{entity_type.__name__}>"

    @property
    def message(self) -> Union[str, dict]:
        """Return the exception message."""
        return self.__message

    @property
    def code(self) -> str:
        """Return the code for exceptions of type 'functional'."""
        return 'NB-ERROR-00401'


class DependencyError(UserError):
    """Raises when a external rest api response fails."""

    def __init__(self, code: str, message: str):
        """Provide the external code and message for the response."""
        self.__code = code
        self.__message = message

    @property
    def message(self) -> str:
        """Return the exception message."""
        return self.__message

    @property
    def code(self) -> str:
        """Return the code for exception generated by the external service."""
        return self.__code


class ResolutionError(UserError):
    """Internal error raised when more than one contact method was found."""

    def __init__(self, contact_method_type: str, user_id: UUID):
        """Indicate the contact method type and user id for more info."""
        self.contact_method_type = contact_method_type
        self.user_id = user_id

    @property
    def message(self) -> str:
        """Return a message specifying contact method type and user id."""
        return 'Too many contact methods '\
               f'with type={self.contact_method_type} '\
               f'and user_id={str(self.user_id)}'

    @property
    def code(self) -> str:
        """Return the status code for this microservice and error."""
        return 'NB-ERROR-00405'


class ValidationError(UserError):
    """Raised when some schema has failed to validate(client request error)."""

    def __init__(self, validation_error: str, code: str = None):
        """Init with validation error message."""
        self.__message = validation_error
        self.__code = code

    @property
    def message(self) -> str:
        """Error message describing the field(s) with error(s)."""
        return self.__message

    @property
    def code(self) -> str:
        """Status code for schema's validation errors."""
        return self.__code or 'NB-ERROR-00402'


class StorageReadError(UserError):
    """Raised when the microservices have a database problem."""

    @property
    def message(self) -> str:
        """Retrive the exception message."""
        return 'Storage Error'

    @property
    def code(self) -> str:
        """Retrive the validation error code."""
        return 'NB-ERROR-00403'


class WrongCCIDError(UserError):
    """When provided str is not possible to be casted as UUID."""

    def __init__(self, uuid: str):
        """Initialize this exception with given str."""
        self.__uuid = uuid

    @property
    def message(self) -> str:
        """Retrieve the exception message."""
        return f'It was not possible to cast "{self.__uuid}" as UUID.'

    @property
    def code(self) -> str:
        """Retrive the error code."""
        return 'NB-ERROR-00410'


class IdentityValidationError(UserError):
    """When requested identity validation is not in the proper state."""

    def __init__(
        self,
        signup_stage_state=None
    ):
        """Initialize with proper attrs."""
        self.__signup_stage_state = signup_stage_state

    @property
    def message(self) -> str:
        """Retrieve the exception message."""
        if self.__signup_stage_state is None:
            return 'User did not perform identity validation yet.'

        return f'Current signup stage is {self.__signup_stage_state}'

    @property
    def code(self) -> str:
        """Retrieve the error code."""
        return 'NB-ERROR-00450'


class EntityGoneError(UserError):
    """When the searched entity has been removed from memory."""

    def __init__(self, entity: str, code: str = None):
        """Initialize indicating the entity which wasn't found for a clearer message."""
        self.__entity = entity
        self.__code = code

    @property
    def message(self) -> str:
        """Return the exception message."""
        return self.__entity

    @property
    def code(self) -> str:
        """Return the code for this kind of exception."""
        return self.__code or 'NB-ERROR-00411'


class AttemptsExceededError(PropagableHttpError):
    """When user has exceeded its identity validation attempts."""

    @property
    def banned_notified(self) -> bool:
        """Return if zendesk ticket was sent."""
        return self.code == 'NB-ERROR-00851'


class IdentityDataError(PropagableHttpError):
    """When identity data response was corrupt."""

    @property
    def banned_notified(self) -> bool:
        """Return if zendesk ticket was sent."""
        return self.code == 'NB-ERROR-00861'


class UserIdentityMinorError(PropagableHttpError):
    """When identity validation response indicates that user is a minor."""

    pass


class MissingAddressError(UserError):
    """When address request did not find anything for the requested user."""

    @property
    def message(self) -> str:
        """Return message."""
        return 'Missing addresses. Must add a new address.'

    @property
    def code(self) -> str:
        """Return error code."""
        return 'NB-ERROR-00451'


class UserIdentityTeenPartialError(Exception):
    """Raised identity validation response indicates that user is a teen."""

    def __init__(self, user_id: UUID):
        """Indicate the user id for the user.status update."""
        self.user_id = user_id


class DuplicatedResourceError(UserError):
    """Raised when more than one resource was found when it should be one."""

    def __init__(self, resource: Type):
        """Initialize with entity name for a clearer error message."""
        self.__resource = resource.__name__

    @property
    def message(self) -> str:
        """Error message."""
        return f'Multiple results for entity {self.__resource} found.'

    @property
    def code(self) -> str:
        """Error code."""
        return 'NB-ERROR-00452'
