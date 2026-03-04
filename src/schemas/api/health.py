from typing import Dict, Optional

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """Individual service status."""

    status: str = Field(..., description="Service status", example="healthy")
    message: Optional[str] = Field(
        None, description="Service message", example="Connected successfully"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status", example="healthy")
    version: str = Field(..., description="Application version", example="0.1.0")
    environment: str = Field(
        ..., description="Deployment environment", example="development"
    )
    service_name: str = Field(..., description="Service identifier", example="rag-api")
    services: Optional[Dict[str, ServiceStatus]] = Field(
        None, description="Detailed status of individual services"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "environment": "development",
                "service_name": "rag-api",
                "services": {
                    "database": {
                        "status": "healthy",
                        "message": "Connected successfully",
                    },
                    "pdf_parser": {
                        "status": "healthy",
                        "message": "Docling parser ready",
                    },
                },
            }
        }
