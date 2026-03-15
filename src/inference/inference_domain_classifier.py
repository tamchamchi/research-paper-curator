import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import get_settings
from src.services.domain_classifier.gemini_domain_classifier import (
    GeminiDomainClassifier,
)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_gemini_domain_classifier():
    settings = get_settings()

    classifier = GeminiDomainClassifier(
        api_key=settings.domain_classifier.gemini_api_key, model_name=settings.domain_classifier.model_name
    )

    test_query = "What are the latest research findings on quantum computing?"

    try:
        classification_result = await classifier.classify(test_query)
        logger.info(
            f"Classification result for query: '{test_query}' -> {classification_result}"
        )
    except Exception as e:
        logger.error(f"Error during domain classification: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_gemini_domain_classifier())
