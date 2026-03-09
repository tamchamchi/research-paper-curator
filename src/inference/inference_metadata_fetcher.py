import asyncio
import logging
import sys
import os
import psutil
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.database import make_database
from src.services.arxiv.factory import make_arxiv_client
from src.services.metadata_fetcher import make_metadata_fetcher
from src.services.pdf_parser.factory import make_pdf_parser_service


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------
# RAM MONITORING UTILITIES
# ---------------------------

def log_memory_usage(tag: str = ""):
    """Log RAM usage of current Python process."""
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)  # MB
    logger.info(f"[{tag}] RAM usage: {mem:.2f} MB")


async def monitor_memory(interval: int = 2):
    """Continuously monitor RAM usage."""
    while True:
        log_memory_usage("monitor")
        await asyncio.sleep(interval)


# ---------------------------
# MAIN TEST FUNCTION
# ---------------------------

async def test_metadata_fetcher():
    """Test the metadata fetcher service."""

    log_memory_usage("start")

    arxiv_client = make_arxiv_client()
    pdf_parser = make_pdf_parser_service()
    database = make_database()

    metadata_fetcher = make_metadata_fetcher(arxiv_client, pdf_parser)

    log_memory_usage("services_initialized")

    with database.get_session() as session:

        task1 = asyncio.create_task(
            metadata_fetcher.fetch_and_process_papers(
                max_results=3,
                from_date="20260101",
                to_date="20260131",
                process_pdfs=True,
                store_to_db=True,
                db_session=session,
            )
        )

        task2 = asyncio.create_task(
            metadata_fetcher.fetch_and_process_papers(
                max_results=3,
                from_date="20250101",
                to_date="20250131",
                process_pdfs=True,
                store_to_db=True,
                db_session=session,
            )
        )

        log_memory_usage("tasks_created")

        await asyncio.gather(task1, task2)

    log_memory_usage("after_processing")


# ---------------------------
# ENTRY POINT
# ---------------------------

async def main():
    """Main async entrypoint."""

    # Start RAM monitoring
    monitor_task = asyncio.create_task(monitor_memory(interval=2))

    try:
        await test_metadata_fetcher()
    finally:
        monitor_task.cancel()


if __name__ == "__main__":
    import time

    start_time = time.time()

    asyncio.run(main())

    end_time = time.time()

    logger.info(
        f"Metadata fetcher test completed in {end_time - start_time:.2f} seconds"
    )