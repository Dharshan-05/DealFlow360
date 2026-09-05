#!/usr/bin/env bash
# ==============================================================================
# DealFlow360 — Backend Production Startup Script
# Phase 467: Process Management & Pre-Flight Migration Execution
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/dealflow360/backend"
ENV_FILE="/etc/dealflow360/backend.env"

echo "=== [DealFlow360] Initializing Backend Service ==="

if [[ -f "$ENV_FILE" ]]; then
    echo "Loading environment from $ENV_FILE..."
    # shellcheck disable=SC1090
    set -a && source "$ENV_FILE" && set +a
else
    echo "WARNING: $ENV_FILE not found, using existing environment variables."
fi

cd "$APP_DIR"

echo "Activating virtual environment..."
source "$APP_DIR/.venv/bin/activate"

echo "Running database schema migrations..."
alembic upgrade head

echo "Starting Uvicorn multi-worker process on ${HOST:-127.0.0.1}:${PORT:-8000}..."
exec uvicorn app.main:app \
    --host "${HOST:-127.0.0.1}" \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-4}" \
    --log-level "${LOG_LEVEL:-info}" \
    --no-access-log
