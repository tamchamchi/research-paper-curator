import os
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


class ArxivSettings(DefaultSettings):
    """Arxiv API client settings."""

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
    search_categories: str = "cs.AI"
    download_max_retries: int = 3
    download_retry_delay_base: float = 5.0  # base delay in seconds for retrying PDF downloads

    @field_validator("pdf_cache_dir")
    @classmethod
    def validate_cache_dir(cls, v: str) -> str:
        os.makedirs(v, exist_ok=True)
        return v


class PDFParserSettings(DefaultSettings):
    """PDF parser settings."""

    max_pages: int = 30
    max_file_size_mb: int = 20
    do_ocr: bool = True
    do_table_structure: bool = True


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

    # arXiv settings
    arxiv: ArxivSettings = Field(default_factory=ArxivSettings)

    # PDF parser settings
    pdf_parser: PDFParserSettings = Field(default_factory=PDFParserSettings)

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
