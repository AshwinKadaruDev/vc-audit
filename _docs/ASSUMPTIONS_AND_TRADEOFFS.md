# Assumptions & Architecture Tradeoffs

This document combines core algorithm assumptions with architecture decisions. It serves as a reference for understanding the reasoning behind the system's design.

---

## Table of Contents

1. [Algorithm Assumptions](#algorithm-assumptions)
   - [Last Round Method](#last-round-method)
   - [Comparables Method](#comparables-method)
   - [Cross-Method Analysis](#cross-method-overall-valuation)
   - [Universal Assumptions](#universal-assumptions-all-methods)
2. [Architecture Tradeoffs](#architecture-tradeoffs)
   - [Backend Decisions](#backend-decisions)
   - [Frontend Decisions](#frontend-decisions)
3. [When Assumptions Are Violated](#when-assumptions-are-violated-what-to-do)
4. [Future Enhancements](#future-enhancements)
5. [References & Sources](#references--sources)

---

# Algorithm Assumptions

**Purpose**: Quick reference for all numerical parameters and assumptions in the valuation algorithms.

---

## Last Round Method

### Parameters

| Parameter | Value | Source/Justification |
|-----------|-------|---------------------|
| **Beta (Volatility Factor)** | 1.5 | Damodaran research (1.3-2.0 range), Korteweg & Sorensen (2010). Conservative mid-range. |
| **Market Index** | NASDAQ Composite | Growth-stock heavy, standard for VC marks (ILPA guidelines) |
| **Max Round Age** | 18 months | ILPA guidelines for quarterly marks. >18mo = stale |
| **HIGH Confidence Threshold** | ≤6 months | Quarterly mark standard (1-2 quarters = reliable) |
| **MEDIUM Confidence Threshold** | 7-12 months | Aging but usable, annual valuations common |
| **LOW Confidence Threshold** | >12 months | Stale, warning issued |

### Core Assumptions

1. **Last round was arms-length transaction at fair market value**
   - Multiple bidders, competitive process
   - NOT: insider round, bridge financing, distressed sale
   - If violated: Price is not representative baseline

2. **Company's risk profile correlates with chosen market index (NASDAQ)**
   - Company moves with tech/growth market
   - Beta of 1.5 assumes 1.5x market volatility
   - If violated: Market adjustment may over/understate true change

3. **No material changes since last round**
   - Company hasn't pivoted
   - No major milestone achieved or major setback
   - Business model remains same
   - If violated: Stale valuation unrelated to current reality

4. **Market indices are efficient and representative**
   - Public markets accurately price aggregate risk
   - NASDAQ represents growth company performance
   - If violated: Bubble/crash conditions make method unreliable

5. **Beta is constant across all companies and time periods**
   - All private companies have 1.5x volatility
   - Beta doesn't vary by sector, stage, or market regime
   - If violated: May overstate/understate volatility for specific companies

---

## Comparables Method

### Parameters

| Parameter | Value | Source/Justification |
|-----------|-------|---------------------|
| **Multiple Statistic** | Median | Robust to outliers, industry standard |
| **Private Company Discounts** | By stage (see below) | Damodaran research, Emory studies (20-40% range) |
| **Minimum Comparables** | 3 companies | Statistical validity, outlier detection |
| **HIGH Confidence (CV)** | <0.3 | Low variability, tight clustering |
| **MEDIUM Confidence (CV)** | 0.3-0.5 | Moderate dispersion |
| **LOW Confidence (CV)** | >0.5 | High dispersion, weak comparability |

### Private Company Illiquidity Discounts

| Stage | Discount | Rationale |
|-------|----------|-----------|
| **Seed** | 35% | 7-10 year horizon, highest risk, limited buyers |
| **Series A** | 30% | 5-7 year horizon, business model validation |
| **Series B** | 25% | 4-6 year horizon, product-market fit proven |
| **Series C** | 20% | 3-5 year horizon, scale-up phase |
| **Growth** | 15% | 1-3 year horizon, secondary markets active, near-IPO |

**Sources**:
- Damodaran: Marketability Discounts research (20-40% range for private equity)
- Emory Studies: Pre-IPO restricted stock discounts (avg 30%, range 20-50%)
- PitchBook: Median time-to-exit data by stage

### Core Assumptions

1. **Public comparables are truly comparable to target company**
   - Similar business model, market, customers, unit economics
   - Comparable growth trajectory and margin profile
   - If violated: Apples-to-oranges comparison produces meaningless result

2. **Revenue is a relevant value driver**
   - For pre-profit companies, assumes revenue scales to profit
   - Higher revenue → higher value
   - If violated: High revenue with no path to profitability → overvalued

3. **Private company discount is predictable based on stage**
   - Earlier stage → longer to liquidity → higher discount
   - Discount follows consistent pattern (35% → 15% as company matures)
   - If violated: Hot sectors (AI 2023) may trade at premium to public comps

4. **Public market multiples are sustainable and representative**
   - Current trading multiples reflect long-term fair value
   - NOT bubble (2000, 2021) or crash (2008, 2022) extremes
   - If violated: Public multiples inflated/depressed → mis-values private company

5. **Median is robust enough to handle comparable selection imperfections**
   - Some comps may be imperfect matches
   - Median filters out outliers and extremes
   - If violated: If ALL comps are bad, median still produces bad result

6. **Small sample size (3-10 companies) is sufficient**
   - Don't need 50+ companies for statistical validity
   - 3-10 well-selected comps better than 50 loosely related comps
   - If violated: Tiny, niche sectors may lack enough comps for validity

---

## Cross-Method (Overall Valuation)

### Parameters

| Parameter | Value | Justification |
|-----------|-------|---------------|
| **Spread Warning Threshold** | 30% | ASC 820 Fair Value Measurement, industry "reasonable range" |
| **Primary Method Selection** | Highest confidence | Most reliable method leads |
| **Tie-breaker** | Last Round (if confidence tied) | More recent transaction data |

### Core Assumptions

1. **Multiple methods provide validation**
   - Agreement → higher confidence in range
   - Disagreement → signals edge case or need for manual review
   - If violated: If all methods have same flaw, agreement is false confidence

2. **Methods are independent measures of value**
   - Last Round uses transaction data
   - Comparables uses public market data
   - Different data sources → true triangulation
   - If violated: If both methods rely on same underlying driver, not independent

3. **30% spread is meaningful threshold**
   - <30% = reasonable range, methods agree
   - >30% = material disagreement, investigation needed
   - If violated: In high-uncertainty environments, >30% spread may be normal

4. **Higher confidence method should be primary**
   - Confidence scoring is meaningful
   - HIGH confidence method more reliable than MEDIUM/LOW
   - If violated: If confidence scoring is wrong, primary selection is wrong

5. **System flags issues but doesn't replace judgment**
   - Auditor reviews all method results
   - Auditor can override primary method selection
   - System provides transparency, not final answer
   - If violated: If used as black box, may miss important context

---

## Universal Assumptions (All Methods)

### Going Concern
- **Assumption**: Company will continue operating as a going concern
- **NOT applicable**: Distressed companies, bankruptcies, liquidation scenarios
- **If violated**: Liquidation value or distressed asset valuation needed instead

### Data Accuracy
- **Assumption**: User-provided data is accurate
- **Inputs**: Revenue, funding round dates/amounts, sector classification
- **If violated**: Garbage in → garbage out (GIGO)
- **Mitigation**: Validate data against external sources (pitch decks, press releases)

### U.S. Market Context
- **Assumption**: Parameters calibrated to U.S. market
- **Applies to**: Beta, discounts, market indices
- **If violated**: International companies need local parameter adjustments
- **Examples**:
  - European companies: Lower beta (more stable markets), different discounts
  - Asian companies: Different liquidity horizons, different market dynamics

### Normal Market Conditions
- **Assumption**: Not in extreme bubble or crash
- **NOT applicable**: 2000 dot-com bubble, 2008 financial crisis, 2020 COVID crash, 2021 SPAC bubble
- **If violated**: All methods questionable, parameters need major adjustments
- **Examples**:
  - 2021: Public multiples 2-3x normal → Comparables method overvalues
  - 2022: Tech selloff, -70% NASDAQ → Last Round method undervalues

### Efficient Markets (Weak Form)
- **Assumption**: Public markets incorporate available information
- **Applies to**: Both market indices (Last Round) and public comps (Comparables)
- **If violated**: Mispricings in public markets propagate to private valuations
- **Note**: Doesn't require strong-form efficiency (insider info), just that prices aren't systematically wrong

---

## Parameters Quick Reference

### Easily Configurable (via `ValuationConfig`)

These can be changed without code modifications (see `backend/src/config.py`):

```python
ValuationConfig(
    default_beta=Decimal("1.5"),              # Volatility factor
    max_round_age_months=18,                  # Skip if older
    stale_round_threshold_months=12,          # Issue warning if older
    min_comparables=3,                        # Require at least N comps
    multiple_percentile=50,                   # 25=conservative, 50=median, 75=aggressive
    high_confidence_spread=Decimal("0.15"),   # Max spread for high confidence
    medium_confidence_spread=Decimal("0.30"), # Max spread for medium confidence
)
```

### Hard-Coded (requires code changes)

These are embedded in method logic:

| Parameter | Location | Value |
|-----------|----------|-------|
| Private discounts by stage | `methods/comps.py` | 35%/30%/25%/20%/15% |
| Confidence thresholds (Last Round) | `methods/last_round.py` | 6mo/12mo |
| Confidence thresholds (Comps CV) | `methods/comps.py` | 0.3/0.5 |
| Market index name | `methods/last_round.py` | "NASDAQ" |

**Why hard-coded?**
- Deeply researched values unlikely to change
- Making everything configurable adds complexity without value
- Can be extracted to config in future if needs arise

---

# Architecture Tradeoffs

This section captures key architectural decisions and their tradeoffs.

---

## Backend Decisions

### 1. JSONB vs Normalized Tables for Audit Trail

**Decision:** Pure JSONB for audit trail details, with key queryable fields extracted to columns on the main `valuations` table.

**Why Pure JSONB:**
- Primary use cases are: create valuation, view by ID, list by company - none require cross-valuation queries on method details
- Audit trails are read as a complete unit - JSONB is perfect for this
- Extracted columns (`primary_value`, `primary_method`, `overall_confidence`) cover the queries we actually need
- If analytics needs arise later, we can add a GIN index or denormalized table - but YAGNI for now
- Simpler write path = fewer failure modes at scale

**Tradeoff Accepted:** Can't efficiently query "all valuations where Comps method had warning X" without GIN index. Acceptable because this is an admin/analytics use case, not a core user flow.

---

### 2. Enums in Database vs Application-Level Validation

**Decision:** Use PostgreSQL ENUM types for constrained fields (confidence, stage, method_name).

**Why ENUMs:**
- Confidence levels (high/medium/low) are unlikely to change - stability favors ENUMs
- Company stages (seed, series_a, etc.) are industry-standard - stability favors ENUMs
- ENUMs are self-documenting in schema
- Prevents invalid data from any source (API, direct DB access, migrations)

**Tradeoff Accepted:** Adding new enum values requires a migration. Mitigated by: chosen fields are genuinely stable in the domain.

---

### 3. Input Snapshot vs Foreign Key Reference

**Decision:** Store full `input_snapshot` as JSONB in valuations table, with optional FK to portfolio_companies.

**Why Snapshot:**
- Audit requirement: "What inputs produced this valuation?" must be answerable years later
- Company data may be updated (new financials, corrected errors) - shouldn't change historical valuations
- Reproducibility: given the same inputs, system should produce same outputs (hash verification)

**Tradeoff Accepted:** Storage overhead from duplicating company data. Mitigated by: JSONB compresses well, and audit integrity is non-negotiable for this domain.

---

### 4. Concurrent I/O Strategy

**Decision:** Parallel fetches only where logically independent - comparables lookup and market index lookup can run concurrently.

**Where parallelism makes sense:**
- Fetching comparable companies (for Comps method)
- Fetching market index data (for Last Round method)
- These are independent data sources with no dependencies

**Where parallelism does NOT make sense:**
- Multiple queries to get comparables by sector - this should be ONE query with `WHERE sector = $1`
- Sequential valuation steps that depend on prior results

**Implementation:**
```python
async def get_valuation_data(sector: str, round_date: date) -> tuple[list[Comparable], list[IndexPoint]]:
    # Parallel fetch - these are independent
    comparables, index_data = await asyncio.gather(
        repo.get_comparables_by_sector(sector),  # ONE query
        repo.get_index_data_for_period(round_date, today),  # ONE query
    )
    return comparables, index_data
```

---

### 5. Pre-Seeded Test Companies

**Decision:** Seed 5 test portfolio companies via migrations for demo and testing purposes.

**Seeded companies (via `alembic/versions/0002_seed_portfolio_companies.py`):**
- **Basis AI** - Series A SaaS (healthy, recent round)
- **TechStart Inc** - Seed fintech (pre-revenue)
- **GrowthCo Analytics** - Series B SaaS (enterprise traction)
- **Legacy Tech** - Series A with stale round (18+ months old)
- **Stealth Labs** - Pre-revenue with no funding round

**Why seeding:**
- Enables immediate testing of all valuation scenarios
- Shows edge cases (pre-revenue, stale rounds, no rounds)
- Distinguishes from reference data (comparables/indices) which is also seeded

**Note:** Seed data for comparables/indices is different - that's reference data, not user data.

---

### 6. Sectors as Reference Table vs Enum

**Decision:** Use a `sectors` reference table with foreign keys, not an ENUM.

**Why reference table:**
- New sectors can be added without schema migration
- Each sector has associated comparable companies - natural FK relationship
- Can store metadata (display_name, description)
- API can return available sectors dynamically

**Contrast with confidence/stage:** Those are truly fixed domain concepts. Sectors are more like configurable reference data.

---

### 7. JSONB for Nested Company Data

**Decision:** Store `financials`, `last_round`, and `adjustments` as JSONB on `portfolio_companies`, not as separate columns or tables.

**Why JSONB:**
- Frontend already sends `{ financials: {...}, last_round: {...}, adjustments: [...] }` - direct mapping
- We don't query across companies by revenue_ttm or last_round_date - queries are always by company ID
- Nullable nested objects (pre-seed companies have no last_round) are natural in JSONB
- Adding new financial metrics doesn't require migrations
- Adjustments are a small array (0-5 items), always read with the company

---

### 8. SQLAlchemy ORM with CRUD Layer

**Decision:** Use SQLAlchemy 2.0 ORM with centralized CRUD layer.

**Architecture:**
```
database/
    database.py           # Engine, SessionLocal, get_db()
    crud.py              # ALL queries centralized
    models/
        base.py          # Base, IdMixin, TimestampMixin
        sector.py        # SQLAlchemy ORM models
        valuation.py
        portfolio_company.py
        ...

services/
    valuations.py        # Orchestration logic

api/
    routes.py            # Thin routes - HTTP concerns only
```

**Why SQLAlchemy ORM:**

1. **Production-Grade Connection Pooling:**
   - `pool_pre_ping=True` - Auto-detect stale connections
   - `pool_size=10`, `max_overflow=20` - Handles load spikes
   - `pool_recycle=3600` - Recycle connections every hour

2. **Type Safety with SQLAlchemy 2.0:**
   - Fully typed ORM models with `Mapped[]` annotations
   - No more dynamic row objects

3. **Centralized CRUD Layer:**
   - All queries in one file, easy to audit
   - Built-in N+1 query prevention with `selectinload()`

4. **Clean Separation of Concerns:**
   ```
   Routes (HTTP) → Services (orchestration) → CRUD (queries) → Models (ORM) → Database
   ```

**Tradeoffs Accepted:**
- Additional abstraction layer (but provides centralized query optimization)
- Larger dependency (~1.5 MB vs asyncpg ~200 KB) (but industry-standard with battle-tested patterns)
- Slight ORM overhead (~5-10%) (but N+1 prevention and pooling far outweigh cost)

---

## Frontend Decisions

### 9. TanStack Query for Server State

**Decision:** Use TanStack Query for all server state management.

**Why TanStack Query:**
- **Before:** Each page had ~15-20 lines of boilerplate (useState, useEffect, try/catch)
- **After:** Single hook call per page
- **Built-in caching:** Navigate away and back = instant load (no refetch)
- **Automatic invalidation:** When mutation succeeds, auto-refetch affected queries

**Tradeoff Accepted:** +13 KB gzipped bundle size (acceptable for the value and developer experience).

---

### 10. Flat Directory Structure

**Decision:** Keep flat structure (`components/`, `pages/`) instead of nested `ui/` folders.

**Why flat:**
- Only 8 components, 4 pages - not enough to justify deep nesting
- Easier to find files
- YAGNI - reorganize if project grows to 50+ components

---

### 11. CSS Variables for Theming

**Decision:** Add CSS variables for all colors, prepared for dark mode.

**Why CSS variables now:**
- Zero runtime cost (native CSS)
- Easier future dark mode implementation
- Semantic tokens (`success-600`, `error-600`) are clearer than raw colors

---

### 12. Centralized Utilities

**Decision:** Extract duplicate formatting/helper functions into `utils/` folder.

**Utilities created:**
- `utils/formatting.ts` - formatCurrency, formatDate, getMethodDisplayName
- `utils/confidence.ts` - getConfidenceBadgeClass, getConfidenceColor

**Result:** ~200 lines of duplicate code removed, single source of truth.

---

# When Assumptions Are Violated: What To Do

| Assumption Violated | Impact | Recommended Action |
|---------------------|--------|-------------------|
| Last round was inside/bridge round | Price below market | Skip Last Round method, use Comparables only |
| Company pivoted since round | Stale valuation | Skip Last Round method, document pivot |
| No good public comparables | Comparables unreliable | Use Last Round only, or manual valuation |
| Extreme market (bubble/crash) | All methods distorted | Apply manual adjustments, increase uncertainty |
| International company | U.S. parameters wrong | Adjust beta/discount for local market, use local indices |
| Pre-revenue startup | Comparables can't run | Last Round only (if available), else out of scope |
| Very early stage (<$500k ARR) | Both methods weak | Consider cost basis or option pricing methods instead |

---

# Future Enhancements

## Algorithm Refinement

### Short-term (Next Version)
1. **Sector-specific beta** - Tech: 1.8, Healthcare: 1.3, etc.
2. **Sector-specific market indices** - Healthcare uses Arca Biotech, not NASDAQ
3. **Revenue size filters for comparables** - Only compare to comps within 0.5-2.0x revenue range
4. **User override for discounts** - Let auditor specify custom discount with justification

### Long-term (Future Research)
1. **Dynamic beta calibration** - Historical analysis of private company returns vs. market
2. **Machine learning for comparable selection** - Multi-factor similarity scoring
3. **Scenario analysis** - Bull/base/bear cases with different parameter assumptions
4. **Time-series confidence** - Track valuation over time, flag anomalies
5. **Geographic parameter sets** - Pre-built configs for EU, Asia, LatAm markets

## Architecture Considerations

### If we needed to support:

**Multi-tenancy:** Add `tenant_id` to all tables, row-level security policies.

**Audit log immutability:** Consider append-only tables or event sourcing pattern.

**Real-time collaboration:** WebSocket layer, optimistic locking on valuations.

**ML-based valuation methods:** JSONB audit trail easily accommodates new method types without schema changes.

**Cross-valuation analytics:** Add GIN indexes on JSONB fields, or materialize a `valuation_methods` table.

---

# References & Sources

## Academic Research
- **Damodaran, A.** - "Marketability and Value: Measuring the Illiquidity Discount"
- **Korteweg & Sorensen (2010)** - "Risk and Return Characteristics of Venture Capital-Backed Entrepreneurial Companies"
- **Ewens, Peters & Wang (2021)** - "Measuring Intangible Capital with Market Prices"

## Industry Guidelines
- **ILPA Valuation Guidelines** - Institutional Limited Partners Association
- **ASC 820** - Fair Value Measurement (FASB Accounting Standards)
- **IPEV Guidelines** - International Private Equity and Venture Capital Valuation

## Empirical Studies
- **Emory Studies** - Pre-IPO Restricted Stock Discounts (1980-2000)
- **PitchBook Exit Timeline Data** - Median time-to-exit by stage and sector
- **SVB State of Markets Reports** - Quarterly VC/startup market data

## Market Data Sources
- **NASDAQ Composite Index** - Public market returns
- **Public company financials** - SEC EDGAR filings for comparables
- **VC funding data** - Crunchbase, PitchBook for last round information
