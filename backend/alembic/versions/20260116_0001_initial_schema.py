"""Initial schema with enums, tables, and seed data.

Revision ID: 0001
Revises: None
Create Date: 2026-01-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    confidence_level = postgresql.ENUM(
        "high", "medium", "low", name="confidence_level", create_type=False
    )
    confidence_level.create(op.get_bind(), checkfirst=True)

    company_stage = postgresql.ENUM(
        "seed", "series_a", "series_b", "series_c", "growth",
        name="company_stage", create_type=False
    )
    company_stage.create(op.get_bind(), checkfirst=True)

    valuation_method = postgresql.ENUM(
        "last_round", "comparables", name="valuation_method", create_type=False
    )
    valuation_method.create(op.get_bind(), checkfirst=True)

    # Create sectors table
    op.create_table(
        "sectors",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create market_indices table
    op.create_table(
        "market_indices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("value", sa.Numeric(18, 2), nullable=False),
        sa.UniqueConstraint("name", "date", name="uq_market_indices_name_date"),
    )
    op.create_index("idx_market_indices_lookup", "market_indices", ["name", "date"])

    # Create comparable_companies table
    op.create_table(
        "comparable_companies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(10), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sector_id", sa.String(50), sa.ForeignKey("sectors.id"), nullable=False),
        sa.Column("revenue_ttm", sa.Numeric(18, 2)),
        sa.Column("market_cap", sa.Numeric(18, 2)),
        sa.Column("ev_revenue_multiple", sa.Numeric(10, 4)),
        sa.Column("revenue_growth_yoy", sa.Numeric(10, 4)),
        sa.Column("as_of_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_comparables_sector", "comparable_companies", ["sector_id"])

    # Create portfolio_companies table
    op.create_table(
        "portfolio_companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sector_id", sa.String(50), sa.ForeignKey("sectors.id"), nullable=False),
        sa.Column("stage", postgresql.ENUM("seed", "series_a", "series_b", "series_c", "growth", name="company_stage", create_type=False), nullable=False),
        sa.Column("founded_date", sa.Date),
        sa.Column("financials", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("last_round", postgresql.JSONB),
        sa.Column("adjustments", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_portfolio_created", "portfolio_companies", ["created_at"], postgresql_ops={"created_at": "DESC"})

    # Create valuations table
    op.create_table(
        "valuations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("portfolio_company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolio_companies.id"), nullable=False),
        sa.Column("input_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("primary_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("primary_method", postgresql.ENUM("last_round", "comparables", name="valuation_method", create_type=False), nullable=False),
        sa.Column("value_range_low", sa.Numeric(18, 2)),
        sa.Column("value_range_high", sa.Numeric(18, 2)),
        sa.Column("overall_confidence", postgresql.ENUM("high", "medium", "low", name="confidence_level", create_type=False), nullable=False),
        sa.Column("summary", postgresql.JSONB, nullable=False),
        sa.Column("method_results", postgresql.JSONB, nullable=False),
        sa.Column("skipped_methods", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("config_snapshot", postgresql.JSONB, nullable=False),
        sa.Column("valuation_date", sa.Date, server_default=sa.text("CURRENT_DATE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_valuations_company", "valuations", ["portfolio_company_id"])
    op.create_index("idx_valuations_created", "valuations", ["created_at"], postgresql_ops={"created_at": "DESC"})

    # Seed data: Sectors
    op.execute("""
        INSERT INTO sectors (id, display_name) VALUES
        ('saas', 'SaaS'),
        ('fintech', 'Fintech')
    """)

    # Seed data: Market Indices
    op.execute("""
        INSERT INTO market_indices (name, date, value) VALUES
        ('NASDAQ', '2022-01-01', 15644.97),
        ('NASDAQ', '2022-07-01', 11028.74),
        ('NASDAQ', '2023-01-01', 10466.48),
        ('NASDAQ', '2023-07-01', 14346.02),
        ('NASDAQ', '2024-01-01', 14765.98),
        ('NASDAQ', '2024-07-01', 17879.30),
        ('NASDAQ', '2025-01-01', 19621.68),
        ('NASDAQ', '2025-07-01', 20145.32),
        ('NASDAQ', '2026-01-01', 21234.56),
        ('SP500', '2022-01-01', 4766.18),
        ('SP500', '2022-07-01', 3785.38),
        ('SP500', '2023-01-01', 3824.14),
        ('SP500', '2023-07-01', 4588.96),
        ('SP500', '2024-01-01', 4769.83),
        ('SP500', '2024-07-01', 5475.09),
        ('SP500', '2025-01-01', 5942.47),
        ('SP500', '2025-07-01', 6124.83),
        ('SP500', '2026-01-01', 6387.21)
    """)

    # Seed data: Comparable Companies - SaaS
    op.execute("""
        INSERT INTO comparable_companies (ticker, name, sector_id, revenue_ttm, market_cap, ev_revenue_multiple, revenue_growth_yoy, as_of_date) VALUES
        ('CRM', 'Salesforce', 'saas', 34860000000, 276000000000, 7.9, 0.11, '2026-01-15'),
        ('NOW', 'ServiceNow', 'saas', 9150000000, 168000000000, 18.4, 0.24, '2026-01-15'),
        ('WDAY', 'Workday', 'saas', 7260000000, 69000000000, 9.5, 0.17, '2026-01-15'),
        ('DDOG', 'Datadog', 'saas', 2120000000, 42000000000, 19.8, 0.26, '2026-01-15'),
        ('ZS', 'Zscaler', 'saas', 1900000000, 28000000000, 14.7, 0.35, '2026-01-15'),
        ('SNOW', 'Snowflake', 'saas', 3100000000, 56000000000, 18.1, 0.32, '2026-01-15')
    """)

    # Seed data: Comparable Companies - Fintech
    op.execute("""
        INSERT INTO comparable_companies (ticker, name, sector_id, revenue_ttm, market_cap, ev_revenue_multiple, revenue_growth_yoy, as_of_date) VALUES
        ('SQ', 'Block (Square)', 'fintech', 21500000000, 47000000000, 2.2, 0.18, '2026-01-15'),
        ('PYPL', 'PayPal', 'fintech', 30200000000, 72000000000, 2.4, 0.08, '2026-01-15'),
        ('AFRM', 'Affirm', 'fintech', 2300000000, 17000000000, 7.4, 0.41, '2026-01-15'),
        ('SOFI', 'SoFi Technologies', 'fintech', 2400000000, 14000000000, 5.8, 0.34, '2026-01-15'),
        ('BILL', 'Bill.com', 'fintech', 1280000000, 8500000000, 6.6, 0.22, '2026-01-15')
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("valuations")
    op.drop_table("portfolio_companies")
    op.drop_table("comparable_companies")
    op.drop_table("market_indices")
    op.drop_table("sectors")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS valuation_method")
    op.execute("DROP TYPE IF EXISTS company_stage")
    op.execute("DROP TYPE IF EXISTS confidence_level")
