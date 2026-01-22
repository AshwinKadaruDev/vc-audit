# VC Audit Tool

A portfolio valuation tool for VC auditors. Estimates fair value of private companies using multiple methods with full audit trails.

## What It Does

- **Two valuation methods**: Last Round (market-adjusted) and Comparable Companies
- **Full audit trail**: Every calculation step documented for compliance
- **Automatic method selection**: Skips methods that lack required data
- **Database persistence**: Save and retrieve valuations

## Quick Start

### Prerequisites

- [PostgreSQL](https://www.postgresql.org/) running locally
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js](https://nodejs.org/) 18+

### 1. Create Database

```bash
psql -U postgres -c "CREATE DATABASE vc_audit;"
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your PostgreSQL password:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/vc_audit
```

### 3. Setup

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**Mac/Linux:**
```bash
chmod +x setup.sh run.sh
./setup.sh
```

### 4. Run

**Windows:**
```powershell
.\run.ps1
```

**Mac/Linux:**
```bash
./run.sh
```

### 5. Open

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
backend/src/
├── main.py              # App entry point
├── config.py            # Settings
├── models.py            # Pydantic models
├── api/                 # HTTP routes
├── valuation/           # Engine + methods (core algorithm)
├── database/            # ORM models, CRUD, data loader
├── services/            # Business logic orchestration
└── utils/               # Helpers

frontend/src/
├── pages/               # React pages
├── components/          # UI components
└── api/                 # API client
```

## Documentation

See `_docs/` for detailed documentation:

| Document | Description |
|----------|-------------|
| `BACKEND_ARCHITECTURE.md` | Full backend walkthrough |
| `BUSINESS_LOGIC.md` | Valuation parameters explained |
| `ASSUMPTIONS_AND_TRADEOFFS.md` | Design decisions |
| `API_AND_SCHEMA.md` | API endpoints and database schema |

## Running Tests

```bash
cd backend
uv run pytest -v
```
