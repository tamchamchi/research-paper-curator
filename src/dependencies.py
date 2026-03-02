from functools import lru_cache
from typing import Annotated, Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.config import Settings
from src.db.interfaces.base import BaseDatabase


@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching."""
    return Settings()


def get_request_settings(request: Request) -> Settings:
    """Get settings from the request state."""
    return request.app.state.settings


def get_database(request: Request) -> BaseDatabase:
    """Get the database instance from the request state."""
    return request.app.state.database


def get_db_session(
    database: BaseDatabase = Depends(get_database),
) -> Generator[Session, None, None]:
    """Get a database session for the request."""
    with database.get_session() as session:
        yield session


# Dependency type aliases for better type hints
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[BaseDatabase, Depends(get_database)]
SessionDep = Annotated[Session, Depends(get_db_session)]
