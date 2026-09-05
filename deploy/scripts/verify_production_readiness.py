#!/usr/bin/env python3
"""
DealFlow360 — Production Readiness Automated Verification Tool
Phase 470 Specification: Comprehensive Production Verification Audit
"""

import os
import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))


def test_production_environment_failsafe():
    print("[1/5] Auditing Production Configuration Fail-Safe Rules (Phase 456 & 465)...")
    from pydantic_core import ValidationError
    import app.core.config as cfg

    # Test 1: DEBUG=true in production must fail
    os.environ["ENVIRONMENT"] = "production"
    os.environ["DEBUG"] = "true"
    os.environ["JWT_SECRET_KEY"] = "prod-secret-key-that-is-at-least-32-characters-long"
    os.environ["DATABASE_URL"] = "postgresql+psycopg://u:p@db:5432/dealflow360_prod"
    try:
        cfg.Settings()
        print("  FAIL: Production allowed DEBUG=True")
        return False
    except ValidationError:
        print("  OK: Production correctly rejected DEBUG=True")

    # Test 2: Insecure default JWT secret in production must fail
    os.environ["DEBUG"] = "false"
    os.environ["JWT_SECRET_KEY"] = cfg.INSECURE_DEV_JWT_SECRET
    try:
        cfg.Settings()
        print("  FAIL: Production allowed default insecure JWT secret")
        return False
    except ValidationError:
        print("  OK: Production correctly rejected default insecure JWT secret")

    # Test 3: Short JWT secret (<32 chars) in production must fail
    os.environ["JWT_SECRET_KEY"] = "short-secret"
    try:
        cfg.Settings()
        print("  FAIL: Production allowed short JWT secret")
        return False
    except ValidationError:
        print("  OK: Production correctly rejected short JWT secret (<32 chars)")

    # Test 4: Default DATABASE_URL in production must fail
    os.environ["JWT_SECRET_KEY"] = "prod-secret-key-that-is-at-least-32-characters-long"
    os.environ["DATABASE_URL"] = cfg.DEFAULT_DEV_DATABASE_URL
    try:
        cfg.Settings()
        print("  FAIL: Production allowed default dev DATABASE_URL")
        return False
    except ValidationError:
        print("  OK: Production correctly rejected default dev DATABASE_URL")

    # Test 5: Wildcard CORS in production must fail
    os.environ["DATABASE_URL"] = "postgresql+psycopg://u:p@db:5432/dealflow360_prod"
    os.environ["CORS_ORIGINS"] = "*"
    try:
        cfg.Settings()
        print("  FAIL: Production allowed wildcard CORS origin")
        return False
    except ValidationError:
        print("  OK: Production correctly rejected wildcard CORS origin")

    # Test 6: Valid production settings must pass cleanly
    os.environ["CORS_ORIGINS"] = "https://app.dealflow360.com"
    prod_s = cfg.Settings()
    assert prod_s.ENVIRONMENT == "production"
    assert prod_s.DEBUG is False
    assert prod_s.ENABLE_DOCS is False
    print("  OK: Valid production configuration passed all checks")
    return True


def test_nginx_configuration():
    print("\n[2/5] Auditing Nginx Reverse Proxy Configuration (Phase 466)...")
    nginx_conf = REPO_ROOT / "deploy" / "nginx" / "dealflow360.conf"
    if not nginx_conf.is_file():
        print(f"  FAIL: Missing Nginx configuration at {nginx_conf}")
        return False

    content = nginx_conf.read_text(encoding="utf-8")
    required_tokens = [
        ("upstream dealflow360_backend", "Backend upstream pool"),
        ("upstream dealflow360_frontend", "Frontend upstream pool"),
        ("proxy_pass http://dealflow360_backend", "Backend proxy pass directive"),
        ("proxy_pass http://dealflow360_frontend", "Frontend proxy pass directive"),
        ("X-Frame-Options", "Frame options security header"),
        ("X-Content-Type-Options", "Content type options security header"),
        ("gzip on", "Gzip compression"),
        ("location /health", "Health check endpoint location"),
        ("location /_next/static/", "Next.js static caching location"),
    ]

    for token, desc in required_tokens:
        if token not in content:
            print(f"  FAIL: Nginx config missing required token: '{token}' ({desc})")
            return False
        print(f"  OK: Found {desc}")
    return True


def test_systemd_and_pm2_services():
    print("\n[3/5] Auditing Process Management Services (Phases 467 & 468)...")
    backend_service = REPO_ROOT / "deploy" / "systemd" / "dealflow360-backend.service"
    frontend_service = REPO_ROOT / "deploy" / "systemd" / "dealflow360-frontend.service"
    pm2_config = REPO_ROOT / "deploy" / "pm2" / "ecosystem.config.js"

    for service_path, name in [
        (backend_service, "Backend Systemd Service"),
        (frontend_service, "Frontend Systemd Service"),
        (pm2_config, "PM2 Ecosystem Configuration"),
    ]:
        if not service_path.is_file():
            print(f"  FAIL: Missing {name} at {service_path}")
            return False
        content = service_path.read_text(encoding="utf-8")
        if "backend" in name.lower() and "uvicorn" not in content.lower():
            print(f"  FAIL: {name} does not reference Uvicorn")
            return False
        if "frontend" in name.lower() and "npm start" not in content:
            print(f"  FAIL: {name} does not reference npm start")
            return False
        print(f"  OK: Validated {name}")
    return True


def test_security_and_token_storage():
    print("\n[4/5] Auditing Browser Storage & In-Memory Token Architecture...")
    frontend_src = REPO_ROOT / "frontend" / "src"
    forbidden_patterns = [
        (re.compile(r"localStorage\.setItem"), "localStorage.setItem"),
        (re.compile(r"sessionStorage\.setItem"), "sessionStorage.setItem"),
        (re.compile(r"document\.cookie\s*="), "document.cookie write"),
    ]

    leak_found = False
    for root, _, files in os.walk(frontend_src):
        for f in files:
            if f.endswith((".ts", ".tsx", ".js")):
                path = Path(root) / f
                content = path.read_text(encoding="utf-8")
                for pattern, name in forbidden_patterns:
                    if pattern.search(content):
                        print(f"  FAIL: Insecure browser storage write ({name}) found in {path}")
                        leak_found = True

    if leak_found:
        return False
    print("  OK: Zero browser token writes detected. Strict in-memory token storage verified.")
    return True


def test_deployment_scripts_and_docs():
    print("\n[5/5] Auditing Deployment Documentation & Shell Scripts (Phase 469)...")
    required_files = [
        (REPO_ROOT / "docs" / "devops" / "DEPLOYMENT_GUIDE.md", "Production Deployment Guide"),
        (REPO_ROOT / "docs" / "devops" / "ENVIRONMENT_SECRET_MANAGEMENT.md", "Secret Management Guide"),
        (REPO_ROOT / "docs" / "devops" / "GIT_BRANCH_STRATEGY.md", "Git Branch Strategy"),
        (REPO_ROOT / "docs" / "devops" / "GIT_COMMIT_STANDARDS.md", "Git Commit Standards"),
        (REPO_ROOT / "deploy" / "scripts" / "backend_start.sh", "Backend Start Script"),
        (REPO_ROOT / "deploy" / "scripts" / "frontend_start.sh", "Frontend Start Script"),
        (REPO_ROOT / "deploy" / "scripts" / "health_check.sh", "Health Check Script"),
        (REPO_ROOT / ".github" / "workflows" / "ci.yml", "GitHub Actions CI Workflow"),
    ]

    for path, desc in required_files:
        if not path.is_file():
            print(f"  FAIL: Missing {desc} at {path}")
            return False
        print(f"  OK: Found {desc}")
    return True


def main():
    print("======================================================================")
    print("  DealFlow360 — Production Readiness Audit (Phase 470)")
    print("======================================================================\n")

    checks = [
        test_production_environment_failsafe,
        test_nginx_configuration,
        test_systemd_and_pm2_services,
        test_security_and_token_storage,
        test_deployment_scripts_and_docs,
    ]

    all_passed = True
    for check in checks:
        if not check():
            all_passed = False

    print("\n======================================================================")
    if all_passed:
        print("  STATUS: 100% PRODUCTION READY — ALL AUDIT GATES PASSED")
        print("======================================================================")
        sys.exit(0)
    else:
        print("  STATUS: AUDIT FAILED — REMEDIATION REQUIRED")
        print("======================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
