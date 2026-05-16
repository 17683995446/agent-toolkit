"""Shared database utilities for Agent Toolkit."""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine

from agent_toolkit.shared.application_settings import get_settings
from agent_toolkit.shared.structured_logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()

_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker] = None


def get_database_url() -> str:
    """Get database URL from settings."""
    settings = get_settings()
    return settings.get_database_url()


def create_async_db_engine() -> AsyncEngine:
    """Create async database engine."""
    global _engine

    if _engine is None:
        url = get_database_url()
        settings = get_settings()

        is_postgres = "postgresql" in url
        pool_class = AsyncAdaptedQueuePool if is_postgres else NullPool

        engine_kwargs = {
            "echo": settings.database.echo,
        }

        if is_postgres:
            engine_kwargs.update({
                "poolclass": pool_class,
                "pool_size": settings.database.pool_size,
                "max_overflow": settings.database.max_overflow,
                "pool_timeout": settings.database.pool_timeout,
                "pool_recycle": settings.database.pool_recycle,
                "pool_pre_ping": settings.database.pool_pre_ping,
            })
        else:
            engine_kwargs["poolclass"] = NullPool

        _engine = create_async_engine(url, **engine_kwargs)

        logger.info("database_engine_created", url=url.split("@")[-1] if "@" in url else url, is_postgres=is_postgres)

    return _engine


def get_engine() -> AsyncEngine:
    """Get the async database engine (alias for create_async_db_engine)."""
    return create_async_db_engine()


def get_async_session_factory() -> async_sessionmaker:
    """Get async session factory."""
    global _async_session_factory

    if _async_session_factory is None:
        engine = create_async_db_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (dependency injection)."""
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session as context manager."""
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database tables."""
    engine = create_async_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def close_db() -> None:
    """Close database connections."""
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("database_closed")
