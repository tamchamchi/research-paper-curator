import os
from pathlib import Path
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class BaseConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        extra="ignore",
        frozen=True,
        env_nested_delimiter="__",
    )


class ArxivSettings(BaseConfigSettings):
    """Arxiv API client settings."""

    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="ARXIV__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )

    base_url: str = "http://export.arxiv.org/api/query"
    namespaces: dict = Field(
        default={
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
    )
    pdf_cache_dir: str = "./data/arxiv_pdfs"
    rate_limit_delay: float = 3.0  # seconds between API calls to respect rate limits
    timeout_seconds: int = 30  # timeout for API requests
    max_results: int = 10  # maximum number of results to fetch per query
    search_category: str = "cs.AI"
    download_max_retries: int = 3
    download_retry_delay_base: float = 5.0
    max_concurrent_downloads: int = 5
    max_concurrent_parsing: int = 1

    @field_validator("pdf_cache_dir")
    @classmethod
    def validate_cache_dir(cls, v: str) -> str:
        os.makedirs(v, exist_ok=True)
        return v


class PDFParserSettings(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="PDF_PARSER__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )

    max_pages: int = 30
    max_file_size_mb: int = 20
    do_ocr: bool = False
    do_table_structure: bool = True


class Settings(BaseConfigSettings):
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

    # arXiv settings
    arxiv: ArxivSettings = Field(default_factory=ArxivSettings)

    # PDF parser settings
    pdf_parser: PDFParserSettings = Field(default_factory=PDFParserSettings)

    @field_validator("mysql_database_url")
    @classmethod
    def validate_mysql_database_url(cls, v) -> str:
        """Validate MySQL database URL format."""
        if not v.startswith("mysql+pymysql://") or v.startswith("mysql://"):
            raise ValueError(
                "Database URL must start with 'mysql+pymysql://' or 'mysql://'"
            )
        return v


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
