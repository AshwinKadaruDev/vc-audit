"""Data loading layer for VC Audit Tool."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from src.config import Settings, get_settings
from src.exceptions import DataLoadError, DataNotFoundError, DataValidationError
from src.models import ComparableCompany, ComparableSet, CompanyData, MarketIndex
from src.utils.retry import retry_on_exception


class DataLoader:
    """Loads and caches company, market, and comparable data."""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._validate_directories()
        self._indices_cache: Optional[dict[str, list[MarketIndex]]] = None
        self._comparables_cache: dict[str, ComparableSet] = {}

    def _validate_directories(self) -> None:
        """Validate that required data directories exist."""
        for dir_path in [
            self._settings.companies_dir,
            self._settings.market_dir,
            self._settings.comparables_dir,
        ]:
            if not dir_path.exists():
                raise DataLoadError(
                    source=str(dir_path),
                    reason="Directory does not exist",
                )

    def list_companies(self) -> list[dict[str, str]]:
        """List all available companies.

        Returns:
            List of dicts with 'id' and 'name' keys.
        """
        companies = []
        for file_path in self._settings.companies_dir.glob("*.json"):
            try:
                data = self._load_json(file_path)
                company_info = data.get("company", {})
                companies.append({
                    "id": company_info.get("id", file_path.stem),
                    "name": company_info.get("name", file_path.stem),
                    "sector": company_info.get("sector", "unknown"),
                    "stage": company_info.get("stage", "unknown"),
                })
            except Exception:
                continue
        return sorted(companies, key=lambda c: c["name"])

    def load_company(self, company_id: str) -> CompanyData:
        """Load company data by ID.

        Args:
            company_id: Company identifier matching the JSON filename.

        Returns:
            CompanyData model with all company information.

        Raises:
            DataNotFoundError: If company file doesn't exist.
            DataValidationError: If data fails validation.
        """
        file_path = self._settings.companies_dir / f"{company_id}.json"
        if not file_path.exists():
            raise DataNotFoundError("Company", company_id)

        data = self._load_json(file_path)
        try:
            return CompanyData.model_validate(data)
        except ValidationError as e:
            raise DataValidationError(
                message=f"Invalid company data for {company_id}",
                validation_errors=[err for err in e.errors()],
            )

    def load_indices(self) -> dict[str, list[MarketIndex]]:
        """Load and cache market indices.

        Returns:
            Dict mapping index name to list of MarketIndex data points.
        """
        if self._indices_cache is not None:
            return self._indices_cache

        file_path = self._settings.market_dir / "indices.json"
        if not file_path.exists():
            raise DataNotFoundError("Market data", "indices.json")

        data = self._load_json(file_path)
        self._indices_cache = {}

        for index_data in data.get("indices", []):
            name = index_data.get("name")
            if not name:
                continue

            points = []
            for point in index_data.get("data", []):
                points.append(
                    MarketIndex(
                        date=date.fromisoformat(point["date"]),
                        value=Decimal(point["value"]),
                        name=name,
                    )
                )
            self._indices_cache[name] = sorted(points, key=lambda p: p.date)

        return self._indices_cache

    def get_index(self, name: str) -> list[MarketIndex]:
        """Get specific market index data.

        Args:
            name: Index name (e.g., 'NASDAQ', 'SP500').

        Returns:
            List of MarketIndex data points sorted by date.

        Raises:
            DataNotFoundError: If index doesn't exist.
        """
        indices = self.load_indices()
        if name not in indices:
            raise DataNotFoundError("Market index", name)
        return indices[name]

    def list_sectors(self) -> list[str]:
        """List all available comparable sectors.

        Returns:
            List of sector names.
        """
        sectors = []
        for file_path in self._settings.comparables_dir.glob("*.json"):
            sectors.append(file_path.stem)
        return sorted(sectors)

    def load_comparables(self, sector: str) -> ComparableSet:
        """Load comparable companies for a sector.

        Args:
            sector: Sector name matching the JSON filename.

        Returns:
            ComparableSet with list of comparable companies.

        Raises:
            DataNotFoundError: If sector file doesn't exist.
        """
        if sector in self._comparables_cache:
            return self._comparables_cache[sector]

        file_path = self._settings.comparables_dir / f"{sector}.json"
        if not file_path.exists():
            raise DataNotFoundError("Comparables", sector)

        data = self._load_json(file_path)

        companies = []
        for comp in data.get("companies", []):
            companies.append(
                ComparableCompany(
                    ticker=comp["ticker"],
                    name=comp["name"],
                    sector=comp["sector"],
                    revenue_ttm=Decimal(comp["revenue_ttm"]),
                    market_cap=Decimal(comp["market_cap"]),
                    ev_revenue_multiple=Decimal(comp["ev_revenue_multiple"]),
                    revenue_growth_yoy=(
                        Decimal(comp["revenue_growth_yoy"])
                        if comp.get("revenue_growth_yoy")
                        else None
                    ),
                )
            )

        comparable_set = ComparableSet(
            sector=data["sector"],
            as_of_date=date.fromisoformat(data["as_of_date"]),
            companies=companies,
        )
        self._comparables_cache[sector] = comparable_set
        return comparable_set

    @retry_on_exception((IOError, OSError))
    def _load_json(self, file_path: Path) -> dict:
        """Load and parse JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            Parsed JSON data as dict.

        Raises:
            DataLoadError: If file cannot be read or parsed.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataLoadError(str(file_path), f"Invalid JSON: {e}")
        except IOError as e:
            raise DataLoadError(str(file_path), str(e))
