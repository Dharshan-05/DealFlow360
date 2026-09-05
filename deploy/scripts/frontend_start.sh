#!/usr/bin/env bash
# ==============================================================================
# DealFlow360 — Frontend Production Startup Script
# Phase 468: Process Management for Next.js
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/dealflow360/frontend"
ENV_FILE="/etc/dealflow360/frontend.env"

echo "=== [DealFlow360] Initializing Frontend Next.js Service ==="

if [[ -f "$ENV_FILE" ]]; then
    echo "Loading environment from $ENV_FILE..."
    # shellcheck disable=SC1090
    set -a && source "$ENV_FILE" && set +a
fi

cd "$APP_DIR"

export NODE_ENV=production
export PORT="${PORT:-3000}"

echo "Starting Next.js production server on port $PORT..."
exec npm start
