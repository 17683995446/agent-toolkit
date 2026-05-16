"""Main application entry point for Tool Registry."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_toolkit.shared.application_settings import get_settings
from agent_toolkit.shared.database_connection import init_db, close_db
from agent_toolkit.shared.structured_logging import setup_logging, get_logger
from agent_toolkit.registry.registry_api_routes import router, categories_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    settings = get_settings()
    setup_logging(level=settings.logging.level, format=settings.logging.format)
    logger.info("starting_application", environment=settings.environment)
    
    await init_db()
    
    yield
    
    logger.info("shutting_down_application")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.registry.title,
        description=settings.registry.description,
        version=settings.registry.version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=settings.security.cors_allow_credentials,
        allow_methods=settings.security.cors_allow_methods,
        allow_headers=settings.security.cors_allow_headers,
    )

    app.include_router(router)
    app.include_router(categories_router)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Agent Toolkit Registry",
            "version": settings.registry.version,
            "docs": "/docs"
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "agent_toolkit.registry.main:app",
        host=settings.registry.host,
        port=settings.registry.port,
        reload=settings.registry.reload,
        workers=settings.registry.workers if not settings.registry.reload else 1,
    )
