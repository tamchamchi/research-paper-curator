from abc import ABC, abstractmethod


class BaseDomainClassifier(ABC):
    @abstractmethod
    async def classify(self, text: str) -> int:
        """Classify the domain of the given text."""
        pass
