import os
from pathlib import Path
from typing import List, Literal, Union

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


class MySQLSettings(BaseConfigSettings):
    """MySQL database configuration settings."""

    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="MYSQL__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )

    database_url: str = "mysql+pymysql://user:password@localhost:3306/database"
    echo_sql: bool = False
    pool_size: int = 10
    max_overflow: int = 0


class OpenSearchSettings(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="OPENSEARCH__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )

    host: str = "http://localhost:9200"
    index_name: str = "arxiv-papers"
    chunk_index_suffix: str = (
        "chunks"  # Creates single hybrid index: {index_name}-{suffix}
    )
    max_text_size: int = 1000000

    # Vector search settings
    vector_dimension: int = 1024  # Jina embeddings dimension
    vector_space_type: str = "cosinesimil"  # cosinesimil, l2, innerproduct

    # Hybrid search settings
    rrf_pipeline_name: str = "hybrid-rrf-pipeline"
    hybrid_search_size_multiplier: int = 2  # Get k*multiplier for better recall


class EmbeddingsSettings(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="EMBEDDINGS__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )

    jina_api_key: str
    dimension: int = 1024
    model_name: str = "jina-embeddings-v3"


class ChunkingSettings(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="CHUNKING__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )

    # General chunking settings
    chunk_size: int = 600  # Target words per chunk
    overlap_size: int = 100  # Words to overlap between chunks
    min_chunk_size: int = 100  # Minimum words for a valid chunk

    # Section-based chunking settings
    section_based: bool = True  # Use section-based chunking when available
    min_words_per_section: int = 100  # Minimum words for a section to be a chunk
    max_words_per_section: int = 800  # Maximum words for a section to be a chunk
    max_section_depth: int = 3

    # Metadata filtering settings
    min_words_per_content: int = 20
    min_section_title_length: int = 5
    max_metadata_title_length: int = 20

    # Metadata detection settings
    max_metadata_content_words: int = 30
    min_metadata_patterns: int = 2

    # Abstract duplicate detection settings
    min_abstract_words_for_duplicate_check: int = 10
    abstract_duplicate_overlap_threshold: float = 0.8

    # Small section merging settings
    min_combined_chunk_words: int = 200
    max_combined_section_titles: int = 3


class DomainClassifierSettings(BaseConfigSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", str(ENV_FILE_PATH)],
        env_prefix="DOMAIN_CLASSIFIER__",
        extra="ignore",
        frozen=True,
        case_sensitive=False,
    )
    classifier_type: str = "gemini"
    api_key: str
    model_name: str = "gemini-2.5-flash-lite"


class Settings(BaseConfigSettings):
    """Application settings."""

    app_version: str = "0.1.0"
    debug: bool = True
    environment: Literal["development", "staging", "production"] = "development"
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

    # OpenSearch settings
    opensearch: OpenSearchSettings = Field(default_factory=OpenSearchSettings)

    # PDF parser settings
    pdf_parser: PDFParserSettings = Field(default_factory=PDFParserSettings)

    # Embeddings settings
    embeddings: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)

    # Text chunker settings
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)

    # MySQL settings
    mysql: MySQLSettings = Field(default_factory=MySQLSettings)

    # Domain classifier settings
    domain_classifier: DomainClassifierSettings = Field(
        default_factory=DomainClassifierSettings
    )

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
