"""Tests for database CRUD operations."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from src.database import crud


@pytest.mark.asyncio
async def test_create_portfolio_company(db_session):
    """Test creating a portfolio company."""
    company = await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
        founded_date=date(2020, 1, 1),
    )

    assert company.id is not None
    assert company.name == "Test Company"
    assert company.sector_id == "saas"
    assert company.stage == "series_a"
    assert company.founded_date == date(2020, 1, 1)
    assert company.created_at is not None


@pytest.mark.asyncio
async def test_get_portfolio_company_by_id(db_session):
    """Test retrieving a portfolio company by ID."""
    # Create a company
    created = await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
    )

    # Retrieve it
    retrieved = await crud.get_portfolio_company_by_id(db_session, created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Test Company"


@pytest.mark.asyncio
async def test_get_nonexistent_company(db_session):
    """Test retrieving a company that doesn't exist."""
    result = await crud.get_portfolio_company_by_id(db_session, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_portfolio_companies(db_session):
    """Test listing portfolio companies."""
    # Create multiple companies
    await crud.create_portfolio_company(
        db=db_session,
        name="Company A",
        sector_id="saas",
        stage="series_a",
    )
    await crud.create_portfolio_company(
        db=db_session,
        name="Company B",
        sector_id="fintech",
        stage="series_b",
    )

    # List companies
    companies = await crud.list_portfolio_companies(db_session)

    assert len(companies) == 2
    names = {c.name for c in companies}
    assert "Company A" in names
    assert "Company B" in names


@pytest.mark.asyncio
async def test_count_portfolio_companies(db_session):
    """Test counting portfolio companies."""
    # Initially empty
    count = await crud.count_portfolio_companies(db_session)
    assert count == 0

    # Create a company
    await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
    )

    # Count should be 1
    count = await crud.count_portfolio_companies(db_session)
    assert count == 1


@pytest.mark.asyncio
async def test_create_valuation(db_session):
    """Test creating a valuation record."""
    # First create a company
    company = await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
    )

    # Create a valuation
    valuation = await crud.create_valuation(
        db=db_session,
        portfolio_company_id=company.id,
        company_name="Test Company",
        input_snapshot={"test": "data"},
        input_hash="abc123",
        primary_value=Decimal("10000000"),
        primary_method="last_round",
        value_range_low=Decimal("9000000"),
        value_range_high=Decimal("11000000"),
        overall_confidence="HIGH",
        summary={"notes": "test"},
        method_results=[],
    )

    assert valuation.id is not None
    assert valuation.portfolio_company_id == company.id
    assert valuation.company_name == "Test Company"
    assert valuation.primary_value == Decimal("10000000")
    assert valuation.primary_method == "last_round"
    assert valuation.overall_confidence == "HIGH"
    assert valuation.created_at is not None


@pytest.mark.asyncio
async def test_get_valuation_by_id(db_session):
    """Test retrieving a valuation by ID."""
    # Create company and valuation
    company = await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
    )

    created = await crud.create_valuation(
        db=db_session,
        portfolio_company_id=company.id,
        company_name="Test Company",
        input_snapshot={"test": "data"},
        input_hash="abc123",
        primary_value=Decimal("10000000"),
        primary_method="last_round",
        value_range_low=Decimal("9000000"),
        value_range_high=Decimal("11000000"),
        overall_confidence="HIGH",
        summary={},
        method_results=[],
    )

    # Retrieve it
    retrieved = await crud.get_valuation_by_id(db_session, created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.company_name == "Test Company"


@pytest.mark.asyncio
async def test_list_recent_valuations(db_session):
    """Test listing recent valuations."""
    # Create company
    company = await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
    )

    # Create multiple valuations
    for i in range(3):
        await crud.create_valuation(
            db=db_session,
            portfolio_company_id=company.id,
            company_name="Test Company",
            input_snapshot={"iteration": i},
            input_hash=f"hash{i}",
            primary_value=Decimal("10000000"),
            primary_method="last_round",
            value_range_low=Decimal("9000000"),
            value_range_high=Decimal("11000000"),
            overall_confidence="HIGH",
            summary={},
            method_results=[],
        )

    # List valuations
    valuations = await crud.list_recent_valuations(db_session)

    assert len(valuations) == 3


@pytest.mark.asyncio
async def test_list_valuations_by_company(db_session):
    """Test listing valuations for a specific company."""
    # Create two companies
    company1 = await crud.create_portfolio_company(
        db=db_session,
        name="Company 1",
        sector_id="saas",
        stage="series_a",
    )
    company2 = await crud.create_portfolio_company(
        db=db_session,
        name="Company 2",
        sector_id="fintech",
        stage="series_b",
    )

    # Create valuations for company1
    await crud.create_valuation(
        db=db_session,
        portfolio_company_id=company1.id,
        company_name="Company 1",
        input_snapshot={},
        input_hash="hash1",
        primary_value=Decimal("10000000"),
        primary_method="last_round",
        value_range_low=Decimal("9000000"),
        value_range_high=Decimal("11000000"),
        overall_confidence="HIGH",
        summary={},
        method_results=[],
    )

    # Create valuation for company2
    await crud.create_valuation(
        db=db_session,
        portfolio_company_id=company2.id,
        company_name="Company 2",
        input_snapshot={},
        input_hash="hash2",
        primary_value=Decimal("20000000"),
        primary_method="comps",
        value_range_low=Decimal("18000000"),
        value_range_high=Decimal("22000000"),
        overall_confidence="MEDIUM",
        summary={},
        method_results=[],
    )

    # List valuations for company1
    valuations = await crud.list_valuations_by_company(db_session, company1.id)

    assert len(valuations) == 1
    assert valuations[0].company_name == "Company 1"


@pytest.mark.asyncio
async def test_get_valuation_by_hash(db_session):
    """Test finding a valuation by input hash."""
    # Create company
    company = await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
    )

    # Create valuation with specific hash
    created = await crud.create_valuation(
        db=db_session,
        portfolio_company_id=company.id,
        company_name="Test Company",
        input_snapshot={},
        input_hash="unique_hash_123",
        primary_value=Decimal("10000000"),
        primary_method="last_round",
        value_range_low=Decimal("9000000"),
        value_range_high=Decimal("11000000"),
        overall_confidence="HIGH",
        summary={},
        method_results=[],
    )

    # Find by hash
    found = await crud.get_valuation_by_hash(db_session, "unique_hash_123")

    assert found is not None
    assert found.id == created.id
    assert found.input_hash == "unique_hash_123"


@pytest.mark.asyncio
async def test_delete_portfolio_company(db_session):
    """Test deleting a portfolio company."""
    # Create a company
    company = await crud.create_portfolio_company(
        db=db_session,
        name="Test Company",
        sector_id="saas",
        stage="series_a",
    )

    # Delete it
    deleted = await crud.delete_portfolio_company(db_session, company.id)
    assert deleted is True

    # Verify it's gone
    retrieved = await crud.get_portfolio_company_by_id(db_session, company.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_delete_nonexistent_company(db_session):
    """Test deleting a company that doesn't exist."""
    result = await crud.delete_portfolio_company(db_session, uuid4())
    assert result is False
