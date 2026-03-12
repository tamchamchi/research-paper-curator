import asyncio
import logging
from typing import List

import httpx

from src.schemas.embeddings.jina import JinaEmbeddingRequest, JinaEmbeddingResponse

logger = logging.getLogger(__name__)


class JinaEmbeddingsClient:
    """Client for Jina AI embeddings API.

    Uses Jina embeddings v3 model with 1024 dimensions optimized for retrieval.
    Documentation: https://jina.ai/embeddings
    """

    def __init__(
        self, api_key: str, model_name: str, base_url: str = "https://api.jina.ai/v1"
    ):
        """Initialize Jina embeddings client.

        :param api_key: Jina API key
        :param model_name: Name of the embedding model to use
        :param base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("Jina embeddings client initialized")

    async def embed_passages(
        self, texts: List[str], batch_size: int = 32
    ) -> List[List[float]]:
        """Embed text passages for indexing."""

        embeddings: List[List[float]] = []

        RPM_LIMIT = 100
        TPM_LIMIT = 100_000

        min_request_interval = 60 / RPM_LIMIT  # 0.6s

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            request_data = JinaEmbeddingRequest(
                model=self.model_name,
                task="retrieval.passage",
                dimensions=1024,
                input=batch,
            )

            retries = 5

            for attempt in range(retries):
                try:
                    response = await self.client.post(
                        f"{self.base_url}/embeddings",
                        headers=self.headers,
                        json=request_data.model_dump(),
                    )

                    response.raise_for_status()

                    result = JinaEmbeddingResponse(**response.json())
                    batch_embeddings = [item["embedding"] for item in result.data]
                    embeddings.extend(batch_embeddings)

                    logger.info(f"Embedded batch of {len(batch)} passages")

                    # ---- TOKEN RATE LIMIT ----
                    usage = response.json().get("usage", {})
                    tokens_used = usage.get("total_tokens", 0)

                    token_sleep = (tokens_used / TPM_LIMIT) * 60
                    sleep_time = max(min_request_interval, token_sleep)

                    logger.info(
                        f"Rate limit sleep: {sleep_time:.2f}s (tokens={tokens_used})"
                    )

                    await asyncio.sleep(sleep_time)

                    break

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 409:
                        wait_time = 2**attempt
                        logger.warning(
                            f"409 rate limit on batch {i // batch_size}, retry in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"HTTP error embedding passages: {e}")
                        raise

                except httpx.HTTPError as e:
                    logger.error(f"HTTP error embedding passages: {e}")
                    raise

                except Exception as e:
                    logger.error(f"Unexpected error in embed_passages: {e}")
                    raise

        logger.info(f"Successfully embedded {len(texts)} passages")
        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Embed a search query.

        :param query: Query text to embed
        :returns: Embedding vector for the query
        """
        request_data = JinaEmbeddingRequest(
            model=self.model_name,
            task="retrieval.query",
            dimensions=1024,
            input=[query],
        )

        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                headers=self.headers,
                json=request_data.model_dump(),
            )
            response.raise_for_status()

            result = JinaEmbeddingResponse(**response.json())
            embedding = result.data[0]["embedding"]

            logger.debug(f"Embedded query: '{query[:50]}...'")
            return embedding

        except httpx.HTTPError as e:
            logger.error(f"Error embedding query: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embed_query: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
