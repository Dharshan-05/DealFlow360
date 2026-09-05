# DealFlow360 — Backend Service

## Runtime & Database Strategy
- **Language**: Python 3.11+ (tested on Python 3.11.9)
- **Framework**: FastAPI with ASGI server Uvicorn
- **Relational Database**: PostgreSQL (version 16/17/18)
- **ORM**: SQLAlchemy 2.0 (`DeclarativeBase`, typed engine & sessionmaker)
- **Migration Engine**: Alembic (bound dynamically to application settings)
- **Isolation**: Local virtual environment in `backend/.venv/` (excluded from version control via root `.gitignore`)

---

## Setup Instructions

### 1. PostgreSQL Prerequisites
Ensure a local PostgreSQL server is running (port 5432). Create the application database:
```sql
CREATE DATABASE dealflow360;
```

### 2. Create and Activate Virtual Environment
From the `backend/` directory:

```bash
# Windows
py -3.11 -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `DATABASE_URL` matches your local credentials:
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/dealflow360
```

### 5. Database Migrations (Alembic)
Check migration status:
```bash
alembic current
```
Apply migrations:
```bash
alembic upgrade head
```
Revert migration (single revision):
```bash
alembic downgrade -1
```
View revision history:
```bash
alembic history
```
- Active Migrations:
  - `239bb096c8fd`: `create_users_table` (Phase 015 User Model)
  - `92dfce60f7a1`: `create_core_models_phases_016_020` (Phases 016–020: Roles, Permissions, Companies, Customers, Customer Tiers)

### 6. Run Development Server
```bash
python run.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Base: `http://localhost:8000`
- API Health Check: `http://localhost:8000/api/v1/health`
- Legacy Health Check: `http://localhost:8000/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- ReDoc Docs: `http://localhost:8000/redoc`

### 7. Run Automated Tests
```bash
pytest
```
Test suite verifies configuration, SQLAlchemy engine, session lifecycle, Alembic integration, PostgreSQL queries, and global error handling.
