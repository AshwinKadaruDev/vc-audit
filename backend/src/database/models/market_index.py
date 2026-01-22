"""Market index ORM model."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MarketIndex(Base):
    """Market index time series data model.

    Used by the Last Round valuation method to adjust valuations
    based on public market performance.

    Composite primary key: (name, date) to store time series data.
    """

    __tablename__ = "market_indices"

    name: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=2), nullable=False)
    source_name: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default="Yahoo Finance API"
    )

    __table_args__ = (PrimaryKeyConstraint("name", "date"),)
