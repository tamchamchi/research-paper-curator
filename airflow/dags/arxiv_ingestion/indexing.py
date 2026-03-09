import logging

from .common import get_cache_services

logger = logging.getLogger(__name__)


def index_papers_to_opensearch(**context):
    """Index papers data to OpenSearch."""

    logger.info("Starting indexing of papers to OpenSearch")

    try:
        fetch_results = context["ti"].xcom_pull(
            task_ids="fetch_daily_papers", key="fetch_results"
        )

        if not fetch_results:
            logger.warning("No fetch results found in XCom. Skipping indexing.")
            return {"status": "skipped", "message": "No papers to index"}

        papers_stored = fetch_results.get("papers_stored", 0)

        if papers_stored == 0:
            logger.info("No papers stored in database. Skipping indexing.")
            return {
                "status": "skipped",
                "papers_indexed": 0,
                "message": "No papers available for indexing",
            }

        logger.info(f"Processing {papers_stored} papers for OpenSearch indexing")

        # Get services
        _arxiv_client, _pdf_parser, database, opensearch_client, _metadata_fetcher = (
            get_cache_services()
        )

        # Check OpenSearch connection
        if not opensearch_client.health_check():
            logger.error("OpenSearch is not healthy, skipping indexing")
            return {
                "status": "failed",
                "papers_indexed": 0,
                "message": "OpenSearch cluster not healthy",
            }

        indexed_count = 0
        failed_count = 0

        with database.get_session() as session:
            from sqlalchemy import text

            from src.repositories.paper import PaperRepository

            paper_repo = PaperRepository(session)

            query = f"""
                SELECT *
                FROM papers
                WHERE created_at >= CURRENT_DATE
                AND created_at < CURRENT_DATE + INTERVAL 2 DAY
                ORDER BY created_at DESC
                LIMIT {fetch_results.get("papers_stored", 0) if fetch_results else 100}
            """

            result = session.execute(text(query))
            papers = result.fetchall()

            logger.info(f"Found {len(papers)} papers from today for indexing")

            for paper in papers:
                try:
                    paper = paper_repo.get_by_id(paper.id)
                    if not paper:
                        continue
                    paper_doc = {
                        "arxiv_id": paper.arxiv_id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "abstract": paper.abstract,
                        "categories": paper.categories,
                        "pdf_url": paper.pdf_url,
                        "published_date": paper.published_date.isoformat(),
                    }

                    # Index document to OpenSearch
                    success = opensearch_client.index_paper(paper_doc)

                    if success:
                        indexed_count += 1
                        logger.info(f"Successfully indexed paper: {paper.arxiv_id}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to index paper: {paper.arxiv_id}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error indexing paper {paper.id}: {e}")
        # Get final index stats
        try:
            final_stats = opensearch_client.get_index_stats()
            total_docs = final_stats.get("document_count", 0) if final_stats else 0
        except Exception:
            total_docs = "unknown"

        indexing_results = {
            "status": "completed",
            "papers_indexed": indexed_count,
            "indexing_failures": failed_count,
            "total_documents_in_index": total_docs,
            "message": f"Indexed {indexed_count} papers, {failed_count} failures",
        }

        # Log detailed summary
        logger.info("=" * 60)
        logger.info("OpenSearch Indexing Summary:")
        logger.info(f"  Papers found in DB: {len(papers)}")
        logger.info(f"  Papers indexed: {indexed_count}")
        logger.info(f"  Indexing failures: {failed_count}")
        logger.info(f"  Total docs in index: {total_docs}")
        logger.info("=" * 60)

        return indexing_results

    except Exception as e:
        error_msg = f"OpenSearch indexing failed: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "papers_indexed": 0, "message": error_msg}
