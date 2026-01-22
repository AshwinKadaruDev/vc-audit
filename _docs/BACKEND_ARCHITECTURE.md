# Backend Architecture Guide

This document explains the complete backend architecture, including the purpose of each folder and file, how data flows through the system, and where the core valuation logic lives.

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Folder Structure](#folder-structure)
3. [The Two "Data" Folders Explained](#the-two-data-folders-explained)
4. [File-by-File Breakdown](#file-by-file-breakdown)
5. [Data Flow](#data-flow)
6. [Database Operations](#database-operations)
7. [The Valuation Algorithm](#the-valuation-algorithm)

---

## High-Level Overview

```
backend/
├── alembic/           # Database migrations (schema + seed data)
├── data/              # JSON seed files (ONLY used during setup)
└── src/               # Application source code
    ├── api/           # HTTP endpoints (routes, request/response schemas)
    ├── database/      # SQLAlchemy models, CRUD operations, DataLoader, connection management
    ├── valuation/     # Valuation engine and methods (THE MAIN ALGORITHM)
    ├── middleware/    # HTTP middleware (logging, rate limiting)
    ├── services/      # Business logic layer
    └── utils/         # Helper functions (math, serialization, retry)
```

---

## Folder Structure

### `backend/alembic/` - Database Migrations

**Purpose:** Create database tables and seed initial data. Alembic is a database migration tool for SQLAlchemy.

| File | Purpose |
|------|---------|
| `alembic.ini` | Alembic configuration (database URL, logging) |
| `env.py` | Migration environment - connects to database, runs migrations |
| `versions/` | Individual migration scripts (numbered for ordering) |

**When it runs:** Only during `setup.ps1` or `alembic upgrade head` command.

**Migration files in `versions/`:**
- `20260116_0001_initial_schema.py` - Creates all database tables (sectors, portfolio_companies, comparable_companies, market_indices, valuations)
- `20260116_0002_seed_portfolio_companies.py` - Seeds initial test companies (legacy, now superseded by 0004)
- `20260122_0003_add_data_sources.py` - Adds source tracking columns to tables
- `20260122_0004_seed_from_json.py` - **Reads JSON files from `backend/data/` and inserts them into the database**

---

### `backend/data/` - JSON Seed Files (Setup Only)

**Purpose:** Store seed data that gets loaded into the database during setup. These files are **NEVER read at runtime** by the application.

```
backend/data/
├── companies/           # Test portfolio companies
│   ├── basis_ai.json
│   ├── techstart.json
│   ├── growthco.json
│   ├── prerevenue_no_round.json
│   └── old_round.json
├── comparables/         # Public company reference data
│   ├── saas.json
│   └── fintech.json
└── market/
    └── indices.json     # Market index time series (NASDAQ, S&P500)
```

**How it works:**
1. You run `setup.ps1` (or `alembic upgrade head`)
2. Migration `0004_seed_from_json.py` reads these JSON files
3. Data is inserted/updated in PostgreSQL tables
4. Application runs - **reads from database, NOT from these files**

**Why this design?**
- Single source of truth for seed data (easy to edit JSON)
- Database provides querying, indexing, relationships
- JSON files are human-readable for debugging

---

### `backend/src/` - Application Source Code

This is where all the runtime application code lives.

---

## The "Data" Folder Explained

| Folder | Purpose | When Used | What It Does |
|--------|---------|-----------|--------------|
| `backend/data/` | JSON seed files | **Setup only** | Stores test data as JSON files |

### `backend/data/` (JSON Files)
- Contains `.json` files with test companies, comparables, market indices
- **Only read by Alembic migrations** during database setup
- If you want to add a new test company, add a JSON file here and re-run migrations

The `DataLoader` class (which reads from PostgreSQL at runtime) lives in `backend/src/database/loader.py`.

```
┌─────────────────────────────────────────────────────────────────┐
│                         SETUP TIME                               │
│                                                                  │
│   backend/data/*.json  ──→  Alembic Migration  ──→  PostgreSQL  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                        (database now has data)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         RUNTIME                                  │
│                                                                  │
│   API Request  ──→  DataLoader  ──→  PostgreSQL  ──→  Response  │
│                     (src/database/)                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File-by-File Breakdown

### Root Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables (DATABASE_URL, etc.) |

---

### `backend/src/` - Main Application

#### `src/main.py` - Application Entry Point

**Responsibility:** Creates and configures the FastAPI application.

```python
# What it does:
1. Initializes database connection on startup (lifespan)
2. Adds middleware (logging, CORS, rate limiting)
3. Mounts API routes at /api prefix
4. Runs with uvicorn when executed directly
```

**Key functions:**
- `create_app()` - Factory function that builds the FastAPI app
- `lifespan()` - Async context manager for startup/shutdown (database init)

---

#### `src/config.py` - Configuration Management

**Responsibility:** Loads settings from environment variables and defines valuation config.

**Key classes:**
- `Settings` - Environment-based config (DATABASE_URL, CORS_ORIGINS, etc.)
- `ValuationConfig` - Algorithm parameters (frozen/immutable)

```python
ValuationConfig:
  max_round_age_months: 18      # Max age for last round to be valid
  stale_round_threshold_months: 12  # When to warn about stale round
  default_beta: 1.5             # Market volatility multiplier
  min_comparables: 3            # Minimum comparable companies required
  multiple_percentile: 50       # Use median (50th percentile)
  high_confidence_spread: 0.15  # <15% spread = high confidence
  medium_confidence_spread: 0.30 # <30% spread = medium confidence
```

---

#### `src/models.py` - Domain Models (Pydantic)

**Responsibility:** Defines all data structures used throughout the application.

**Key models:**
- `Company`, `Financials`, `LastRound`, `Adjustment` - Input data
- `CompanyData` - Complete company input bundle
- `MethodResult` - Output from a valuation method
- `ValuationResult` - Complete valuation output with audit trail
- `AuditStep` - Single calculation step for transparency

---

#### `src/exceptions.py` - Custom Exceptions

**Responsibility:** Defines application-specific errors.

```python
ValuationError (base)
├── DataNotFoundError      # Company/sector not found
├── DataValidationError    # Input validation failed
├── DataLoadError          # Database read failed
├── InsufficientDataError  # Missing required fields
├── NoValidMethodsError    # No methods can run
└── CalculationError       # Math error during valuation
```

---

### `backend/src/api/` - HTTP Layer

#### `src/api/routes.py` - API Endpoints

**Responsibility:** Defines all HTTP endpoints and handles request/response.

**Key endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/companies` | GET | List test companies |
| `/api/sectors` | GET | List available sectors |
| `/api/indices` | GET | List market indices |
| `/api/valuations` | POST | Run valuation by company ID |
| `/api/valuations/custom` | POST | Run with custom company data |
| `/api/valuations/run-and-save` | POST | Run and persist to database |
| `/api/valuations/saved` | GET | List saved valuations |
| `/api/valuations/saved/{id}` | GET | Get specific valuation |
| `/api/valuations/saved/{id}` | DELETE | Delete valuation |
| `/api/portfolio-companies` | GET | List portfolio companies |
| `/api/portfolio-companies/random` | GET | Get random company |

**Dependency injection:** Routes use `Depends(get_db)` to get database sessions.

---

#### `src/api/schemas.py` - Request/Response Schemas

**Responsibility:** Pydantic models for API validation and serialization.

- `ValuationRequest` - Input for POST /valuations
- `CustomValuationRequest` - Input for POST /valuations/custom
- `ValuationResponse` - Output format for valuations

---

### `backend/src/database/` - Database Layer

#### `src/database/database.py` - Connection Management

**Responsibility:** Creates and manages SQLAlchemy database connections.

**Two connection types:**
1. **Async (asyncpg)** - Used by FastAPI routes for non-blocking I/O
2. **Sync (psycopg2)** - Used by DataLoader for blocking operations

**Key functions:**

```python
# Async (for routes)
async def get_db() -> AsyncSession
    # FastAPI dependency - yields session, auto-commits/rollbacks

# Sync (for DataLoader)
def get_sync_db() -> Session
    # Context manager for sync operations
```

**Lifecycle:**
1. `main.py` calls `create_engine()` on startup
2. Engine stored globally via `set_engine()`
3. Session factory created via `create_session_factory()`
4. Routes use `Depends(get_db)` to get sessions
5. Engine disposed on shutdown

---

#### `src/database/crud.py` - CRUD Operations

**Responsibility:** All database read/write operations. Keeps SQL logic separate from business logic.

**Key functions:**

```python
# Sectors
get_all_sectors(db) -> list[Sector]
get_sector_by_id(db, sector_id) -> Sector | None

# Portfolio Companies
create_portfolio_company(db, data) -> PortfolioCompany
list_portfolio_companies(db, limit) -> list[PortfolioCompany]
get_portfolio_company_by_id(db, id) -> PortfolioCompany | None

# Valuations
create_valuation(db, data) -> Valuation
list_recent_valuations(db, limit) -> list[Valuation]
get_valuation_by_id(db, id) -> Valuation | None
delete_valuation(db, id) -> bool

# Reference Data
get_comparables_by_sector(db, sector) -> list[ComparableCompany]
get_market_index_time_series(db, name) -> list[MarketIndex]
```

**Sync variants:** Most functions have `_sync` versions for DataLoader (e.g., `get_all_sectors_sync`).

---

#### `src/database/loader.py` - DataLoader Class

**Responsibility:** Loads data from PostgreSQL at runtime. This is the **only** place where business logic reads data.

**Key methods:**

```python
class DataLoader:
    def list_companies() -> list[dict]
        # Lists all portfolio companies from database

    def load_company(company_id: str) -> CompanyData
        # Loads full company data for valuation

    def load_comparables(sector: str) -> ComparableSet
        # Loads public company comparables by sector
        # CACHED after first load

    def load_indices() -> dict[str, list[MarketIndex]]
        # Loads market index time series
        # CACHED after first load

    def get_index(name: str) -> list[MarketIndex]
        # Gets specific index (e.g., "NASDAQ")
```

**Important:** Uses **synchronous** database sessions because valuation methods are not async.

---

#### `src/database/models/` - SQLAlchemy ORM Models

**Responsibility:** Define database table structures.

| File | Table | Purpose |
|------|-------|---------|
| `base.py` | - | Base class with mixins (IdMixin, TimestampMixin) |
| `sector.py` | `sectors` | Reference data: saas, fintech, etc. |
| `portfolio_company.py` | `portfolio_companies` | Companies to value (JSONB for financials) |
| `comparable_company.py` | `comparable_companies` | Public company reference data |
| `market_index.py` | `market_indices` | Time series market data |
| `valuation.py` | `valuations` | Saved valuation results with audit trail |

**JSONB columns:** `portfolio_companies` stores `financials`, `last_round`, `adjustments` as JSONB for flexibility.

---

### `backend/src/valuation/` - Valuation Engine and Methods ⭐ CORE ALGORITHM

#### `src/valuation/engine.py` - ValuationEngine Class

**Responsibility:** This is the **main orchestration logic** that runs valuations.

**How it works:**

```python
class ValuationEngine:
    def run(company_id: str) -> ValuationResult:
        # 1. Load company data from database
        # 2. Call run_with_data()

    def run_with_data(company_data: CompanyData) -> ValuationResult:
        # 1. Create all registered valuation methods
        methods = MethodRegistry.create_all(company_data, config, loader)

        # 2. Run each method
        for method in methods:
            result = method.run()  # Returns MethodResult or MethodSkipped

        # 3. Compare results across methods
        cross_analysis = self._compare_methods(results)

        # 4. Generate summary (pick primary, calculate range)
        summary = self._summarize(results, cross_analysis)

        # 5. Return complete result with audit trail
        return ValuationResult(...)
```

**Method selection logic:**
1. Sort by confidence (HIGH > MEDIUM > LOW)
2. If tied, prefer Last Round (real transaction) over Comparables (estimate)
3. Calculate spread between methods
4. Adjust overall confidence if methods disagree >30%

---

#### `src/valuation/base.py` - Base Class and Registry

**Responsibility:** Defines the interface all valuation methods must implement.

```python
class ValuationMethod(ABC):
    @abstractmethod
    def check_prerequisites() -> Optional[str]:
        # Return None if can run, or reason string if cannot

    @abstractmethod
    def execute() -> MethodResult:
        # Perform the valuation calculation

    def run() -> MethodResult | MethodSkipped:
        # Calls check_prerequisites(), then execute()
        # Handles errors, builds audit trail

    def _add_step(step: AuditStep):
        # Adds step to audit trail for transparency

    def _apply_company_adjustments():
        # Applies user-provided adjustment factors
```

**MethodRegistry:** Decorator-based registration system.

```python
@MethodRegistry.register
class LastRoundMethod(ValuationMethod):
    ...

# Later, create all registered methods:
methods = MethodRegistry.create_all(company_data, config, loader)
```

---

#### `src/valuation/last_round.py` - Last Round Method ⭐

**Responsibility:** Values company based on most recent funding round.

**Algorithm:**
```
1. Check prerequisites:
   - Has last round data?
   - Round < 18 months old?
   - Market index available?

2. Anchor value = Post-money valuation from funding round

3. Market adjustment:
   - Get market return since funding date
   - market_factor = 1 + (market_return × beta)
   - Adjusted value = Anchor × market_factor

4. Company adjustments (user-provided factors):
   - For each adjustment: value = value × factor

5. Determine confidence:
   - HIGH if round ≤ 6 months old
   - MEDIUM if round ≤ 12 months old
   - LOW if round > 12 months old

6. Build audit trail with each step
```

---

#### `src/valuation/comps.py` - Comparables Method ⭐

**Responsibility:** Values company based on public company multiples.

**Algorithm:**
```
1. Check prerequisites:
   - Has revenue data?
   - Sector has ≥ 3 comparable companies?

2. Load comparables for sector

3. Calculate median EV/Revenue multiple from comparables

4. Apply private company discount (stage-based):
   - seed: 35%
   - series_a: 30%
   - series_b: 25%
   - series_c: 20%
   - growth: 15%

5. Calculate value:
   - Value = Revenue × (Multiple × (1 - Discount))

6. Company adjustments (user-provided factors)

7. Determine confidence based on multiple dispersion:
   - LOW std dev = HIGH confidence
   - HIGH std dev = LOW confidence

8. Build audit trail with each step
```

---

### `backend/src/services/` - Business Logic Layer

#### `src/services/valuations.py` - Valuation Service

**Responsibility:** Coordinates between routes and engine, handles persistence.

```python
async def run_and_save_valuation(company_data, db):
    # 1. Run the valuation engine
    result = engine.run_with_data(company_data)

    # 2. Convert result to JSON-serializable format
    result_dict = convert_result_for_response(result)

    # 3. Save to database
    valuation = await crud.create_valuation(db, {
        "company_name": result.company_name,
        "input_snapshot": company_data.model_dump(),
        "input_hash": sha256(input_json),
        "primary_value": result.summary.primary_value,
        ...
    })

    # 4. Return result + valuation ID
    return result_dict, valuation.id
```

---

#### `src/services/portfolio_companies.py` - Portfolio Company Service

**Responsibility:** Business logic for portfolio company operations.

```python
async def get_random_company(db) -> PortfolioCompany | None:
    # Returns a random portfolio company for testing
```

---

### `backend/src/middleware/` - HTTP Middleware

#### `src/middleware/logging_middleware.py`

**Responsibility:** Logs all HTTP requests and responses.

```
INFO: POST /api/valuations/run-and-save 200 OK (234ms)
```

#### `src/middleware/rate_limit.py`

**Responsibility:** Rate limiting in production (per-IP request limits).

---

### `backend/src/utils/` - Utility Functions

| File | Purpose |
|------|---------|
| `math_utils.py` | `format_currency()`, `round_decimal()`, `median()`, `percentile()` |
| `serialization.py` | `make_json_serializable()` - converts Decimal, date, Enum for JSON |
| `retry.py` | `@async_retry_on_exception` decorator for transient failures |

---

## Data Flow

### Complete Request Flow: POST /api/valuations/run-and-save

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. HTTP Request arrives at FastAPI                                       │
│    POST /api/valuations/run-and-save                                    │
│    Body: { company: {...}, financials: {...}, last_round: {...} }       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. routes.py: run_and_save_valuation()                                  │
│    - Validates request with Pydantic schema                             │
│    - Gets database session via Depends(get_db)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. services/valuations.py: run_and_save_valuation()                     │
│    - Creates ValuationEngine                                            │
│    - Calls engine.run_with_data(company_data)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. engine/engine.py: ValuationEngine.run_with_data()                    │
│    - Creates all registered methods                                      │
│    - For each method: method.run()                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ 5a. LastRoundMethod.run()     │   │ 5b. ComparablesMethod.run()   │
│     - check_prerequisites()   │   │     - check_prerequisites()   │
│     - execute()               │   │     - execute()               │
│     - Build audit trail       │   │     - Load comparables from DB│
│     - Load market index from  │   │     - Calculate median        │
│       database (DataLoader)   │   │     - Apply discount          │
└───────────────────────────────┘   └───────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. engine/engine.py: Compare methods, generate summary                  │
│    - Calculate spread between methods                                   │
│    - Select primary (highest confidence)                                │
│    - Adjust overall confidence if disagreement                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 7. services/valuations.py: Save to database                             │
│    - Convert result to JSON-serializable                                │
│    - Hash input for reproducibility                                     │
│    - crud.create_valuation() → PostgreSQL                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 8. HTTP Response                                                        │
│    { valuation_id: "uuid", result: { summary: {...}, ... } }           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Database Operations

### Reading Data

**Routes (async):**
```python
@router.get("/sectors")
async def get_sectors(db: AsyncSession = Depends(get_db)):
    sectors = await crud.get_all_sectors(db)
    return [s.id for s in sectors]
```

**DataLoader (sync):**
```python
def load_comparables(self, sector: str) -> ComparableSet:
    with get_sync_db() as db:
        companies = crud.get_comparables_by_sector_sync(db, sector)
    return ComparableSet(companies=companies, ...)
```

### Writing Data

```python
# In services/valuations.py
async def run_and_save_valuation(company_data, db):
    ...
    valuation = await crud.create_valuation(db, {
        "company_name": result.company_name,
        "primary_value": result.summary.primary_value,
        "method_results": serialize(result.method_results),
        ...
    })
```

---

## The Valuation Algorithm

### Summary

The system implements two valuation methods:

1. **Last Round** - Based on actual funding transaction
   - Uses post-money valuation as anchor
   - Adjusts for market movement since funding
   - High confidence for recent rounds

2. **Comparables** - Based on public company multiples
   - Uses EV/Revenue multiples from sector peers
   - Applies private company discount
   - Works when no recent funding

### Method Selection

```
IF both methods run:
    - Compare confidence levels
    - If equal confidence, prefer Last Round (real transaction)
    - Calculate spread between values
    - If spread > 30%, flag for review (LOW confidence)

IF only one method runs:
    - Use that method's result
    - Confidence = that method's confidence
```

### Audit Trail

Every calculation step is recorded in `AuditStep` objects:
- Description of what's being calculated
- Input values used
- Formula or calculation performed
- Result produced
- Data source citation

This creates a complete, reproducible audit trail stored as JSONB in the database.

---

## Quick Reference

| Need to... | Look in... |
|------------|------------|
| Add an API endpoint | `src/api/routes.py` |
| Change valuation logic | `src/valuation/engine.py` |
| Modify Last Round method | `src/valuation/last_round.py` |
| Modify Comparables method | `src/valuation/comps.py` |
| Add a new valuation method | Create file in `src/valuation/`, use `@MethodRegistry.register` |
| Change database schema | Create new migration in `alembic/versions/` |
| Add seed data | Add JSON to `backend/data/`, re-run migrations |
| Change config defaults | `src/config.py` |
| Add a database query | `src/database/crud.py` |
