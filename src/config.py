from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DefaultSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        frozen=True,
        env_nested_delimiter="__",
    )


class Settings(DefaultSettings):
    """Application settings."""

    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"
    service_name: str = "rag-api"

    # MySQL configuration
    mysql_database_url: str = "mysql+pymysql://rag_user:rag_password@localhost:3306/rag_db"
    mysql_echo_sql: bool = False
    mysql_pool_size: int = 20
    mysql_max_overflow: int = 0


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
