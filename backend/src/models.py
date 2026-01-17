"""Domain models for VC Audit Tool."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from typing_extensions import Self

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Enums
# ============================================================================

class CompanyStage(str, Enum):
    """Company funding stage."""
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    GROWTH = "growth"


class MethodName(str, Enum):
    """Available valuation methods."""
    LAST_ROUND = "last_round"
    COMPARABLES = "comparables"


class Confidence(str, Enum):
    """Confidence level in valuation result."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Company Models
# ============================================================================

class Company(BaseModel):
    """Basic company information."""
    id: str
    name: str
    sector: str
    stage: CompanyStage
    founded_date: Optional[date] = None


class Financials(BaseModel):
    """Company financial metrics."""
    revenue_ttm: Optional[Decimal] = Field(
        default=None,
        description="Trailing twelve months revenue"
    )
    revenue_growth_yoy: Optional[Decimal] = Field(
        default=None,
        description="Year-over-year revenue growth rate"
    )
    gross_margin: Optional[Decimal] = None
    burn_rate: Optional[Decimal] = None
    runway_months: Optional[int] = None

    @field_validator("revenue_ttm", "burn_rate")
    @classmethod
    def validate_positive(cls, v: Decimal | None) -> Decimal | None:
        """Validate that revenue_ttm and burn_rate are positive."""
        if v is not None and v < 0:
            raise ValueError("Must be positive")
        return v

    @field_validator("gross_margin")
    @classmethod
    def validate_margin(cls, v: Decimal | None) -> Decimal | None:
        """Validate that gross_margin is between 0 and 1."""
        if v is not None and not (0 <= v <= 1):
            raise ValueError("Gross margin must be between 0 and 1")
        return v


class LastRound(BaseModel):
    """Last funding round details."""
    date: date
    valuation_pre: Decimal = Field(description="Pre-money valuation")
    valuation_post: Decimal = Field(description="Post-money valuation")
    amount_raised: Decimal
    lead_investor: Optional[str] = None

    @field_validator("valuation_pre", "valuation_post", "amount_raised")
    @classmethod
    def validate_positive(cls, v: Decimal) -> Decimal:
        """Validate that valuations and amount raised are positive."""
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        """Validate that funding round date is not in the future."""
        from datetime import date as date_cls
        if v > date_cls.today():
            raise ValueError("Funding round date cannot be in the future")
        return v

    @model_validator(mode="after")
    def validate_post_money(self) -> Self:
        """Validate that post-money equals pre-money plus amount raised."""
        expected_post = self.valuation_pre + self.amount_raised
        if abs(self.valuation_post - expected_post) > Decimal("0.01"):
            raise ValueError("Post-money must equal pre-money + amount raised")
        return self


class Adjustment(BaseModel):
    """Company-specific valuation adjustment."""
    name: str
    factor: Decimal = Field(description="Multiplier (1.0 = no change)")
    reason: str

    @field_validator("factor")
    @classmethod
    def validate_factor(cls, v: Decimal) -> Decimal:
        """Validate that adjustment factor is positive and reasonable."""
        if v <= 0:
            raise ValueError("Adjustment factor must be positive")
        if v > 10:
            raise ValueError("Adjustment factor seems unreasonably high (>10x)")
        return v


class CompanyData(BaseModel):
    """Complete company data for valuation."""
    company: Company
    financials: Financials
    last_round: Optional[LastRound] = None
    adjustments: list[Adjustment] = Field(default_factory=list)


# ============================================================================
# Market Models
# ============================================================================

class MarketIndex(BaseModel):
    """Market index data point."""
    date: date
    value: Decimal
    name: str


class ComparableCompany(BaseModel):
    """Public comparable company data."""
    ticker: str
    name: str
    sector: str
    revenue_ttm: Decimal
    market_cap: Decimal
    ev_revenue_multiple: Decimal
    revenue_growth_yoy: Optional[Decimal] = None


class ComparableSet(BaseModel):
    """Set of comparable companies for a sector."""
    sector: str
    as_of_date: date
    companies: list[ComparableCompany]


# ============================================================================
# Result Models
# ============================================================================

class AuditStep(BaseModel):
    """Single step in the audit trail."""
    step_number: int
    description: str
    inputs: dict = Field(default_factory=dict)
    calculation: Optional[str] = None
    result: Optional[str] = None


class MethodResult(BaseModel):
    """Result from a single valuation method."""
    method: MethodName
    value: Decimal
    confidence: Confidence
    audit_trail: list[AuditStep]
    warnings: list[str] = Field(default_factory=list)


class MethodSkipped(BaseModel):
    """Record of a skipped valuation method."""
    method: MethodName
    reason: str


class MethodComparisonItem(BaseModel):
    """Single method in the comparison summary."""
    method: MethodName
    value: Decimal
    confidence: Confidence
    is_primary: bool = False


class MethodComparisonData(BaseModel):
    """Structured comparison data for all methods."""
    methods: list[MethodComparisonItem]
    spread_percent: Optional[Decimal] = Field(
        default=None,
        description="Percentage spread between highest and lowest values"
    )
    spread_warning: Optional[str] = Field(
        default=None,
        description="Warning message if spread is significant"
    )
    selection_steps: list[str] = Field(
        default_factory=list,
        description="Steps explaining how primary method was selected"
    )


class ValuationSummary(BaseModel):
    """Executive summary of valuation."""
    primary_value: Decimal
    primary_method: MethodName
    value_range_low: Optional[Decimal] = None
    value_range_high: Optional[Decimal] = None
    overall_confidence: Confidence
    summary_text: str
    selection_reason: str = Field(
        default="",
        description="Plain-language explanation of why the primary method was chosen"
    )
    method_comparison: Optional[MethodComparisonData] = Field(
        default=None,
        description="Structured comparison of all methods"
    )


class ValuationResult(BaseModel):
    """Complete valuation result with full audit trail."""
    company_id: str
    company_name: str
    valuation_date: date
    summary: ValuationSummary
    method_results: list[MethodResult]
    skipped_methods: list[MethodSkipped] = Field(default_factory=list)
    cross_method_analysis: Optional[str] = None
    config_snapshot: dict = Field(description="Configuration used for this valuation")
