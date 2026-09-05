# DealFlow360 — Architectural Reference

## 1. Product Vision & Flow Reference
The visual flow diagram located at `docs/architecture/DealFlow360_End_to_End_Product_Flow.png` represents the **target product vision** for DealFlow360.

### Core Business Purpose
> "DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."

The central decision layer is the **Discount Governance Engine**, which continuously assesses deals across key dimensions:
- Customer Tier (Bronze, Silver, Gold)
- Product & Category Limits
- Sales Representative & Management Authority
- Product Cost & Blended Margin Floor
- Deal Value & Multi-warehouse Inventory Situation
- AI Risk Scoring & Factor Explainability

---

## 2. Implementation Scope vs. Product Vision

> [!IMPORTANT]
> The architectural diagram represents the **FINAL END-TO-END PRODUCT VISION**.
> It does **NOT** authorize premature implementation of future modules.
> The **520-phase DealFlow360 Roadmap** strictly governs the sequence of development.

### Scope Distinction:
- **Product/UX Flow Reference**: Defines screen relationships, future data-model boundaries, state transitions, and integration points.
- **Phase Roadmap**: Defines the active, authorized implementation scope.

---

## 3. Current Phase Status: G01 (Phases 001–005)

The current phase is strictly limited to foundational setup:
- **Phase 001**: Project Initialization
- **Phase 002**: Git Repository Setup & Secret Protection
- **Phase 003**: Monorepo Architecture
- **Phase 004**: Frontend Next.js Foundation
- **Phase 005**: Backend FastAPI Foundation

### Excluded from G01 (Reserved for Future Authorized Phases):
- ❌ Database, PostgreSQL, SQLAlchemy, Alembic
- ❌ Authentication, JWT, RBAC, Multi-role logins
- ❌ Customer & Product Management
- ❌ Quotation Lifecycle & Line Items
- ❌ Discount Governance Rules & Approval Chains
- ❌ AI Risk Scoring, SHAP Explainability, ML Models
- ❌ Multi-Warehouse Inventory & Fulfillment
- ❌ Customer Portal Negotiation & AI Intent Extraction
- ❌ Invoicing, Milestones, and Razorpay Payments
- ❌ Deal Health Telemetry & Anomaly Analytics
- ❌ Mock APIs or fake business placeholders

Future phases will cleanly build on top of the modular monorepo foundation established in G01.
