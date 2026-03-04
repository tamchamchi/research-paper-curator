import asyncio
import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from src.database import make_database
from src.services.arxiv.factory import make_arxiv_client
from src.services.metadata_fetcher import make_metadata_fetcher
from src.services.pdf_parser.factory import make_pdf_parser_service

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_metadata_fetcher():
    """Test the metadata fetcher service."""
    arxiv_client = make_arxiv_client()
    pdf_parser = make_pdf_parser_service()
    database = make_database()

    metadata_fetcher = make_metadata_fetcher(arxiv_client, pdf_parser)

    # Fetch papers from arXiv
    with database.get_session() as session:
        return await metadata_fetcher.fetch_and_process_papers(
            max_results=10,
            from_date="20260101",
            to_date="20260131",
            process_pdfs=True,
            store_to_db=True,
            db_session=session,
        )


if __name__ == "__main__":
    asyncio.run(test_metadata_fetcher())
