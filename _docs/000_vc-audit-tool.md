# Product Requirements Document: VC Portfolio Valuation Audit Tool

---

## 1. Overview

### 1.1 Purpose

Build a full-stack application that helps auditors estimate fair value of private portfolio companies with complete audit trails. The system supports multiple valuation methodologies, automatically selects applicable methods based on available data, and presents results through a clean web interface.

### 1.2 Core Principles

1. **Auditability first**: Every calculation step must be traceable and reproducible
2. **Graceful degradation**: Missing data disables specific methods, not the whole system
3. **Configuration over code**: Tunable parameters are externalized, not hardcoded
4. **Reproducibility**: Same inputs + same config = same outputs (results include input hash)
5. **Versioned methods**: Algorithm changes are tracked for historical audit compliance

### 1.3 Scope

**In scope:**
- Last Round Adjusted valuation method
- Comparable Company Analysis (revenue multiples)
- Method selection logic based on data availability
- Complete audit trail generation
- REST API with OpenAPI documentation
- React/TypeScript frontend for auditor workflow
- Batch valuation support
- Mock data system

**Out of scope (documented as extension points):**
- DCF method
- Real external API integrations
- User authentication
- Database persistence (using JSON files)
- Deployment infrastructure

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/TS)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Company     │  │ Valuation   │  │ Audit Trail             │  │
│  │ Selector    │  │ Results     │  │ Viewer                  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ API Routes  │  │ Valuation   │  │ Data                    │  │
│  │             │──│ Engine      │──│ Loader                  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                          │                     │                 │
│                          ▼                     ▼                 │
│                   ┌─────────────┐       ┌─────────────┐         │
│                   │ Methods     │       │ JSON Files  │         │
│                   │ Registry    │       │ (Mock DB)   │         │
│                   └─────────────┘       └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
vc-audit-tool/
├── README.md
├── docker-compose.yml          # Optional: run both services
│
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # ValuationConfig + Settings
│   │   ├── models.py           # All Pydantic models
│   │   ├── exceptions.py       # Custom exceptions
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py       # API endpoints
│   │   │   └── schemas.py      # Request/Response schemas
│   │   │
│   │   ├── valuation/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Abstract base + registry
│   │   │   ├── engine.py       # ValuationEngine (selector + executor)
│   │   │   ├── last_round.py   # Last Round Adjusted
│   │   │   └── comps.py        # Comparable Company Analysis
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── math_utils.py
│   │       └── hashing.py      # Input hashing for reproducibility
│   │
│   ├── data/                   # Mock database (JSON files)
│   │   ├── companies/
│   │   │   ├── basis_ai.json
│   │   │   ├── techstart.json
│   │   │   ├── growthco.json
│   │   │   └── prerevenue_co.json
│   │   │
│   │   ├── market/
│   │   │   └── indices.json
│   │   │
│   │   └── comparables/
│   │       ├── saas.json
│   │       └── fintech.json
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_loader.py
│       ├── test_methods.py
│       └── test_engine.py
│
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    │
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   │
    │   ├── api/
    │   │   └── client.ts       # API client with types
    │   │
    │   ├── types/
    │   │   └── index.ts        # TypeScript types (mirror backend)
    │   │
    │   ├── components/
    │   │   ├── CompanySelector.tsx
    │   │   ├── ValuationCard.tsx
    │   │   ├── AuditTrail.tsx
    │   │   ├── MethodBadge.tsx
    │   │   └── ErrorBoundary.tsx
    │   │
    │   ├── pages/
    │   │   ├── HomePage.tsx
    │   │   └── ValuationPage.tsx
    │   │
    │   └── hooks/
    │       └── useValuation.ts
    │
    └── public/
```

---

## 3. Configuration System

### 3.1 Valuation Configuration

All tunable parameters are centralized in a configuration object. This allows:
- Easy adjustment without code changes
- Configuration snapshots in results for audit
- Environment-specific overrides

```python
# backend/src/config.py

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from decimal import Decimal
from typing import Optional
from functools import lru_cache


class ValuationConfig(BaseModel):
    """
    All tunable valuation parameters.
    Stored with each result for reproducibility.
    """
    
    # Last Round Method
    max_round_age_months: int = Field(
        default=24,
        description="Maximum age of last round to be considered valid"
    )
    stale_round_warning_months: int = Field(
        default=18,
        description="Age at which to warn about stale round data"
    )
    
    # Comps Method
    min_comparables: int = Field(
        default=3,
        description="Minimum comparable companies required"
    )
    illiquidity_discount: Decimal = Field(
        default=Decimal("-0.15"),
        description="Discount applied for private company illiquidity (as decimal, e.g., -0.15 = -15%)"
    )
    
    # General
    default_index: str = Field(
        default="NASDAQ",
        description="Default market index for adjustments"
    )
    
    class Config:
        frozen = True  # Immutable once created


class Settings(BaseSettings):
    """
    Application settings from environment.
    """
    
    app_name: str = "VC Audit Tool"
    debug: bool = False
    data_dir: str = "data"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## 4. Data Models

### 4.1 Core Domain Models

```python
# backend/src/models.py

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, Literal
from datetime import date
from decimal import Decimal
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class CompanyStage(str, Enum):
    PRE_SEED = "Pre-Seed"
    SEED = "Seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    GROWTH = "Growth"
    LATE = "Late"


class MethodName(str, Enum):
    LAST_ROUND_ADJUSTED = "last_round_adjusted"
    COMPS_REVENUE = "comps_revenue"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# COMPANY DATA
# =============================================================================

class Company(BaseModel):
    """Basic company identification."""
    
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    sector: str = Field(..., description="Must match a comparables file if using comps method")
    stage: CompanyStage
    description: Optional[str] = None
    
    class Config:
        frozen = True


class Financials(BaseModel):
    """Company financial metrics."""
    
    as_of_date: date
    ltm_revenue: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Last twelve months revenue in USD. Null if pre-revenue."
    )
    revenue_growth_yoy: Optional[Decimal] = Field(
        default=None,
        ge=-1,
        le=10,
        description="Year-over-year growth as decimal (0.5 = 50%)"
    )
    
    @field_validator('ltm_revenue', mode='before')
    @classmethod
    def coerce_revenue(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class LastRound(BaseModel):
    """Most recent funding round."""
    
    round_type: str = Field(..., description="e.g., 'Series A', 'Seed'")
    date: date
    post_money_valuation: Decimal = Field(..., gt=0)
    lead_investor: Optional[str] = None
    
    @field_validator('post_money_valuation', mode='before')
    @classmethod
    def coerce_valuation(cls, v):
        return Decimal(str(v))


class Adjustment(BaseModel):
    """
    A manual adjustment to valuation.
    
    Simplified from complex event types - auditor specifies the adjustment directly.
    This is more flexible and auditable than inferring adjustments from event categories.
    """
    
    date: date
    description: str = Field(..., min_length=1, description="What happened")
    percent: Decimal = Field(
        ...,
        ge=Decimal("-0.50"),
        le=Decimal("0.50"),
        description="Adjustment as decimal (-0.10 = -10%, 0.05 = +5%)"
    )
    
    @field_validator('percent', mode='before')
    @classmethod
    def coerce_percent(cls, v):
        return Decimal(str(v))


class CompanyData(BaseModel):
    """Complete portfolio company data bundle."""
    
    company: Company
    financials: Financials
    last_round: Optional[LastRound] = None
    adjustments: list[Adjustment] = Field(default_factory=list)
    
    @computed_field
    @property
    def has_revenue(self) -> bool:
        return self.financials.ltm_revenue is not None and self.financials.ltm_revenue > 0
    
    @computed_field
    @property
    def has_last_round(self) -> bool:
        return self.last_round is not None


# =============================================================================
# MARKET DATA
# =============================================================================

class IndexValue(BaseModel):
    """Single index data point."""
    date: date
    value: Decimal


class MarketIndex(BaseModel):
    """Market index with historical values."""
    
    name: str
    values: dict[str, Decimal] = Field(
        ...,
        description="ISO date string -> value mapping"
    )
    
    def get_value_at(self, target_date: date) -> Optional[Decimal]:
        """Get value at or nearest before target date."""
        target_str = target_date.isoformat()
        
        if target_str in self.values:
            return self.values[target_str]
        
        # Find nearest date before target
        valid_dates = [d for d in self.values.keys() if d <= target_str]
        if not valid_dates:
            return None
        
        nearest = max(valid_dates)
        return self.values[nearest]
    
    def get_percent_change(self, from_date: date, to_date: date) -> Optional[Decimal]:
        """Calculate percentage change between two dates."""
        from_val = self.get_value_at(from_date)
        to_val = self.get_value_at(to_date)
        
        if from_val is None or to_val is None or from_val == 0:
            return None
        
        return (to_val - from_val) / from_val


class ComparableCompany(BaseModel):
    """A public company used as a comparable."""
    
    ticker: str
    name: str
    enterprise_value: Decimal = Field(..., gt=0)
    ltm_revenue: Decimal = Field(..., gt=0)
    revenue_growth: Optional[Decimal] = None
    
    @computed_field
    @property
    def ev_revenue_multiple(self) -> Decimal:
        return self.enterprise_value / self.ltm_revenue


class ComparableSet(BaseModel):
    """Collection of comparable companies for a sector."""
    
    sector: str
    as_of_date: date
    source: str = Field(default="Mock Data", description="Data source for citation")
    companies: list[ComparableCompany] = Field(..., min_length=1)
    
    def get_multiples(self) -> list[Decimal]:
        return [c.ev_revenue_multiple for c in self.companies]


# =============================================================================
# VALUATION RESULTS
# =============================================================================

class AuditStep(BaseModel):
    """
    Single step in the audit trail.
    
    Designed to be human-readable and machine-parseable.
    """
    
    step: int
    name: str
    description: str
    inputs: dict = Field(default_factory=dict)
    calculation: Optional[str] = None  # Formula shown to auditor
    result: dict = Field(default_factory=dict)


class MethodResult(BaseModel):
    """Result from a single valuation method."""
    
    method: MethodName
    method_version: str = Field(..., description="Algorithm version for audit tracking")
    fair_value: Decimal
    confidence: Confidence
    
    value_low: Optional[Decimal] = None
    value_high: Optional[Decimal] = None
    
    audit_trail: list[AuditStep] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class MethodSkipped(BaseModel):
    """Record of why a method was not executed."""
    
    method: MethodName
    reason: str
    missing_data: list[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ValuationSummary(BaseModel):
    """Executive summary for the valuation."""
    
    primary_estimate: Decimal
    estimate_low: Decimal
    estimate_high: Decimal
    confidence: Confidence
    primary_method: str
    methods_used: list[str]
    key_assumptions: list[str]


class ValuationResult(BaseModel):
    """Complete valuation output with full audit trail."""
    
    # Identification
    id: str = Field(..., description="Unique result ID")
    company_id: str
    company_name: str
    valuation_date: date
    generated_at: str  # ISO timestamp
    
    # Reproducibility
    input_hash: str = Field(
        ...,
        description="SHA256 of inputs - same hash = same inputs"
    )
    config_snapshot: dict = Field(
        ...,
        description="Exact configuration used for this valuation"
    )
    
    # Results
    summary: ValuationSummary
    method_results: list[MethodResult] = Field(default_factory=list)
    methods_skipped: list[MethodSkipped] = Field(default_factory=list)
    
    # Cross-method comparison (when multiple methods run)
    method_comparison: Optional[dict] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat(),
        }
```

---

## 5. Mock Database Schema

### 5.1 Company Files

Each company is a separate JSON file in `data/companies/`.

**`data/companies/basis_ai.json`** - Standard case with revenue and recent round:
```json
{
  "company": {
    "id": "basis_ai",
    "name": "Basis AI",
    "sector": "saas",
    "stage": "Series A",
    "description": "AI-powered analytics platform for enterprise"
  },
  "financials": {
    "as_of_date": "2024-12-15",
    "ltm_revenue": 10000000,
    "revenue_growth_yoy": 0.50
  },
  "last_round": {
    "round_type": "Series A",
    "date": "2024-03-15",
    "post_money_valuation": 50000000,
    "lead_investor": "Sequoia Capital"
  },
  "adjustments": [
    {
      "date": "2024-09-01",
      "description": "Lost major customer TechCorp ($500K ARR churned)",
      "percent": -0.08
    },
    {
      "date": "2024-11-01",
      "description": "Hired VP Sales from Salesforce",
      "percent": 0.03
    }
  ]
}
```

**`data/companies/techstart.json`** - Pre-revenue company (only Last Round method applies):
```json
{
  "company": {
    "id": "techstart",
    "name": "TechStart",
    "sector": "saas",
    "stage": "Seed",
    "description": "Early-stage developer tools startup"
  },
  "financials": {
    "as_of_date": "2024-12-01",
    "ltm_revenue": null,
    "revenue_growth_yoy": null
  },
  "last_round": {
    "round_type": "Seed",
    "date": "2024-06-01",
    "post_money_valuation": 8000000,
    "lead_investor": "Y Combinator"
  },
  "adjustments": []
}
```

**`data/companies/growthco.json`** - High growth company with stale round:
```json
{
  "company": {
    "id": "growthco",
    "name": "GrowthCo",
    "sector": "fintech",
    "stage": "Series B",
    "description": "B2B payments infrastructure"
  },
  "financials": {
    "as_of_date": "2024-12-15",
    "ltm_revenue": 25000000,
    "revenue_growth_yoy": 0.80
  },
  "last_round": {
    "round_type": "Series B",
    "date": "2023-06-15",
    "post_money_valuation": 120000000,
    "lead_investor": "Andreessen Horowitz"
  },
  "adjustments": [
    {
      "date": "2024-03-01",
      "description": "Launched payment processing product - exceeded targets",
      "percent": 0.12
    }
  ]
}
```

**`data/companies/prerevenue_no_round.json`** - Edge case: no methods can run:
```json
{
  "company": {
    "id": "prerevenue_no_round",
    "name": "Stealth Startup",
    "sector": "saas",
    "stage": "Pre-Seed",
    "description": "Pre-product stealth startup"
  },
  "financials": {
    "as_of_date": "2024-12-01",
    "ltm_revenue": null,
    "revenue_growth_yoy": null
  },
  "last_round": null,
  "adjustments": []
}
```

**`data/companies/old_round.json`** - Edge case: round too old:
```json
{
  "company": {
    "id": "old_round",
    "name": "Stale Data Corp",
    "sector": "saas",
    "stage": "Series A",
    "description": "Company with outdated round data"
  },
  "financials": {
    "as_of_date": "2024-12-15",
    "ltm_revenue": 5000000,
    "revenue_growth_yoy": 0.20
  },
  "last_round": {
    "round_type": "Series A",
    "date": "2022-01-15",
    "post_money_valuation": 30000000,
    "lead_investor": "First Round Capital"
  },
  "adjustments": []
}
```

### 5.2 Market Index File

**`data/market/indices.json`**:
```json
{
  "NASDAQ": {
    "2022-01-15": 14500,
    "2022-06-15": 11100,
    "2022-12-15": 10500,
    "2023-01-15": 11500,
    "2023-03-15": 11800,
    "2023-06-15": 13500,
    "2023-09-15": 13200,
    "2023-12-15": 14800,
    "2024-01-15": 15000,
    "2024-03-15": 16000,
    "2024-06-15": 17200,
    "2024-09-15": 17000,
    "2024-12-15": 17400,
    "2025-01-15": 17600
  },
  "SP500": {
    "2022-01-15": 4650,
    "2022-06-15": 3750,
    "2022-12-15": 3850,
    "2023-01-15": 3900,
    "2023-03-15": 4050,
    "2023-06-15": 4400,
    "2023-09-15": 4300,
    "2023-12-15": 4750,
    "2024-01-15": 4850,
    "2024-03-15": 5100,
    "2024-06-15": 5450,
    "2024-09-15": 5400,
    "2024-12-15": 5550,
    "2025-01-15": 5600
  }
}
```

### 5.3 Comparable Company Files

Each sector has a separate file in `data/comparables/`.

**`data/comparables/saas.json`**:
```json
{
  "sector": "saas",
  "sector_display_name": "SaaS / Software",
  "as_of_date": "2025-01-15",
  "source": "Public market data (mocked for demonstration)",
  "companies": [
    {
      "ticker": "DDOG",
      "name": "Datadog",
      "enterprise_value": 39800000000,
      "ltm_revenue": 2100000000,
      "revenue_growth": 0.25
    },
    {
      "ticker": "SNOW",
      "name": "Snowflake",
      "enterprise_value": 52000000000,
      "ltm_revenue": 2800000000,
      "revenue_growth": 0.30
    },
    {
      "ticker": "MDB",
      "name": "MongoDB",
      "enterprise_value": 17500000000,
      "ltm_revenue": 1700000000,
      "revenue_growth": 0.20
    },
    {
      "ticker": "ESTC",
      "name": "Elastic",
      "enterprise_value": 8200000000,
      "ltm_revenue": 1200000000,
      "revenue_growth": 0.15
    },
    {
      "ticker": "DT",
      "name": "Dynatrace",
      "enterprise_value": 14000000000,
      "ltm_revenue": 1450000000,
      "revenue_growth": 0.18
    }
  ]
}
```

**`data/comparables/fintech.json`**:
```json
{
  "sector": "fintech",
  "sector_display_name": "Fintech / Payments",
  "as_of_date": "2025-01-15",
  "source": "Public market data (mocked for demonstration)",
  "companies": [
    {
      "ticker": "SQ",
      "name": "Block (Square)",
      "enterprise_value": 45000000000,
      "ltm_revenue": 21500000000,
      "revenue_growth": 0.12
    },
    {
      "ticker": "AFRM",
      "name": "Affirm",
      "enterprise_value": 15000000000,
      "ltm_revenue": 2300000000,
      "revenue_growth": 0.35
    },
    {
      "ticker": "BILL",
      "name": "Bill.com",
      "enterprise_value": 8000000000,
      "ltm_revenue": 1250000000,
      "revenue_growth": 0.22
    },
    {
      "ticker": "TOST",
      "name": "Toast",
      "enterprise_value": 14500000000,
      "ltm_revenue": 4200000000,
      "revenue_growth": 0.28
    }
  ]
}
```

---

## 6. Custom Exceptions

```python
# backend/src/exceptions.py

from typing import Optional


class ValuationError(Exception):
    """Base exception for all valuation errors."""
    
    def __init__(self, message: str, code: str, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


class DataNotFoundError(ValuationError):
    """Requested data does not exist."""
    
    def __init__(self, entity: str, identifier: str):
        super().__init__(
            message=f"{entity} not found: {identifier}",
            code="DATA_NOT_FOUND",
            details={"entity": entity, "identifier": identifier}
        )


class DataValidationError(ValuationError):
    """Data failed validation."""
    
    def __init__(self, entity: str, errors: list):
        super().__init__(
            message=f"Validation failed for {entity}",
            code="VALIDATION_ERROR",
            details={"entity": entity, "errors": errors}
        )


class DataLoadError(ValuationError):
    """Failed to load data from source."""
    
    def __init__(self, source: str, reason: str):
        super().__init__(
            message=f"Failed to load {source}: {reason}",
            code="DATA_LOAD_ERROR",
            details={"source": source, "reason": reason}
        )


class InsufficientDataError(ValuationError):
    """Not enough data to perform valuation."""
    
    def __init__(self, method: str, missing: list[str]):
        super().__init__(
            message=f"Cannot run {method}: missing {', '.join(missing)}",
            code="INSUFFICIENT_DATA",
            details={"method": method, "missing_fields": missing}
        )


class NoValidMethodsError(ValuationError):
    """No valuation methods could be executed."""
    
    def __init__(self, skip_reasons: dict[str, str]):
        super().__init__(
            message="No valuation methods could be executed with available data",
            code="NO_VALID_METHODS",
            details={"method_skip_reasons": skip_reasons}
        )


class CalculationError(ValuationError):
    """Error during calculation."""
    
    def __init__(self, method: str, step: str, reason: str):
        super().__init__(
            message=f"Calculation error in {method} at '{step}': {reason}",
            code="CALCULATION_ERROR",
            details={"method": method, "step": step, "reason": reason}
        )
```

---

## 7. Data Loading Layer

```python
# backend/src/database/loader.py

import json
from pathlib import Path
from decimal import Decimal
from datetime import date
from typing import Optional

from src.models import (
    CompanyData, Company, Financials, LastRound, Adjustment,
    MarketIndex, ComparableSet, ComparableCompany
)
from src.exceptions import DataNotFoundError, DataLoadError, DataValidationError
from pydantic import ValidationError


class DataLoader:
    """
    Loads and validates data from JSON files.
    
    In production, this would be swapped for database/API clients.
    The interface (method signatures) would remain the same.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._validate_structure()
        
        # Caches
        self._indices_cache: Optional[dict[str, MarketIndex]] = None
        self._comparables_cache: dict[str, ComparableSet] = {}
    
    def _validate_structure(self) -> None:
        """Verify required directories exist."""
        required = ["companies", "market", "comparables"]
        for name in required:
            path = self.data_dir / name
            if not path.exists():
                raise DataLoadError(
                    source="data_directory",
                    reason=f"Required directory '{name}' not found at {path}"
                )
    
    def _read_json(self, path: Path) -> dict:
        """Read and parse JSON file with error handling."""
        if not path.exists():
            raise DataNotFoundError(entity="file", identifier=str(path))
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataLoadError(source=str(path), reason=f"Invalid JSON: {e}")
    
    # -------------------------------------------------------------------------
    # Company Data
    # -------------------------------------------------------------------------
    
    def list_companies(self) -> list[dict]:
        """
        List all available companies with basic info.
        Returns list of {id, name, sector, stage} for UI display.
        """
        companies = []
        company_dir = self.data_dir / "companies"
        
        for path in company_dir.glob("*.json"):
            try:
                data = self._read_json(path)
                companies.append({
                    "id": data["company"]["id"],
                    "name": data["company"]["name"],
                    "sector": data["company"]["sector"],
                    "stage": data["company"]["stage"]
                })
            except Exception:
                # Skip malformed files in listing
                continue
        
        return sorted(companies, key=lambda x: x["name"])
    
    def load_company(self, company_id: str) -> CompanyData:
        """
        Load complete company data by ID.
        
        Args:
            company_id: Unique identifier (matches filename without .json)
        
        Returns:
            Validated CompanyData object
        
        Raises:
            DataNotFoundError: Company file doesn't exist
            DataValidationError: Data fails schema validation
        """
        path = self.data_dir / "companies" / f"{company_id}.json"
        raw = self._read_json(path)
        
        try:
            company = Company(**raw["company"])
            financials = Financials(**raw["financials"])
            
            last_round = None
            if raw.get("last_round"):
                last_round = LastRound(**raw["last_round"])
            
            adjustments = [
                Adjustment(**adj) for adj in raw.get("adjustments", [])
            ]
            
            return CompanyData(
                company=company,
                financials=financials,
                last_round=last_round,
                adjustments=adjustments
            )
        
        except ValidationError as e:
            raise DataValidationError(
                entity=f"company:{company_id}",
                errors=e.errors()
            )
    
    # -------------------------------------------------------------------------
    # Market Data
    # -------------------------------------------------------------------------
    
    def load_indices(self) -> dict[str, MarketIndex]:
        """Load all market indices (cached)."""
        if self._indices_cache is not None:
            return self._indices_cache
        
        path = self.data_dir / "market" / "indices.json"
        raw = self._read_json(path)
        
        indices = {}
        for name, values in raw.items():
            # Convert to Decimal for precision
            decimal_values = {k: Decimal(str(v)) for k, v in values.items()}
            indices[name] = MarketIndex(name=name, values=decimal_values)
        
        self._indices_cache = indices
        return indices
    
    def get_index(self, name: str) -> MarketIndex:
        """Get specific market index by name."""
        indices = self.load_indices()
        
        if name not in indices:
            raise DataNotFoundError(
                entity="market_index",
                identifier=f"{name} (available: {list(indices.keys())})"
            )
        
        return indices[name]
    
    # -------------------------------------------------------------------------
    # Comparables
    # -------------------------------------------------------------------------
    
    def list_sectors(self) -> list[str]:
        """List available comparable sectors."""
        comp_dir = self.data_dir / "comparables"
        return [p.stem for p in comp_dir.glob("*.json")]
    
    def load_comparables(self, sector: str) -> ComparableSet:
        """
        Load comparable companies for a sector.
        
        Args:
            sector: Sector key (matches filename without .json)
        
        Returns:
            ComparableSet with all comparable companies
        
        Raises:
            DataNotFoundError: No comparables for sector
        """
        # Normalize sector key
        sector_key = sector.lower().replace(" ", "_").replace("/", "_")
        
        if sector_key in self._comparables_cache:
            return self._comparables_cache[sector_key]
        
        path = self.data_dir / "comparables" / f"{sector_key}.json"
        
        if not path.exists():
            available = self.list_sectors()
            raise DataNotFoundError(
                entity="comparables",
                identifier=f"{sector} (available: {available})"
            )
        
        raw = self._read_json(path)
        
        try:
            companies = [ComparableCompany(**c) for c in raw["companies"]]
            
            comp_set = ComparableSet(
                sector=raw["sector"],
                as_of_date=date.fromisoformat(raw["as_of_date"]),
                source=raw.get("source", "Unknown"),
                companies=companies
            )
            
            self._comparables_cache[sector_key] = comp_set
            return comp_set
        
        except ValidationError as e:
            raise DataValidationError(
                entity=f"comparables:{sector}",
                errors=e.errors()
            )
```

---

## 8. Valuation Methods

### 8.1 Base Class and Registry

```python
# backend/src/valuation/base.py

from abc import ABC, abstractmethod
from typing import Optional
from decimal import Decimal

from src.models import (
    MethodName, MethodResult, AuditStep, Confidence,
    CompanyData, MarketIndex, ComparableSet
)
from src.config import ValuationConfig


class ValuationMethod(ABC):
    """
    Abstract base class for all valuation methods.
    
    Each method must:
    1. Declare its name and version
    2. Implement prerequisite checking
    3. Implement the valuation calculation with audit trail
    """
    
    # Subclasses must override these
    name: MethodName
    version: str  # Semantic version, bump when algorithm changes
    display_name: str
    
    def __init__(self, config: ValuationConfig):
        self.config = config
        self._steps: list[AuditStep] = []
        self._warnings: list[str] = []
        self._step_counter: int = 0
    
    def _reset(self) -> None:
        """Reset state for a new valuation."""
        self._steps = []
        self._warnings = []
        self._step_counter = 0
    
    def _add_step(
        self,
        name: str,
        description: str,
        inputs: dict,
        result: dict,
        calculation: Optional[str] = None
    ) -> None:
        """Record an audit step."""
        self._step_counter += 1
        
        # Serialize Decimals for JSON
        def serialize(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [serialize(i) for i in obj]
            return obj
        
        self._steps.append(AuditStep(
            step=self._step_counter,
            name=name,
            description=description,
            inputs=serialize(inputs),
            calculation=calculation,
            result=serialize(result)
        ))
    
    def _warn(self, message: str) -> None:
        """Add a warning to the result."""
        self._warnings.append(message)
    
    @abstractmethod
    def check_prerequisites(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: Optional[ComparableSet],
        valuation_date
    ) -> tuple[bool, list[str]]:
        """
        Check if this method can run with available data.
        
        Returns:
            (can_run, list_of_missing_fields)
        """
        pass
    
    @abstractmethod
    def execute(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: Optional[ComparableSet],
        valuation_date
    ) -> MethodResult:
        """
        Execute the valuation and return result with audit trail.
        """
        pass


# -----------------------------------------------------------------------------
# Method Registry
# -----------------------------------------------------------------------------

class MethodRegistry:
    """
    Registry for valuation methods.
    
    Allows dynamic method registration and discovery.
    """
    
    _methods: dict[MethodName, type[ValuationMethod]] = {}
    
    @classmethod
    def register(cls, method_class: type[ValuationMethod]) -> type[ValuationMethod]:
        """Decorator to register a method class."""
        cls._methods[method_class.name] = method_class
        return method_class
    
    @classmethod
    def get_all(cls, config: ValuationConfig) -> list[ValuationMethod]:
        """Get instances of all registered methods."""
        return [method_cls(config) for method_cls in cls._methods.values()]
    
    @classmethod
    def get(cls, name: MethodName, config: ValuationConfig) -> ValuationMethod:
        """Get a specific method by name."""
        if name not in cls._methods:
            raise ValueError(f"Unknown method: {name}")
        return cls._methods[name](config)
```

### 8.2 Last Round Adjusted Method

```python
# backend/src/valuation/last_round.py

from typing import Optional
from decimal import Decimal
from datetime import date

from src.valuation.base import ValuationMethod, MethodRegistry
from src.models import (
    MethodName, MethodResult, Confidence,
    CompanyData, MarketIndex, ComparableSet
)
from src.exceptions import CalculationError


@MethodRegistry.register
class LastRoundAdjustedMethod(ValuationMethod):
    """
    Values a company by adjusting its last funding round valuation for:
    1. Public market movements (index change)
    2. Company-specific events (manual adjustments)
    
    Best for: Companies with recent funding rounds (< 24 months)
    """
    
    name = MethodName.LAST_ROUND_ADJUSTED
    version = "1.0.0"
    display_name = "Last Round Adjusted"
    
    def check_prerequisites(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: Optional[ComparableSet],
        valuation_date: date
    ) -> tuple[bool, list[str]]:
        """Check if last round data exists and is recent enough."""
        missing = []
        
        # Must have last round
        if not company.has_last_round:
            missing.append("last_round")
            return (False, missing)
        
        # Check round age
        round_date = company.last_round.date
        months_old = self._months_between(round_date, valuation_date)
        
        if months_old > self.config.max_round_age_months:
            missing.append(
                f"last_round (too old: {months_old} months, max: {self.config.max_round_age_months})"
            )
            return (False, missing)
        
        # Check index has data for date range
        if index.get_value_at(round_date) is None:
            missing.append(f"index_value_at_round_date ({round_date})")
        
        if index.get_value_at(valuation_date) is None:
            missing.append(f"index_value_at_valuation_date ({valuation_date})")
        
        return (len(missing) == 0, missing)
    
    def execute(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: Optional[ComparableSet],
        valuation_date: date
    ) -> MethodResult:
        """Execute Last Round Adjusted valuation."""
        self._reset()
        
        last_round = company.last_round
        anchor = last_round.post_money_valuation
        
        # Step 1: Establish anchor
        self._add_step(
            name="Establish Anchor Value",
            description="Start with post-money valuation from most recent funding round",
            inputs={
                "round_type": last_round.round_type,
                "round_date": last_round.date,
                "lead_investor": last_round.lead_investor,
                "post_money_valuation": anchor
            },
            result={"anchor_value": anchor}
        )
        
        # Check for stale round warning
        months_old = self._months_between(last_round.date, valuation_date)
        if months_old > self.config.stale_round_warning_months:
            self._warn(
                f"Last round is {months_old} months old. "
                f"Consider additional scrutiny or weight toward other methods."
            )
        
        # Step 2: Market adjustment
        index_at_round = index.get_value_at(last_round.date)
        index_now = index.get_value_at(valuation_date)
        
        if index_at_round is None or index_now is None or index_at_round == 0:
            raise CalculationError(
                method=self.display_name,
                step="market_adjustment",
                reason="Could not retrieve index values"
            )
        
        market_change = (index_now - index_at_round) / index_at_round
        market_adjusted = anchor * (1 + market_change)
        
        self._add_step(
            name="Apply Market Adjustment",
            description=f"Adjust for {index.name} index movement since funding round",
            inputs={
                "index_name": index.name,
                "index_at_round": index_at_round,
                "index_at_round_date": last_round.date,
                "index_current": index_now,
                "index_current_date": valuation_date
            },
            calculation=f"anchor × (1 + market_change) = {anchor:,.0f} × (1 + {float(market_change):.4f})",
            result={
                "market_change_percent": f"{float(market_change) * 100:+.2f}%",
                "value_after_market_adjustment": market_adjusted
            }
        )
        
        # Step 3: Company-specific adjustments
        current_value = market_adjusted
        
        if company.adjustments:
            adjustment_details = []
            
            for adj in company.adjustments:
                value_before = current_value
                current_value = current_value * (1 + adj.percent)
                
                adjustment_details.append({
                    "date": adj.date,
                    "description": adj.description,
                    "percent": f"{float(adj.percent) * 100:+.1f}%",
                    "value_before": value_before,
                    "value_after": current_value
                })
            
            self._add_step(
                name="Apply Company Adjustments",
                description="Adjust for company-specific events since funding round",
                inputs={"adjustment_count": len(company.adjustments)},
                calculation="value × (1 + adjustment_percent) for each event",
                result={
                    "adjustments": adjustment_details,
                    "final_value": current_value
                }
            )
        else:
            self._add_step(
                name="Company Adjustments",
                description="Check for company-specific events",
                inputs={},
                result={"note": "No adjustments recorded - value unchanged"}
            )
        
        # Determine confidence
        confidence = self._calculate_confidence(months_old)
        
        return MethodResult(
            method=self.name,
            method_version=self.version,
            fair_value=current_value,
            confidence=confidence,
            value_low=None,  # Point estimate only
            value_high=None,
            audit_trail=self._steps,
            warnings=self._warnings
        )
    
    def _months_between(self, from_date: date, to_date: date) -> int:
        """Calculate months between two dates."""
        return (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)
    
    def _calculate_confidence(self, round_age_months: int) -> Confidence:
        """Confidence decreases with round age."""
        if round_age_months <= 6:
            return Confidence.HIGH
        elif round_age_months <= 12:
            return Confidence.MEDIUM
        return Confidence.LOW
```

### 8.3 Comparable Company Method

```python
# backend/src/valuation/comps.py

from typing import Optional
from decimal import Decimal
from datetime import date

from src.valuation.base import ValuationMethod, MethodRegistry
from src.models import (
    MethodName, MethodResult, Confidence,
    CompanyData, MarketIndex, ComparableSet
)
from src.utils.math_utils import median, percentile


@MethodRegistry.register
class ComparableCompanyMethod(ValuationMethod):
    """
    Values a company by applying EV/Revenue multiples from
    comparable public companies.
    
    Best for: Companies with meaningful revenue and good public comps
    """
    
    name = MethodName.COMPS_REVENUE
    version = "1.0.0"
    display_name = "Comparable Company Analysis"
    
    def check_prerequisites(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: Optional[ComparableSet],
        valuation_date: date
    ) -> tuple[bool, list[str]]:
        """Check for revenue and sufficient comparables."""
        missing = []
        
        if not company.has_revenue:
            missing.append("ltm_revenue (company is pre-revenue)")
        
        if comparables is None:
            missing.append("comparable_companies")
        elif len(comparables.companies) < self.config.min_comparables:
            missing.append(
                f"comparable_companies (need {self.config.min_comparables}, "
                f"have {len(comparables.companies)})"
            )
        
        return (len(missing) == 0, missing)
    
    def execute(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: ComparableSet,
        valuation_date: date
    ) -> MethodResult:
        """Execute Comparable Company Analysis."""
        self._reset()
        
        target_revenue = company.financials.ltm_revenue
        
        # Step 1: Document target metrics
        self._add_step(
            name="Target Company Metrics",
            description="Extract financial metrics for the company being valued",
            inputs={
                "company": company.company.name,
                "ltm_revenue": target_revenue,
                "revenue_growth": company.financials.revenue_growth_yoy,
                "as_of_date": company.financials.as_of_date
            },
            result={"primary_metric": "LTM Revenue", "value": target_revenue}
        )
        
        # Step 2: Calculate comparable multiples
        comp_details = []
        for comp in comparables.companies:
            comp_details.append({
                "ticker": comp.ticker,
                "name": comp.name,
                "enterprise_value": comp.enterprise_value,
                "ltm_revenue": comp.ltm_revenue,
                "ev_revenue_multiple": comp.ev_revenue_multiple
            })
        
        self._add_step(
            name="Comparable Company Data",
            description=f"EV/Revenue multiples for {comparables.sector} sector",
            inputs={
                "sector": comparables.sector,
                "data_source": comparables.source,
                "as_of_date": comparables.as_of_date,
                "company_count": len(comparables.companies)
            },
            result={"comparables": comp_details}
        )
        
        # Step 3: Calculate statistics
        multiples = comparables.get_multiples()
        
        stats = {
            "min": float(min(multiples)),
            "percentile_25": float(percentile(multiples, 25)),
            "median": float(median(multiples)),
            "percentile_75": float(percentile(multiples, 75)),
            "max": float(max(multiples))
        }
        
        self._add_step(
            name="Multiple Statistics",
            description="Statistical summary of comparable multiples",
            inputs={"multiples": [float(m) for m in multiples]},
            result=stats
        )
        
        # Step 4: Select multiple and apply discount
        base_multiple = median(multiples)
        illiquidity_discount = self.config.illiquidity_discount
        
        # Apply discount as adjustment to multiple
        # e.g., 10x multiple with -15% discount = 10x × 0.85 = 8.5x
        adjusted_multiple = base_multiple * (1 + illiquidity_discount)
        adjusted_multiple = max(adjusted_multiple, Decimal("1.0"))  # Floor at 1x
        
        self._add_step(
            name="Select Valuation Multiple",
            description="Apply illiquidity discount to median multiple for private company",
            inputs={
                "base_multiple": base_multiple,
                "illiquidity_discount": f"{float(illiquidity_discount) * 100:.0f}%"
            },
            calculation=f"median × (1 + discount) = {base_multiple:.2f}x × {1 + float(illiquidity_discount):.2f}",
            result={"selected_multiple": adjusted_multiple}
        )
        
        # Step 5: Calculate fair value
        fair_value = target_revenue * adjusted_multiple
        
        # Calculate range using percentiles (also adjusted)
        p25_adj = percentile(multiples, 25) * (1 + illiquidity_discount)
        p75_adj = percentile(multiples, 75) * (1 + illiquidity_discount)
        
        value_low = target_revenue * max(p25_adj, Decimal("1.0"))
        value_high = target_revenue * p75_adj
        
        self._add_step(
            name="Calculate Fair Value",
            description="Apply selected multiple to target company revenue",
            inputs={
                "target_revenue": target_revenue,
                "selected_multiple": adjusted_multiple
            },
            calculation=f"${target_revenue:,.0f} × {adjusted_multiple:.2f}x",
            result={
                "fair_value": fair_value,
                "range_low": value_low,
                "range_high": value_high
            }
        )
        
        # Determine confidence based on comp quality
        confidence = self._calculate_confidence(multiples)
        
        return MethodResult(
            method=self.name,
            method_version=self.version,
            fair_value=fair_value,
            confidence=confidence,
            value_low=value_low,
            value_high=value_high,
            audit_trail=self._steps,
            warnings=self._warnings
        )
    
    def _calculate_confidence(self, multiples: list[Decimal]) -> Confidence:
        """Confidence based on comp dispersion."""
        if len(multiples) < 3:
            return Confidence.LOW
        
        # Calculate coefficient of variation
        mean_val = sum(multiples) / len(multiples)
        if mean_val == 0:
            return Confidence.LOW
        
        range_pct = (max(multiples) - min(multiples)) / mean_val
        
        if len(multiples) >= 5 and range_pct < Decimal("1.0"):
            return Confidence.HIGH
        elif range_pct < Decimal("2.0"):
            return Confidence.MEDIUM
        return Confidence.LOW
```

---

## 9. Valuation Engine

```python
# backend/src/valuation/engine.py

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import hashlib
import json
import uuid

from src.config import ValuationConfig
from src.models import (
    CompanyData, MarketIndex, ComparableSet,
    ValuationResult, ValuationSummary, MethodResult, MethodSkipped, Confidence
)
from src.valuation.base import MethodRegistry, ValuationMethod
from src.exceptions import NoValidMethodsError, CalculationError


class ValuationEngine:
    """
    Orchestrates the valuation workflow:
    1. Selects applicable methods based on data
    2. Executes each method
    3. Compares and summarizes results
    4. Produces complete audit output
    """
    
    def __init__(self, config: Optional[ValuationConfig] = None):
        self.config = config or ValuationConfig()
    
    def run(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: Optional[ComparableSet],
        valuation_date: Optional[date] = None
    ) -> ValuationResult:
        """
        Execute complete valuation for a company.
        
        Args:
            company: Company data to value
            index: Market index for adjustments
            comparables: Comparable companies (optional)
            valuation_date: As-of date (defaults to today)
        
        Returns:
            Complete ValuationResult with all method results and audit trail
        
        Raises:
            NoValidMethodsError: If no methods can be executed
        """
        valuation_date = valuation_date or date.today()
        
        # Get all registered methods
        methods = MethodRegistry.get_all(self.config)
        
        # Select applicable methods
        methods_to_run: list[ValuationMethod] = []
        methods_skipped: list[MethodSkipped] = []
        
        for method in methods:
            can_run, missing = method.check_prerequisites(
                company, index, comparables, valuation_date
            )
            
            if can_run:
                methods_to_run.append(method)
            else:
                methods_skipped.append(MethodSkipped(
                    method=method.name,
                    reason=f"Missing required data",
                    missing_data=missing
                ))
        
        # Must have at least one method
        if not methods_to_run:
            raise NoValidMethodsError({
                skip.method.value: skip.reason for skip in methods_skipped
            })
        
        # Execute methods
        method_results: list[MethodResult] = []
        
        for method in methods_to_run:
            try:
                result = method.execute(company, index, comparables, valuation_date)
                method_results.append(result)
            except CalculationError as e:
                # Record failure but continue with other methods
                methods_skipped.append(MethodSkipped(
                    method=method.name,
                    reason=f"Calculation failed: {e.message}",
                    missing_data=[]
                ))
        
        # Must have at least one successful result
        if not method_results:
            raise NoValidMethodsError({
                skip.method.value: skip.reason for skip in methods_skipped
            })
        
        # Generate comparison (if multiple methods)
        comparison = self._compare_methods(method_results) if len(method_results) > 1 else None
        
        # Generate summary
        summary = self._summarize(method_results, company, index, valuation_date)
        
        # Calculate input hash for reproducibility
        input_hash = self._hash_inputs(company, index, comparables, valuation_date)
        
        return ValuationResult(
            id=str(uuid.uuid4()),
            company_id=company.company.id,
            company_name=company.company.name,
            valuation_date=valuation_date,
            generated_at=datetime.utcnow().isoformat(),
            input_hash=input_hash,
            config_snapshot=self.config.model_dump(),
            summary=summary,
            method_results=method_results,
            methods_skipped=methods_skipped,
            method_comparison=comparison
        )
    
    def _compare_methods(self, results: list[MethodResult]) -> dict:
        """Compare results across methods."""
        values = [(r.method.value, r.fair_value) for r in results]
        fair_values = [v[1] for v in values]
        
        avg = sum(fair_values) / len(fair_values)
        
        comparison = {
            "method_values": [
                {
                    "method": name,
                    "fair_value": float(val),
                    "vs_average": f"{float((val - avg) / avg * 100):+.1f}%" if avg else "N/A"
                }
                for name, val in values
            ],
            "average": float(avg),
            "spread": float(max(fair_values) - min(fair_values)),
            "spread_percent": float((max(fair_values) - min(fair_values)) / avg * 100) if avg else 0
        }
        
        # Flag significant divergence
        if comparison["spread_percent"] > 30:
            comparison["warning"] = (
                "Methods diverged by more than 30%. Review individual method "
                "audit trails to understand drivers."
            )
        
        return comparison
    
    def _summarize(
        self,
        results: list[MethodResult],
        company: CompanyData,
        index: MarketIndex,
        valuation_date: date
    ) -> ValuationSummary:
        """Generate executive summary."""
        
        # Calculate primary estimate
        if len(results) == 1:
            primary = results[0].fair_value
            primary_method = results[0].method.value
        else:
            # Simple average when multiple methods
            primary = sum(r.fair_value for r in results) / len(results)
            primary_method = "average_of_methods"
        
        # Calculate range
        all_values = [r.fair_value for r in results]
        for r in results:
            if r.value_low:
                all_values.append(r.value_low)
            if r.value_high:
                all_values.append(r.value_high)
        
        # Overall confidence (conservative: use lowest)
        confidence_order = [Confidence.HIGH, Confidence.MEDIUM, Confidence.LOW]
        confidences = [r.confidence for r in results]
        overall_confidence = max(confidences, key=lambda c: confidence_order.index(c))
        
        # Key assumptions
        assumptions = [
            f"Valuation date: {valuation_date}",
            f"Market index: {index.name}",
        ]
        if company.has_revenue:
            assumptions.append(f"LTM Revenue: ${company.financials.ltm_revenue:,.0f}")
        if company.has_last_round:
            assumptions.append(
                f"Last round: {company.last_round.round_type} on {company.last_round.date}"
            )
        
        return ValuationSummary(
            primary_estimate=primary,
            estimate_low=min(all_values),
            estimate_high=max(all_values),
            confidence=overall_confidence,
            primary_method=primary_method,
            methods_used=[r.method.value for r in results],
            key_assumptions=assumptions
        )
    
    def _hash_inputs(
        self,
        company: CompanyData,
        index: MarketIndex,
        comparables: Optional[ComparableSet],
        valuation_date: date
    ) -> str:
        """Generate deterministic hash of inputs for reproducibility."""
        # Serialize inputs to canonical JSON
        data = {
            "company": company.model_dump(mode="json"),
            "index_name": index.name,
            "comparables_sector": comparables.sector if comparables else None,
            "valuation_date": valuation_date.isoformat(),
            "config": self.config.model_dump()
        }
        
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
```

---

## 10. Utility Functions

```python
# backend/src/utils/math_utils.py

from decimal import Decimal


def median(values: list[Decimal]) -> Decimal:
    """Calculate median of Decimal list."""
    if not values:
        raise ValueError("Cannot calculate median of empty list")
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    if n % 2 == 1:
        return sorted_vals[n // 2]
    else:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2


def percentile(values: list[Decimal], p: int) -> Decimal:
    """Calculate percentile (0-100) using linear interpolation."""
    if not values:
        raise ValueError("Cannot calculate percentile of empty list")
    if not 0 <= p <= 100:
        raise ValueError("Percentile must be 0-100")
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    k = (n - 1) * p / 100
    f = int(k)
    c = min(f + 1, n - 1)
    
    if f == c:
        return sorted_vals[f]
    
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * Decimal(str(k - f))
```

---

## 11. API Layer

### 11.1 Request/Response Schemas

```python
# backend/src/api/schemas.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class CompanyListItem(BaseModel):
    """Company summary for listing."""
    id: str
    name: str
    sector: str
    stage: str


class ValuationRequest(BaseModel):
    """Request to value a company."""
    company_id: str
    valuation_date: Optional[date] = Field(
        default=None,
        description="As-of date for valuation. Defaults to today."
    )
    index_name: Optional[str] = Field(
        default=None,
        description="Market index to use. Defaults to NASDAQ."
    )


class BatchValuationRequest(BaseModel):
    """Request to value multiple companies."""
    company_ids: list[str] = Field(..., min_length=1, max_length=50)
    valuation_date: Optional[date] = None
    index_name: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    data_dir: str
    companies_available: int
    sectors_available: int
```

### 11.2 API Routes

```python
# backend/src/api/routes.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import date

from src.api.schemas import (
    CompanyListItem, ValuationRequest, BatchValuationRequest,
    ErrorResponse, HealthResponse
)
from src.models import ValuationResult
from src.database.loader import DataLoader
from src.valuation.engine import ValuationEngine
from src.config import ValuationConfig, get_settings, Settings
from src.exceptions import (
    ValuationError, DataNotFoundError, NoValidMethodsError
)


router = APIRouter()


def get_loader(settings: Settings = Depends(get_settings)) -> DataLoader:
    return DataLoader(settings.data_dir)


def get_engine() -> ValuationEngine:
    return ValuationEngine(ValuationConfig())


# -----------------------------------------------------------------------------
# Health & Discovery
# -----------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
def health_check(loader: DataLoader = Depends(get_loader)):
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        data_dir=str(loader.data_dir),
        companies_available=len(loader.list_companies()),
        sectors_available=len(loader.list_sectors())
    )


@router.get("/companies", response_model=list[CompanyListItem])
def list_companies(loader: DataLoader = Depends(get_loader)):
    """List all available portfolio companies."""
    return loader.list_companies()


@router.get("/sectors", response_model=list[str])
def list_sectors(loader: DataLoader = Depends(get_loader)):
    """List available comparable sectors."""
    return loader.list_sectors()


@router.get("/indices", response_model=list[str])
def list_indices(loader: DataLoader = Depends(get_loader)):
    """List available market indices."""
    indices = loader.load_indices()
    return list(indices.keys())


# -----------------------------------------------------------------------------
# Valuation
# -----------------------------------------------------------------------------

@router.post("/valuations", response_model=ValuationResult)
def run_valuation(
    request: ValuationRequest,
    loader: DataLoader = Depends(get_loader),
    engine: ValuationEngine = Depends(get_engine)
):
    """
    Run valuation for a single company.
    
    Returns complete valuation result with audit trail.
    """
    try:
        # Load company
        company = loader.load_company(request.company_id)
        
        # Load index
        index_name = request.index_name or engine.config.default_index
        index = loader.get_index(index_name)
        
        # Try to load comparables for company's sector
        comparables = None
        try:
            comparables = loader.load_comparables(company.company.sector)
        except DataNotFoundError:
            pass  # Method selection will handle missing comps
        
        # Run valuation
        result = engine.run(
            company=company,
            index=index,
            comparables=comparables,
            valuation_date=request.valuation_date
        )
        
        return result
    
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except NoValidMethodsError as e:
        raise HTTPException(status_code=422, detail=e.to_dict())
    except ValuationError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/valuations/batch", response_model=list[ValuationResult | ErrorResponse])
def run_batch_valuation(
    request: BatchValuationRequest,
    loader: DataLoader = Depends(get_loader),
    engine: ValuationEngine = Depends(get_engine)
):
    """
    Run valuation for multiple companies.
    
    Returns list of results (successful valuations or error objects).
    Individual failures don't fail the whole batch.
    """
    results = []
    
    for company_id in request.company_ids:
        try:
            company = loader.load_company(company_id)
            index = loader.get_index(request.index_name or engine.config.default_index)
            
            comparables = None
            try:
                comparables = loader.load_comparables(company.company.sector)
            except DataNotFoundError:
                pass
            
            result = engine.run(
                company=company,
                index=index,
                comparables=comparables,
                valuation_date=request.valuation_date
            )
            results.append(result)
        
        except ValuationError as e:
            results.append(ErrorResponse(**e.to_dict()))
        except Exception as e:
            results.append(ErrorResponse(
                error="UNEXPECTED_ERROR",
                message=str(e),
                details={"company_id": company_id}
            ))
    
    return results


# -----------------------------------------------------------------------------
# Debug / Detail Endpoints
# -----------------------------------------------------------------------------

@router.get("/companies/{company_id}")
def get_company(company_id: str, loader: DataLoader = Depends(get_loader)):
    """Get full company data (for debugging/inspection)."""
    try:
        return loader.load_company(company_id).model_dump()
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


@router.get("/comparables/{sector}")
def get_comparables(sector: str, loader: DataLoader = Depends(get_loader)):
    """Get comparable companies for a sector."""
    try:
        return loader.load_comparables(sector).model_dump()
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
```

### 11.3 Main Application

```python
# backend/src/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="VC Portfolio Company Valuation Tool with Audit Trail",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routes
    app.include_router(router, prefix="/api")
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## 12. Frontend (React + TypeScript)

### 12.1 TypeScript Types

```typescript
// frontend/src/types/index.ts

export interface Company {
  id: string;
  name: string;
  sector: string;
  stage: string;
}

export type Confidence = 'high' | 'medium' | 'low';

export interface AuditStep {
  step: number;
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  calculation?: string;
  result: Record<string, unknown>;
}

export interface MethodResult {
  method: string;
  method_version: string;
  fair_value: number;
  confidence: Confidence;
  value_low?: number;
  value_high?: number;
  audit_trail: AuditStep[];
  warnings: string[];
}

export interface MethodSkipped {
  method: string;
  reason: string;
  missing_data: string[];
}

export interface ValuationSummary {
  primary_estimate: number;
  estimate_low: number;
  estimate_high: number;
  confidence: Confidence;
  primary_method: string;
  methods_used: string[];
  key_assumptions: string[];
}

export interface MethodComparison {
  method_values: Array<{
    method: string;
    fair_value: number;
    vs_average: string;
  }>;
  average: number;
  spread: number;
  spread_percent: number;
  warning?: string;
}

export interface ValuationResult {
  id: string;
  company_id: string;
  company_name: string;
  valuation_date: string;
  generated_at: string;
  input_hash: string;
  config_snapshot: Record<string, unknown>;
  summary: ValuationSummary;
  method_results: MethodResult[];
  methods_skipped: MethodSkipped[];
  method_comparison?: MethodComparison;
}

export interface ValuationRequest {
  company_id: string;
  valuation_date?: string;
  index_name?: string;
}

export interface ApiError {
  error: string;
  message: string;
  details: Record<string, unknown>;
}
```

### 12.2 API Client

```typescript
// frontend/src/api/client.ts

import type { 
  Company, 
  ValuationResult, 
  ValuationRequest, 
  ApiError 
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw error;
    }

    return response.json();
  }

  // Discovery
  async listCompanies(): Promise<Company[]> {
    return this.fetch<Company[]>('/companies');
  }

  async listSectors(): Promise<string[]> {
    return this.fetch<string[]>('/sectors');
  }

  async listIndices(): Promise<string[]> {
    return this.fetch<string[]>('/indices');
  }

  // Valuation
  async runValuation(request: ValuationRequest): Promise<ValuationResult> {
    return this.fetch<ValuationResult>('/valuations', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async runBatchValuation(
    companyIds: string[], 
    valuationDate?: string
  ): Promise<Array<ValuationResult | ApiError>> {
    return this.fetch<Array<ValuationResult | ApiError>>('/valuations/batch', {
      method: 'POST',
      body: JSON.stringify({
        company_ids: companyIds,
        valuation_date: valuationDate,
      }),
    });
  }

  // Debug
  async getCompany(companyId: string): Promise<Record<string, unknown>> {
    return this.fetch<Record<string, unknown>>(`/companies/${companyId}`);
  }
}

export const api = new ApiClient();
```

### 12.3 Custom Hook

```typescript
// frontend/src/hooks/useValuation.ts

import { useState, useCallback } from 'react';
import { api } from '../api/client';
import type { ValuationResult, ValuationRequest, ApiError } from '../types';

interface UseValuationReturn {
  result: ValuationResult | null;
  loading: boolean;
  error: ApiError | null;
  runValuation: (request: ValuationRequest) => Promise<void>;
  reset: () => void;
}

export function useValuation(): UseValuationReturn {
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const runValuation = useCallback(async (request: ValuationRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.runValuation(request);
      setResult(data);
    } catch (err) {
      setError(err as ApiError);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, runValuation, reset };
}
```

### 12.4 Main Components

```tsx
// frontend/src/components/CompanySelector.tsx

import { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { Company } from '../types';

interface Props {
  onSelect: (company: Company) => void;
  selectedId?: string;
}

export function CompanySelector({ onSelect, selectedId }: Props) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listCompanies()
      .then(setCompanies)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="animate-pulse h-10 bg-gray-200 rounded" />;
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Select Company
      </label>
      <select
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        value={selectedId || ''}
        onChange={(e) => {
          const company = companies.find(c => c.id === e.target.value);
          if (company) onSelect(company);
        }}
      >
        <option value="">-- Select a company --</option>
        {companies.map((company) => (
          <option key={company.id} value={company.id}>
            {company.name} ({company.stage} · {company.sector})
          </option>
        ))}
      </select>
    </div>
  );
}
```

```tsx
// frontend/src/components/ValuationCard.tsx

import type { ValuationSummary, Confidence } from '../types';

interface Props {
  summary: ValuationSummary;
  companyName: string;
  valuationDate: string;
}

const confidenceStyles: Record<Confidence, string> = {
  high: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-red-100 text-red-800',
};

function formatCurrency(value: number): string {
  if (value >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(2)}B`;
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(2)}M`;
  }
  return `$${value.toLocaleString()}`;
}

export function ValuationCard({ summary, companyName, valuationDate }: Props) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{companyName}</h2>
          <p className="text-sm text-gray-500">As of {valuationDate}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${confidenceStyles[summary.confidence]}`}>
          {summary.confidence.toUpperCase()} confidence
        </span>
      </div>

      <div className="mb-6">
        <p className="text-sm text-gray-500">Fair Value Estimate</p>
        <p className="text-4xl font-bold text-gray-900">
          {formatCurrency(summary.primary_estimate)}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Range: {formatCurrency(summary.estimate_low)} — {formatCurrency(summary.estimate_high)}
        </p>
      </div>

      <div className="border-t pt-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Methods Used</p>
        <div className="flex flex-wrap gap-2">
          {summary.methods_used.map((method) => (
            <span 
              key={method}
              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
            >
              {method.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      </div>

      <div className="border-t pt-4 mt-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Key Assumptions</p>
        <ul className="text-sm text-gray-600 space-y-1">
          {summary.key_assumptions.map((assumption, i) => (
            <li key={i}>• {assumption}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/components/AuditTrail.tsx

import { useState } from 'react';
import type { MethodResult, AuditStep } from '../types';

interface Props {
  methodResults: MethodResult[];
}

function StepCard({ step }: { step: AuditStep }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <button
        className="w-full text-left flex justify-between items-center"
        onClick={() => setExpanded(!expanded)}
      >
        <div>
          <span className="inline-block w-6 h-6 bg-blue-500 text-white text-sm rounded-full text-center mr-2">
            {step.step}
          </span>
          <span className="font-medium">{step.name}</span>
        </div>
        <span className="text-gray-400">{expanded ? '−' : '+'}</span>
      </button>

      {expanded && (
        <div className="mt-4 space-y-3 text-sm">
          <p className="text-gray-600">{step.description}</p>

          {step.calculation && (
            <div className="bg-white p-3 rounded border font-mono text-xs">
              {step.calculation}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="font-medium text-gray-700 mb-1">Inputs</p>
              <pre className="bg-white p-2 rounded border text-xs overflow-auto">
                {JSON.stringify(step.inputs, null, 2)}
              </pre>
            </div>
            <div>
              <p className="font-medium text-gray-700 mb-1">Result</p>
              <pre className="bg-white p-2 rounded border text-xs overflow-auto">
                {JSON.stringify(step.result, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function AuditTrail({ methodResults }: Props) {
  const [selectedMethod, setSelectedMethod] = useState(0);
  const current = methodResults[selectedMethod];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Audit Trail</h3>

      {/* Method tabs */}
      {methodResults.length > 1 && (
        <div className="flex gap-2 mb-4 border-b">
          {methodResults.map((result, i) => (
            <button
              key={result.method}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
                i === selectedMethod
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setSelectedMethod(i)}
            >
              {result.method.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      )}

      {/* Method info */}
      <div className="mb-4 text-sm text-gray-600">
        <p>Method version: <code className="bg-gray-100 px-1 rounded">{current.method_version}</code></p>
        <p>Fair value: <strong>${current.fair_value.toLocaleString()}</strong></p>
      </div>

      {/* Warnings */}
      {current.warnings.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="font-medium text-yellow-800 text-sm">Warnings</p>
          <ul className="text-sm text-yellow-700 mt-1">
            {current.warnings.map((w, i) => (
              <li key={i}>• {w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Steps */}
      <div className="space-y-3">
        {current.audit_trail.map((step) => (
          <StepCard key={step.step} step={step} />
        ))}
      </div>
    </div>
  );
}
```

### 12.5 Main Page

```tsx
// frontend/src/pages/ValuationPage.tsx

import { useState } from 'react';
import { CompanySelector } from '../components/CompanySelector';
import { ValuationCard } from '../components/ValuationCard';
import { AuditTrail } from '../components/AuditTrail';
import { useValuation } from '../hooks/useValuation';
import type { Company } from '../types';

export function ValuationPage() {
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const { result, loading, error, runValuation, reset } = useValuation();

  const handleCompanySelect = (company: Company) => {
    setSelectedCompany(company);
    reset();
  };

  const handleRunValuation = () => {
    if (!selectedCompany) return;
    runValuation({ company_id: selectedCompany.id });
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          VC Portfolio Valuation Tool
        </h1>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <CompanySelector
                onSelect={handleCompanySelect}
                selectedId={selectedCompany?.id}
              />
            </div>
            <button
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!selectedCompany || loading}
              onClick={handleRunValuation}
            >
              {loading ? 'Running...' : 'Run Valuation'}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="font-medium text-red-800">{error.error}</p>
            <p className="text-red-600 text-sm">{error.message}</p>
            {error.details && (
              <pre className="mt-2 text-xs text-red-500 overflow-auto">
                {JSON.stringify(error.details, null, 2)}
              </pre>
            )}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <ValuationCard
              summary={result.summary}
              companyName={result.company_name}
              valuationDate={result.valuation_date}
            />
            <AuditTrail methodResults={result.method_results} />
          </div>
        )}

        {/* Skipped methods */}
        {result && result.methods_skipped.length > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              Methods Not Executed
            </h3>
            <div className="space-y-2">
              {result.methods_skipped.map((skip) => (
                <div key={skip.method} className="text-sm">
                  <span className="font-medium text-gray-700">
                    {skip.method.replace(/_/g, ' ')}:
                  </span>{' '}
                  <span className="text-gray-500">{skip.reason}</span>
                  {skip.missing_data.length > 0 && (
                    <ul className="ml-4 text-gray-400">
                      {skip.missing_data.map((field, i) => (
                        <li key={i}>• {field}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reproducibility footer */}
        {result && (
          <div className="mt-8 text-center text-xs text-gray-400">
            <p>
              Result ID: {result.id} | Input Hash: {result.input_hash} |
              Generated: {new Date(result.generated_at).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 13. Test Strategy

### 13.1 Test Structure

```
backend/tests/
├── conftest.py           # Shared fixtures
├── test_models.py        # Pydantic validation
├── test_loader.py        # Data loading
├── test_math_utils.py    # Utility functions
├── test_last_round.py    # Last Round method
├── test_comps.py         # Comps method
├── test_engine.py        # Engine integration
└── test_api.py           # API endpoint tests
```

### 13.2 Key Test Cases

```python
# backend/tests/conftest.py

import pytest
from decimal import Decimal
from datetime import date

from src.models import (
    Company, Financials, LastRound, Adjustment, CompanyData,
    MarketIndex, ComparableSet, ComparableCompany, CompanyStage
)
from src.config import ValuationConfig


@pytest.fixture
def config():
    return ValuationConfig()


@pytest.fixture
def sample_company_with_revenue():
    return CompanyData(
        company=Company(
            id="test-co",
            name="Test Company",
            sector="saas",
            stage=CompanyStage.SERIES_A
        ),
        financials=Financials(
            as_of_date=date(2024, 12, 15),
            ltm_revenue=Decimal("10000000"),
            revenue_growth_yoy=Decimal("0.50")
        ),
        last_round=LastRound(
            round_type="Series A",
            date=date(2024, 3, 15),
            post_money_valuation=Decimal("50000000")
        ),
        adjustments=[]
    )


@pytest.fixture
def sample_company_prerevenue():
    return CompanyData(
        company=Company(
            id="prerev",
            name="PreRevenue Co",
            sector="saas",
            stage=CompanyStage.SEED
        ),
        financials=Financials(
            as_of_date=date(2024, 12, 15),
            ltm_revenue=None
        ),
        last_round=LastRound(
            round_type="Seed",
            date=date(2024, 6, 1),
            post_money_valuation=Decimal("8000000")
        ),
        adjustments=[]
    )


@pytest.fixture
def sample_company_no_round():
    return CompanyData(
        company=Company(
            id="noround",
            name="No Round Co",
            sector="saas",
            stage=CompanyStage.PRE_SEED
        ),
        financials=Financials(
            as_of_date=date(2024, 12, 15),
            ltm_revenue=Decimal("1000000")
        ),
        last_round=None,
        adjustments=[]
    )


@pytest.fixture
def sample_index():
    return MarketIndex(
        name="NASDAQ",
        values={
            "2024-03-15": Decimal("16000"),
            "2024-06-01": Decimal("17000"),
            "2024-12-15": Decimal("17600"),
            "2025-01-15": Decimal("17800")
        }
    )


@pytest.fixture
def sample_comparables():
    return ComparableSet(
        sector="saas",
        as_of_date=date(2025, 1, 15),
        source="Test Data",
        companies=[
            ComparableCompany(
                ticker="AAA",
                name="Company A",
                enterprise_value=Decimal("10000000000"),
                ltm_revenue=Decimal("1000000000"),
                revenue_growth=Decimal("0.20")
            ),
            ComparableCompany(
                ticker="BBB",
                name="Company B",
                enterprise_value=Decimal("8000000000"),
                ltm_revenue=Decimal("1000000000"),
                revenue_growth=Decimal("0.15")
            ),
            ComparableCompany(
                ticker="CCC",
                name="Company C",
                enterprise_value=Decimal("12000000000"),
                ltm_revenue=Decimal("1000000000"),
                revenue_growth=Decimal("0.25")
            ),
        ]
    )
```

```python
# backend/tests/test_engine.py

import pytest
from datetime import date

from src.valuation.engine import ValuationEngine
from src.exceptions import NoValidMethodsError


class TestValuationEngine:
    """Integration tests for the valuation engine."""
    
    def test_both_methods_run_when_data_available(
        self, config, sample_company_with_revenue, sample_index, sample_comparables
    ):
        engine = ValuationEngine(config)
        result = engine.run(
            company=sample_company_with_revenue,
            index=sample_index,
            comparables=sample_comparables,
            valuation_date=date(2025, 1, 15)
        )
        
        assert len(result.method_results) == 2
        assert len(result.methods_skipped) == 0
        assert result.method_comparison is not None
    
    def test_only_last_round_when_prerevenue(
        self, config, sample_company_prerevenue, sample_index, sample_comparables
    ):
        engine = ValuationEngine(config)
        result = engine.run(
            company=sample_company_prerevenue,
            index=sample_index,
            comparables=sample_comparables,
            valuation_date=date(2025, 1, 15)
        )
        
        assert len(result.method_results) == 1
        assert result.method_results[0].method == "last_round_adjusted"
        assert len(result.methods_skipped) == 1
    
    def test_only_comps_when_no_round(
        self, config, sample_company_no_round, sample_index, sample_comparables
    ):
        engine = ValuationEngine(config)
        result = engine.run(
            company=sample_company_no_round,
            index=sample_index,
            comparables=sample_comparables,
            valuation_date=date(2025, 1, 15)
        )
        
        assert len(result.method_results) == 1
        assert result.method_results[0].method == "comps_revenue"
    
    def test_no_methods_raises_error(self, config, sample_index):
        """Pre-revenue company with no round = no valid methods."""
        company = CompanyData(
            company=Company(id="x", name="X", sector="saas", stage=CompanyStage.PRE_SEED),
            financials=Financials(as_of_date=date(2024, 12, 15), ltm_revenue=None),
            last_round=None,
            adjustments=[]
        )
        
        engine = ValuationEngine(config)
        
        with pytest.raises(NoValidMethodsError):
            engine.run(
                company=company,
                index=sample_index,
                comparables=None,
                valuation_date=date(2025, 1, 15)
            )
    
    def test_input_hash_reproducibility(
        self, config, sample_company_with_revenue, sample_index, sample_comparables
    ):
        """Same inputs should produce same hash."""
        engine = ValuationEngine(config)
        
        result1 = engine.run(
            company=sample_company_with_revenue,
            index=sample_index,
            comparables=sample_comparables,
            valuation_date=date(2025, 1, 15)
        )
        
        result2 = engine.run(
            company=sample_company_with_revenue,
            index=sample_index,
            comparables=sample_comparables,
            valuation_date=date(2025, 1, 15)
        )
        
        assert result1.input_hash == result2.input_hash
    
    def test_config_snapshot_included(
        self, config, sample_company_with_revenue, sample_index, sample_comparables
    ):
        engine = ValuationEngine(config)
        result = engine.run(
            company=sample_company_with_revenue,
            index=sample_index,
            comparables=sample_comparables,
            valuation_date=date(2025, 1, 15)
        )
        
        assert "max_round_age_months" in result.config_snapshot
        assert "illiquidity_discount" in result.config_snapshot
```

---

## 14. README

```markdown
# VC Portfolio Valuation Audit Tool

A full-stack application for estimating fair value of private portfolio companies
with complete audit trails for compliance review.

## Features

- **Multiple Valuation Methods**: Last Round Adjusted and Comparable Company Analysis
- **Automatic Method Selection**: System determines applicable methods based on available data
- **Complete Audit Trail**: Every calculation step logged with inputs, formulas, and outputs
- **Reproducibility**: Results include input hash and config snapshot
- **Batch Processing**: Value multiple companies in a single request
- **Clean Web UI**: React frontend for auditor workflow

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run server
python -m src.main
# API docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   FastAPI   │────▶│  Valuation  │
│  (React)    │     │   Backend   │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ Data Loader │     │  Methods    │
                    │ (JSON)      │     │  Registry   │
                    └─────────────┘     └─────────────┘
```

## Design Decisions

1. **Method Registry Pattern**: New valuation methods are added by creating a class
   and decorating with `@MethodRegistry.register`. No other code changes needed.

2. **Configuration Object**: All tunable parameters (round age limits, discounts, etc.)
   are centralized in `ValuationConfig`. Config is snapshotted with each result.

3. **Input Hashing**: Each result includes a hash of inputs. Same hash = same inputs,
   enabling reproducibility verification.

4. **Graceful Degradation**: Missing data skips individual methods rather than
   failing the entire valuation. Skipped methods are documented in output.

5. **Simplified Adjustments**: Instead of complex event categorization, auditors
   specify adjustment percentages directly. More flexible and auditable.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/companies` | List available companies |
| GET | `/api/sectors` | List comparable sectors |
| POST | `/api/valuations` | Run single valuation |
| POST | `/api/valuations/batch` | Run batch valuation |

## Adding a New Valuation Method

```python
# src/valuation/new_method.py

from src.valuation.base import ValuationMethod, MethodRegistry
from src.models import MethodName, MethodResult

@MethodRegistry.register
class NewMethod(ValuationMethod):
    name = MethodName.NEW_METHOD  # Add to enum
    version = "1.0.0"
    display_name = "New Method"
    
    def check_prerequisites(self, company, index, comparables, date):
        # Return (can_run: bool, missing_fields: list)
        pass
    
    def execute(self, company, index, comparables, date):
        # Return MethodResult with audit trail
        pass
```

## Potential Improvements

- **DCF Method**: Add discounted cash flow for companies with projections
- **Real Data Integration**: Replace mock JSON with Yahoo Finance, PitchBook APIs
- **User Authentication**: Add login for multi-user audit workflows
- **Result Storage**: Persist valuations to database for historical comparison
- **PDF Export**: Generate formatted audit reports
- **Parallel Batch Processing**: Use async/await for concurrent valuations

## Running Tests

```bash
cd backend
pytest tests/ -v --cov=src
```
```

---

This PRD should give you everything needed to build a complete, production-quality solution that demonstrates system design thinking without over-engineering the financial domain. Ready to start building?