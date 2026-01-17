# VC Audit Tool

A production-ready portfolio valuation platform for VC auditors to estimate fair values of private, illiquid portfolio companies. Implements multiple valuation methodologies with comprehensive audit trails for compliance and reproducibility.

## Overview

Private companies lack readily available market prices and often have sparse financial data. The VC Audit Tool provides:

- **Multiple Valuation Methods**: Last Round (market-adjusted) and Comparable Companies, with extensible architecture
- **Full Audit Trail**: Every calculation step documented with inputs, formulas, and results for compliance
- **Reproducibility**: SHA256 input hashing and configuration snapshots ensure verifiable results
- **Graceful Degradation**: Methods that lack required data are skipped rather than causing failures
- **Database Persistence**: Save valuations with full input snapshots for historical reference

## Core Valuation Algorithms

### 1. Last Round (Market-Adjusted) Valuation

Values the company based on its last funding round, adjusted for market movements and company-specific factors.

**Process**:
1. **Anchor Value**: Uses last funding round post-money valuation as starting point
2. **Market Adjustment**: Applies market index change (e.g., NASDAQ) since funding round with volatility factor (beta = 1.5 for early-stage)
3. **Company Adjustments**: Applies user-defined adjustment factors (e.g., +10% for strong team, -15% for competitive pressure)
4. **Confidence**: HIGH if round ≤6 months, MEDIUM if ≤12 months, LOW if >12 months

**Prerequisites**: Last funding round ≤18 months old, market index data available

### 2. Comparable Companies Valuation

Values the company based on revenue multiples from public comparable companies in the same sector.

**Process**:
1. **Load Comparables**: Fetch public companies in same sector (minimum 3 required)
2. **Calculate Multiple**: Compute median EV/Revenue multiple from comparables
3. **Private Discount**: Apply stage-based discount (40% for Seed, 35% for Series A, 30% for Series B, etc.)
4. **Valuation**: Company revenue × adjusted multiple

**Prerequisites**: Company has revenue >$0, sector has ≥3 comparable companies

### Cross-Method Analysis

When multiple methods run successfully, the engine:
- Calculates spread between methods
- Selects primary method based on highest confidence
- Documents selection reasoning in audit trail
- Flags high variance (>30% spread) as warning

## Technology Stack

**Backend**:
- **FastAPI** - Modern Python web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation

**Frontend**:
- **React 18** with TypeScript
- **React Router v6** - SPA routing
- **TanStack Query v5** - Server state management
- **Tailwind CSS** - Styling
- **Vite** - Build tool

## Project Structure

### Backend (`backend/src/`)

```
src/
├── main.py                    # FastAPI app initialization
├── config.py                  # Environment settings
├── models.py                  # Pydantic domain models
│
├── api/
│   ├── routes.py             # REST endpoints (thin HTTP layer)
│   └── schemas.py            # Request/response models
│
├── engine/
│   └── engine.py             # Valuation orchestration
│
├── methods/
│   ├── base.py               # ValuationMethod base class + registry
│   ├── last_round.py         # Last Round implementation
│   └── comps.py              # Comparables implementation
│
├── database/
│   ├── database.py           # SQLAlchemy setup + connection pooling
│   ├── crud.py               # Centralized database operations
│   └── models/               # ORM models (Valuation, PortfolioCompany, etc.)
│
├── services/
│   ├── portfolio_companies.py # Company business logic
│   └── valuations.py          # Valuation service orchestration
│
└── utils/
    ├── math_utils.py         # Currency formatting, decimal rounding
    ├── serialization.py      # JSON helpers
    └── retry.py              # Async retry decorator
```

### Frontend (`frontend/src/`)

```
src/
├── main.tsx                  # React entry point
├── App.tsx                   # Router setup
│
├── pages/
│   ├── NewValuationPage.tsx        # Create new valuation
│   ├── ValuationDetailPage.tsx     # View saved valuation
│   └── ValuationsListPage.tsx      # List all valuations
│
├── components/
│   ├── CompanyForm.tsx       # Input form for company data
│   ├── CompanySelector.tsx   # Load company from database
│   ├── ValuationCard.tsx     # Summary display
│   └── AuditTrail.tsx        # Detailed calculation steps viewer
│
├── hooks/
│   ├── queries/              # TanStack Query hooks (fetch data)
│   └── mutations/            # TanStack Query mutations (write data)
│
└── api/
    ├── companies.ts          # Company endpoints
    ├── portfolioCompanies.ts # Portfolio company endpoints
    └── valuations.ts         # Valuation endpoints
```

### Documentation (`_docs/`)

- `000_problem_statement.md` - Original requirements
- `000_vc-audit-tool.md` - Detailed design document
- `SCHEMA.md` - Database schema explanation
- `TRADEOFFS.md` - Architecture decisions and tradeoffs
- `TANSTACK_QUERY_EXPLAINED.md` - Frontend state management

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** - Python package manager
- **[Node.js](https://nodejs.org/)** 18+
- **[PostgreSQL](https://www.postgresql.org/)** running locally

## Setup Instructions

### 1. Create PostgreSQL Database

```bash
psql -U postgres -c "CREATE DATABASE vc_audit;"
```

**Important**: The database name must be `vc_audit` for the default configuration to work.

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your PostgreSQL credentials:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/vc_audit
```

Additional configuration options (all have sensible defaults):
- **Database pool settings**: Connection pooling, timeouts, recycling
- **Logging**: Level (DEBUG/INFO/WARNING/ERROR), format (text/JSON)
- **Rate limiting**: Requests per IP, time window
- **Retry logic**: Max attempts, delays for transient failures
- **Environment**: development/production mode

See `backend/.env.example` for detailed documentation of all settings.

### 3. Run Setup Script

The setup script will:
1. Install Python dependencies with `uv sync`
2. Run Alembic migrations to create database tables
3. Seed test data (companies, comparables, market indices)
4. Install frontend dependencies with `npm install`

**Windows (PowerShell)**:
```powershell
.\setup.ps1
```

**Mac/Linux**:
```bash
chmod +x setup.sh run.sh
./setup.sh
```

**What Alembic Does**:
- Creates all database tables (portfolio_companies, valuations, sectors, comparable_companies, market_indices)
- Creates PostgreSQL ENUM types for confidence levels, stages, methods
- Seeds initial reference data
- All migrations are in `backend/alembic/versions/`

## Running the Application

### Start Both Backend and Frontend

**Windows (PowerShell)**:
```powershell
.\run.ps1
```

**Mac/Linux**:
```bash
./run.sh
```

### Start Individual Services

```bash
./run.sh backend    # Backend only (port 8000)
./run.sh frontend   # Frontend only (port 5173)
./run.sh migrate    # Run migrations only
```

### Access URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/companies` | GET | List test companies (for demo) |
| `/sectors` | GET | List comparable sectors |
| `/indices` | GET | List market indices |

### Valuation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /valuations` | POST | Run valuation by company ID, then save to database |
| `POST /valuations/custom` | POST | Run valuation with custom data (no database save) |
| `POST /valuations/batch` | POST | Batch valuations |
| `GET /valuations` | GET | List all saved valuations |
| `GET /valuations/{id}` | GET | Get valuation detail with full audit trail |
| `DELETE /valuations/{id}` | DELETE | Delete valuation |

### Portfolio Company Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /portfolio-companies` | GET | List all portfolio companies |
| `POST /portfolio-companies` | POST | Create portfolio company |
| `POST /portfolio-companies/random` | POST | Get random existing company (for testing) |

## Design Decisions and Tradeoffs

Key architectural decisions documented in `_docs/TRADEOFFS.md`:

1. **JSONB vs Normalized Tables**: Audit trail stored as JSONB for simplicity and auditability. Extracted columns (primary_value, confidence) for common queries.

2. **PostgreSQL ENUMs**: Used for stable domain types (confidence, stage, method) for type safety and query efficiency.

3. **Input Snapshots**: Full company data stored with each valuation (JSONB) for reproducibility, despite storage overhead.

4. **SQLAlchemy ORM**: Migrated from asyncpg for type safety, production-grade connection pooling, and N+1 query prevention.

5. **TanStack Query**: Frontend uses industry-standard server state management for automatic caching and invalidation.

6. **Method Registry Pattern**: Extensible architecture using decorators - add new valuation methods without modifying engine code.

7. **Decimal for Money**: All monetary values use Python `Decimal` to avoid floating-point precision issues.

8. **Immutable Config**: `ValuationConfig` is frozen (Pydantic) to ensure reproducibility.

See `_docs/TRADEOFFS.md` for detailed analysis of each decision.

## How to Use

### 1. Create a New Valuation

Navigate to http://localhost:5173/valuations/new

**Option A: Load Existing Company**
1. Click "Load from database" dropdown
2. Select a portfolio company
3. Modify data if needed
4. Click "Run Valuation"

**Option B: Enter Custom Data**
1. Fill out company form (name, sector, stage, financials)
2. Optionally add last funding round data
3. Optionally add adjustment factors
4. Click "Run Valuation"

**Option C: Use Test Data**
1. Click "Randomize" to load test company
2. Click "Run Valuation"

### 2. Review Results

The system will display:
- **Valuation Card**: Summary with primary value, confidence, and method used
- **Audit Trail**: Expandable sections for each method showing:
  - Every calculation step with inputs and formulas
  - Warnings (if any)
  - Reason why method was selected as primary
- **Skipped Methods**: Methods that couldn't run and why

### 3. Save Valuation (Optional)

Click "Save Valuation" to store in database. The system saves:
- Full input snapshot (for reproducibility)
- Complete audit trail
- Input hash (SHA256) for verification
- Configuration snapshot

### 4. View Saved Valuations

Navigate to http://localhost:5173/valuations to see all saved valuations. Click any valuation to view full details.

## Adding New Valuation Methods

The method registry pattern makes adding new methods straightforward:

1. **Create new file** in `backend/src/methods/new_method.py`

```python
from decimal import Decimal
from typing import Optional
from src.methods.base import MethodRegistry, ValuationMethod
from src.models import MethodName, MethodResult, Confidence

@MethodRegistry.register
class NewMethod(ValuationMethod):
    method_name = MethodName.NEW_METHOD  # Add to MethodName enum first

    def check_prerequisites(self) -> Optional[str]:
        """Return None if method can run, or reason string if not."""
        if not self.company_data.some_required_field:
            return "Missing required data for new method"
        return None

    def execute(self) -> MethodResult:
        """Run valuation and return result."""
        # Add calculation steps to audit trail
        self._add_step(
            description="Step 1: Calculate base value",
            inputs={"revenue": "$10M"},
            calculation="revenue × 5",
            result="$50M"
        )

        # More steps...

        return MethodResult(
            method=self.method_name,
            value=Decimal("50000000"),
            confidence=Confidence.MEDIUM,
            audit_trail=self._audit_steps,
            warnings=[]
        )
```

2. **Add to MethodName enum** in `src/models.py`:

```python
class MethodName(str, Enum):
    LAST_ROUND = "last_round"
    COMPARABLES = "comparables"
    NEW_METHOD = "new_method"  # Add here
```

3. **Import in engine.py** to register:

```python
from src.methods import last_round, comps, new_method  # noqa: F401
```

The engine will automatically discover and run your new method!

## Database Schema

### Key Tables

- **`valuations`**: Saved valuation results with full audit trail (JSONB)
- **`portfolio_companies`**: User-created companies with financials
- **`sectors`**: Reference table for comparable sectors
- **`comparable_companies`**: Public company data with multiples
- **`market_indices`**: Time-series market index data (NASDAQ, S&P500)

All tables use UUIDs as primary keys. See `_docs/SCHEMA.md` for detailed schema documentation.

### Reproducibility Features

Every valuation stores:
- `input_snapshot` (JSONB): Full company data used
- `input_hash` (VARCHAR): SHA256 hash for verification
- `config_snapshot` (JSONB): All configuration parameters
- `method_results` (JSONB): Complete audit trail
- Extracted columns: `primary_value`, `primary_method`, `overall_confidence` for efficient queries

## Running Tests

```bash
cd backend
uv run pytest              # Run all tests
uv run pytest -v           # Verbose output
uv run pytest --cov=src    # With coverage report
```

Test configuration in `backend/pyproject.toml`. Tests cover:
- CRUD operations
- Valuation engine
- Individual methods
- Rate limiting
- Retry logic
- Serialization

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ CompanyForm  │  │ ValuationCard│  │    AuditTrail        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                    TanStack Query (caching, invalidation)       │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP/JSON
┌───────────────────────────────▼─────────────────────────────────┐
│                      API Layer (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /valuations  /portfolio-companies  /sectors  /health    │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     Valuation Engine                            │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐   │
│  │ Run Methods    │  │ Compare Results│  │ Generate Summary│   │
│  └────────────────┘  └────────────────┘  └─────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     Method Registry                             │
│  ┌────────────────────────┐  ┌────────────────────────────┐    │
│  │ LastRoundMethod        │  │ ComparablesMethod          │    │
│  │ - Market adjustment    │  │ - Multiple statistics      │    │
│  │ - Company adjustments  │  │ - Private discount         │    │
│  │ - Confidence scoring   │  │ - Confidence scoring       │    │
│  └────────────────────────┘  └────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│              Database Layer (SQLAlchemy + PostgreSQL)           │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────────┐ │
│  │  Valuations  │ │  Portfolio   │ │  Comparables + Indices  │ │
│  │  (JSONB)     │ │  Companies   │ │  (Reference Data)       │ │
│  └──────────────┘ └──────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Test Companies

The seed migration includes test companies demonstrating different scenarios:

| Company | Revenue | Last Round | Expected Methods |
|---------|---------|------------|------------------|
| `basis_ai` | $10M | 9 months ago | Both methods |
| `techstart` | None | 7 months ago | Last Round only |
| `growthco` | $25M | 19 months ago | Both (with staleness warning) |
| `prerevenue_no_round` | None | None | Error - no valid methods |
| `old_round` | $5M | 36 months ago | Comparables only |

## Future Enhancements

- **Additional Methods**: DCF (Discounted Cash Flow), Option Pricing Model
- **Historical Analysis**: Compare valuations over time, track trends
- **Export**: Generate PDF reports, Excel exports
- **User Authentication**: Multi-user support with roles
- **Batch Processing**: Progress tracking for large portfolios
- **Method Weighting**: User-customizable method preference and weighting

## Contributing

See `_docs/` folder for detailed design documentation and architectural decisions.
