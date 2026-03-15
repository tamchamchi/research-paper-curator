from functools import lru_cache

from src.config import get_settings
from src.services.embeddings.factory import make_embeddings_client

from .small_talk_handler import SmallTalkHandler


@lru_cache(maxsize=1)
def make_small_talk_handler() -> SmallTalkHandler:
    """Factory function to create SmallTalkHandler instance.

    Creates a new instance each time. Uses configuration settings to initialize the handler.

    :returns: New instance of SmallTalkHandler
    :rtype: SmallTalkHandler
    """
    settings = get_settings()
    embedding_service = make_embeddings_client(settings)

    return SmallTalkHandler(embeddings_service=embedding_service, settings=settings)
