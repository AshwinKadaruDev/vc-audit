# API & Database Schema Reference

This document explains the API data structures and database schema. If you're building a client to consume this API or understanding the data model, this is your reference.

---

## Table of Contents

1. [Quick Start: The Main Endpoint](#quick-start-the-main-endpoint)
2. [Input: What You Send](#input-what-you-send)
3. [Output: What You Get Back](#output-what-you-get-back)
4. [Complete Response Example](#complete-response-example)
5. [Data Model Reference](#data-model-reference)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Error Responses](#error-responses)

---

## Quick Start: The Main Endpoint

**Endpoint:** `POST /api/valuations/run-and-save`

This is the primary endpoint. You send company data, get back a valuation with full audit trail, and it's saved to the database.

```bash
curl -X POST http://localhost:8000/api/valuations/run-and-save \
  -H "Content-Type: application/json" \
  -d '{
    "company": {
      "id": "my-company-1",
      "name": "Acme Corp",
      "sector": "saas",
      "stage": "series_b"
    },
    "financials": {
      "revenue_ttm": "10000000",
      "revenue_growth_yoy": "0.50"
    },
    "last_round": {
      "date": "2025-06-15",
      "valuation_pre": "40000000",
      "valuation_post": "50000000",
      "amount_raised": "10000000",
      "lead_investor": "Sequoia Capital"
    },
    "adjustments": []
  }'
```

---

## Input: What You Send

### `CompanyData` - The Input Object

```typescript
interface CompanyData {
  company: Company;
  financials: Financials;
  last_round?: LastRound;      // Optional - needed for Last Round method
  adjustments: Adjustment[];   // Optional - custom adjustment factors
}

interface Company {
  id: string;                  // Your identifier for the company
  name: string;                // Display name
  sector: string;              // Must match available sectors: "saas", "fintech", etc.
  stage: CompanyStage;         // "seed" | "series_a" | "series_b" | "series_c" | "growth"
  founded_date?: string;       // ISO date (optional)
}

interface Financials {
  revenue_ttm?: string;        // Trailing 12-month revenue (Decimal as string)
  revenue_growth_yoy?: string; // Year-over-year growth rate (e.g., "0.50" = 50%)
  gross_margin?: string;       // Gross margin (e.g., "0.70" = 70%)
  burn_rate?: string;          // Monthly burn rate
  runway_months?: number;      // Months of runway
}

interface LastRound {
  date: string;                // ISO date of funding round
  valuation_pre: string;       // Pre-money valuation (Decimal as string)
  valuation_post: string;      // Post-money valuation (must equal pre + raised)
  amount_raised: string;       // Amount raised in round
  lead_investor?: string;      // Lead investor name (optional)
}

interface Adjustment {
  name: string;                // Adjustment name (e.g., "Key Person Risk")
  factor: string;              // Multiplier (e.g., "0.90" = 10% decrease)
  reason: string;              // Explanation for the adjustment
}
```

### Input Validation Rules

- `revenue_ttm` and `burn_rate` must be positive if provided
- `gross_margin` must be between 0 and 1
- `valuation_post` must equal `valuation_pre + amount_raised`
- `adjustment.factor` must be positive and ≤ 10
- All monetary values are strings (Decimals) to avoid floating-point issues

---

## Output: What You Get Back

### `SavedValuationResponse` - The Response Object

```typescript
interface SavedValuationResponse {
  id: string;                           // UUID - use this to fetch later
  company_id: string;                   // Your original company ID
  company_name: string;                 // Company name
  valuation_date: string;               // ISO date when valuation was run
  summary: ValuationSummary;            // Executive summary with primary value
  method_results: MethodResult[];       // Results from each method (with audit trails)
  skipped_methods: MethodSkipped[];     // Methods that couldn't run (with reasons)
  cross_method_analysis?: string;       // Comparison between methods (if multiple ran)
  config_snapshot: ConfigSnapshot;      // Algorithm config used (for reproducibility)
}
```

### `ValuationSummary` - The Executive Summary

```typescript
interface ValuationSummary {
  primary_value: string;                // The recommended valuation (Decimal)
  primary_method: MethodName;           // "last_round" or "comparables"
  value_range_low?: string;             // Lowest value across methods
  value_range_high?: string;            // Highest value across methods
  overall_confidence: Confidence;       // "high" | "medium" | "low"
  confidence_explanation: string;       // Why this confidence level
  summary_text: string;                 // Human-readable summary paragraph
  selection_reason: string;             // Why this method was chosen as primary
  method_comparison?: MethodComparisonData;  // Structured comparison
}

interface MethodComparisonData {
  methods: MethodComparisonItem[];      // All methods with values
  spread_percent?: string;              // Difference between methods as %
  spread_warning?: string;              // Warning if spread is high
  selection_steps: string[];            // Step-by-step selection logic
}

interface MethodComparisonItem {
  method: MethodName;
  value: string;
  confidence: Confidence;
  is_primary: boolean;
}
```

### `MethodResult` - Individual Method Output (THE AUDIT TRAIL)

This is where all the detailed calculations live.

```typescript
interface MethodResult {
  method: MethodName;                   // "last_round" or "comparables"
  value: string;                        // Final value from this method (Decimal)
  confidence: Confidence;               // This method's confidence level
  confidence_explanation: string;       // Why this confidence level
  audit_trail: AuditStep[];             // THE DETAILED CALCULATION STEPS
  warnings: string[];                   // Any warnings generated
}
```

### `AuditStep` - Single Calculation Step

Each step in the audit trail has this structure:

```typescript
interface AuditStep {
  step_number: number;                  // Sequential step number
  description: string;                  // What this step is doing
  inputs: Record<string, any>;          // All input data for this step
  calculation?: string;                 // Human-readable calculation explanation
  result?: string;                      // Outcome of this step
}
```

The `inputs` object varies by step type. See examples below.

---

## Complete Response Example

Here's a realistic full response from `POST /api/valuations/run-and-save`:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "company_id": "acme-corp-1",
  "company_name": "Acme Corp",
  "valuation_date": "2026-01-22",
  "summary": {
    "primary_value": "52650000",
    "primary_method": "last_round",
    "value_range_low": "48750000",
    "value_range_high": "52650000",
    "overall_confidence": "high",
    "confidence_explanation": "HIGH confidence: Methods agree well (8.0% spread, below 15% threshold). Values: Last Round: $52,650,000, Comparables: $48,750,000. Using highest individual method confidence.",
    "summary_text": "Primary valuation: $52,650,000 (via last_round method, high confidence). Supporting methods: comparables: $48,750,000.",
    "selection_reason": "We used 2 valuation methods. Last Round was selected as primary because both methods have high confidence, and Last Round reflects what informed investors actually paid for this specific company after due diligence, rather than an estimate derived from similar but different public companies. The 8.0% spread shows good agreement between methods.",
    "method_comparison": {
      "methods": [
        {
          "method": "last_round",
          "value": "52650000",
          "confidence": "high",
          "is_primary": true
        },
        {
          "method": "comparables",
          "value": "48750000",
          "confidence": "high",
          "is_primary": false
        }
      ],
      "spread_percent": "8.0",
      "spread_warning": null,
      "selection_steps": [
        "Ran all applicable valuation methods: Last Round, Comparables",
        "Assessed confidence: Last Round: HIGH; Comparables: HIGH",
        "Selected Last Round as primary (high confidence)"
      ]
    }
  },
  "method_results": [
    {
      "method": "last_round",
      "value": "52650000",
      "confidence": "high",
      "confidence_explanation": "HIGH confidence: The funding round is 7 months old...",
      "audit_trail": [
        {
          "step_number": 1,
          "description": "Starting Point: Last Funding Round",
          "inputs": {
            "type": "funding_round",
            "round_date": "June 15, 2025",
            "pre_money_valuation": "$40,000,000",
            "amount_raised": "$10,000,000",
            "post_money_valuation": "$50,000,000",
            "lead_investor": "Sequoia Capital"
          },
          "calculation": null,
          "result": "Starting valuation: $50,000,000"
        },
        {
          "step_number": 2,
          "description": "Market Adjustment: How Has the Market Moved?",
          "inputs": {
            "type": "market_adjustment",
            "index_name": "NASDAQ",
            "market_change_percent": "+3.5%",
            "volatility_factor": "1.5",
            "adjusted_change_percent": "+5.3%",
            "data_source": {
              "name": "Yahoo Finance API",
              "retrieved_at": "2026-01-22"
            }
          },
          "calculation": "The NASDAQ increased by 3.5%...",
          "result": "Market-adjusted valuation: $52,650,000"
        }
      ],
      "warnings": []
    }
  ],
  "skipped_methods": [],
  "cross_method_analysis": "Cross-method comparison: 2 methods executed...",
  "config_snapshot": {
    "max_round_age_months": 18,
    "stale_round_threshold_months": 12,
    "default_beta": "1.5",
    "min_comparables": 3,
    "multiple_percentile": 50,
    "high_confidence_spread": "0.15",
    "medium_confidence_spread": "0.30"
  }
}
```

---

## Data Model Reference

### Enums

```typescript
type MethodName = "last_round" | "comparables";
type Confidence = "high" | "medium" | "low";
type CompanyStage = "seed" | "series_a" | "series_b" | "series_c" | "growth";
```

### Audit Step Input Types

The `inputs.type` field tells you what kind of step this is:

| Type | Method | Description |
|------|--------|-------------|
| `funding_round` | Last Round | Starting point from funding round |
| `market_adjustment` | Last Round | Market movement calculation |
| `target_metrics` | Comparables | Company's financial metrics |
| `comparable_companies` | Comparables | List of public comparables |
| `multiple_statistics` | Comparables | Multiple analysis (median, range) |
| `private_discount` | Comparables | Illiquidity discount calculation |
| `final_calculation` | Comparables | Base value calculation |
| `company_adjustments` | Both | User-provided adjustments |
| `final_formula` | Both | Summary formula with all variables |

### Key Fields in Audit Steps

**`funding_round` step:**
```typescript
{
  type: "funding_round",
  round_date: string,           // Human-readable date
  pre_money_valuation: string,  // Formatted currency
  amount_raised: string,        // Formatted currency
  post_money_valuation: string, // Formatted currency
  lead_investor: string         // Investor name or "Not disclosed"
}
```

**`market_adjustment` step:**
```typescript
{
  type: "market_adjustment",
  index_name: string,              // "NASDAQ"
  round_date: string,              // When funding happened
  round_index_value: string,       // Index value at funding
  today_date: string,              // Today's date
  today_index_value: string,       // Current index value
  market_change_percent: string,   // e.g., "+3.5%"
  market_direction: string,        // "increased" | "decreased" | "remained flat"
  volatility_factor: string,       // e.g., "1.5"
  adjusted_change_percent: string, // After applying beta
  data_source: {
    name: string,                  // "Yahoo Finance API"
    retrieved_at: string,          // ISO date
    citation: string               // Full citation
  }
}
```

**`comparable_companies` step:**
```typescript
{
  type: "comparable_companies",
  sector: string,
  data_as_of: string,           // When data was pulled
  companies: Array<{
    ticker: string,
    name: string,
    revenue: string,            // Formatted currency
    market_cap: string,         // Formatted currency
    revenue_multiple: string,   // e.g., "7.8x"
    growth: string              // e.g., "11%"
  }>,
  data_source: { name, retrieved_at, citation }
}
```

**`private_discount` step:**
```typescript
{
  type: "private_discount",
  public_multiple: string,      // Starting multiple
  discount_percent: string,     // e.g., "25%"
  company_stage: string,        // e.g., "Series B"
  adjusted_multiple: string,    // After discount
  explanation: string           // Why we discount
}
```

**`final_formula` step:**
```typescript
{
  type: "final_formula",
  formula_template: string,     // e.g., "V = P × M × C"
  formula_display: string,      // Human-readable formula
  formula_with_values: string,  // Formula with actual numbers
  variables: Array<{
    name: string,               // e.g., "Post-Money Valuation"
    symbol: string,             // e.g., "P"
    value: string,              // e.g., "$50,000,000"
    derivation: string          // How this value was derived
  }>,
  final_value: string,          // Final answer
  method_name: string           // "Last Round" or "Comparables"
}
```

---

## Database Schema

### Overview

PostgreSQL schema with JSONB for flexible nested data, explicit columns for queryable fields.

```
sectors (reference)
    │
    ├── comparable_companies (seeded public companies)
    │
    └── portfolio_companies (user-created + seeded test data)
            │
            └── valuations (audit results)

market_indices (seeded time series)
```

### Enums

```sql
CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE company_stage AS ENUM ('seed', 'series_a', 'series_b', 'series_c', 'growth');
CREATE TYPE valuation_method AS ENUM ('last_round', 'comparables');
```

### Tables

#### sectors
```sql
CREATE TABLE sectors (
    id VARCHAR(50) PRIMARY KEY,              -- 'saas', 'fintech'
    display_name VARCHAR(100) NOT NULL,      -- 'SaaS', 'Fintech'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### market_indices
```sql
CREATE TABLE market_indices (
    -- Composite primary key: (name, date)
    name VARCHAR(50) NOT NULL,               -- 'NASDAQ', 'SP500'
    date DATE NOT NULL,
    value DECIMAL(20,2) NOT NULL,
    source_name VARCHAR(100) NOT NULL DEFAULT 'Yahoo Finance API',
    PRIMARY KEY (name, date)
);

CREATE INDEX idx_market_indices_lookup ON market_indices(name, date);
```

#### comparable_companies
```sql
CREATE TABLE comparable_companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    sector_id VARCHAR(50) NOT NULL REFERENCES sectors(id),
    revenue_ttm DECIMAL(20,2),
    market_cap DECIMAL(20,2),
    ev_revenue_multiple DECIMAL(10,2),
    revenue_growth_yoy DECIMAL(10,4),
    as_of_date DATE NOT NULL,
    source_name VARCHAR(100) NOT NULL DEFAULT 'Yahoo Finance API',
    source_url VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comparables_sector ON comparable_companies(sector_id);
```

#### portfolio_companies
```sql
CREATE TABLE portfolio_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    sector_id VARCHAR(50) NOT NULL REFERENCES sectors(id),
    stage company_stage NOT NULL,
    founded_date DATE,

    -- Nested data as JSONB
    financials JSONB NOT NULL DEFAULT '{}',
    last_round JSONB,
    adjustments JSONB NOT NULL DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_portfolio_created ON portfolio_companies(created_at DESC);
```

**JSONB Structures:**
```typescript
// financials
{
  revenue_ttm?: string,        // Decimal as string for precision
  revenue_growth_yoy?: string,
  gross_margin?: string,
  burn_rate?: string,
  runway_months?: number
}

// last_round (nullable)
{
  date: string,                // ISO date
  valuation_pre: string,
  valuation_post: string,
  amount_raised: string,
  lead_investor?: string
}

// adjustments
[
  { name: string, factor: string, reason: string }
]
```

#### valuations
```sql
CREATE TABLE valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_company_id UUID NOT NULL REFERENCES portfolio_companies(id),

    -- Snapshot for auditability
    input_snapshot JSONB NOT NULL,
    input_hash VARCHAR(64) NOT NULL,

    -- Extracted queryable fields
    company_name VARCHAR(200) NOT NULL,
    primary_value DECIMAL(18,2) NOT NULL,
    primary_method valuation_method NOT NULL,
    value_range_low DECIMAL(18,2),
    value_range_high DECIMAL(18,2),
    overall_confidence confidence_level NOT NULL,

    -- Full results as JSONB
    summary JSONB NOT NULL,
    method_results JSONB NOT NULL,
    skipped_methods JSONB NOT NULL DEFAULT '[]',
    config_snapshot JSONB NOT NULL,

    valuation_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_valuations_company ON valuations(portfolio_company_id);
CREATE INDEX idx_valuations_created ON valuations(created_at DESC);
```

### Why JSONB?

The audit trail is stored as JSONB (JSON Binary) because:

1. **Flexibility:** Audit steps have varying structures by method
2. **Immutability:** Full record preserved exactly as calculated
3. **Reproducibility:** `input_snapshot` + `config_snapshot` = can re-run exactly
4. **Auditability:** Complete calculation history for compliance

### Common Queries

```sql
-- Get comparables for a sector (single efficient query)
SELECT * FROM comparable_companies WHERE sector_id = $1;

-- Get index value at a specific date (for Last Round method)
SELECT value FROM market_indices
WHERE name = $1 AND date <= $2
ORDER BY date DESC LIMIT 1;

-- List recent valuations
SELECT id, company_name, primary_value, primary_method, overall_confidence, created_at
FROM valuations ORDER BY created_at DESC LIMIT 20;

-- Get full valuation with company
SELECT v.*, pc.sector_id, pc.stage
FROM valuations v
JOIN portfolio_companies pc ON v.portfolio_company_id = pc.id
WHERE v.id = $1;

-- Get all high-confidence valuations over $50M
SELECT id, company_name, primary_value, primary_method
FROM valuations
WHERE overall_confidence = 'high'
  AND primary_value > 50000000
ORDER BY created_at DESC;

-- Find valuations with high method disagreement
SELECT id, company_name, summary->>'spread_percent' as spread
FROM valuations
WHERE (summary->'method_comparison'->>'spread_percent')::numeric > 30;
```

---

## API Endpoints

### Run and Save Valuation

```
POST /api/valuations/run-and-save
```

Primary endpoint - runs valuation, saves to database, returns full result with audit trail.

### List Saved Valuations

```
GET /api/valuations/saved
```

Returns lightweight list (no audit trails):

```json
[
  {
    "id": "a1b2c3d4-...",
    "company_name": "Acme Corp",
    "primary_value": "52650000",
    "primary_method": "last_round",
    "overall_confidence": "high",
    "valuation_date": "2026-01-22",
    "created_at": "2026-01-22T14:30:00Z"
  }
]
```

### Get Single Valuation

```
GET /api/valuations/saved/{id}
```

Returns full `ValuationDetail` with complete audit trail.

### Delete Valuation

```
DELETE /api/valuations/saved/{id}
```

### List Available Sectors

```
GET /api/sectors
```

Returns: `["saas", "fintech"]`

### List Portfolio Companies

```
GET /api/portfolio-companies
```

Returns list of companies (seeded test companies + user-created).

### Get Random Test Company

```
GET /api/portfolio-companies/random
```

Returns a random company with all fields populated - useful for testing.

---

## Error Responses

All errors follow this format:

```json
{
  "error_type": "NoValidMethodsError",
  "message": "No valid valuation methods could be executed for company xyz",
  "details": {
    "company_id": "xyz",
    "skip_reasons": {
      "last_round": "No last funding round data available",
      "comparables": "Company has no revenue data (pre-revenue)"
    }
  }
}
```

### Error Types

| Error Type | HTTP Code | Meaning |
|------------|-----------|---------|
| `DataNotFoundError` | 404 | Company or sector doesn't exist |
| `DataValidationError` | 400 | Input validation failed |
| `NoValidMethodsError` | 422 | No valuation methods could run |
| `CalculationError` | 500 | Math error during valuation |
