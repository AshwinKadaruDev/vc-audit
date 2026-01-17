"""SQLAlchemy database engine and session management."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import get_settings


def get_database_url() -> str:
    """Get database URL from environment.

    Returns:
        Database URL string for SQLAlchemy (postgresql+asyncpg://...).

    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    settings = get_settings()
    # Try settings first, then fall back to os.getenv for backward compatibility
    url = settings.database_url or os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it in .env file."
        )

    # SQLAlchemy uses postgresql+asyncpg:// instead of postgresql://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def create_engine() -> AsyncEngine:
    """Create SQLAlchemy async engine with production settings.

    Returns:
        Configured AsyncEngine with connection pooling.
    """
    settings = get_settings()
    return create_async_engine(
        get_database_url(),
        # Connection pool settings for production
        pool_pre_ping=True,  # Auto-detect stale connections
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        # Connection and query timeouts
        connect_args={
            "timeout": settings.db_connect_timeout,
            "command_timeout": settings.db_command_timeout,
        },
        # Disable echo in production (set to True for debugging)
        echo=False,
    )


# Global engine instance - initialized by FastAPI lifespan
_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    """Get the global database engine instance.

    Returns:
        The initialized AsyncEngine.

    Raises:
        RuntimeError: If engine has not been initialized.
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine not initialized. "
            "Ensure the FastAPI app lifespan has started."
        )
    return _engine


def set_engine(engine: AsyncEngine) -> None:
    """Set the global database engine instance.

    This is called during FastAPI app startup.

    Args:
        engine: The AsyncEngine to set as global.
    """
    global _engine
    _engine = engine


# Session factory - configured when engine is set
SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create session factory with production settings.

    Args:
        engine: The AsyncEngine to use for creating sessions.

    Returns:
        Configured async_sessionmaker.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Keep objects usable after commit
        autoflush=False,  # Manual flush for better control
    )


def set_session_factory(factory: async_sessionmaker[AsyncSession]) -> None:
    """Set the global session factory.

    Args:
        factory: The session factory to set as global.
    """
    global SessionLocal
    SessionLocal = factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Provides a database session to route handlers.
    Automatically commits on success, rolls back on error.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            return await crud.get_items(db)

    Yields:
        AsyncSession: Database session for the request.
    """
    if SessionLocal is None:
        raise RuntimeError("Session factory not initialized.")

    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions in services.

    Use this in service layer when you need manual session management.
    Automatically commits on success, rolls back on error.

    Usage:
        async with get_db_context() as db:
            await crud.create_item(db, item)

    Yields:
        AsyncSession: Database session.
    """
    if SessionLocal is None:
        raise RuntimeError("Session factory not initialized.")

    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
