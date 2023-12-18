from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from logging import Logger
from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, Session, sessionmaker


class Database:
    """Represent the database objent interface."""

    def __init__(self, db_uri: str, logger: Logger):
        """Initialize the database connection base components."""
        self.__logger = logger
        self.__engine = create_engine(
            db_uri,
            echo=False,
            future=True,
            pool_pre_ping=True
        )
        self.__session_factory = scoped_session(
            sessionmaker(
                bind=self.__engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        )

    @contextmanager
    def session(self) -> Callable[..., AbstractContextManager[Session]]:
        """Provide a session on a context manager for the repositories."""
        session: Session = self.__session_factory()
        try:
            yield session
        except Exception as error:
            self.__logger.exception(error)
            session.rollback()
            raise
        finally:
            session.close()
