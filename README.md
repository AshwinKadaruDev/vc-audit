# VC Audit Tool

A full-stack portfolio valuation tool demonstrating clean architecture, audit trails, and reproducibility.

## Features

- **Multiple Valuation Methods**: Last Round (with market adjustment) and Comparable Companies
- **Full Audit Trail**: Every calculation step is documented with inputs, formulas, and results
- **Method Registry Pattern**: Extensible architecture for adding new valuation methods
- **Input Hashing**: SHA256 hash for reproducibility verification
- **Configuration Snapshots**: Full config captured with each valuation
- **Graceful Degradation**: Missing data skips methods instead of failing

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager
- [Node.js](https://nodejs.org/) 18+
- [PostgreSQL](https://www.postgresql.org/) running locally

## Quick Start

### 1. Clone the repository

```bash
git clone <repo-url>
cd vc-audit-tool
```

### 2. Create the PostgreSQL database

```sql
CREATE DATABASE vc_audit;
```

### 3. Configure environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your PostgreSQL credentials:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/vc_audit
```

The `.env` file includes additional configuration options for:
- **Database pool settings** (connection pooling, timeouts)
- **Logging** (level, format - text or JSON)
- **Rate limiting** (requests per IP, time window)
- **Retry logic** (max attempts, delays for transient failures)
- **Environment** (development/production mode)

All settings have sensible defaults. See `backend/.env.example` for detailed documentation.

### 4. Run setup

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**Mac/Linux:**
```bash
chmod +x setup.sh run.sh
./setup.sh
```

This installs all dependencies and runs database migrations.

### 5. Start the application

**Windows (PowerShell):**
```powershell
.\run.ps1
```

**Mac/Linux:**
```bash
./run.sh
```

### URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ CompanySelect│  │ ValuationCard│  │    AuditTrail        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP/JSON
┌───────────────────────────────▼─────────────────────────────────┐
│                      API Layer (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/valuations  /api/companies  /api/health            │  │
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
│  └────────────────────────┘  └────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     Data Layer                                  │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ Companies     │  │ Market Indices │  │ Comparables      │   │
│  └───────────────┘  └────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/companies` | GET | List all companies |
| `/api/sectors` | GET | List comparable sectors |
| `/api/indices` | GET | List market indices |
| `/api/valuations` | POST | Run single valuation |
| `/api/valuations/batch` | POST | Run batch valuation |
| `/api/companies/{id}` | GET | Get company data (debug) |
| `/api/comparables/{sector}` | GET | Get comparables (debug) |

## Test Companies

| Company | Revenue | Last Round | Expected Methods |
|---------|---------|------------|------------------|
| `basis_ai` | $10M | 9 months ago | Both |
| `techstart` | None | 7 months ago | Last Round only |
| `growthco` | $25M | 19 months ago | Both (with warning) |
| `prerevenue_no_round` | None | None | Error (422) |
| `old_round` | $5M | 36 months ago | Comparables only |

## Adding New Methods

1. Create a new file in `backend/src/methods/`
2. Implement `ValuationMethod` base class
3. Use `@MethodRegistry.register` decorator
4. Import in `engine.py` to register

```python
from src.methods.base import MethodRegistry, ValuationMethod

@MethodRegistry.register
class NewMethod(ValuationMethod):
    method_name = MethodName.NEW_METHOD

    def check_prerequisites(self) -> Optional[str]:
        # Return None if can run, or reason string if not
        pass

    def execute(self) -> MethodResult:
        # Run valuation, use self._add_step() for audit trail
        pass
```

## Design Decisions

1. **Decimal for Money**: All monetary values use Python Decimal to avoid floating-point precision issues
2. **Frozen Config**: ValuationConfig is immutable to ensure reproducibility
3. **Audit Steps**: Each calculation step captures inputs, formula, and result
4. **Method Independence**: Methods run independently and failures are isolated
5. **Input Hashing**: Deterministic SHA256 hash of all inputs for verification

## Running Tests

```bash
cd backend
uv run pytest
```

## Future Improvements

- Add more valuation methods (DCF, Option Pricing)
- Historical valuation comparison
- Export to PDF/Excel
- User authentication
- Batch processing with progress
- Method weighting customization
