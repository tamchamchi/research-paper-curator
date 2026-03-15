from pydantic import BaseModel, Field


class DomainClassifierRequest(BaseModel):
    """Request model for domain classification."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Text to classify into a research domain",
    )


class DomainClassifierResponse(BaseModel):
    """Response model for domain classification."""

    text: str = Field(..., description="Input text that was classified")
    domain: str = Field(..., description="Predicted research domain")
    model_used: str = Field(
        ..., description="Name of the model used for classification"
    )
