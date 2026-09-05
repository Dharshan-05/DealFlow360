# DealFlow360

> **"DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."**

DealFlow360 is an enterprise deal orchestration and discount governance platform designed to guide deals end-to-end—from initial quotation, dynamic policy and margin protection, multi-warehouse fulfillment, and customer negotiation, through to automated billing and payment settlement.

---

## Current Status: G03 (Phases 011–015 Complete)

Implementation strictly adheres to the **520-Phase Master Implementation Roadmap**. Development is strictly phased to ensure clean, decoupled architecture without premature mock modules.

### ✅ Implemented Foundations
- **G01 (Phases 001–005)**:
  - **Phase 001**: Project Initialization (monorepo root, documentation, architecture assets).
  - **Phase 002**: Git Repository Setup (repository initialized, robust `.gitignore` protecting secrets, env files, and build outputs).
  - **Phase 003**: Monorepo Structure (modular separation between `frontend/`, `backend/`, and `docs/`).
  - **Phase 004**: Frontend Next.js Foundation (Next.js with TypeScript, React, responsive app shell).
  - **Phase 005**: Backend FastAPI Foundation (Python FastAPI service, `/health` endpoint, clean architecture).
- **G02 (Phases 006–010)**:
  - **Phase 006**: TypeScript Configuration (strict compiler options, path aliases, generic API contract types).
  - **Phase 007**: Python Environment Setup (isolated `.venv/` virtual environment, reproducible dependencies, Python 3.11+).
  - **Phase 008**: Environment Variables (safe `.env.example` templates for frontend and backend, no hardcoded secrets).
  - **Phase 009**: API Architecture (modular versioned router `/api/v1/health`, consistent response envelopes, backward-compatible `/health`).
  - **Phase 010**: Global Error Handling (centralized exception handlers for 422 validation, HTTP errors, domain application errors, sanitized 500 internal errors, structured logging).
- **G03 (Phases 011–015)**:
  - **Phase 011**: PostgreSQL Setup (PostgreSQL relational database configuration via environment variables, psycopg driver).
  - **Phase 012**: SQLAlchemy Setup (SQLAlchemy 2.0 centralized engine, SessionLocal session factory, `get_db` dependency).
  - **Phase 013**: Alembic Setup (Alembic migration infrastructure configured, bound dynamically to application settings and Base metadata).
  - **Phase 014**: Database Base Model (Foundational `DeclarativeBase` with standard PostgreSQL constraint naming conventions).
  - **Phase 015**: Database Connection / Session Foundation (isolated session lifecycle, non-blocking connectivity check in `/api/v1/health`, 13 automated tests).

### ⏳ Not Yet Implemented (Scheduled for Future Authorized Phases)
- Core database models & tables (Users, Roles, Customers, Products, Warehouses, Quotes) — *G04*
- Authentication & Multi-role RBAC (Sales Rep, Manager, Finance, Operations, Customer)
- Quotation Lifecycle & Line Items
- AI Discount Governance Engine & Approval Routing
- Machine Learning Risk Scoring & Explainability
- Multi-Warehouse Inventory Allocation & Fulfillment Tracking
- Customer Negotiation Portal & AI Intent Extraction
- Invoicing, Milestone Billing, and Razorpay Payments
- Deal Health Telemetry & Anomaly Analytics
- Realtime events & WebSockets

---

## Tech Stack (Foundation)

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Monorepo** | Modular layout | Clean decoupled root containing `frontend/`, `backend/`, and `docs/` |
| **Frontend** | Next.js 14+, React, TypeScript | App Router, static & dynamic SSR, strict typing, generic API schemas |
| **Backend** | Python 3.11+, FastAPI, Uvicorn | High-performance asynchronous API, versioned routers, global error filters |
| **Database** | PostgreSQL, SQLAlchemy 2.0, Alembic | Declarative ORM base, deterministic constraint conventions, migration framework |
| **Documentation** | Markdown + Architectural Diagrams | Visual product flow and phase roadmap tracking |

---

## Project Structure

```text
DealFlow360/
├── frontend/                     # Next.js TypeScript application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx        # Root application layout
│   │   │   ├── page.tsx          # Foundation operational screen
│   │   │   └── globals.css       # Core styling
│   │   └── types/
│   │       └── api.ts            # Generic API contract types
│   ├── .env.example              # Frontend environment template
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.mjs
│
├── backend/                      # Python FastAPI application
│   ├── alembic/                  # Database migration framework
│   │   ├── env.py                # Bound to app settings & Base metadata
│   │   ├── script.py.mako
│   │   └── versions/             # Migration revisions
│   ├── alembic.ini               # Alembic configuration
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py # Versioned health & DB connectivity check
│   │   │       └── api.py        # API router aggregator
│   │   ├── core/
│   │   │   ├── config.py         # App configuration & env loader
│   │   │   ├── error_handlers.py # Centralized global error handling
│   │   │   ├── errors.py         # ApplicationError base exceptions
│   │   │   └── logging.py        # Application structured logger
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # DeclarativeBase with constraint naming conventions
│   │   │   └── session.py        # SQLAlchemy engine, sessionmaker, get_db
│   │   ├── schemas/
│   │   │   └── response.py       # Standardized response envelopes
│   │   ├── main.py               # FastAPI entrypoint & router mounts
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_database.py      # Database engine, session, Alembic tests
│   │   ├── test_errors.py        # Global error handling test suite
│   │   ├── test_health.py        # Health & OpenAPI test suite
│   │   └── __init__.py
│   ├── .env.example              # Backend environment template
│   ├── README.md                 # Backend environment & database guide
│   ├── requirements.txt          # Backend dependencies
│   └── run.py                    # Local server launcher
│
├── docs/                         # Architecture & Roadmap documentation
│   └── architecture/
│       ├── ARCHITECTURE_REFERENCE.md
│       └── DealFlow360_End_to_End_Product_Flow.png
│
├── .gitignore                    # Environment & secret exclusion rules
└── README.md                     # Master project documentation
```

---

## Getting Started (Local Development)

### 1. Prerequisites
- **Node.js**: v18+ (tested with v24)
- **Python**: 3.11+ (tested with Python 3.11.9)
- **PostgreSQL**: v16+ (tested with PostgreSQL on localhost:5432)
- **Git**

### 2. Frontend Setup
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the operational foundation screen.

### 3. Backend Setup
```bash
cd backend
py -3.11 -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python run.py
```
- Versioned API Health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- OpenAPI Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

To run migrations:
```bash
alembic current
```

To run test suite:
```bash
pytest
```
