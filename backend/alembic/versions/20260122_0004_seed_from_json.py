"""Seed database tables from JSON files.

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-22

This migration reads seed data from JSON files in backend/data/ and
upserts it into the database. This replaces the hardcoded seed data
in migrations 0001 and 0002, ensuring JSON files are the single source
of truth for seed data.

Uses ON CONFLICT to handle re-runs gracefully - existing data is updated
rather than causing duplicate key errors.
"""

import json
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_data_dir() -> Path:
    """Get the data directory path relative to this migration file."""
    # This migration file is in backend/alembic/versions/
    # Data files are in backend/data/
    migration_dir = Path(__file__).parent
    return migration_dir.parent.parent / "data"


def upgrade() -> None:
    data_dir = get_data_dir()
    conn = op.get_bind()

    # =========================================================================
    # SEED MARKET INDICES from backend/data/market/indices.json
    # =========================================================================
    indices_file = data_dir / "market" / "indices.json"
    if indices_file.exists():
        with open(indices_file, "r", encoding="utf-8") as f:
            indices_data = json.load(f)

        for index_info in indices_data.get("indices", []):
            index_name = index_info.get("name")
            source_name = index_info.get("source_name", "Yahoo Finance API")

            for point in index_info.get("data", []):
                # Use ON CONFLICT to upsert - update if exists, insert if not
                # The unique constraint is on (name, date)
                conn.execute(
                    sa.text("""
                        INSERT INTO market_indices (name, date, value, source_name)
                        VALUES (:name, :date, :value, :source_name)
                        ON CONFLICT (name, date)
                        DO UPDATE SET value = EXCLUDED.value, source_name = EXCLUDED.source_name
                    """),
                    {
                        "name": index_name,
                        "date": point["date"],
                        "value": point["value"],
                        "source_name": source_name,
                    },
                )

    # =========================================================================
    # SEED COMPARABLE COMPANIES from backend/data/comparables/*.json
    # =========================================================================
    comparables_dir = data_dir / "comparables"
    if comparables_dir.exists():
        for comp_file in comparables_dir.glob("*.json"):
            with open(comp_file, "r", encoding="utf-8") as f:
                comp_data = json.load(f)

            sector_id = comp_data.get("sector")
            as_of_date = comp_data.get("as_of_date")
            sector_source_name = comp_data.get("source_name", "Yahoo Finance API")

            for company in comp_data.get("companies", []):
                # Per-company source_name overrides sector-level source_name
                company_source = company.get("source_name", sector_source_name)

                # Use ON CONFLICT on ticker (unique) to upsert
                conn.execute(
                    sa.text("""
                        INSERT INTO comparable_companies
                            (ticker, name, sector_id, revenue_ttm, market_cap,
                             ev_revenue_multiple, revenue_growth_yoy, as_of_date, source_name)
                        VALUES
                            (:ticker, :name, :sector_id, :revenue_ttm, :market_cap,
                             :ev_revenue_multiple, :revenue_growth_yoy, :as_of_date, :source_name)
                        ON CONFLICT (ticker)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            sector_id = EXCLUDED.sector_id,
                            revenue_ttm = EXCLUDED.revenue_ttm,
                            market_cap = EXCLUDED.market_cap,
                            ev_revenue_multiple = EXCLUDED.ev_revenue_multiple,
                            revenue_growth_yoy = EXCLUDED.revenue_growth_yoy,
                            as_of_date = EXCLUDED.as_of_date,
                            source_name = EXCLUDED.source_name
                    """),
                    {
                        "ticker": company["ticker"],
                        "name": company["name"],
                        "sector_id": company.get("sector", sector_id),
                        "revenue_ttm": company.get("revenue_ttm"),
                        "market_cap": company.get("market_cap"),
                        "ev_revenue_multiple": company.get("ev_revenue_multiple"),
                        "revenue_growth_yoy": company.get("revenue_growth_yoy"),
                        "as_of_date": as_of_date,
                        "source_name": company_source,
                    },
                )

    # =========================================================================
    # SEED PORTFOLIO COMPANIES from backend/data/companies/*.json
    # =========================================================================
    # Note: Portfolio companies use UUIDs generated by the database, so we
    # use ON CONFLICT on name to handle re-runs. This means company names
    # must be unique.
    companies_dir = data_dir / "companies"
    if companies_dir.exists():
        for company_file in companies_dir.glob("*.json"):
            with open(company_file, "r", encoding="utf-8") as f:
                company_data = json.load(f)

            company_info = company_data.get("company", {})
            financials = company_data.get("financials", {})
            last_round = company_data.get("last_round")
            adjustments = company_data.get("adjustments", [])

            # Convert to JSON strings for JSONB columns
            financials_json = json.dumps(financials)
            last_round_json = json.dumps(last_round) if last_round else None
            adjustments_json = json.dumps(adjustments)

            # Use name for conflict detection since UUIDs are auto-generated
            # First, try to update existing company by name
            # Note: Use CAST() instead of :: to avoid conflict with SQLAlchemy's :param syntax
            result = conn.execute(
                sa.text("""
                    UPDATE portfolio_companies
                    SET sector_id = :sector_id,
                        stage = :stage,
                        founded_date = :founded_date,
                        financials = CAST(:financials AS jsonb),
                        last_round = CAST(:last_round AS jsonb),
                        adjustments = CAST(:adjustments AS jsonb)
                    WHERE name = :name
                """),
                {
                    "name": company_info.get("name"),
                    "sector_id": company_info.get("sector"),
                    "stage": company_info.get("stage"),
                    "founded_date": company_info.get("founded_date"),
                    "financials": financials_json,
                    "last_round": last_round_json,
                    "adjustments": adjustments_json,
                },
            )

            # If no rows updated, insert new company
            if result.rowcount == 0:
                conn.execute(
                    sa.text("""
                        INSERT INTO portfolio_companies
                            (name, sector_id, stage, founded_date, financials, last_round, adjustments)
                        VALUES
                            (:name, :sector_id, :stage, :founded_date,
                             CAST(:financials AS jsonb), CAST(:last_round AS jsonb), CAST(:adjustments AS jsonb))
                    """),
                    {
                        "name": company_info.get("name"),
                        "sector_id": company_info.get("sector"),
                        "stage": company_info.get("stage"),
                        "founded_date": company_info.get("founded_date"),
                        "financials": financials_json,
                        "last_round": last_round_json,
                        "adjustments": adjustments_json,
                    },
                )


def downgrade() -> None:
    # This migration only upserts data, so downgrade just removes the
    # JSON-sourced updates. The original hardcoded data from 0001/0002
    # would need to be re-applied if you want to restore that state.
    #
    # In practice, downgrading seed data migrations is rarely needed.
    # If you need to reset, use `alembic downgrade base` and re-run.
    pass
