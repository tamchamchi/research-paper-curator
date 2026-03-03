import logging
from typing import Dict

import httpx

from src.config import Settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with the Ollama API."""

    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_host
        logger.info(f"OllamaClient initialized with base URL: {self.base_url}")

    async def check_health(self) -> Dict[str, str]:
        """Check the health of the Ollama service."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}")
                if response.status_code == 200:
                    return {"status": "healthy", "message": "Ollama service is running"}
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Ollama returned status code {response.status_code}",
                    }

        except Exception as e:
            logger.error(f"Error checking Ollama health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
