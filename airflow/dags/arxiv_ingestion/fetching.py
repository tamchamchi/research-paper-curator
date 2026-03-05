import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict

from .common import get_cache_services

logger = logging.getLogger(__name__)


async def run_paper_ingestion_pipeline(
    target_date: datetime = None,
    process_pdfs: bool = True,
) -> Dict:
    """Async wrapper for the paper ingestion pipeline.

    :param target_date: Date to fetch papers for (YYYYMMDD format)
    :param process_pdfs: Whether to download and process PDFs
    :returns: Dictionary with ingestion statistics
    """
    arxiv_client, _pdf_parser, database, _opensearch_client, metadata_fetcher = (
        get_cache_services()
    )

    max_results = arxiv_client.max_results
    logger.info(
        f"Using default max_results from arxiv_client configuration: {max_results}"
    )

    with database.get_session() as session:
        return await metadata_fetcher.fetch_and_process_papers(
            max_results=max_results,
            from_date=target_date,
            to_date=target_date,
            process_pdfs=process_pdfs,
            store_to_db=True,
            db_session=session,
        )


def fetch_daily_papers(**context):
    """Fetch daily papers from arXiv and store in PostgreSQL.

    This task:
    1. Determines the target date (defaults to yesterday)
    2. Fetches papers from arXiv API
    3. Downloads and processes PDFs using Docling
    4. Stores metadata and parsed content in PostgreSQL

    """

    logger.info("Starting daily paper ingestion pipeline")
    execution_date = context.get("execution_date")

    if execution_date:
        target_dt = execution_date - timedelta(days=1)
        target_date = target_dt.strftime("%Y%m%d")
    else:
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime("%Y%m%d")

    logger.info(f"Fetching papers for date: {target_date}")

    results = asyncio.run(
        run_paper_ingestion_pipeline(target_date=target_date, process_pdfs=True)
    )

    logger.info(
        f"Daily fetch complete: {results['papers_fetched']} papers for {target_date}"
    )

    results["date"] = target_date
    task_instance = context.get("ti")
    if task_instance:
        task_instance.xcom_push(key="fetch_results", value=results)

    return results
