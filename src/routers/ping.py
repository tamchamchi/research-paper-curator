from fastapi import APIRouter
from sqlalchemy import text

from ..dependencies import DatabaseDep, SettingsDep
from ..schemas.api.health import HealthResponse, ServiceStatus
from ..services.ollama import OllamaClient

router = APIRouter()


@router.get("/ping", tags=["Health"])
async def ping():
    """
    Health check endpoint to verify that the API is running.
    """
    return {"status": "ok", "message": "pong"}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health and status of the API service including database connectivity.",
    response_description="Service health information",
    tags=["Health"],
)
async def health_check(settings: SettingsDep, database: DatabaseDep) -> HealthResponse:
    """
    Comprehensive health check endpoint for monitoring and load balancer probes.

    This endpoint provides information about the service health, version,
    environment, and checks connectivity to dependent services like database.

    Returns:
        HealthResponse: Contains service status, version, environment, and service checks

    Example:
        Response:
        ```
        {
            "status": "ok",
            "version": "0.1.0",
            "environment": "development",
            "service_name": "rag-api",
            "services": {
                "database": {"status": "healthy", "message": "Connected successfully"}
            }
        }
        ```
    """
    services = {}
    overall_status = "ok"

    def _check_service(name: str, check_func, *args, **kwargs):
        """Helper to standardize service health checks."""
        try:
            if kwargs.get("is_async"):
                # Handle async functions separately in the calling code
                return check_func(*args)
            result = check_func(*args)
            services[name] = result
            if result.status != "healthy":
                nonlocal overall_status
                overall_status = "degraded"
        except Exception as e:
            services[name] = ServiceStatus(status="unhealthy", message=str(e))
            overall_status = "degraded"

    # Database check
    def _check_database():
        with database.get_session() as session:
            session.execute(text("SELECT 1"))
        return ServiceStatus(status="healthy", message="Connected successfully")


    # Run synchronous checks
    _check_service("database", _check_database)

    # Test Ollama connectivity (if OLLAMA_HOST is set)
    try:
        ollama_client = OllamaClient(settings)
        ollama_health = await ollama_client.check_health()
        services["ollama"] = ServiceStatus(
            status=ollama_health["status"], message=ollama_health["message"]
        )
        if ollama_health["status"] != "healthy":
            overall_status = "degraded"
    except Exception as e:
        services["ollama"] = ServiceStatus(
            status="unhealthy", message=f"Ollama check failed: {str(e)}"
        )
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        service_name=settings.service_name,
        services=services,
    )
