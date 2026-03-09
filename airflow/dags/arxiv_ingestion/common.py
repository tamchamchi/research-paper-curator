import logging
import sys
from functools import lru_cache
from typing import Any, Tuple

# Add project root to Python path for imports
sys.path.insert(0, "/opt/airflow")

from src.database import make_database
from src.services.arxiv.factory import make_arxiv_client
from src.services.metadata_fetcher import make_metadata_fetcher
from src.services.opensearch.factory import make_opensearch_client
from src.services.pdf_parser.factory import make_pdf_parser_service

# Setup logging
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_cache_services() -> Tuple[Any, Any, Any, Any, Any]:
    """Get cached service instances using lru_cache for automatic memoization.

    :returns: Tuple of (arxiv_client, pdf_parser, database, opensearch_client, metadata_fetcher)
    """

    logger.info("Initializing services (cached with lru_cache)")

    arxiv_client = make_arxiv_client()
    pdf_parser = make_pdf_parser_service()
    database = make_database()
    opensearch_client = make_opensearch_client()

    # Create metadata fetcher with dependencies
    metadata_fetcher = make_metadata_fetcher(arxiv_client, pdf_parser)

    logger.info("Services initialized and cached successfully")
    return arxiv_client, pdf_parser, database, opensearch_client, metadata_fetcher
