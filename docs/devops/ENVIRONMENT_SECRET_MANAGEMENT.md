# DealFlow360 — Environment Secret Management & Security Protocol

**Phases 456 & 465 Specification: Production Secret Architecture**

---

## 1. Zero-Trust Secret Architecture

DealFlow360 enforces a strict **Zero-Trust & Zero-Leakage** security model:
1. **Never Commit Secrets to Version Control**: No real passwords, connection strings, private keys, or API tokens may exist in Git history, pull requests, commit messages, or branches.
2. **Never Expose Backend Secrets to the Frontend**:
   - `NEXT_PUBLIC_*` variables are embedded into public client-side JavaScript bundles sent to all browsers.
   - Database credentials, `JWT_SECRET_KEY`, and encryption keys are strictly restricted to the backend execution context.
3. **Fail-Safe Startup Verification**:
   - The FastAPI backend validates all production environment variables on boot.
   - If `ENVIRONMENT=production` and default development secrets or missing credentials are detected, the process halts immediately with a fatal configuration error.

---

## 2. Environment Variables Matrix

### Backend Environment Variables (`/etc/dealflow360/backend.env`)

| Variable | Required in Prod | Sensitivity | Purpose & Format |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | **Yes** | Public | Must be `production`. Triggers strict startup validation. |
| `DEBUG` | **Yes** | Sensitive | Must be `false`. Insecure if set to `true` in production. |
| `HOST` | **Yes** | Sensitive | `127.0.0.1` (never bind `0.0.0.0` directly without Nginx proxy). |
| `PORT` | **Yes** | Public | `8000` |
| `API_V1_STR` | Optional | Public | `/api/v1` |
| `PROJECT_NAME` | Optional | Public | `DealFlow360` |
| `CORS_ORIGINS` | **Yes** | Sensitive | Comma-separated list of exact production domains (e.g. `https://app.dealflow360.com`). Wildcard `*` is strictly forbidden. |
| `LOG_LEVEL` | Optional | Public | `INFO` (use `WARNING` or `ERROR` for high volume). |
| `DATABASE_URL` | **Yes** | **Critical Secret** | PostgreSQL connection string: `postgresql+psycopg://<user>:<password>@<host>:<port>/<dbname>`. |
| `DB_ECHO_LOG` | Optional | Sensitive | `false` (SQL statement dumping disabled in production). |
| `JWT_SECRET_KEY` | **Yes** | **Critical Secret** | Cryptographically random 256-bit key ($\ge 32$ chars). Generated via `openssl rand -hex 32`. |
| `JWT_ALGORITHM` | Optional | Public | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Public | `30` minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Optional | Public | `7` days |
| `ENABLE_DOCS` | Optional | Sensitive | `false` in production to prevent public API schema harvesting. |

### Frontend Environment Variables (`/etc/dealflow360/frontend.env`)

| Variable | Required in Prod | Sensitivity | Scope |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | **Yes** | Public | `https://app.dealflow360.com` (proxied root) |
| `NEXT_PUBLIC_API_V1_STR`| Optional | Public | `/api/v1` |
| `PORT` | Optional | Public | `3000` |
| `NODE_ENV` | **Yes** | Public | `production` |

---

## 3. GitHub Actions CI/CD Secrets

For automated CI/CD validation and deployment:

| GitHub Secret Name | Scope | Description |
| :--- | :--- | :--- |
| `CI_TEST_JWT_SECRET` | CI Testing | Ephemeral 64-char key used exclusively by CI test containers. |
| `PROD_SSH_HOST` | Deployment | Target Linux production server IP / hostname. |
| `PROD_SSH_USER` | Deployment | Deployer user on target server (e.g., `deployer`). |
| `PROD_SSH_KEY` | Deployment | Private SSH key for secure host authentication. |
| `PROD_DATABASE_URL` | Deployment | Dedicated production PostgreSQL database URI. |
| `PROD_JWT_SECRET_KEY`| Deployment | Production JWT signing secret ($\ge 32$ characters). |

---

## 4. Secret Generation Runbook

Run the following commands on a secure operational machine to generate production secrets:

```bash
# Generate 256-bit JWT signing key:
openssl rand -hex 32

# Generate strong PostgreSQL database password:
openssl rand -base64 24
```

---

## 5. Host File Permissions & Ownership

In Linux production:
```bash
# Secure directory owned by root, accessible only by service user
sudo mkdir -p /etc/dealflow360
sudo chown -R root:dealflow360 /etc/dealflow360
sudo chmod 750 /etc/dealflow360

# Secure environment files
sudo chmod 640 /etc/dealflow360/backend.env
sudo chmod 640 /etc/dealflow360/frontend.env
```

---

## 6. Security Audit Checklist

- [x] No plaintext `.env` committed to repository.
- [x] All `.env` and `.env.*` (except `.env.example`) excluded in `.gitignore`.
- [x] Frontend code contains zero private server-side secrets or DB credentials.
- [x] Tokens are maintained exclusively in-memory (no `localStorage`, `sessionStorage`, or `document.cookie`).
- [x] Fail-safe validation triggers on missing or default secrets in `production`.
