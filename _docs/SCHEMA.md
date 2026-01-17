# Database Schema

## Overview

Simple, extensible PostgreSQL schema. JSONB for flexible nested data, explicit columns for queryable fields.

```
sectors (reference)
    │
    ├── comparable_companies (seeded public companies)
    │
    └── portfolio_companies (user-created)
            │
            └── valuations (audit results)

market_indices (seeded time series)
```

## Enums

```sql
CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE company_stage AS ENUM ('seed', 'series_a', 'series_b', 'series_c', 'growth');
CREATE TYPE valuation_method AS ENUM ('last_round', 'comparables');
```

## Tables

### sectors
```sql
CREATE TABLE sectors (
    id VARCHAR(50) PRIMARY KEY,              -- 'saas', 'fintech'
    display_name VARCHAR(100) NOT NULL,      -- 'SaaS', 'Fintech'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### market_indices
```sql
CREATE TABLE market_indices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,               -- 'NASDAQ', 'SP500'
    date DATE NOT NULL,
    value DECIMAL(18,2) NOT NULL,
    UNIQUE(name, date)
);

CREATE INDEX idx_market_indices_lookup ON market_indices(name, date);
```

### comparable_companies
```sql
CREATE TABLE comparable_companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    sector_id VARCHAR(50) NOT NULL REFERENCES sectors(id),
    revenue_ttm DECIMAL(18,2),
    market_cap DECIMAL(18,2),
    ev_revenue_multiple DECIMAL(10,4),
    revenue_growth_yoy DECIMAL(10,4),
    as_of_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_comparables_sector ON comparable_companies(sector_id);
```

### portfolio_companies
```sql
CREATE TABLE portfolio_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    sector_id VARCHAR(50) NOT NULL REFERENCES sectors(id),
    stage company_stage NOT NULL,
    founded_date DATE,

    -- Nested data as JSONB (see TRADEOFFS.md #7)
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

### valuations
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

## Seed Data

```sql
-- Sectors
INSERT INTO sectors (id, display_name) VALUES
    ('saas', 'SaaS'),
    ('fintech', 'Fintech');

-- Market Indices
INSERT INTO market_indices (name, date, value) VALUES
    ('NASDAQ', '2022-01-01', 15644.97),
    ('NASDAQ', '2022-07-01', 11028.74),
    ('NASDAQ', '2023-01-01', 10466.48),
    ('NASDAQ', '2023-07-01', 14346.02),
    ('NASDAQ', '2024-01-01', 14765.98),
    ('NASDAQ', '2024-07-01', 17879.30),
    ('NASDAQ', '2025-01-01', 19621.68),
    ('NASDAQ', '2025-07-01', 20145.32),
    ('NASDAQ', '2026-01-01', 21234.56),
    ('SP500', '2022-01-01', 4766.18),
    ('SP500', '2022-07-01', 3785.38),
    ('SP500', '2023-01-01', 3824.14),
    ('SP500', '2023-07-01', 4588.96),
    ('SP500', '2024-01-01', 4769.83),
    ('SP500', '2024-07-01', 5475.09),
    ('SP500', '2025-01-01', 5942.47),
    ('SP500', '2025-07-01', 6124.83),
    ('SP500', '2026-01-01', 6387.21);

-- Comparable Companies - SaaS
INSERT INTO comparable_companies (ticker, name, sector_id, revenue_ttm, market_cap, ev_revenue_multiple, revenue_growth_yoy, as_of_date) VALUES
    ('CRM', 'Salesforce', 'saas', 34860000000, 276000000000, 7.9, 0.11, '2026-01-15'),
    ('NOW', 'ServiceNow', 'saas', 9150000000, 168000000000, 18.4, 0.24, '2026-01-15'),
    ('WDAY', 'Workday', 'saas', 7260000000, 69000000000, 9.5, 0.17, '2026-01-15'),
    ('DDOG', 'Datadog', 'saas', 2120000000, 42000000000, 19.8, 0.26, '2026-01-15'),
    ('ZS', 'Zscaler', 'saas', 1900000000, 28000000000, 14.7, 0.35, '2026-01-15'),
    ('SNOW', 'Snowflake', 'saas', 3100000000, 56000000000, 18.1, 0.32, '2026-01-15');

-- Comparable Companies - Fintech
INSERT INTO comparable_companies (ticker, name, sector_id, revenue_ttm, market_cap, ev_revenue_multiple, revenue_growth_yoy, as_of_date) VALUES
    ('SQ', 'Block (Square)', 'fintech', 21500000000, 47000000000, 2.2, 0.18, '2026-01-15'),
    ('PYPL', 'PayPal', 'fintech', 30200000000, 72000000000, 2.4, 0.08, '2026-01-15'),
    ('AFRM', 'Affirm', 'fintech', 2300000000, 17000000000, 7.4, 0.41, '2026-01-15'),
    ('SOFI', 'SoFi Technologies', 'fintech', 2400000000, 14000000000, 5.8, 0.34, '2026-01-15'),
    ('BILL', 'Bill.com', 'fintech', 1280000000, 8500000000, 6.6, 0.22, '2026-01-15');
```

## Common Queries

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
```
