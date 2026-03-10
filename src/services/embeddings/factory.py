from typing import Optional

from src.config import Settings, get_settings

from .jina_client import JinaEmbeddingsClient


def make_embeddings_service(
    settings: Optional[Settings] = None,
) -> JinaEmbeddingsClient:
    """Factory function to create embeddings service.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: JinaEmbeddingsClient instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.embeddings.jina_api_key
    model_name = settings.embeddings.model_name

    return JinaEmbeddingsClient(api_key=api_key, model_name=model_name)


def make_embeddings_client(settings: Optional[Settings] = None) -> JinaEmbeddingsClient:
    """Factory function to create embeddings client.

    Creates a new client instance each time to avoid closed client issues.

    :param settings: Optional settings instance
    :returns: JinaEmbeddingsClient instance
    """
    if settings is None:
        settings = get_settings()

    # Get API key from settings
    api_key = settings.embeddings.jina_api_key
    model_name = settings.embeddings.model_name

    return JinaEmbeddingsClient(api_key=api_key, model_name=model_name)
