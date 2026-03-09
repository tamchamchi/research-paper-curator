import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.database import make_database
from src.services.opensearch.factory import make_opensearch_client

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_opensearch_indexing():
    """Test indexing documents into OpenSearch."""

    database = make_database()
    opensearch_client = make_opensearch_client()
    health = opensearch_client.health_check()
    if not health:
        logger.error("OpenSearch cluster is not healthy. Cannot proceed with indexing.")
        return {"status": "error", "papers_indexed": 0, "message": "OpenSearch cluster not healthy"}

    indices = opensearch_client.create_index(force=True)
    if not indices:
        logger.error("Failed to create OpenSearch index. Cannot proceed with indexing.")
        return {"status": "error", "papers_indexed": 0, "message": "Failed to create OpenSearch index"}

    try:
        indexed_count = 0
        failed_count = 0

        with database.get_session() as session:
            from sqlalchemy import text

            from src.repositories.paper import PaperRepository

            paper_repo = PaperRepository(session)

            query = """
                SELECT *
                FROM papers
                LIMIT 100;
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

        # Log detailed summary
        logger.info("=" * 60)
        logger.info("OpenSearch Indexing Summary:")
        logger.info(f"  Papers found in DB: {len(papers)}")
        logger.info(f"  Papers indexed: {indexed_count}")
        logger.info(f"  Indexing failures: {failed_count}")
        logger.info(f"  Total docs in index: {total_docs}")
        logger.info("=" * 60)

    except Exception as e:
        error_msg = f"OpenSearch indexing failed: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "papers_indexed": 0, "message": error_msg}
    

    search_results = opensearch_client.search_papers(query="machine learning", size=5, from_=4)
    logger.info(f"Search results for 'machine learning': {search_results}")
    logger.info(f"{len(search_results.get('hits', []))} papers found in search results")

    

if __name__ == "__main__":
    results = test_opensearch_indexing()
    logger.info(f"Indexing results: {results}")