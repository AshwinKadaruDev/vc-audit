# VC Audit Tool - Setup Script
#
# Prerequisites:
#   1. uv (https://docs.astral.sh/uv/)
#   2. Node.js 18+
#   3. PostgreSQL running with database 'vc_audit' created
#
# This script will:
#   - Install backend Python dependencies
#   - Run database migrations (creates tables + seeds sample data from JSON files)
#   - Install frontend Node.js dependencies

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== VC Audit Tool Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check uv
Write-Host "[1/6] Checking uv..." -ForegroundColor Yellow
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: uv not found. Install from https://docs.astral.sh/uv/" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: $(uv --version)" -ForegroundColor Green

# Check Node
Write-Host "[2/6] Checking Node.js..." -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: Node.js not found" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: Node $(node --version)" -ForegroundColor Green

# Check .env file
Write-Host "[3/6] Checking environment..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.env")) {
    Write-Host "  backend\.env not found - creating from .env.example" -ForegroundColor Yellow

    if (-not (Test-Path "backend\.env.example")) {
        Write-Host "  ERROR: backend\.env.example not found" -ForegroundColor Red
        exit 1
    }

    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "  Created backend\.env from template" -ForegroundColor Green
    Write-Host ""
    Write-Host "  IMPORTANT: Edit backend\.env and update DATABASE_URL with your PostgreSQL credentials" -ForegroundColor Yellow
    Write-Host "  Example: DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/vc_audit" -ForegroundColor Cyan
    Write-Host ""

    $response = Read-Host "Press Enter to open backend\.env in notepad, or type 'skip' to continue"
    if ($response -ne 'skip') {
        notepad "backend\.env"
        Write-Host ""
        $ready = Read-Host "Have you updated DATABASE_URL? (y/n)"
        if ($ready -ne 'y') {
            Write-Host "  Setup cancelled. Please update backend\.env and run setup again." -ForegroundColor Yellow
            exit 0
        }
    }
} else {
    # Check if .env has all required variables from .env.example
    $envContent = Get-Content "backend\.env" -Raw
    $exampleContent = Get-Content "backend\.env.example" -Raw

    # Check for key variables that should exist
    $requiredVars = @("DB_POOL_SIZE", "LOG_LEVEL", "RATE_LIMIT_REQUESTS", "RETRY_MAX_ATTEMPTS")
    $missingVars = $requiredVars | Where-Object { $envContent -notmatch $_ }

    if ($missingVars.Count -gt 0) {
        Write-Host "  WARNING: backend\.env is missing new configuration variables" -ForegroundColor Yellow
        Write-Host "  Missing: $($missingVars -join ', ')" -ForegroundColor Yellow
        Write-Host ""
        $update = Read-Host "Would you like to update backend\.env with new variables? (y/n)"

        if ($update -eq 'y') {
            # Backup current .env
            Copy-Item "backend\.env" "backend\.env.backup"
            Write-Host "  Created backup: backend\.env.backup" -ForegroundColor Cyan

            # Copy new template
            Copy-Item "backend\.env.example" "backend\.env"

            # Try to preserve DATABASE_URL from old file
            $oldEnv = Get-Content "backend\.env.backup" -Raw
            if ($oldEnv -match 'DATABASE_URL=(.+)') {
                $oldDbUrl = $matches[1].Trim()
                (Get-Content "backend\.env") -replace 'DATABASE_URL=.+', "DATABASE_URL=$oldDbUrl" | Set-Content "backend\.env"
                Write-Host "  Preserved your DATABASE_URL from old .env" -ForegroundColor Green
            }

            Write-Host "  Updated backend\.env with new configuration variables" -ForegroundColor Green
            Write-Host "  Your old .env is saved as backend\.env.backup" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  OK: backend\.env exists" -ForegroundColor Green
    }
}

# Setup backend with uv
Write-Host "[4/6] Installing backend dependencies..." -ForegroundColor Yellow
Push-Location backend
uv sync --all-extras
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "  ERROR: uv sync failed" -ForegroundColor Red
    exit 1
}
Pop-Location
Write-Host "  OK: Python dependencies installed" -ForegroundColor Green

# Run migrations
Write-Host "[5/6] Running database migrations..." -ForegroundColor Yellow
Write-Host "  This creates tables and seeds sample data from JSON files" -ForegroundColor Gray
Push-Location backend
# Load .env for DATABASE_URL
Get-Content ".env" | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $val = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $val, "Process")
    }
}
uv run alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "  ERROR: Migration failed. Check DATABASE_URL in backend\.env" -ForegroundColor Red
    Write-Host "  Make sure PostgreSQL is running and the database 'vc_audit' exists." -ForegroundColor Yellow
    exit 1
}
Pop-Location
Write-Host "  OK: Database tables created and sample data seeded" -ForegroundColor Green

# Frontend
Write-Host "[6/6] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install --silent 2>$null
Pop-Location
Write-Host "  OK: Frontend dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "         Setup Complete!              " -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "  .\run.ps1" -ForegroundColor White
Write-Host ""
Write-Host "This will start:" -ForegroundColor Gray
Write-Host "  - Backend API at http://localhost:8000" -ForegroundColor Gray
Write-Host "  - Frontend at http://localhost:5173" -ForegroundColor Gray
Write-Host ""
