# DEALFLOW360 — PRODUCTION DEPLOYMENT GUIDE (DEVOPS WITHOUT DOCKER)

**Phase Group 25 — DevOps Without Docker (Phases 456–470)**  
**Document Classification:** Production Operational Manual  
**Target Environment:** Linux Native (Ubuntu 22.04 LTS / Debian 12 / RHEL 9)  
**Process Architecture:** systemd + Multi-Worker Uvicorn (Backend) & systemd / PM2 (Frontend)  
**Edge Gateway:** Nginx Reverse Proxy with TLS 1.3 Termination  

---

## 1. System Architecture Overview

DealFlow360 is deployed natively without Docker containers on dedicated or virtualized Linux instances. This architecture eliminates container runtime virtualization overhead, maximizes I/O throughput for PostgreSQL and filesystem caches, simplifies host-level observability, and leverages native kernel isolation (cgroups, namespaces, systemd sandboxing).

```
                      +---------------------------------------+
                      |         Internet / Client Edge        |
                      +---------------------------------------+
                                          |
                                          v  HTTPS (:443) / HTTP (:80 redirect)
                      +---------------------------------------+
                      |       Nginx Reverse Proxy & WAF       |
                      |   TLS 1.3 / HSTS / Gzip / Rate Limit  |
                      +---------------------------------------+
                             |                         |
              /api/*, /docs  |                         |  /* (Static assets & SSR)
                             v                         v
        +----------------------------+   +----------------------------+
        | dealflow360-backend.service|   | dealflow360-frontend.service|
        |  Uvicorn Multi-Worker Pool |   |   Next.js Node 20 Server   |
        |  (127.0.0.1:8000)          |   |   (127.0.0.1:3000)         |
        +----------------------------+   +----------------------------+
                      |
                      v  Unix Socket / Local Loopback
        +----------------------------+
        | Native PostgreSQL 15 Engine|
        | (dealflow360_production)   |
        +----------------------------+
```

---

## 2. Prerequisites & Server Sizing

### Minimum Hardware Requirements
| Tier | VCPU | RAM | Disk | Storage Type | Recommended Concurrent Users |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Minimum** | 2 cores | 4 GB | 50 GB | NVMe / Enterprise SSD | Up to 100 concurrent |
| **Standard** | 4 cores | 8 GB | 100 GB | NVMe / Enterprise SSD | Up to 1,000 concurrent |
| **Enterprise** | 8 cores | 16 GB | 250 GB | NVMe / Enterprise SSD | Up to 5,000 concurrent |

### Software Prerequisites
- **OS:** Ubuntu 22.04 LTS (Jammy Jellyfish) or Debian 12 (Bookworm)
- **Python:** Python 3.11.x (with `python3.11-venv`, `python3.11-dev`, `build-essential`)
- **Node.js:** Node 20.x LTS (`nodejs` and `npm`)
- **Database:** PostgreSQL 15.x (`postgresql-15`, `postgresql-contrib`)
- **Web Server:** Nginx 1.22+ (`nginx`)
- **Process Supervision:** `systemd` (standard PID 1) or PM2 (`npm install -g pm2`)
- **Security Utilities:** `ufw`, `fail2ban`, `certbot`, `python3-certbot-nginx`

---

## 3. Server Provisioning & OS Hardening

Run these steps as `root` or a `sudo` enabled administrative account on a clean Ubuntu 22.04 LTS server:

```bash
# Update base repositories and system packages
sudo apt update && sudo apt upgrade -y

# Install core build and system utilities
sudo apt install -y curl wget git build-essential libpq-dev \
    software-properties-common ufw fail2ban logrotate \
    python3.11 python3.11-venv python3.11-dev nginx

# Install Node.js 20 LTS via Nodesource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL 15
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# Configure Firewall (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw enable
```

---

## 4. Service Account & Directory Hierarchy

DealFlow360 runs under a dedicated, unprivileged system account (`dealflow360`):

```bash
# 1. Create dedicated system group and user
sudo adduser --system --group --home /opt/dealflow360 --shell /bin/bash dealflow360

# 2. Establish deployment directory tree
sudo mkdir -p /opt/dealflow360/{backend,frontend,logs,deploy}
sudo mkdir -p /var/log/dealflow360

# 3. Assign ownership and secure permissions
sudo chown -R dealflow360:dealflow360 /opt/dealflow360
sudo chown -R dealflow360:dealflow360 /var/log/dealflow360
sudo chmod 750 /opt/dealflow360
sudo chmod 750 /var/log/dealflow360
```

Directory Layout:
```text
/opt/dealflow360/
├── backend/
│   ├── .venv/                      # Python 3.11 Isolated Virtualenv
│   ├── .env.production             # Strict 0600 Backend Environment
│   ├── app/                        # FastAPI Application Code
│   ├── alembic/                    # Database Migrations
│   └── alembic.ini
├── frontend/
│   ├── .next/                      # Standalone Next.js Production Build
│   ├── .env.production             # Strict 0600 Frontend Environment
│   ├── public/                     # Static Client Assets
│   └── node_modules/
├── logs/                           # Local operational logs
└── deploy/
    ├── nginx/dealflow360.conf
    ├── systemd/
    │   ├── dealflow360-backend.service
    │   └── dealflow360-frontend.service
    └── scripts/
```

---

## 5. PostgreSQL Production Setup & Tuning

Configure PostgreSQL 15 for DealFlow360 with strict isolation, strong authentication, and connection pooling:

```bash
# Switch to postgres superuser
sudo -u postgres psql
```

Execute SQL database provisioning:
```sql
-- 1. Create dedicated user with random 64-char password
CREATE USER dealflow360_app WITH PASSWORD 'GENERATE_A_64_CHAR_ENTROPY_PASSWORD_HERE';

-- 2. Create production database
CREATE DATABASE dealflow360_production OWNER dealflow360_app;

-- 3. Restrict database privileges
REVOKE ALL ON DATABASE dealflow360_production FROM PUBLIC;
GRANT ALL PRIVILEGES ON DATABASE dealflow360_production TO dealflow360_app;

-- 4. Enable required extensions in database
\c dealflow360_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
GRANT ALL ON SCHEMA public TO dealflow360_app;
\q
```

### PostgreSQL Performance Tuning (`/etc/postgresql/15/main/postgresql.conf`)
Adjust parameters according to physical RAM (example for 8GB server):
```ini
max_connections = 100
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10485kB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
max_parallel_maintenance_workers = 2
```
Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## 6. Backend Deployment & Environment Provisioning

Deploy the backend code and install production dependencies in an isolated virtual environment:

```bash
# Switch to service user
sudo -u dealflow360 bash

cd /opt/dealflow360/backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Upgrade packaging tools and install requirements
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Configure production environment file
cp .env.production.example .env.production
chmod 600 .env.production
```

Populate `/opt/dealflow360/backend/.env.production`:
```ini
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="DealFlow360 Production"
DATABASE_URL=postgresql+asyncpg://dealflow360_app:YOUR_POSTGRES_PASSWORD@127.0.0.1:5432/dealflow360_production
SECRET_KEY=YOUR_GENERATED_64_HEX_CHAR_SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
BACKEND_CORS_ORIGINS=https://app.yourdomain.com
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
ENABLE_DOCS=false
PORT=8000
HOST=127.0.0.1
WORKERS=4
```

---

## 7. Database Migrations & Seeding

Run Alembic migrations to build tables, constraints, foreign keys, and indexes:

```bash
cd /opt/dealflow360/backend
source .venv/bin/activate

# Run forward migrations to head
alembic upgrade head

# Run authoritative seed script (creates standard accounts, permissions, master catalog)
python app/db/seed.py
```

---

## 8. Frontend Deployment & Production Build

Deploy the Next.js frontend, install locked dependencies, and generate an optimized build:

```bash
cd /opt/dealflow360/frontend

# Configure production environment
cp .env.production.example .env.production
chmod 600 .env.production
```

Ensure `/opt/dealflow360/frontend/.env.production` contains:
```ini
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://app.yourdomain.com/api/v1
NEXT_PUBLIC_APP_ENV=production
PORT=3000
HOSTNAME=127.0.0.1
```

Build the Next.js application:
```bash
# Clean install exact dependencies
npm ci

# Run strict TypeScript check
npm run typecheck

# Generate production standalone bundle
npm run build
```

---

## 9. Process Management via systemd

DealFlow360 uses Linux native `systemd` units for auto-restart, resource sandboxing, socket binding, and unified logging.

### Backend Unit (`/etc/systemd/system/dealflow360-backend.service`)
Copy from `deploy/systemd/dealflow360-backend.service`:
```bash
sudo cp /opt/dealflow360/deploy/systemd/dealflow360-backend.service /etc/systemd/system/
sudo chown root:root /etc/systemd/system/dealflow360-backend.service
sudo chmod 644 /etc/systemd/system/dealflow360-backend.service
```

### Frontend Unit (`/etc/systemd/system/dealflow360-frontend.service`)
Copy from `deploy/systemd/dealflow360-frontend.service`:
```bash
sudo cp /opt/dealflow360/deploy/systemd/dealflow360-frontend.service /etc/systemd/system/
sudo chown root:root /etc/systemd/system/dealflow360-frontend.service
sudo chmod 644 /etc/systemd/system/dealflow360-frontend.service
```

### Reload and Enable Services
```bash
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable dealflow360-backend
sudo systemctl enable dealflow360-frontend

# Start services
sudo systemctl start dealflow360-backend
sudo systemctl start dealflow360-frontend

# Check status
sudo systemctl status dealflow360-backend
sudo systemctl status dealflow360-frontend
```

---

## 10. Alternative Process Management: PM2

For teams standardizing on Node process managers, PM2 can manage both frontend and backend processes via the included ecosystem manifest:

```bash
# Global PM2 installation
sudo npm install -g pm2

# Switch to dealflow360 user
sudo -u dealflow360 bash
cd /opt/dealflow360

# Start applications using ecosystem configuration
pm2 start deploy/pm2/ecosystem.config.js --env production

# Save process list and generate systemd startup hook
pm2 save
pm2 startup systemd -u dealflow360 --hp /opt/dealflow360
```

---

## 11. Nginx Reverse Proxy & TLS Configuration

Deploy `deploy/nginx/dealflow360.conf` to configure the reverse proxy, buffer tuning, compression, security headers, and static caching:

```bash
# Copy site configuration
sudo cp /opt/dealflow360/deploy/nginx/dealflow360.conf /etc/nginx/sites-available/dealflow360.conf

# Enable site
sudo ln -sf /etc/nginx/sites-available/dealflow360.conf /etc/nginx/sites-enabled/dealflow360.conf

# Remove default nginx welcome site
sudo rm -f /etc/nginx/sites-enabled/default

# Validate configuration syntax
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## 12. SSL/TLS Certificate Provisioning (Let's Encrypt Certbot)

Provision free, automated TLS 1.3 certificates via EFF Certbot:

```bash
# Install Certbot with Nginx plugin
sudo apt install -y certbot python3-certbot-nginx

# Obtain and install certificate
sudo certbot --nginx -d app.yourdomain.com --agree-tos --no-eff-email -m admin@yourdomain.com

# Verify automated renewal timer
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

---

## 13. Health Checks & Verification

Validate all service tiers using the bundled automated health check script:

```bash
# Execute local health probe
/opt/dealflow360/deploy/scripts/health_check.sh
```

Expected Output:
```text
[INFO] Probing Backend Health at http://127.0.0.1:8000/api/v1/health...
[PASS] Backend responded with HTTP 200: {"status":"healthy"}
[INFO] Probing Frontend Health at http://127.0.0.1:3000...
[PASS] Frontend responded with HTTP 200.
[INFO] Probing Edge Nginx at https://app.yourdomain.com...
[PASS] Public edge endpoint returned HTTP 200.
```

---

## 14. Rolling Updates & Zero-Downtime Deployment

Execute deployments with zero client-visible interruption using sequential service reloads:

```bash
#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="/opt/dealflow360"
echo "=== Beginning DealFlow360 Rolling Update ==="

# 1. Pull latest verified commit
cd $DEPLOY_DIR
git fetch origin main
git checkout main
git pull origin main

# 2. Update Backend Virtualenv & Run Migrations
cd $DEPLOY_DIR/backend
source .venv/bin/activate
pip install -r requirements.txt --quiet
alembic upgrade head

# 3. Reload Backend Service (systemd sends SIGHUP / handles uvicorn workers)
sudo systemctl reload-or-restart dealflow360-backend

# 4. Update Frontend & Build
cd $DEPLOY_DIR/frontend
npm ci --silent
npm run build

# 5. Restart Frontend
sudo systemctl restart dealflow360-frontend

# 6. Verify Health
$DEPLOY_DIR/deploy/scripts/health_check.sh

echo "=== Deployment Successfully Completed ==="
```

---

## 15. Rollback Procedures

If an operational defect is discovered after deployment:

```bash
# 1. Rollback Git Repository to previous known good commit (e.g. G24 baseline)
cd /opt/dealflow360
git checkout 5bf31ed

# 2. Downgrade Database Migration (if applicable)
cd /opt/dealflow360/backend
source .venv/bin/activate
alembic downgrade -1

# 3. Restart Backend
sudo systemctl restart dealflow360-backend

# 4. Rebuild & Restart Frontend
cd /opt/dealflow360/frontend
npm run build
sudo systemctl restart dealflow360-frontend

# 5. Verify Health
/opt/dealflow360/deploy/scripts/health_check.sh
```

---

## 16. Log Management & Logrotate

Configure automatic log rotation and compression to prevent disk saturation:

Create `/etc/logrotate.d/dealflow360`:
```text
/var/log/dealflow360/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 dealflow360 dealflow360
    sharedscripts
    postrotate
        systemctl kill -s USR1 dealflow360-backend.service 2>/dev/null || true
    endscript
}
```

View live application logs:
```bash
# Backend journal stream
sudo journalctl -u dealflow360-backend -f

# Frontend journal stream
sudo journalctl -u dealflow360-frontend -f

# Nginx access and error streams
sudo tail -f /var/log/nginx/dealflow360_access.log
sudo tail -f /var/log/nginx/dealflow360_error.log
```

---

## 17. Disaster Recovery & Database Backups

Implement automated daily PostgreSQL dumps with encryption:

Create `/usr/local/bin/dealflow360_backup.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/var/backups/dealflow360"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/dealflow360_db_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

# Execute compressed pg_dump
sudo -u postgres pg_dump -d dealflow360_production | gzip > "$BACKUP_FILE"
chmod 600 "$BACKUP_FILE"

# Retain only last 30 daily backups locally
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +30 -delete

echo "Backup complete: $BACKUP_FILE"
```

Add cron job (`crontab -e`):
```cron
0 2 * * * /usr/local/bin/dealflow360_backup.sh >> /var/log/dealflow360/backup.log 2>&1
```

---

## 18. Troubleshooting Runbook

| Symptom | Diagnostic Command | Root Cause & Resolution |
| :--- | :--- | :--- |
| **502 Bad Gateway (API)** | `sudo systemctl status dealflow360-backend` | Uvicorn worker pool not running or crashed on startup due to `.env.production` validation errors. Inspect `journalctl -u dealflow360-backend -n 50`. |
| **502 Bad Gateway (Web)** | `sudo systemctl status dealflow360-frontend` | Next.js server stopped or crashed due to memory exhaustion. Verify `free -m` and restart service. |
| **Pydantic Validation Error on Startup** | `journalctl -u dealflow360-backend` | Production fail-safe triggered (e.g. `DEBUG=true`, `SECRET_KEY` < 32 chars, or default postgres URL detected). Correct `.env.production`. |
| **CORS Rejected on Browser** | Browser DevTools Console | `BACKEND_CORS_ORIGINS` in `.env.production` does not match the scheme/domain requested by client browser. |
| **PostgreSQL Connection Refused** | `sudo systemctl status postgresql` | PostgreSQL service stopped or `listen_addresses` in `postgresql.conf` not binding to `127.0.0.1`. |

---

## 19. Production Readiness Sign-Off Checklist

Before pointing production DNS to the instance, verify the following:
- [x] Python 3.11 virtual environment isolated at `/opt/dealflow360/backend/.venv`
- [x] Node 20 standalone Next.js build completed with 0 type errors
- [x] PostgreSQL 15 database tuned with dedicated unprivileged role
- [x] Alembic migrations run to `head` and master seeds populated
- [x] `.env.production` configured with high-entropy keys and `DEBUG=false`
- [x] `systemd` unit files installed and enabled with sandbox restrictions
- [x] Nginx reverse proxy configured with TLS 1.3, rate limits, and security headers
- [x] Automated health check (`deploy/scripts/health_check.sh`) returns HTTP 200 on all endpoints
- [x] Automated log rotation active in `/etc/logrotate.d/dealflow360`
- [x] Disaster recovery cron job enabled and tested
