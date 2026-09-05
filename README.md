# DealFlow360

> **"DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."**

DealFlow360 is an enterprise deal orchestration and discount governance platform designed to guide deals end-to-end—from initial quotation, dynamic policy and margin protection, multi-warehouse fulfillment, and customer negotiation, through to automated billing and payment settlement.

---

### Current Status: G15 Complete (Phases 001–075)

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
  - **Phase 014**: Database Base Models (Foundational `DeclarativeBase` with deterministic PostgreSQL constraint naming conventions).
  - **Phase 015**: User Model (Foundational `User` entity, `users` table migration `239bb096c8fd`, UUID primary key, indexed unique email, active flag, timestamps).
- **G04 (Phases 016–020 Core Database Models)**:
  - **Phase 016**: Role Model (`Role` entity, `roles` table, unique name, `user_roles` association).
  - **Phase 017**: Permission Model (`Permission` entity, `permissions` table, resource-action pair, `role_permissions` association).
  - **Phase 018**: Company Model (`Company` entity, `companies` table, organization profile, `users` and `customers` relationships).
  - **Phase 019**: Customer Model (`Customer` entity, `customers` table, scoped customer_code uniqueness, company FK, tier FK).
  - **Phase 020**: Customer Tier Model (`CustomerTier` entity, `customer_tiers` table, unique name/code, discount limit check constraint).
- **G05 (Phases 021–025 Product, Warehouse, Audit & Seed Foundation)**:
  - **Phase 021**: Product Model (`Product` entity, `products` table, unique sku, cost, base price, tax rate, unit, category relationship).
  - **Phase 022**: Product Category Model (`ProductCategory` entity, `product_categories` table, unique code and name, `products` relationship).
  - **Phase 023**: Warehouse Model (`Warehouse` entity, `warehouses` table, scoped `(company_id, code)` uniqueness, company relationship).
  - **Phase 024**: Audit Log Model (`AuditLog` entity, `audit_logs` table, append-only without `updated_at`, PostgreSQL JSONB `context_metadata`, nullable user/company FKs).
  - **Phase 025**: Database Seed System (`backend/app/db/seed.py`, deterministic, idempotent master reference data seeding).
- **G06 (Phases 026–030 Authentication Foundation)**:
  - **Phase 026**: User Registration (`POST /api/v1/auth/register`, Argon2id password hashing, email normalization, safe User response).
  - **Phase 027**: Login (`POST /api/v1/auth/login`, constant-time credential validation, inactive account rejection, access/refresh token issuance).
  - **Phase 028**: JWT Authentication (`get_current_user` dependency, Bearer token verification, `GET /api/v1/auth/me` protected context).
  - **Phase 029**: Password Hashing (`app/core/security.py`, Argon2id password hasher with constant-time verification, no plaintext storage).
  - **Phase 030**: Refresh Token (`POST /api/v1/auth/refresh`, server-side `RefreshToken` rotation model, replay attack prevention).
- **G07 (Phases 031–035 Logout + RBAC Foundation + Business Roles)**:
  - **Phase 031**: Logout (`POST /api/v1/auth/logout`, server-side refresh token revocation, session invalidation).
  - **Phase 032**: Role-Based Access Control (`app/services/rbac.py`, role/permission lookup, duplicate-safe role assignment/removal).
  - **Phase 033**: Sales Representative Role (canonical role definition, quotation draft/read capabilities).
  - **Phase 034**: Sales Manager Role (canonical role definition, quotation review/approve capabilities).
  - **Phase 035**: Finance & Operations Roles (canonical roles for margin/billing oversight and warehouse/logistics management).
- **G08 (Phases 036–040 Authorization Extensions & Auth UI)**:
  - **Phase 036**: Customer Portal Role (canonical role definition, scoped customer/quote/product viewing permissions).
  - **Phase 037**: Admin Role (canonical role definition, comprehensive administrative permissions).
  - **Phase 038**: Object-Level Authorization (`app/services/authorization.py`, `AuthorizationService`, multi-tenant isolation, company boundary validation, customer resource access checks).
  - **Phase 039**: Permission Middleware (`app/api/v1/endpoints/deps.py`, `require_permission` and `require_role` FastAPI dependency factories).
  - **Phase 040**: Authentication UI & Token Security Hardening (in-memory access tokens, HttpOnly refresh cookie rotation, `ProtectedRoute` wrapper).
- **G09 (Phases 041–045 Application Shell & UI State)**:
  - **Phase 041**: Application Shell (`ApplicationShell` responsive container, desktop sidebar & mobile drawer).
  - **Phase 042**: Global Navigation (`NAVIGATION_ITEMS` centralized structure with typed icons and routes).
  - **Phase 043**: Role-Aware Navigation (`filterNavItems` role filtering, canonical role views).
  - **Phase 044**: Global UI State (`UIContext` managing sidebar collapse and mobile drawer toggle with Escape listener).
  - **Phase 045**: Design System Integration (`Button`, `Badge`, `Card` reusable Tailwind primitives).
- **G10 (Phases 046–050 Navigation & UI States)**:
  - **Phase 046**: Top Navigation (`TopNav` component, header banner, brand, active route title, user info, role badge, sign-out action).
  - **Phase 047**: Responsive Layout (Accessible skip-to-content link, horizontal overflow prevention, responsive desktop/mobile transitions).
  - **Phase 048**: Loading States (`LoadingState` with spinner, inline, page, and skeleton variants, root `app/loading.tsx` boundary).
  - **Phase 049**: Empty States (`EmptyState` with contextual variants, role region semantics, title, description, and action slots).
  - **Phase 050**: Error States (`ErrorState` with generic, server, network, notFound, and permission variants, `app/error.tsx`, `app/not-found.tsx`).
- **G11 (Phases 051–055 UI Infrastructure)**:
  - **Phase 051**: Toast Notifications (`ToastContext`, `useToast`, `ToastContainer` with success, error, warning, and info variants, auto-dismiss, ARIA live regions).
  - **Phase 052**: Modal System (`Modal` component with focus trap, backdrop dismissal, escape key listener, scroll containment, and default/destructive/confirmation variants).
  - **Phase 053**: Form System (`FormItem`, `FormLabel`, `FormControl`, `Input`, `Textarea`, `Select`, `Checkbox` with accessible error wiring and ARIA descriptions).
  - **Phase 054**: Data Table System (`DataTable` typed generic table with column definitions, sorting, pagination, selectable rows, and integrated loading/empty/error states).
  - **Phase 055**: Charts System (`LineChart`, `BarChart`, `AreaChart`, `DonutChart` responsive SVG chart primitives with accessible data representations).
- **G12 (Phases 056–060 Customer Management Foundation)**:
  - **Phase 056**: Customer CRUD (`POST`, `GET`, `PUT`, `DELETE /api/v1/customers`, company tenant isolation, code uniqueness, soft deletion, responsive list & create/edit modals).
  - **Phase 057**: Customer Profile (`GET /api/v1/customers/{id}`, `/customers/[id]` page, contact, address, metadata, system timestamps).
  - **Phase 058**: Customer Tier Management (`PATCH /api/v1/customers/{id}/tier`, `CustomerTier` validation, discount ceiling display & modal switching).
  - **Phase 059**: Customer Purchase History (`GET`, `POST /api/v1/customers/{id}/purchase-history`, `customer_purchase_history` table, `DataTable` view, transaction recording).
  - **Phase 060**: Customer Deal History (`GET`, `POST /api/v1/customers/{id}/deal-history`, `customer_deal_history` table, `DataTable` view, lifecycle stages).
- **G13 (Phases 061–065 Customer Financial Intelligence Foundation)**:
  - **Phase 061**: Customer Discount History (`GET`, `POST /api/v1/customers/{id}/discount-history`, `customer_discount_history` table, normalized append-only historical discount model, service, API, and profile integration).
  - **Phase 062**: Customer Payment History (`GET`, `POST /api/v1/customers/{id}/payment-history`, `customer_payment_history` table, normalized append-only historical payment model, service, API, and profile integration).
  - **Phase 063**: Customer LTV Calculation (`CustomerFinancialIntelligenceService.calculate_ltv`, deterministic customer-level lifetime value aggregation across purchases/settlements with zero-division safety).
  - **Phase 064**: Customer Discount Sensitivity (`CustomerFinancialIntelligenceService.calculate_discount_sensitivity`, deterministic explainable sensitivity scoring: `LOW`, `MODERATE`, `HIGH`, `INSUFFICIENT_DATA`).
  - **Phase 065**: Customer Risk Profile (`CustomerFinancialIntelligenceService.calculate_risk_profile`, deterministic multi-factor risk scoring: `LOW`, `MEDIUM`, `HIGH`, payment failure ratio, inactive account penalty).
- **G14 (Phases 066–070 Customer Analytics, Search, Filtering, Segmentation, Dashboard)**:
  - **Phase 066**: Customer Analytics (`GET /api/v1/customers/analytics`, deterministic portfolio aggregations, total customers, tier distribution breakdown, financial totals).
  - **Phase 067**: Customer Search (Multi-field case-insensitive partial matching across `customer_code`, `name`, `email`, and `phone`, debounced UI input).
  - **Phase 068**: Customer Filtering (Composable query filtering by `is_active`, `tier_id`, and search keyword with instant reset capability).
  - **Phase 069**: Customer Segmentation (`GET /api/v1/customers/segmentation`, deterministic rule-based explainable categorization: Champions, Growth Potential, Discount Dependent, At Risk, Unclassified).
  - **Phase 070**: Customer Dashboard (`GET /api/v1/customers/dashboard`, consolidated KPI summary cards, interactive DonutChart and BarChart visualizations, directory and segmentation views).
- **G15 (Phases 071–075 Product CRUD, Categories, Pricing, Cost, Margin)**:
  - **Phase 071**: Product CRUD (`GET`, `POST`, `PUT`, `DELETE /api/v1/products`, complete catalog lifecycle, SKU uniqueness, soft deletion, pagination, and audit trails).
  - **Phase 072**: Product Categories (`GET`, `POST`, `PUT`, `DELETE /api/v1/product-categories`, classification grouping, code/name uniqueness, relationship integrity, reference safety).
  - **Phase 073**: Product Pricing (Explicit deterministic base selling price, `base_price >= 0` validation, Decimal precision, currency-safe representation).
  - **Phase 074**: Product Cost (Explicit product unit cost management, `cost >= 0` validation, Decimal precision).
  - **Phase 075**: Product Margin (Deterministic gross margin amount `base_price - cost`, margin percentage `((base_price - cost) / base_price) * 100`, zero-division safety when price is zero, live modal calculation).

### ⏳ Not Yet Implemented (Scheduled for Future Authorized Phases)
- Phase 076+ (Product Tax, Product Units, Product Variants, Product Attributes, Subscriptions, Inventory, Product Search/Filtering/Dashboard)
- Warehouses and Logistics Fulfillment Engine
- Quotation Business Logic, Pricing Engine, and Discount Matrix
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
