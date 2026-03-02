from pydantic_settings import BaseSettings, SettingsConfigDict


class DefaultSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        frozen=True,  # Make settings immutable after initialization
        env_nested_delimiter="__",  # Support nested environment variables using double underscores
    )


class Settings(DefaultSettings):
    """Application configuration settings."""

    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    service_name: str = "rag-api"

    # MySQL Database Settings
    mysql_url: str = "mysql+pymysql://user:password@localhost:3306/database"
    mysql_echo_sql: bool = False
    mysql_pool_size: int = 20
    mysql_max_overflow: int = 0


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
