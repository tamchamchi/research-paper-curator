import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI

from src.config import get_settings
from src.db.factory import make_database
from src.routers import papers, ping, search
from src.services.arxiv.factory import make_arxiv_client
from src.services.opensearch.factory import make_opensearch_client
from src.services.pdf_parser.factory import make_pdf_parser_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Week 1: Simplified lifespan for learning purposes."""
    logger.info("Starting RAG API...")

    # Initialize settings and database (Week 1 essentials)
    settings = get_settings()
    app.state.settings = settings
    print(f"Loaded settings: {settings.dict()}")

    # Initialize Database
    database = make_database()
    app.state.database = database
    logger.info("Database connected")

    # Initialize OpenSearch client
    opensearch_client = make_opensearch_client()
    app.state.opensearch_client = opensearch_client

    # Verify OpenSearch connection
    if opensearch_client.health_check():
        logger.info("Connected to OpenSearch")

        # Ensure index exists
        if opensearch_client.create_index(force=False):
            logger.info("OpenSearch index is ready")
        else:
            logger.error("Failed to create OpenSearch index")

        # Get index statistics
        stats = opensearch_client.get_index_stats()
        logger.info(
            f"OpenSearch ready: {stats.get('document_count', 0)} documents indexed"
        )
    else:
        logger.error("Failed to connect to OpenSearch")

    # Initialize other services (kept for future endpoints and notebook demos)
    app.state.arxiv_client = make_arxiv_client()
    app.state.pdf_parser = make_pdf_parser_service()
    logger.info("Services initialized: arXiv API client, PDF parser, OpenSearch")

    logger.info("API ready")
    yield

    # Cleanup
    database.teardown()
    logger.info("API shutdown complete")


app = FastAPI(
    title="arXiv Paper Curator API",
    description="Personal arXiv CS.AI paper curator with RAG capabilities",
    version=os.getenv("APP_VERSION", "0.1.0"),
    root_path="/api/v1",
    lifespan=lifespan,
)

# Include routers
app.include_router(ping.router)
app.include_router(papers.router)
app.include_router(search.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000, host="0.0.0.0")
