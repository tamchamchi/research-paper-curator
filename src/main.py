import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the application...")
    # Perform any startup tasks here (e.g., connect to databases, initialize resources)
    yield
    logger.info("Shutting down the application...")
    # Perform any cleanup tasks here (e.g., close database connections, release resources)


app = FastAPI(
    title="arXiv Paper Curator API",
    description="Personal arXiv CS.AI paper curator with RAG capabilities",
    version=os.getenv("APP_VERSION", "0.1.0"),
    root_path="/api/v1",
    lifespan=lifespan,
)

if __name__ == "__main__":
    import uvicorn  # type: ignore

    uvicorn.run(app, port=8000, host="0.0.0.0")
