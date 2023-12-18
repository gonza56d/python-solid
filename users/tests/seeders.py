from typing import Any

from dependency_injector.wiring import inject, Provide

from users.containers import UserContainer
from users.core.models.locals import User
from users.core.models.states import UserStatus
from users.orm import Database


@inject
def seed(entity: Any, database: Database = Provide[UserContainer.database]):
    """Persist a object into de posgresql database."""
    with database.session() as session:
        session.add(entity)
        session.commit()


def seed_user(**kwargs):
    """Create and persist a User object into the database."""
    user = User(
        service_agr_id=1,
        status=UserStatus.ACTIVE,
        **kwargs
    )
    seed(user)
    return user
