# VC Audit Tool - Run Script
# Usage:
#   .\run.ps1          - Start both backend and frontend servers
#   .\run.ps1 migrate  - Run database migrations
#   .\run.ps1 backend  - Start backend only
#   .\run.ps1 frontend - Start frontend only

param(
    [Parameter(Position=0)]
    [string]$Command = "all"
)

$ErrorActionPreference = "Stop"

# Check if setup has been run (uv creates .venv)
if (-not (Test-Path "backend\.venv")) {
    Write-Host "ERROR: Backend virtual environment not found." -ForegroundColor Red
    Write-Host "Please run .\setup.ps1 first." -ForegroundColor Yellow
    exit 1
}

# Load .env file for database connection
$envFile = "backend\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

function Run-Migrations {
    Write-Host "=== Running Database Migrations ===" -ForegroundColor Cyan
    Write-Host ""

    Push-Location backend
    uv run alembic upgrade head
    $exitCode = $LASTEXITCODE
    Pop-Location

    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "Migrations completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Migration failed. Check your DATABASE_URL in backend\.env" -ForegroundColor Red
        exit 1
    }
}

function Start-Backend {
    Write-Host "Starting backend server..." -ForegroundColor Yellow
    $process = Start-Process -FilePath "uv" `
        -ArgumentList "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory "backend" `
        -PassThru `
        -NoNewWindow
    return $process
}

function Start-Frontend {
    Write-Host "Starting frontend server..." -ForegroundColor Yellow
    $process = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "npm run dev" `
        -WorkingDirectory "frontend" `
        -PassThru `
        -NoNewWindow
    return $process
}

function Stop-Servers {
    Write-Host ""
    Write-Host "Stopping servers..." -ForegroundColor Yellow

    if ($script:backendProcess -and !$script:backendProcess.HasExited) {
        Stop-Process -Id $script:backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($script:frontendProcess -and !$script:frontendProcess.HasExited) {
        Stop-Process -Id $script:frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }

    # Kill any orphaned processes on our ports
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }

    Write-Host "Servers stopped." -ForegroundColor Green
}

# Main execution
switch ($Command.ToLower()) {
    "migrate" {
        Run-Migrations
    }
    "backend" {
        Write-Host "=== VC Audit Tool - Backend ===" -ForegroundColor Cyan
        try {
            $script:backendProcess = Start-Backend
            Write-Host ""
            Write-Host "Backend API:  http://localhost:8000" -ForegroundColor White
            Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor White
            Write-Host ""
            Write-Host "Press Enter to stop..." -ForegroundColor Gray
            $null = Read-Host
        } finally {
            Stop-Servers
        }
    }
    "frontend" {
        Write-Host "=== VC Audit Tool - Frontend ===" -ForegroundColor Cyan
        try {
            $script:frontendProcess = Start-Frontend
            Write-Host ""
            Write-Host "Frontend:     http://localhost:5173" -ForegroundColor White
            Write-Host ""
            Write-Host "Press Enter to stop..." -ForegroundColor Gray
            $null = Read-Host
        } finally {
            Stop-Servers
        }
    }
    default {
        # Start both servers
        Write-Host "=== VC Audit Tool ===" -ForegroundColor Cyan
        Write-Host ""

        if (-not (Test-Path "frontend\node_modules")) {
            Write-Host "ERROR: Frontend node_modules not found." -ForegroundColor Red
            Write-Host "Please run .\setup.ps1 first." -ForegroundColor Yellow
            exit 1
        }

        try {
            $script:backendProcess = Start-Backend
            $script:frontendProcess = Start-Frontend

            Start-Sleep -Seconds 3

            Write-Host ""
            Write-Host "=== Servers Running ===" -ForegroundColor Green
            Write-Host ""
            Write-Host "Backend API:  http://localhost:8000" -ForegroundColor White
            Write-Host "API Docs:     http://localhost:8000/docs" -ForegroundColor White
            Write-Host "Frontend:     http://localhost:5173" -ForegroundColor White
            Write-Host ""
            Write-Host "Press Enter to stop all servers..." -ForegroundColor Gray
            Write-Host ""

            $null = Read-Host
        } finally {
            Stop-Servers
        }
    }
}
