"""API request and response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
    """Request to value a single company."""

    company_id: str = Field(description="Company identifier")


class BatchValuationRequest(BaseModel):
    """Request to value multiple companies."""

    company_ids: list[str] = Field(description="List of company identifiers")


class CompanyListItem(BaseModel):
    """Company item for list response."""

    id: str
    name: str
    sector: str
    stage: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    """Error response schema."""

    error_type: str
    message: str
    details: Optional[dict] = None


# New schemas for saved valuations

class ValuationListItem(BaseModel):
    """Lightweight valuation item for list views."""

    id: UUID
    company_name: str
    primary_value: Decimal
    primary_method: str
    overall_confidence: str
    valuation_date: date
    created_at: datetime


class ValuationDetail(BaseModel):
    """Full valuation detail with audit trail."""

    id: UUID
    portfolio_company_id: UUID
    company_name: str
    input_snapshot: dict[str, Any]
    primary_value: Decimal
    primary_method: str
    value_range_low: Optional[Decimal]
    value_range_high: Optional[Decimal]
    overall_confidence: str
    summary: dict[str, Any]
    method_results: list[dict[str, Any]]
    skipped_methods: list[dict[str, Any]]
    config_snapshot: dict[str, Any]
    valuation_date: date
    created_at: datetime


class PortfolioCompanyResponse(BaseModel):
    """Portfolio company response."""

    id: UUID
    name: str
    sector_id: str
    stage: str
    founded_date: Optional[date]
    financials: dict[str, Any]
    last_round: Optional[dict[str, Any]]
    adjustments: list[dict[str, Any]]
    created_at: Optional[datetime]


class SavedValuationResponse(BaseModel):
    """Response for saved valuation with ID."""

    id: UUID
    company_id: str
    company_name: str
    valuation_date: date
    summary: dict[str, Any]
    method_results: list[dict[str, Any]]
    skipped_methods: list[dict[str, Any]]
    cross_method_analysis: Optional[str]
    config_snapshot: dict[str, Any]
