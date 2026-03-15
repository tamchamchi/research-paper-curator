import json
import logging

import httpx

from .base import BaseDomainClassifier
from .prompts import DOMAIN_CLASSIFIER_PROMPT_TEMPLATE

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"

logger = logging.getLogger(__name__)


class GeminiDomainClassifier(BaseDomainClassifier):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    async def classify(self, text: str) -> int:
        """Classify the domain of the given text using Gemini API.
        Args:
            text (str): The user query to classify.
        Returns:
            int: 1 if the query is classified as 'Academic Research', 0 if 'Out-of-Domain'.
        """
        prompt = self._build_prompt(text)

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        url = f"{GEMINI_API_BASE_URL}{self.model_name}:generateContent"

        try:
            logger.info(
                f"Sending request to Gemini API for domain classification. Model: {self.model_name}"
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return self._parse_response(result)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Gemini API call: {e}")
            raise RuntimeError(f"HTTP error during Gemini API call: {e}")
        except Exception as e:
            logger.error(f"Failed to parse Gemini API response: {e}")
            raise RuntimeError(f"Failed to parse Gemini API response: {e}")

    def _build_prompt(self, text: str) -> str:
        return f"{DOMAIN_CLASSIFIER_PROMPT_TEMPLATE}\n\nQuery User:\n{text}\n"

    def _parse_response(self, response: dict) -> int:
        try:
            content = response["candidates"][0]["content"]["parts"][0]["text"]
            logger.debug(f"Raw response content from Gemini API: {content}")

            # Extract the JSON part from the response
            json_start = content.find("```json")
            json_end = content.rfind("```")

            if json_start != -1 and json_end != -1 and json_start < json_end:
                json_string = content[json_start + len("```json") : json_end].strip()
            else:
                json_string = content.strip()

            result = json.loads(json_string)

            classified_domain = result.get("output", None)
            if classified_domain is None:
                logger.error("Output field not found in Gemini API response.")
                raise RuntimeError("Output field not found in Gemini API response.")
            return int(classified_domain)

        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing Gemini API response: {e}")
            raise RuntimeError(f"Error parsing Gemini API response: {e}")
