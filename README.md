# DealFlow360

> **"DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."**

DealFlow360 is an enterprise deal orchestration and discount governance platform designed to guide deals end-to-end—from initial quotation, dynamic policy and margin protection, multi-warehouse fulfillment, and customer negotiation, through to automated billing and payment settlement.

---

## Current Status: G01 (Phases 001–005 Foundation)

Implementation follows the **520-Phase Master Implementation Roadmap**. Development is strictly phased to ensure clean, decoupled architecture without premature mock modules.

### ✅ Implemented (G01: Phases 001–005)
- **Phase 001**: Project Initialization (monorepo root, documentation, architecture reference assets).
- **Phase 002**: Git Repository Setup (repository initialized, robust `.gitignore` protecting secrets, env files, and build outputs).
- **Phase 003**: Monorepo Structure (modular separation between `frontend/`, `backend/`, and `docs/`).
- **Phase 004**: Frontend Next.js Foundation (Next.js with TypeScript, React, responsive app shell, verified typecheck & production build).
- **Phase 005**: Backend FastAPI Foundation (Python FastAPI service, `/health` endpoint, clean architecture, automated health tests).

### ⏳ Not Yet Implemented (Scheduled for Future Authorized Phases)
- Database (PostgreSQL, SQLAlchemy, Alembic migrations)
- Authentication & Multi-role RBAC (Sales Rep, Manager, Finance, Operations, Customer)
- Business entities (Customers, Products, Catalog, Warehouses)
- Quotation Engine & Line Items
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
| **Frontend** | Next.js 14+, React, TypeScript | App Router, static & dynamic SSR, strict typing |
| **Backend** | Python 3.11+, FastAPI, Uvicorn | High-performance asynchronous API, Pydantic schemas |
| **Documentation** | Markdown + Architectural Diagrams | Visual product flow and phase roadmap tracking |

---

## Project Structure

```text
DealFlow360/
├── frontend/                     # Next.js TypeScript application
│   ├── src/
│   │   └── app/
│   │       ├── layout.tsx        # Root application layout
│   │       ├── page.tsx          # Foundation operational screen
│   │       └── globals.css       # Core styling
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.mjs
│
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py         # Application settings
│   │   ├── main.py               # FastAPI entrypoint & routes
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_health.py        # Automated health verification
│   │   └── __init__.py
│   └── requirements.txt          # Backend dependencies
│
├── docs/                         # Architecture & Roadmap documentation
│   └── architecture/
│       ├── ARCHITECTURE_REFERENCE.md
│       └── DealFlow360_End_to_End_Product_Flow.png
│
├── .gitignore                    # Environment & secret exclusion rules
└── README.md                     # Project documentation
```

---

## Getting Started (Local Development)

### 1. Prerequisites
- **Node.js**: v18+ (tested with v24)
- **Python**: 3.10+ (tested with Python 3.11)
- **Git**

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the operational foundation screen.

To verify the production build:
```bash
npm run build
```

### 3. Backend Setup
```bash
cd backend
py -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Health Check Endpoint: [http://localhost:8000/health](http://localhost:8000/health)  
Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

To run automated tests:
```bash
pytest
```

---

## Architectural Reference
The complete visual product flow reference is available at [`docs/architecture/DealFlow360_End_to_End_Product_Flow.png`](docs/architecture/DealFlow360_End_to_End_Product_Flow.png). It details the eventual 18-screen lifecycle of DealFlow360 from login to Razorpay reconciliation.
