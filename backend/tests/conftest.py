"""Shared test fixtures for VC Audit Tool."""

import pytest
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings, ValuationConfig
from src.data.loader import DataLoader
from src.database import models
from src.engine.engine import ValuationEngine


@pytest.fixture
def test_data_dir() -> Path:
    """Return the test data directory (using actual data)."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def settings(test_data_dir: Path) -> Settings:
    """Create test settings pointing to actual data."""
    return Settings(data_dir=test_data_dir)


@pytest.fixture
def loader(settings: Settings) -> DataLoader:
    """Create a data loader with test settings."""
    return DataLoader(settings)


@pytest.fixture
def config() -> ValuationConfig:
    """Create default valuation config."""
    return ValuationConfig()


@pytest.fixture
def engine(loader: DataLoader, config: ValuationConfig) -> ValuationEngine:
    """Create valuation engine with test fixtures."""
    return ValuationEngine(loader, config)


@pytest.fixture
async def test_db_engine(settings: Settings) -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine.

    Uses in-memory SQLite for testing to avoid affecting real database.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Each test gets a fresh session that's rolled back after the test.
    """
    # Create session factory
    session_factory = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        # Rollback any changes after each test
        await session.rollback()
