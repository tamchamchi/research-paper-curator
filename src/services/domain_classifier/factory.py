from src.config import get_settings

from .base import BaseDomainClassifier
from .gemini_domain_classifier import GeminiDomainClassifier


def make_domain_classifier() -> BaseDomainClassifier:
    settings = get_settings()

    if settings.domain_classifier.classifier_type == "gemini":
        return GeminiDomainClassifier(
            api_key=settings.domain_classifier.api_key,
            model_name=settings.domain_classifier.model_name,
        )
