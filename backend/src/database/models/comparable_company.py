"""Comparable company ORM model."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ComparableCompany(Base):
    """Public company used as a comparable for valuation.

    These are the public companies we compare against when using
    the Comparable Company Analysis (Comps) valuation method.
    """

    __tablename__ = "comparable_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sector_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("sectors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revenue_ttm: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=2), nullable=True
    )
    market_cap: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=2), nullable=True
    )
    ev_revenue_multiple: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    revenue_growth_yoy: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=4), nullable=True
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_name: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default="Yahoo Finance API"
    )
    source_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
