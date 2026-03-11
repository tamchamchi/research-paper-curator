import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from src.db.factory import make_database
from src.services.indexing.factory import make_hybrid_indexing_service

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_hybrid_indexing():
    database = make_database()
    indexing_service = make_hybrid_indexing_service()

    with database.get_session() as session:
        from sqlalchemy import text

        query = """
            SELECT *
            FROM papers
            LIMIT 100;
        """

        result = session.execute(text(query))
        papers = result.fetchall()

        logger.info(f"Found {len(papers)} papers for hybrid indexing")

        papers_data = []
        for paper in papers:
            if hasattr(paper, "__dict__"):
                paper_dict = {
                    "id": str(paper.id),
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "categories": paper.categories,
                    "published_date": paper.published_date,
                    "raw_text": paper.raw_text,
                    "sections": paper.sections,
                }
            else:
                paper_dict = paper
            papers_data.append(paper_dict)

        stats = await indexing_service.index_papers_batch(
            papers=papers_data, replace_existing=True
        )
        logger.info(f"Hybrid indexing completed: {stats}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_hybrid_indexing())
