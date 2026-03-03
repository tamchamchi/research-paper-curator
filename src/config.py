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
    mysql_database_url: str = (
        "mysql+pymysql://rag_user:rag_password@localhost:3306/rag_db"
    )
    mysql_echo_sql: bool = False
    mysql_pool_size: int = 20
    mysql_max_overflow: int = 0

    # Ollama configuration
    ollama_host: str = "http://localhost:11434"
    ollama_models: Union[str, List[str]] = Field(default=["llama3.2:1b", "gpt-oss:20b"])
    ollama_default_model: str = "llama3.2:1b"
    ollama_timeout: int = 300  # 5 minutes for larger models operations

    @field_validator("ollama_models", mode="before")
    @classmethod
    def validate_ollama_models(cls, v):
        """Parse comma-separated string of models into a list."""
        if isinstance(v, str):
            return [model.strip() for model in v.split(",")]
        return v


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
