import logging

from sqlalchemy import text

from .common import get_cache_services

logger = logging.getLogger(__name__)


def setup_environment():
    """Setup environment and verify dependencies."""
    logger.info("Setting up environment for arXiv paper ingestion")

    try:
        arxiv_client, _pdf_parser, database, _opensearch_client, _metadata_fetcher = (
            get_cache_services()
        )

        with database.get_session() as session:
            session.execute(text("SELECT 1"))
            logger.info("Database connection successful")

        logger.info(f"arXiv client ready: {arxiv_client.base_url}")
        logger.info("PDF parser service ready (Docling models cached)")

        return {"status": "success", "message": "Environment setup completed"}

    except Exception as e:
        error_msg = f"Environment setup failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
