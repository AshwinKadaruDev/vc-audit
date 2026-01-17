"""Valuation ORM model."""

from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TimestampMixin


class Valuation(Base, IdMixin, TimestampMixin):
    """A valuation result with full audit trail.

    This is the core output of the system - a complete record
    of a valuation including inputs, methodology, calculations,
    and results for audit purposes.
    """

    __tablename__ = "valuations"

    portfolio_company_id: Mapped[UUID] = mapped_column(
        ForeignKey("portfolio_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=2), nullable=False
    )
    primary_method: Mapped[str] = mapped_column(
        ENUM("last_round", "comparables", name="valuation_method", create_type=False),
        nullable=False
    )
    value_range_low: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=2), nullable=True
    )
    value_range_high: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=20, scale=2), nullable=True
    )
    overall_confidence: Mapped[str] = mapped_column(
        ENUM("high", "medium", "low", name="confidence_level", create_type=False),
        nullable=False
    )
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    method_results: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False
    )
    skipped_methods: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_valuations_portfolio_company_id", "portfolio_company_id"),
        Index("ix_valuations_input_hash", "input_hash"),
        Index("ix_valuations_created_at", "created_at"),
    )
