"""Seed portfolio companies from JSON data.

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-16
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Seed portfolio companies from JSON data files
    # These are the 5 sample companies used for testing and demo

    # Basis AI - Series A SaaS company
    op.execute("""
        INSERT INTO portfolio_companies (name, sector_id, stage, founded_date, financials, last_round, adjustments)
        VALUES (
            'Basis AI',
            'saas',
            'series_a',
            '2021-03-15',
            '{"revenue_ttm": "10000000", "revenue_growth_yoy": "1.20", "gross_margin": "0.75", "burn_rate": "500000", "runway_months": 18}',
            '{"date": "2025-04-15", "valuation_pre": "40000000", "valuation_post": "50000000", "amount_raised": "10000000", "lead_investor": "Sequoia Capital"}',
            '[{"name": "Strong Team", "factor": "1.05", "reason": "Experienced founding team with prior exits"}, {"name": "Market Position", "factor": "1.03", "reason": "Leading position in emerging AI vertical"}]'
        )
    """)

    # TechStart Inc - Seed stage fintech
    op.execute("""
        INSERT INTO portfolio_companies (name, sector_id, stage, founded_date, financials, last_round, adjustments)
        VALUES (
            'TechStart Inc',
            'fintech',
            'seed',
            '2024-01-10',
            '{"revenue_ttm": null, "revenue_growth_yoy": null, "gross_margin": null, "burn_rate": "150000", "runway_months": 14}',
            '{"date": "2025-06-01", "valuation_pre": "8000000", "valuation_post": "10000000", "amount_raised": "2000000", "lead_investor": "Y Combinator"}',
            '[]'
        )
    """)

    # GrowthCo Analytics - Series B SaaS
    op.execute("""
        INSERT INTO portfolio_companies (name, sector_id, stage, founded_date, financials, last_round, adjustments)
        VALUES (
            'GrowthCo Analytics',
            'saas',
            'series_b',
            '2019-08-20',
            '{"revenue_ttm": "25000000", "revenue_growth_yoy": "0.65", "gross_margin": "0.82", "burn_rate": "800000", "runway_months": 24}',
            '{"date": "2024-06-15", "valuation_pre": "100000000", "valuation_post": "125000000", "amount_raised": "25000000", "lead_investor": "Andreessen Horowitz"}',
            '[{"name": "Enterprise Traction", "factor": "1.08", "reason": "Signed 3 Fortune 500 contracts in last quarter"}]'
        )
    """)

    # Legacy Tech - Series A with old round
    op.execute("""
        INSERT INTO portfolio_companies (name, sector_id, stage, founded_date, financials, last_round, adjustments)
        VALUES (
            'Legacy Tech',
            'saas',
            'series_a',
            '2020-02-01',
            '{"revenue_ttm": "5000000", "revenue_growth_yoy": "0.35", "gross_margin": "0.70", "burn_rate": "300000", "runway_months": 12}',
            '{"date": "2023-01-15", "valuation_pre": "20000000", "valuation_post": "25000000", "amount_raised": "5000000", "lead_investor": "First Round Capital"}',
            '[{"name": "Slower Growth", "factor": "0.95", "reason": "Growth has decelerated below sector average"}]'
        )
    """)

    # Stealth Labs - Pre-revenue with no funding round
    op.execute("""
        INSERT INTO portfolio_companies (name, sector_id, stage, founded_date, financials, last_round, adjustments)
        VALUES (
            'Stealth Labs',
            'saas',
            'seed',
            '2025-09-01',
            '{"revenue_ttm": null, "revenue_growth_yoy": null, "gross_margin": null, "burn_rate": "50000", "runway_months": 8}',
            NULL,
            '[]'
        )
    """)


def downgrade() -> None:
    # Remove seeded portfolio companies
    op.execute("""
        DELETE FROM portfolio_companies
        WHERE name IN ('Basis AI', 'TechStart Inc', 'GrowthCo Analytics', 'Legacy Tech', 'Stealth Labs')
    """)
