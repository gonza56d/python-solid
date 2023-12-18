from typing import Dict, Text
from uuid import UUID, uuid4

from nwevents import Event

from users.core.models import ContactMethod, SignUp, User


class SavedSignUp(Event):
    """Event releated to a sign up saved on the database."""

    def __init__(
        self,
        sign_up: SignUp,
        user: User,
        contact_method: ContactMethod
    ):
        """Init event class by providing an ID in order to track it."""
        self.__sign_up = sign_up
        self.__user = user
        self.__contact_method = contact_method

    @property
    def ccid(self) -> UUID:
        """Retrive the correlational id of the operation saved."""
        return uuid4()

    @property
    def source(self) -> Text:
        """Retrive the sign up exchange name."""
        return 'signup'

    @property
    def name(self) -> Text:
        """Retrive the event name."""
        return 'saved'

    @property
    def payload(self) -> Dict:
        """Retrive event payload."""
        return {
            'sign_up_id': str(self.__sign_up.id),
            'service_agr_id': self.__user.service_agr_id,
            'email': self.__contact_method.value,
            'confirmation_token': (
                self.__contact_method.contact_confirmation.value
            )
        }


class SavedContactMethod(Event):
    """Event releated to create phone confirm saved on the database."""

    def __init__(
        self,
        phone_number: str,
        confirmation_otp: str
    ):
        """Init event class by providing an ID in order to track it."""
        self.__phone_number = phone_number
        self.__confirmation_otp = confirmation_otp

    @property
    def ccid(self) -> UUID:
        """Retrive the correlational id of the operation saved."""
        return uuid4()

    @property
    def source(self) -> Text:
        """Retrive the sign up exchange name."""
        return 'users'

    @property
    def name(self) -> Text:
        """Retrive the event name."""
        return 'contact_method_saved'

    @property
    def payload(self) -> Dict:
        """Retrive event payload."""
        return {
            'recipients': [self.__phone_number],
            'body': self.__confirmation_otp
        }
