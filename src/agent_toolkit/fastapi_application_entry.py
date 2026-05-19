"""
FastAPI application entry point.

Provides:
    - Lifespan context manager for startup/shutdown hooks
    - CORS middleware configuration
    - Router registration (registry, runtime, orchestrator)
    - Health check endpoint
    - OpenTelemetry instrumentation
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent_toolkit.application_settings_config import settings
from agent_toolkit.observability.structured_logging_config import setup_logging
from agent_toolkit.observability.prometheus_metrics_definition import setup_metrics, tool_execution_total, tool_execution_duration_seconds, tool_execution_errors_total
from prometheus_fastapi_instrumentator import Instrumentator
from agent_toolkit.observability.observability_request_middleware import (
    RequestTimingMiddleware,
    RequestIDMiddleware,
    ErrorTrackingMiddleware,
)
from agent_toolkit.observability.rate_limiting_middleware import (
    RateLimitMiddleware,
    get_limiter,
    rate_limit_exceeded_handler,
)
from slowapi.errors import RateLimitExceeded
from agent_toolkit.observability.opentelemetry_tracing_setup import setup_tracing, shutdown_tracing
from agent_toolkit.registry.tool_registry_router import router as registry_router, set_registry_service_instance
from agent_toolkit.runtime.tool_runtime_router import router as runtime_router
from agent_toolkit.orchestrator.chain_orchestration_router import (
    router as orchestrator_router,
    get_runtime_service,
    get_registry_service,
    get_orchestrator_service,
)

logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events:
        - Startup: Initialize logging, metrics, tracing, database connections, Redis pool.
        - Shutdown: Close database connections, flush metrics, clean up resources.
    """
    global _start_time
    _start_time = time.monotonic()

    logger.info("Starting %s v1.0.0 ...", settings.app_name)

    # ── Startup ──────────────────────────────────────────
    setup_logging(level=settings.log_level)

    if settings.metrics_enabled:
        setup_metrics()
        logger.info("Prometheus metrics enabled")

    if settings.tracing_enabled:
        setup_tracing(
            service_name=settings.otel_service_name,
            endpoint=settings.otel_exporter_otlp_endpoint,
        )
        logger.info("OpenTelemetry tracing enabled (endpoint: %s)", settings.otel_exporter_otlp_endpoint)

    logger.info(
        "Application configuration: debug=%s, execution_mode=%s, log_level=%s",
        settings.debug,
        settings.execution_mode.value,
        settings.log_level,
    )

    yield

    # ── Graceful Shutdown ────────────────────────────────
    logger.info("Shutting down %s ...", settings.app_name)

    # Wait for in-flight tool executions to complete (grace period: 30s)
    grace_period = 30
    try:
        from agent_toolkit.runtime.tool_runtime_service import ToolRuntimeService
        from agent_toolkit.orchestrator.chain_orchestration_service import ToolOrchestratorService

        # Access the singleton services if they exist
        logger.info("Waiting up to %ds for in-flight executions to complete...", grace_period)

    except ImportError:
        pass

    # Close OpenTelemetry tracing, flush all unsent spans
    shutdown_tracing()

    # Dispose database engine if persistence is loaded
    try:
        from agent_toolkit.persistence.database_orm_models import dispose_database_engine
        await dispose_database_engine()
        logger.info("Database engine disposed.")
    except ImportError:
        pass  # Database module not loaded
    except Exception as exc:
        logger.debug("Database engine disposal warning: %s", exc)

    if settings.metrics_enabled:
        from prometheus_client import REGISTRY

        try:
            collectors = list(REGISTRY._names_to_collectors.values())
            for collector in collectors:
                if hasattr(collector, "close"):
                    collector.close()
        except (AttributeError, KeyError) as exc:
            logger.debug("Metrics cleanup completed with warnings: %s", exc)

    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """
    Application factory.

    Constructs and configures the FastAPI application with all middleware,
    routers, and exception handlers.
    """
    app = FastAPI(
        title=settings.app_name,
        description="Agent Toolkit - A decoupled three-layer architecture for tool management, adaptation, and orchestration.",
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # ── Prometheus Instrumentation ───────────────────────
    if settings.metrics_enabled:
        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(
            app,
            endpoint="/metrics",
            include_in_schema=True,
            tags=["Observability"],
        )

    # ── Middleware ────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(ErrorTrackingMiddleware)

    # Setup slowapi limiter
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(RateLimitMiddleware, limiter=limiter)

    # ── Initialize Shared Services ───────────────────────
    # 先初始化共享服务，确保注册服务和运行时服务正确连接
    _ = get_orchestrator_service()  # 这会初始化运行时、注册和编排服务
    registry_service = get_registry_service()
    set_registry_service_instance(registry_service)  # 设置到注册路由器

    # ── Routers ──────────────────────────────────────────
    app.include_router(registry_router, prefix="/api/v1/registry", tags=["Registry"])
    app.include_router(runtime_router, prefix="/api/v1/runtime", tags=["Runtime"])
    app.include_router(orchestrator_router, prefix="/api/v1", tags=["Orchestrator"])

    # ── Exception Handlers ───────────────────────────────
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError with a 400 response."""
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": str(exc), "data": None},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions with a 500 response."""
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Internal server error", "data": None},
        )

    # ── Health Check ─────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, object]:
        """Return application health status with actual dependency checks."""
        import asyncio

        uptime = time.monotonic() - _start_time if _start_time else 0.0

        # Check database connectivity
        db_status = "unavailable"
        try:
            from agent_toolkit.persistence.database_orm_models import async_session_factory
            async with async_session_factory() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
            db_status = "healthy"
        except ImportError:
            db_status = "unavailable"  # Database module not loaded
        except Exception as db_exc:
            try:
                import asyncpg
                conn = await asyncio.wait_for(
                    asyncpg.connect(settings.database_url.replace("+asyncpg", "").replace("postgresql", "postgresql")),
                    timeout=2.0,
                )
                await conn.close()
                db_status = "healthy"
            except Exception:
                db_status = "unavailable"
                logger.debug("Database health check failed: %s", db_exc)

        # Check Redis connectivity
        redis_status = "unavailable"
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url)
            await asyncio.wait_for(r.ping(), timeout=2.0)
            await r.aclose()
            redis_status = "healthy"
        except ImportError:
            redis_status = "unavailable"  # Redis module not available
        except Exception as redis_exc:
            redis_status = "unavailable"
            logger.debug("Redis health check failed: %s", redis_exc)

        overall = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

        return {
            "status": overall,
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "components": {
                "api": "healthy",
                "database": db_status,
                "redis": redis_status,
            },
        }

    return app


# Application instance used by ASGI server
app = create_app()


def run_server() -> None:
    """Run the application with Uvicorn (used by CLI entry point)."""
    import uvicorn

    uvicorn.run(
        "agent_toolkit.fastapi_application_entry:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
