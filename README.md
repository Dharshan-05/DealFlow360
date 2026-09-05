# DealFlow360

> **"DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."**

DealFlow360 is an enterprise deal orchestration and discount governance platform designed to guide deals end-to-end—from initial quotation, dynamic policy and margin protection, multi-warehouse fulfillment, and customer negotiation, through to automated billing and payment settlement.

---

### Current Status: G21 Complete (Phases 001–105)

Implementation strictly adheres to the **520-Phase Master Implementation Roadmap**. Development is strictly phased to ensure clean, decoupled architecture without premature mock modules.

### ✅ Implemented Foundations
- **G01 (Phases 001–005)**: Project Foundation (Monorepo, Next.js, FastAPI, health endpoints).
- **G02 (Phases 006–010)**: Configuration, Versioning & Global Error Handling.
- **G03 (Phases 011–015)**: Database Foundation, PostgreSQL, SQLAlchemy 2.0, Alembic, and User Model.
- **G04 (Phases 016–020)**: Core RBAC, Company, Customer, and Customer Tier Models.
- **G05 (Phases 021–025)**: Product, Category, Warehouse, Audit Log, and Seed Foundation.
- **G06 (Phases 026–030)**: Authentication (Register, Login, JWT, Argon2id, Refresh Tokens).
- **G07 (Phases 031–035)**: Logout, RBAC Service, and Canonical Business Roles.
- **G08 (Phases 036–040)**: Customer Portal, Admin, Object-Level Authorization, and Security Hardening.
- **G09 (Phases 041–045)**: Application Shell, Global Navigation, Role-Aware Nav, UI State, Design System.
- **G10 (Phases 046–050)**: Top Navigation, Responsive Layout, Loading, Empty, and Error States.
- **G11 (Phases 051–055)**: UI Infrastructure (Toasts, Modals, Forms, DataTable, Charts).
- **G12 (Phases 056–060)**: Customer Management Foundation (CRUD, Profile, Tiers, Purchase & Deal History).
- **G13 (Phases 061–065)**: Customer Financial Intelligence (Discount/Payment History, LTV, Sensitivity, Risk).
- **G14 (Phases 066–070)**: Customer Analytics, Multi-field Search, Filtering, Segmentation & Dashboard.
- **G15 (Phases 071–075)**: Product CRUD, Categories, Base Pricing, Unit Cost, and Gross Margins.
- **G16 (Phases 076–080)**: Product Tax, Units, Variants, Attributes, and Subscription Products.
- **G17 (Phases 081–085)**: Recurring Frequency, Product Inventory, Search, Filtering, and Product Dashboard.
- **G18 (Phases 086–090 Warehouse & Inventory Foundation)**:
  - **Phase 086**: Warehouse CRUD (Facility lifecycle management, unique code per company, location metadata, safe soft deactivation).
  - **Phase 087**: Warehouse Stock (Warehouse-specific inventory balance tracking `WarehouseStock` model, `quantity >= 0`, `reserved_quantity <= quantity`).
  - **Phase 088**: Stock Availability API (Deterministic evaluation of stock quantity, reserved quantity, and available quantity per warehouse & product).
  - **Phase 089**: Reserved Stock (Foundational reserve and release operations preserving non-negative quantities and stock integrity).
  - **Phase 090**: Available-to-Promise (ATP) Calculation (Deterministic calculation `ATP = max(quantity - reserved_quantity, 0)`, reusable `AvailableToPromiseService`).
- **G19 (Phases 091–095 Warehouse Priority & Allocation)**:
  - **Phase 091**: Warehouse Priority (Deterministic fulfillment priority `priority: int >= 1` with 1 = highest priority, index, and check constraint).
  - **Phase 092**: Warehouse Selection (`WarehouseSelectionService` determining preferred facility for requested quantity based on priority and ATP).
  - **Phase 093**: Multi-Warehouse Stock (`MultiWarehouseStockService` aggregating physical stock, reservations, and ATP across all facilities).
  - **Phase 094**: Fulfillment Allocation (`FulfillmentAllocationService` sequentially allocating requested quantities up to ATP in priority order without backorders).
  - **Phase 095**: Stock Reservation (`StockReservationService` performing transaction-locked atomic reservations with pessimistic row locking `with_for_update()`).
- **G20 (Phases 096–100 Inventory, Backorders & Fulfillment Operations)**:
  - **Phase 096**: Backorder Engine (`Backorder` entity created when requested quantity exceeds available allocation; supports `OPEN`, `FULFILLED`, `CANCELLED` statuses without mutating stock).
  - **Phase 097**: Partial Fulfillment (`Fulfillment` entity orchestrating priority allocation, stock reservation, and backorder linkage; supports `PENDING`, `PARTIALLY_FULFILLED`, `FULFILLED`).
  - **Phase 098**: Delivery Status (`FulfillmentService.update_delivery_status` state machine enforcing `NOT_STARTED` -> `READY` -> `DISPATCHED` -> `IN_TRANSIT` -> `DELIVERED` with AuditLog history).
  - **Phase 099**: Inventory Alerts (`InventoryAlertService` scanning for `OUT_OF_STOCK` [CRITICAL], `LOW_STOCK` [WARNING], and `BACKORDER` [WARNING] with automatic deduplication and resolution).
  - **Phase 100**: Inventory Dashboard (`InventoryDashboardService` aggregating total physical, reserved, ATP, out-of-stock/low-stock counts, open backorders, fulfillment distributions, and active alerts at `/inventory`).
- **G21 (Phases 101–105 Discount Governance Foundation)**:
  - **Phase 101**: Discount Configuration (`DiscountConfiguration` entity managing company-wide baseline discount ceilings, effective validity windows, and ownership tracking).
  - **Phase 102**: Customer Discount Ceiling (`CustomerDiscountCeiling` entity establishing account-specific maximum discount limits with partial unique index protecting active records).
  - **Phase 103**: Category Discount Ceiling (`CategoryDiscountCeiling` entity establishing product category discount limits with partial unique index preventing active duplicates).
  - **Phase 104**: Product Discount Ceiling (`ProductDiscountCeiling` entity establishing SKU-level maximum discount limits protecting high-demand / high-cost product margins).
  - **Phase 105**: Sales Rep Authority Limit (`SalesRepAuthorityLimit` entity establishing user-level maximum discretionary discount limits; strictly enforces prohibition against Sales Rep self-escalation or self-modification).

### ⏳ Not Yet Implemented (Scheduled for Future Authorized Phases)
- Phase 106+ (Manager Authority Limits, Finance Authority Limits, Policy Evaluation Engine, Discount Validation Engine, Recommended Discounts, Margin Protection Engine, Discount Decision Engine)
- Quotation Business Logic, Pricing Engine, and Discount Matrix
- AI Discount Governance Engine & Approval Routing
- Machine Learning Risk Scoring & Explainability
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
│   │       ├── 239bb096c8fd_create_users_table.py
│   │       └── 92dfce60f7a1_create_core_models_phases_016_020.py
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
│   │   ├── models/
│   │   │   ├── __init__.py       # Model registry exporting all core models
│   │   │   ├── associations.py   # user_roles & role_permissions M2M tables
│   │   │   ├── company.py        # Phase 018 Company model
│   │   │   ├── customer.py       # Phase 019 Customer model
│   │   │   ├── customer_tier.py  # Phase 020 CustomerTier model
│   │   │   ├── permission.py     # Phase 017 Permission model
│   │   │   ├── role.py           # Phase 016 Role model
│   │   │   └── user.py           # Phase 015 User model
│   │   ├── schemas/
│   │   │   └── response.py       # Standardized response envelopes
│   │   ├── main.py               # FastAPI entrypoint & router mounts
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_core_models.py   # G04 core models & relationships tests
│   │   ├── test_database.py      # Database engine, session, Alembic tests
│   │   ├── test_errors.py        # Global error handling test suite
│   │   ├── test_health.py        # Health & OpenAPI test suite
│   │   ├── test_user_model.py    # Phase 015 User model & persistence tests
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
alembic upgrade head
```

To run test suite:
```bash
pytest
```
