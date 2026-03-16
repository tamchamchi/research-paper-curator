from functools import lru_cache
from typing import Annotated, Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.config import Settings
from src.db.interfaces.base import BaseDatabase
from src.services.arxiv.client import ArxivClient
from src.services.cache.client import CacheClient
from src.services.domain_classifier.base import BaseDomainClassifier
from src.services.embeddings.jina_client import JinaEmbeddingsClient
from src.services.ollama.client import OllamaClient
from src.services.opensearch.client import OpenSearchClient
from src.services.pdf_parser.parser import PDFParserService
from src.services.small_talk_handle.small_talk_handler import SmallTalkHandler


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


def get_opensearch_client(request: Request) -> OpenSearchClient:
    """Get the OpenSearch client instance from the request state."""
    return request.app.state.opensearch_client


def get_arxiv_client(request: Request) -> ArxivClient:
    """Get the arXiv API client instance from the request state."""
    return request.app.state.arxiv_client


def get_pdf_parser(request: Request) -> PDFParserService:
    """Get the PDF parser service instance from the request state."""
    return request.app.state.pdf_parser


def get_embeddings_service(request: Request) -> JinaEmbeddingsClient:
    """Get embeddings service from the request state."""
    return request.app.state.embeddings_service


def get_ollama_client(request: Request) -> OllamaClient:
    """Get Ollama client from the request state."""
    return request.app.state.ollama_client


def get_domain_classifier(request: Request) -> BaseDomainClassifier:
    """Get the domain classifier instance from the request state."""
    return request.app.state.domain_classifier


def get_small_talk_handler(request: Request):
    """Get the small talk handler instance from the request state."""
    return request.app.state.small_talk_handler


def get_cache_client(request: Request) -> CacheClient:
    """Get the cache client instance from the request state."""
    return request.app.state.cache_client


# Dependency type aliases for better type hints
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[BaseDatabase, Depends(get_database)]
SessionDep = Annotated[Session, Depends(get_db_session)]
OpenSearchDep = Annotated[OpenSearchClient, Depends(get_opensearch_client)]
ArxivDep = Annotated[ArxivClient, Depends(get_arxiv_client)]
PDFParserDep = Annotated[PDFParserService, Depends(get_pdf_parser)]
EmbeddingsDep = Annotated[JinaEmbeddingsClient, Depends(get_embeddings_service)]
OllamaDep = Annotated[OllamaClient, Depends(get_ollama_client)]
DomainClassifierDep = Annotated[BaseDomainClassifier, Depends(get_domain_classifier)]
SmallTalkHandlerDep = Annotated[SmallTalkHandler, Depends(get_small_talk_handler)]
CacheDep = Annotated[CacheClient, Depends(get_cache_client)]
