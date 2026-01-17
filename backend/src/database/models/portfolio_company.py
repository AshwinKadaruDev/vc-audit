"""Portfolio company ORM model."""

from datetime import date
from typing import Any, Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TimestampMixin


class PortfolioCompany(Base, IdMixin, TimestampMixin):
    """A private portfolio company to be valued.

    This represents user-created company data. The nested structures
    (financials, last_round, adjustments) are stored as JSONB in the
    database for flexibility - see TRADEOFFS.md #7.
    """

    __tablename__ = "portfolio_companies"

    name: Mapped[str] = mapped_column(String, nullable=False)
    sector_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("sectors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        ENUM("seed", "series_a", "series_b", "series_c", "growth", name="company_stage", create_type=False),
        nullable=False
    )
    founded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    financials: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    last_round: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    adjustments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
