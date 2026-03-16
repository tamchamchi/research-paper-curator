import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.services.cache.factory import make_cache_client
from src.config import get_settings

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def test_cache_client():
    settings = get_settings()
    print(f"Testing cache client with settings: {settings.redis.dict()}")
    try:
        cache_client = make_cache_client(settings)
        test_key = "test_key"
        test_value = "test_value"

        # Set a value in the cache
        await cache_client.store_response(test_key, test_value)
        logger.info(f"Set cache key: {test_key} with value: {test_value}")

        # Get the value back from the cache
        retrieved_value = await cache_client.find_cached_response(test_key)
        logger.info(f"Retrieved cache key: {test_key} with value: {retrieved_value}")

        assert retrieved_value == test_value, "Cache retrieval did not return expected value"
        logger.info("Cache client test passed successfully")

    except Exception as e:
        logger.error(f"Error testing cache client: {e}")
if __name__ == "__main__":
    import asyncio

    asyncio.run(test_cache_client())
