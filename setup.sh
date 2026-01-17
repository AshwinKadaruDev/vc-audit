#!/bin/bash
# VC Audit Tool - Setup Script
#
# Prerequisites:
#   1. uv (https://docs.astral.sh/uv/)
#   2. Node.js 18+
#   3. PostgreSQL running with database 'vc_audit' created
#   4. backend/.env file configured (copy from backend/.env.example)

set -e

echo ""
echo "=== VC Audit Tool Setup ==="
echo ""

# Check uv
echo "[1/4] Checking uv..."
if ! command -v uv &> /dev/null; then
    echo "  ERROR: uv not found. Install from https://docs.astral.sh/uv/"
    exit 1
fi
echo "  OK: $(uv --version)"

# Check Node
echo "[2/4] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "  ERROR: Node.js not found"
    exit 1
fi
echo "  OK: Node $(node --version)"

# Check .env file
echo "[3/4] Checking environment..."
if [ ! -f "backend/.env" ]; then
    echo "  backend/.env not found - creating from .env.example"

    if [ ! -f "backend/.env.example" ]; then
        echo "  ERROR: backend/.env.example not found"
        exit 1
    fi

    cp "backend/.env.example" "backend/.env"
    echo "  Created backend/.env from template"
    echo ""
    echo "  IMPORTANT: Edit backend/.env and update DATABASE_URL with your PostgreSQL credentials"
    echo "  Example: DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/vc_audit"
    echo ""

    read -p "Press Enter to open backend/.env in your editor, or type 'skip' to continue: " response
    if [ "$response" != "skip" ]; then
        ${EDITOR:-nano} "backend/.env"
        echo ""
        read -p "Have you updated DATABASE_URL? (y/n): " ready
        if [ "$ready" != "y" ]; then
            echo "  Setup cancelled. Please update backend/.env and run setup again."
            exit 0
        fi
    fi
else
    # Check if .env has all required variables
    if ! grep -q "DB_POOL_SIZE" "backend/.env" || ! grep -q "LOG_LEVEL" "backend/.env" || \
       ! grep -q "RATE_LIMIT_REQUESTS" "backend/.env" || ! grep -q "RETRY_MAX_ATTEMPTS" "backend/.env"; then
        echo "  WARNING: backend/.env is missing new configuration variables"
        echo ""
        read -p "Would you like to update backend/.env with new variables? (y/n): " update

        if [ "$update" = "y" ]; then
            # Backup current .env
            cp "backend/.env" "backend/.env.backup"
            echo "  Created backup: backend/.env.backup"

            # Extract DATABASE_URL from old file
            old_db_url=$(grep "^DATABASE_URL=" "backend/.env.backup" | head -1)

            # Copy new template
            cp "backend/.env.example" "backend/.env"

            # Restore DATABASE_URL if it existed
            if [ -n "$old_db_url" ]; then
                sed -i.tmp "s|^DATABASE_URL=.*|$old_db_url|" "backend/.env"
                rm -f "backend/.env.tmp"
                echo "  Preserved your DATABASE_URL from old .env"
            fi

            echo "  Updated backend/.env with new configuration variables"
            echo "  Your old .env is saved as backend/.env.backup"
        fi
    else
        echo "  OK: backend/.env exists"
    fi
fi

# Setup backend with uv
echo "[4/4] Setting up backend..."
cd backend
uv sync --all-extras
if [ $? -ne 0 ]; then
    echo "  ERROR: uv sync failed"
    exit 1
fi
cd ..
echo "  OK: Python dependencies installed"

# Run migrations
echo ""
echo "[5/5] Running database migrations..."
cd backend
export $(grep -v '^#' .env | xargs)
uv run alembic upgrade head
if [ $? -ne 0 ]; then
    echo "  ERROR: Migration failed. Check DATABASE_URL in backend/.env"
    exit 1
fi
cd ..
echo "  OK: Database ready"

# Frontend
echo ""
echo "[6/6] Installing frontend dependencies..."
cd frontend
npm install --silent 2>/dev/null
cd ..
echo "  OK: Frontend ready"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Run the app:  ./run.sh"
echo ""
