#!/usr/bin/env bash
# ==============================================================================
# DealFlow360 — Operational Health Check Probe
# Phase 466 & 470: Endpoint Connectivity and Status Verification
# ==============================================================================
set -euo pipefail

BACKEND_URL="http://127.0.0.1:8000"
FRONTEND_URL="http://127.0.0.1:3000"
NGINX_URL="http://127.0.0.1"

echo "=== [DealFlow360] Health Check Probing ==="

# 1. Probe Backend
echo -n "Checking FastAPI Backend ($BACKEND_URL/api/v1/health)... "
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/health" || echo "FAILED")
if [[ "$BACKEND_STATUS" == "200" ]]; then
    echo "OK (HTTP 200)"
else
    echo "ERROR (HTTP $BACKEND_STATUS)"
    exit 1
fi

# 2. Probe Frontend
echo -n "Checking Next.js Frontend ($FRONTEND_URL)... "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" || echo "FAILED")
if [[ "$FRONTEND_STATUS" == "200" || "$FRONTEND_STATUS" == "307" || "$FRONTEND_STATUS" == "308" ]]; then
    echo "OK (HTTP $FRONTEND_STATUS)"
else
    echo "ERROR (HTTP $FRONTEND_STATUS)"
    exit 1
fi

# 3. Probe Nginx Reverse Proxy
echo -n "Checking Nginx Reverse Proxy ($NGINX_URL/health)... "
NGINX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$NGINX_URL/health" || echo "FAILED")
if [[ "$NGINX_STATUS" == "200" ]]; then
    echo "OK (HTTP 200)"
else
    echo "WARNING (HTTP $NGINX_STATUS - Nginx may not be running locally)"
fi

echo "=== Health check completed successfully ==="
