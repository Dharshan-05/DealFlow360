# DealFlow360

> **"DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."**

DealFlow360 is an enterprise deal orchestration and discount governance platform designed to guide deals end-to-end—from initial quotation, dynamic policy and margin protection, multi-warehouse fulfillment, and customer negotiation, through to automated billing and payment settlement.

---

## Current Status: G02 (Phases 006–010 Complete)

Implementation strictly adheres to the **520-Phase Master Implementation Roadmap**. Development is strictly phased to ensure clean, decoupled architecture without premature mock modules.

### ✅ Implemented Foundations
- **G01 (Phases 001–005)**:
  - **Phase 001**: Project Initialization (monorepo root, documentation, architecture assets).
  - **Phase 002**: Git Repository Setup (repository initialized, robust `.gitignore` protecting secrets, env files, and build outputs).
  - **Phase 003**: Monorepo Structure (modular separation between `frontend/`, `backend/`, and `docs/`).
  - **Phase 004**: Frontend Next.js Foundation (Next.js with TypeScript, React, responsive app shell).
  - **Phase 005**: Backend FastAPI Foundation (Python FastAPI service, `/health` endpoint, clean architecture).
- **G02 (Phases 006–010)**:
  - **Phase 006**: TypeScript Configuration (strict modern compiler options, path aliases, generic API contract types).
  - **Phase 007**: Python Environment Setup (isolated `.venv/` virtual environment, reproducible dependencies, Python 3.11+).
  - **Phase 008**: Environment Variables (safe `.env.example` templates for frontend and backend, no hardcoded secrets).
  - **Phase 009**: API Architecture (modular versioned router `/api/v1/health`, consistent response envelopes, backward-compatible `/health`).
  - **Phase 010**: Global Error Handling (centralized exception handlers for 422 validation, HTTP errors, domain application errors, sanitized 500 internal errors, structured logging).

### ⏳ Not Yet Implemented (Scheduled for Future Authorized Phases)
- Database (PostgreSQL, SQLAlchemy, Alembic migrations)
- Authentication & Multi-role RBAC (Sales Rep, Manager, Finance, Operations, Customer)
- Business entities (Customers, Products, Catalog, Warehouses)
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
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py # Versioned health endpoint
│   │   │       └── api.py        # API router aggregator
│   │   ├── core/
│   │   │   ├── config.py         # App configuration & env loader
│   │   │   ├── error_handlers.py # Centralized global error handling
│   │   │   ├── errors.py         # ApplicationError base exceptions
│   │   │   └── logging.py        # Application structured logger
│   │   ├── schemas/
│   │   │   └── response.py       # Standardized response envelopes
│   │   ├── main.py               # FastAPI entrypoint & router mounts
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_errors.py        # Global error handling test suite
│   │   ├── test_health.py        # Health & OpenAPI test suite
│   │   └── __init__.py
│   ├── .env.example              # Backend environment template
│   ├── README.md                 # Backend environment guide
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
- **Git**

### 2. Frontend Setup
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the operational foundation screen.

To verify type checking and production build:
```bash
npm run typecheck
npm run build
```

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
- Backward-Compatible Health: [http://localhost:8000/health](http://localhost:8000/health)
- OpenAPI Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI Specification: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

To run automated test suite:
```bash
pytest
```
