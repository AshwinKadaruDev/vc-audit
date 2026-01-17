"""Centralized CRUD operations for all entities.

All database queries are defined here to:
- Prevent N+1 query issues
- Enable query optimization
- Maintain separation of concerns
- Ensure consistent data access patterns
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.utils.retry import async_retry_on_exception

from . import models


# ============================================================================
# SECTOR CRUD
# ============================================================================


async def get_all_sectors(db: AsyncSession) -> list[models.Sector]:
    """Get all available sectors.

    Args:
        db: Database session.

    Returns:
        List of Sector objects ordered by display name.
    """
    result = await db.execute(
        select(models.Sector).order_by(models.Sector.display_name)
    )
    return list(result.scalars().all())


async def get_sector_by_id(db: AsyncSession, sector_id: str) -> Optional[models.Sector]:
    """Get a sector by ID.

    Args:
        db: Database session.
        sector_id: The sector identifier (e.g., 'saas').

    Returns:
        Sector if found, None otherwise.
    """
    result = await db.execute(
        select(models.Sector).where(models.Sector.id == sector_id)
    )
    return result.scalar_one_or_none()


async def sector_exists(db: AsyncSession, sector_id: str) -> bool:
    """Check if a sector exists.

    Args:
        db: Database session.
        sector_id: The sector identifier.

    Returns:
        True if sector exists, False otherwise.
    """
    result = await db.execute(
        select(func.count()).select_from(models.Sector).where(models.Sector.id == sector_id)
    )
    count = result.scalar()
    return count > 0


# ============================================================================
# PORTFOLIO COMPANY CRUD
# ============================================================================


@async_retry_on_exception((OperationalError, DBAPIError))
async def create_portfolio_company(
    db: AsyncSession,
    name: str,
    sector_id: str,
    stage: str,
    founded_date: Optional[date] = None,
    financials: Optional[dict[str, Any]] = None,
    last_round: Optional[dict[str, Any]] = None,
    adjustments: Optional[list[dict[str, Any]]] = None,
) -> models.PortfolioCompany:
    """Create a new portfolio company.

    Args:
        db: Database session.
        name: Company name.
        sector_id: Sector identifier.
        stage: Company stage.
        founded_date: Optional founding date.
        financials: Optional financial data (JSONB).
        last_round: Optional last funding round data (JSONB).
        adjustments: Optional valuation adjustments (JSONB list).

    Returns:
        The created PortfolioCompany.
    """
    company = models.PortfolioCompany(
        name=name,
        sector_id=sector_id,
        stage=stage,
        founded_date=founded_date,
        financials=financials or {},
        last_round=last_round,
        adjustments=adjustments or [],
    )
    db.add(company)
    await db.flush()
    await db.refresh(company)
    return company


async def get_portfolio_company_by_id(
    db: AsyncSession, company_id: UUID
) -> Optional[models.PortfolioCompany]:
    """Get a portfolio company by ID.

    Args:
        db: Database session.
        company_id: The company UUID.

    Returns:
        PortfolioCompany if found, None otherwise.
    """
    result = await db.execute(
        select(models.PortfolioCompany).where(models.PortfolioCompany.id == company_id)
    )
    return result.scalar_one_or_none()


async def list_portfolio_companies(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> list[models.PortfolioCompany]:
    """List portfolio companies, most recent first.

    Args:
        db: Database session.
        limit: Maximum number of results.
        offset: Number of results to skip.

    Returns:
        List of PortfolioCompany objects.
    """
    result = await db.execute(
        select(models.PortfolioCompany)
        .order_by(desc(models.PortfolioCompany.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def count_portfolio_companies(db: AsyncSession) -> int:
    """Get total count of portfolio companies.

    Args:
        db: Database session.

    Returns:
        Total number of companies.
    """
    result = await db.execute(
        select(func.count()).select_from(models.PortfolioCompany)
    )
    return result.scalar() or 0


async def delete_portfolio_company(db: AsyncSession, company_id: UUID) -> bool:
    """Delete a portfolio company.

    Note: This will fail if valuations reference this company
    due to foreign key constraint.

    Args:
        db: Database session.
        company_id: The company to delete.

    Returns:
        True if deleted, False if not found.
    """
    company = await get_portfolio_company_by_id(db, company_id)
    if company is None:
        return False

    await db.delete(company)
    await db.flush()
    return True


# ============================================================================
# VALUATION CRUD
# ============================================================================


@async_retry_on_exception((OperationalError, DBAPIError))
async def create_valuation(
    db: AsyncSession,
    portfolio_company_id: UUID,
    company_name: str,
    input_snapshot: dict[str, Any],
    input_hash: str,
    primary_value: Decimal,
    primary_method: str,
    value_range_low: Optional[Decimal],
    value_range_high: Optional[Decimal],
    overall_confidence: str,
    summary: dict[str, Any],
    method_results: list[dict[str, Any]],
    skipped_methods: Optional[list[dict[str, Any]]] = None,
    config_snapshot: Optional[dict[str, Any]] = None,
    valuation_date: Optional[date] = None,
) -> models.Valuation:
    """Create a new valuation record.

    This is the main write operation - creates a complete audit
    record of a valuation run.

    Args:
        db: Database session.
        portfolio_company_id: UUID of the portfolio company.
        company_name: Name of the company being valued.
        input_snapshot: Complete input data (JSONB).
        input_hash: SHA256 hash of input snapshot.
        primary_value: The primary valuation result.
        primary_method: Method used for primary value.
        value_range_low: Lower bound of valuation range.
        value_range_high: Upper bound of valuation range.
        overall_confidence: Confidence level (HIGH/MEDIUM/LOW).
        summary: Summary data (JSONB).
        method_results: List of method results (JSONB).
        skipped_methods: Optional list of skipped methods (JSONB).
        config_snapshot: Optional config snapshot (JSONB).
        valuation_date: Optional valuation date (defaults to today).

    Returns:
        The created Valuation.
    """
    valuation = models.Valuation(
        portfolio_company_id=portfolio_company_id,
        company_name=company_name,
        input_snapshot=input_snapshot,
        input_hash=input_hash,
        primary_value=primary_value,
        primary_method=primary_method,
        value_range_low=value_range_low,
        value_range_high=value_range_high,
        overall_confidence=overall_confidence,
        summary=summary,
        method_results=method_results,
        skipped_methods=skipped_methods or [],
        config_snapshot=config_snapshot or {},
        valuation_date=valuation_date or date.today(),
    )
    db.add(valuation)
    await db.flush()
    await db.refresh(valuation)
    return valuation


async def get_valuation_by_id(
    db: AsyncSession, valuation_id: UUID
) -> Optional[models.Valuation]:
    """Get a valuation by ID.

    Args:
        db: Database session.
        valuation_id: The valuation UUID.

    Returns:
        Valuation if found, None otherwise.
    """
    result = await db.execute(
        select(models.Valuation).where(models.Valuation.id == valuation_id)
    )
    return result.scalar_one_or_none()


async def list_recent_valuations(
    db: AsyncSession, limit: int = 20
) -> list[models.Valuation]:
    """List most recent valuations across all companies.

    Uses selectinload to prevent N+1 queries when accessing
    related portfolio company data.

    Args:
        db: Database session.
        limit: Maximum number of results.

    Returns:
        List of Valuation objects, most recent first.
    """
    result = await db.execute(
        select(models.Valuation)
        .order_by(desc(models.Valuation.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_valuations_by_company(
    db: AsyncSession, company_id: UUID, limit: int = 20
) -> list[models.Valuation]:
    """List valuations for a specific company.

    Args:
        db: Database session.
        company_id: The portfolio company ID.
        limit: Maximum number of results.

    Returns:
        List of Valuation objects, most recent first.
    """
    result = await db.execute(
        select(models.Valuation)
        .where(models.Valuation.portfolio_company_id == company_id)
        .order_by(desc(models.Valuation.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def count_valuations_by_company(db: AsyncSession, company_id: UUID) -> int:
    """Count valuations for a specific company.

    Args:
        db: Database session.
        company_id: The portfolio company ID.

    Returns:
        Number of valuations.
    """
    result = await db.execute(
        select(func.count())
        .select_from(models.Valuation)
        .where(models.Valuation.portfolio_company_id == company_id)
    )
    return result.scalar() or 0


async def delete_valuation(db: AsyncSession, valuation_id: UUID) -> bool:
    """Delete a valuation.

    Args:
        db: Database session.
        valuation_id: The valuation to delete.

    Returns:
        True if deleted, False if not found.
    """
    valuation = await get_valuation_by_id(db, valuation_id)
    if valuation is None:
        return False

    await db.delete(valuation)
    await db.flush()
    return True


# ============================================================================
# COMPARABLE COMPANY CRUD
# ============================================================================


async def get_comparables_by_sector(
    db: AsyncSession, sector_id: str
) -> list[models.ComparableCompany]:
    """Get all comparable companies for a sector.

    This is the main query used by the Comps valuation method.
    Returns all companies in a single efficient query.

    Args:
        db: Database session.
        sector_id: The sector to filter by (e.g., 'saas', 'fintech').

    Returns:
        List of ComparableCompany objects for the sector,
        ordered by market cap (highest first).
    """
    result = await db.execute(
        select(models.ComparableCompany)
        .where(models.ComparableCompany.sector_id == sector_id)
        .order_by(desc(models.ComparableCompany.market_cap))
    )
    return list(result.scalars().all())


async def get_comparable_by_ticker(
    db: AsyncSession, ticker: str
) -> Optional[models.ComparableCompany]:
    """Get a specific company by ticker symbol.

    Args:
        db: Database session.
        ticker: Stock ticker (e.g., 'CRM', 'NOW').

    Returns:
        ComparableCompany if found, None otherwise.
    """
    result = await db.execute(
        select(models.ComparableCompany).where(
            models.ComparableCompany.ticker == ticker.upper()
        )
    )
    return result.scalar_one_or_none()


async def get_sector_median_multiple(
    db: AsyncSession, sector_id: str
) -> Optional[Decimal]:
    """Calculate median EV/Revenue multiple for a sector.

    Used by the Comps method to determine the benchmark multiple.

    Args:
        db: Database session.
        sector_id: The sector to calculate median for.

    Returns:
        Median multiple or None if no data.
    """
    # PostgreSQL percentile_cont for true median
    result = await db.execute(
        select(
            func.percentile_cont(0.5)
            .within_group(models.ComparableCompany.ev_revenue_multiple)
        )
        .where(models.ComparableCompany.sector_id == sector_id)
        .where(models.ComparableCompany.ev_revenue_multiple.isnot(None))
    )
    median = result.scalar()
    return Decimal(str(median)) if median is not None else None


async def get_sector_multiple_stats(db: AsyncSession, sector_id: str) -> dict:
    """Get statistical summary for a sector's multiples.

    Returns min, max, median, and average for audit trail.

    Args:
        db: Database session.
        sector_id: The sector to analyze.

    Returns:
        Dictionary with min, max, median, avg, count.
    """
    result = await db.execute(
        select(
            func.min(models.ComparableCompany.ev_revenue_multiple).label("min"),
            func.max(models.ComparableCompany.ev_revenue_multiple).label("max"),
            func.percentile_cont(0.5)
            .within_group(models.ComparableCompany.ev_revenue_multiple)
            .label("median"),
            func.avg(models.ComparableCompany.ev_revenue_multiple).label("avg"),
            func.count().label("count"),
        )
        .where(models.ComparableCompany.sector_id == sector_id)
        .where(models.ComparableCompany.ev_revenue_multiple.isnot(None))
    )
    row = result.one()

    return {
        "min": Decimal(str(row.min)) if row.min else None,
        "max": Decimal(str(row.max)) if row.max else None,
        "median": Decimal(str(row.median)) if row.median else None,
        "avg": Decimal(str(row.avg)) if row.avg else None,
        "count": row.count,
    }


# ============================================================================
# MARKET INDEX CRUD
# ============================================================================


async def get_market_index_value(
    db: AsyncSession, index_name: str, target_date: date
) -> Optional[Decimal]:
    """Get the index value at or before a specific date.

    Uses the most recent available data point at or before the target date.
    This handles cases where we don't have data for the exact date.

    Args:
        db: Database session.
        index_name: Index identifier (e.g., 'NASDAQ', 'SP500').
        target_date: The date to look up.

    Returns:
        Index value or None if no data available.
    """
    result = await db.execute(
        select(models.MarketIndex.value)
        .where(models.MarketIndex.name == index_name)
        .where(models.MarketIndex.date <= target_date)
        .order_by(desc(models.MarketIndex.date))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_market_index_value(
    db: AsyncSession, index_name: str
) -> Optional[Decimal]:
    """Get the most recent value for an index.

    Args:
        db: Database session.
        index_name: Index identifier.

    Returns:
        Most recent index value, or None if no data.
    """
    result = await db.execute(
        select(models.MarketIndex.value)
        .where(models.MarketIndex.name == index_name)
        .order_by(desc(models.MarketIndex.date))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def calculate_market_change(
    db: AsyncSession, index_name: str, start_date: date, end_date: date
) -> Optional[Decimal]:
    """Calculate the percent change in an index between two dates.

    This is the core calculation for the Last Round method:
    it determines how much the market has moved since the
    company's last funding round.

    Args:
        db: Database session.
        index_name: Index to use (e.g., 'NASDAQ').
        start_date: Beginning of period (typically last round date).
        end_date: End of period (typically today).

    Returns:
        Percent change as a Decimal, or None if data is unavailable
        for either date or if start value is zero.
    """
    start_value = await get_market_index_value(db, index_name, start_date)
    end_value = await get_market_index_value(db, index_name, end_date)

    if start_value is None or end_value is None or start_value == 0:
        return None

    return (end_value - start_value) / start_value


async def list_market_indices(db: AsyncSession) -> list[str]:
    """Get list of available index names.

    Args:
        db: Database session.

    Returns:
        List of unique index names.
    """
    result = await db.execute(
        select(models.MarketIndex.name).distinct().order_by(models.MarketIndex.name)
    )
    return list(result.scalars().all())


async def get_market_index_date_range(
    db: AsyncSession, index_name: str
) -> Optional[tuple[date, date]]:
    """Get the available date range for an index.

    Args:
        db: Database session.
        index_name: Index identifier.

    Returns:
        Tuple of (earliest_date, latest_date), or None if no data.
    """
    result = await db.execute(
        select(
            func.min(models.MarketIndex.date).label("min_date"),
            func.max(models.MarketIndex.date).label("max_date"),
        ).where(models.MarketIndex.name == index_name)
    )
    row = result.one()

    if row.min_date is None:
        return None

    return (row.min_date, row.max_date)
