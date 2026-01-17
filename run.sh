#!/bin/bash
# VC Audit Tool - Run Script
# Usage:
#   ./run.sh          - Start both backend and frontend servers
#   ./run.sh migrate  - Run database migrations
#   ./run.sh backend  - Start backend only
#   ./run.sh frontend - Start frontend only

set -e

COMMAND=${1:-all}

# Check if setup has been run (uv creates .venv)
if [ ! -d "backend/.venv" ]; then
    echo "ERROR: Backend virtual environment not found."
    echo "Please run ./setup.sh first."
    exit 1
fi

# Load .env file
if [ -f "backend/.env" ]; then
    export $(grep -v '^#' backend/.env | xargs)
fi

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "Servers stopped."
    exit 0
}

run_migrations() {
    echo "=== Running Database Migrations ==="
    echo ""
    cd backend
    uv run alembic upgrade head
    cd ..
    echo ""
    echo "Migrations completed successfully!"
}

start_backend() {
    echo "Starting backend server..."
    cd backend
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
}

start_frontend() {
    echo "Starting frontend server..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
}

case $COMMAND in
    migrate)
        run_migrations
        ;;
    backend)
        echo "=== VC Audit Tool - Backend ==="
        trap cleanup SIGINT SIGTERM EXIT
        start_backend
        echo ""
        echo "Backend API:  http://localhost:8000"
        echo "API Docs:     http://localhost:8000/docs"
        echo ""
        echo "Press Ctrl+C to stop..."
        wait $BACKEND_PID
        ;;
    frontend)
        echo "=== VC Audit Tool - Frontend ==="
        trap cleanup SIGINT SIGTERM EXIT
        start_frontend
        echo ""
        echo "Frontend:     http://localhost:5173"
        echo ""
        echo "Press Ctrl+C to stop..."
        wait $FRONTEND_PID
        ;;
    *)
        echo "=== VC Audit Tool ==="
        echo ""

        if [ ! -d "frontend/node_modules" ]; then
            echo "ERROR: Frontend node_modules not found."
            echo "Please run ./setup.sh first."
            exit 1
        fi

        trap cleanup SIGINT SIGTERM EXIT

        start_backend
        start_frontend

        sleep 3

        echo ""
        echo "=== Servers Running ==="
        echo ""
        echo "Backend API:  http://localhost:8000"
        echo "API Docs:     http://localhost:8000/docs"
        echo "Frontend:     http://localhost:5173"
        echo ""
        echo "Press Ctrl+C to stop all servers..."
        echo ""

        wait $BACKEND_PID $FRONTEND_PID
        ;;
esac
