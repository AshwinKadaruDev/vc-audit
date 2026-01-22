"""Data loading layer for VC Audit Tool.

All runtime data is loaded from the database. JSON files in backend/data/
are only used during setup (alembic migrations) to seed the database.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from src.config import Settings, get_settings
from src.database import crud
from src.database.database import get_sync_db
from src.exceptions import DataNotFoundError
from src.models import (
    Adjustment,
    ComparableCompany,
    ComparableSet,
    Company,
    CompanyData,
    DataSource,
    Financials,
    LastRound,
    MarketIndex,
)


class DataLoader:
    """Loads and caches company, market, and comparable data from the database.

    All data is read from PostgreSQL. JSON files are only used during
    setup.ps1 to seed the database via Alembic migrations.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._indices_cache: Optional[dict[str, list[MarketIndex]]] = None
        self._index_sources: dict[str, str] = {}
        self._comparables_cache: dict[str, ComparableSet] = {}

    def list_companies(self) -> list[dict[str, str]]:
        """List all available portfolio companies from the database.

        Returns:
            List of dicts with 'id', 'name', 'sector', 'stage' keys.
        """
        with get_sync_db() as db:
            companies = crud.list_portfolio_companies_sync(db, limit=1000)

        return sorted(
            [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "sector": c.sector_id,
                    "stage": c.stage,
                }
                for c in companies
            ],
            key=lambda c: c["name"],
        )

    def load_company(self, company_id: str) -> CompanyData:
        """Load company data by ID from the database.

        Args:
            company_id: Company UUID as string.

        Returns:
            CompanyData model with all company information.

        Raises:
            DataNotFoundError: If company doesn't exist.
        """
        try:
            uuid_id = UUID(company_id)
        except ValueError:
            raise DataNotFoundError("Company", company_id)

        with get_sync_db() as db:
            company = crud.get_portfolio_company_by_id_sync(db, uuid_id)

        if company is None:
            raise DataNotFoundError("Company", company_id)

        # Convert database model to Pydantic model
        financials_data = company.financials or {}
        last_round_data = company.last_round
        adjustments_data = company.adjustments or []

        # Build Company
        company_model = Company(
            id=str(company.id),
            name=company.name,
            sector=company.sector_id,
            stage=company.stage,
            founded_date=company.founded_date,
        )

        # Build Financials
        financials = Financials(
            revenue_ttm=(
                Decimal(financials_data["revenue_ttm"])
                if financials_data.get("revenue_ttm")
                else None
            ),
            revenue_growth_yoy=(
                Decimal(financials_data["revenue_growth_yoy"])
                if financials_data.get("revenue_growth_yoy")
                else None
            ),
            gross_margin=(
                Decimal(financials_data["gross_margin"])
                if financials_data.get("gross_margin")
                else None
            ),
            burn_rate=(
                Decimal(financials_data["burn_rate"])
                if financials_data.get("burn_rate")
                else None
            ),
            runway_months=financials_data.get("runway_months"),
        )

        # Build LastRound if exists
        last_round = None
        if last_round_data:
            last_round = LastRound(
                date=date.fromisoformat(last_round_data["date"]),
                valuation_pre=Decimal(last_round_data["valuation_pre"]),
                valuation_post=Decimal(last_round_data["valuation_post"]),
                amount_raised=Decimal(last_round_data["amount_raised"]),
                lead_investor=last_round_data.get("lead_investor"),
            )

        # Build adjustments
        adjustments = [
            Adjustment(
                name=adj["name"],
                factor=Decimal(adj["factor"]),
                reason=adj.get("reason", ""),
            )
            for adj in adjustments_data
        ]

        return CompanyData(
            company=company_model,
            financials=financials,
            last_round=last_round,
            adjustments=adjustments,
        )

    def _load_index(self, name: str) -> None:
        """Load a single index into cache if not already loaded."""
        if self._indices_cache is None:
            self._indices_cache = {}

        if name in self._indices_cache:
            return

        with get_sync_db() as db:
            db_indices = crud.get_market_index_time_series_sync(db, name)

        if not db_indices:
            return

        self._index_sources[name] = db_indices[0].source_name
        self._indices_cache[name] = sorted(
            [
                MarketIndex(
                    date=idx.date,
                    value=idx.value,
                    name=idx.name,
                    source_name=idx.source_name,
                )
                for idx in db_indices
            ],
            key=lambda p: p.date,
        )

    def load_indices(self) -> dict[str, list[MarketIndex]]:
        """Load and cache all known market indices.

        Returns:
            Dict mapping index name to list of MarketIndex data points.
        """
        for index_name in ["NASDAQ", "SP500"]:
            self._load_index(index_name)
        return self._indices_cache or {}

    def get_index(self, name: str) -> list[MarketIndex]:
        """Get specific market index data.

        Args:
            name: Index name (e.g., 'NASDAQ', 'SP500').

        Returns:
            List of MarketIndex data points sorted by date.

        Raises:
            DataNotFoundError: If index doesn't exist.
        """
        self._load_index(name)

        if self._indices_cache is None or name not in self._indices_cache:
            raise DataNotFoundError("Market index", name)

        return self._indices_cache[name]

    def get_index_source(self, name: str) -> DataSource:
        """Get the data source info for a market index.

        Args:
            name: Index name.

        Returns:
            DataSource with source information.
        """
        self._load_index(name)

        return DataSource(
            name=self._index_sources.get(name, "Yahoo Finance API"),
            retrieved_at=date.today(),
            is_mock=True,
        )

    def list_sectors(self) -> list[str]:
        """List all available sectors from the database.

        Returns:
            List of sector IDs.
        """
        with get_sync_db() as db:
            sectors = crud.get_all_sectors_sync(db)

        return sorted([s.id for s in sectors])

    def load_comparables(self, sector: str) -> ComparableSet:
        """Load comparable companies for a sector from the database.

        Args:
            sector: Sector ID (e.g., 'saas', 'fintech').

        Returns:
            ComparableSet with list of comparable companies.

        Raises:
            DataNotFoundError: If no comparables found for sector.
        """
        if sector in self._comparables_cache:
            return self._comparables_cache[sector]

        with get_sync_db() as db:
            db_companies = crud.get_comparables_by_sector_sync(db, sector)

        if not db_companies:
            raise DataNotFoundError("Comparables", sector)

        # Get source info from first company
        source_name = db_companies[0].source_name if db_companies else "Yahoo Finance API"
        as_of_date = db_companies[0].as_of_date if db_companies else date.today()

        companies = [
            ComparableCompany(
                ticker=c.ticker,
                name=c.name,
                sector=c.sector_id,
                revenue_ttm=c.revenue_ttm or Decimal("0"),
                market_cap=c.market_cap or Decimal("0"),
                ev_revenue_multiple=c.ev_revenue_multiple or Decimal("0"),
                revenue_growth_yoy=c.revenue_growth_yoy,
                source_name=c.source_name,
            )
            for c in db_companies
        ]

        comparable_set = ComparableSet(
            sector=sector,
            as_of_date=as_of_date,
            companies=companies,
            source=DataSource(
                name=source_name,
                retrieved_at=as_of_date,
                is_mock=True,
            ),
        )
        self._comparables_cache[sector] = comparable_set
        return comparable_set
