"""Add data source columns to comparable_companies and market_indices tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-01-22

Adds source tracking for audit trail citations:
- comparable_companies: source_name, source_url
- market_indices: source_name
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source columns to comparable_companies
    op.add_column(
        "comparable_companies",
        sa.Column(
            "source_name",
            sa.String(100),
            nullable=False,
            server_default="Yahoo Finance API",
        ),
    )
    op.add_column(
        "comparable_companies",
        sa.Column("source_url", sa.String(255), nullable=True),
    )

    # Add source column to market_indices
    op.add_column(
        "market_indices",
        sa.Column(
            "source_name",
            sa.String(100),
            nullable=False,
            server_default="Yahoo Finance API",
        ),
    )


def downgrade() -> None:
    # Remove source columns from market_indices
    op.drop_column("market_indices", "source_name")

    # Remove source columns from comparable_companies
    op.drop_column("comparable_companies", "source_url")
    op.drop_column("comparable_companies", "source_name")
