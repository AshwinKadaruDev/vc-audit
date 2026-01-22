"""SQLAlchemy database engine and session management."""

import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings


def _get_raw_database_url() -> str:
    """Get raw database URL from environment.

    Returns:
        Raw database URL string.

    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    settings = get_settings()
    url = settings.database_url or os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it in .env file."
        )
    return url


def get_database_url() -> str:
    """Get database URL for async driver (asyncpg).

    Returns:
        Database URL string for SQLAlchemy (postgresql+asyncpg://...).

    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    url = _get_raw_database_url()

    # SQLAlchemy uses postgresql+asyncpg:// instead of postgresql://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def get_sync_database_url() -> str:
    """Get database URL for sync driver (psycopg2).

    Returns:
        Database URL string for SQLAlchemy (postgresql+psycopg2://...).

    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    url = _get_raw_database_url()

    # Use psycopg2 for sync operations
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)

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


# ============================================================================
# SYNCHRONOUS DATABASE ACCESS
# ============================================================================
# Used by DataLoader for sync operations (e.g., valuation methods that are
# not async). The async FastAPI app uses the async engine/session above.

# Global sync session factory - lazily initialized
_SyncSessionLocal: Optional[sessionmaker[Session]] = None


def _get_sync_session_factory() -> sessionmaker[Session]:
    """Get or create the sync session factory.

    Lazily creates the sync engine and session factory on first use.

    Returns:
        Configured sessionmaker for sync sessions.
    """
    global _SyncSessionLocal
    if _SyncSessionLocal is None:
        sync_engine = create_sync_engine(
            get_sync_database_url(),
            pool_pre_ping=True,
            pool_size=5,  # Smaller pool for sync operations
            max_overflow=10,
        )
        _SyncSessionLocal = sessionmaker(
            bind=sync_engine,
            expire_on_commit=False,
            autoflush=False,
        )
    return _SyncSessionLocal


@contextmanager
def get_sync_db() -> Generator[Session, None, None]:
    """Context manager for synchronous database sessions.

    Use this in DataLoader and other sync code that needs DB access.
    Automatically commits on success, rolls back on error.

    Usage:
        with get_sync_db() as db:
            sectors = crud.get_all_sectors_sync(db)

    Yields:
        Session: Synchronous database session.
    """
    factory = _get_sync_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
