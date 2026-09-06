# 🚀 DEALFLOW360

### Intelligent End-to-End Deal Management & Governance Platform

[![CI/CD Pipeline](https://github.com/Dharshan-05/DealFlow360/actions/workflows/ci.yml/badge.svg)](https://github.com/Dharshan-05/DealFlow360/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0%2B-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.0%2B-646CFF.svg)](https://vitejs.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7%2B-3178C6.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B%20%2F%2016%2B-336791.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-28%20Migrations-red.svg)](https://alembic.sqlalchemy.org/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind-v4.0-38B2AC.svg)](https://tailwindcss.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-452%20Passing-success.svg)](#-testing--quality-assurance)

> **"DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."**

**DEALFLOW360** is an enterprise-grade, multi-tenant deal orchestration, discount governance, and revenue intelligence platform. Designed to eliminate margin leakage, spreadsheet fragmentation, and approval bottlenecks, DEALFLOW360 provides end-to-end guidance and automated guardrails across the entire commercial lifecycle:

$$\text{Discover} \longrightarrow \text{Qualify} \longrightarrow \text{Analyze} \longrightarrow \text{Collaborate} \longrightarrow \text{Negotiate} \longrightarrow \text{Approve} \longrightarrow \text{Execute} \longrightarrow \text{Track} \longrightarrow \text{Close}$$

---

## 📸 Architectural Blueprint & Product Flow

The target product flow illustrates how commercial opportunities progress through multi-warehouse inventory allocation, discount governance ceilings, AI risk scoring, quotation generation, multi-tier approvals, deal conversion, and downstream invoicing.

![DealFlow360 End-to-End Product Flow](docs/architecture/DealFlow360_End_to_End_Product_Flow.png)

---

## 📑 Table of Contents

1. [Platform Overview](#-platform-overview)
2. [The Problem Statement](#-the-problem-statement)
3. [The Solution](#-the-solution)
4. [Key Features & Implementation Status Matrix](#-key-features--implementation-status-matrix)
5. [The Commercial Deal Lifecycle](#-the-commercial-deal-lifecycle)
6. [Deal Management Engine](#-deal-management-engine)
7. [Pipeline & Kanban Board](#-pipeline--kanban-board)
8. [Operational Dashboards & Command Center](#-operational-dashboards--command-center)
9. [AI, Machine Learning & Revenue Intelligence](#-ai-machine-learning--revenue-intelligence)
10. [Approval Engine & Governance Workflow](#-approval-engine--governance-workflow)
11. [Multi-Warehouse Inventory & Fulfillment](#-multi-warehouse-inventory--fulfillment)
12. [Customer Negotiation Portal](#-customer-negotiation-portal)
13. [Subscriptions & Invoicing Engine](#-subscriptions--invoicing-engine)
14. [Real-time WebSockets & Event Bus](#-real-time-websockets--event-bus)
15. [User Roles & RBAC Matrix](#-user-roles--rbac-matrix)
16. [Security & Production Guardrails](#-security--production-guardrails)
17. [Technical System Architecture](#-technical-system-architecture)
18. [Interactive Mermaid Diagrams](#-interactive-mermaid-diagrams)
19. [Technology Stack](#-technology-stack)
20. [Project Structure](#-project-structure)
21. [Database Schema & Persistence Models](#-database-schema--persistence-models)
22. [API Documentation & Verified Endpoints](#-api-documentation--verified-endpoints)
23. [Installation & Getting Started](#-installation--getting-started)
24. [Environment Configuration](#-environment-configuration)
25. [Running Locally](#-running-locally)
26. [DevOps & Production Deployment (Without Docker)](#-devops--production-deployment-without-docker)
27. [Testing & Quality Assurance](#-testing--quality-assurance)
28. [End-to-End Demo Walkthrough](#-end-to-end-demo-walkthrough)
29. [Enterprise Use Cases](#-enterprise-use-cases)
30. [Competitive Differentiation](#-competitive-differentiation)
31. [Product Philosophy](#-product-philosophy)
32. [Implementation Roadmap](#-implementation-roadmap)
33. [Known Limitations & Transparency](#-known-limitations--transparency)
34. [Responsible AI & Governance Principles](#-responsible-ai--governance-principles)
35. [Contributing Guidelines](#-contributing-guidelines)
36. [License & Acknowledgments](#-license--acknowledgments)
37. [Hackathon Evaluator Summary](#-hackathon-evaluator-summary)

---

## 🌐 Platform Overview

### What is DEALFLOW360?
DEALFLOW360 is a full-stack deal lifecycle platform unifying CRM capabilities with strict financial margin governance, multi-warehouse Available-to-Promise (ATP) inventory allocation, machine learning risk assessment, multi-stakeholder approval hierarchies, and downstream billing execution.

### What problem does it solve?
Traditional CRMs treat deals as passive database records where sales reps enter speculative numbers and arbitrary discounts. This leads to **silent margin erosion**, unfulfillable delivery promises, opaque email-based approval delays, and disconnected post-sale invoicing. DEALFLOW360 acts as a continuous governor: every quote is validated against active discount policies, blended margin floors, inventory ATP, and ML risk scores before commitments can be made.

### Who is it for?
* **B2B Sales Teams & Account Executives**: Quote complex product mixes with instant feedback on pricing safety, margin health, and AI-recommended upsells.
* **Sales Directors & Deal Desk Managers**: Prevent rogue discounting with automated approval routing, SLA timers, and team velocity metrics.
* **Finance Officers & Controllers**: Enforce non-negotiable gross margin thresholds and monitor expected probability-weighted pipeline revenue.
* **Operations & Fulfillment Leads**: Prevent overselling through real-time multi-warehouse stock reservation and automated backorder generation.
* **Enterprise Customers**: Review quotes, engage in structured counter-offer negotiations, and accept agreements through a dedicated Customer Portal.

---

## ⚠️ The Problem Statement

Mid-market and enterprise organizations lose **3% to 8% of top-line revenue annually** to operational inefficiencies across the deal cycle:

| Operational Bottleneck | Real-World Consequence | DEALFLOW360 Solution |
| :--- | :--- | :--- |
| **Rogue Discretionary Discounting** | Sales reps offer steep discounts to hit quota, wiping out operating profit margins. | Real-time **Discount Governance Engine** with hierarchical company, customer, category, and product ceilings. |
| **Inventory Blind Spots** | Sales teams commit to delivery dates for products that are out of stock or reserved. | Deterministic **Available-to-Promise (ATP)** service with transaction-locked stock reservations. |
| **Approval Deadlocks** | Exception requests stall in executive inboxes, causing deals to go cold. | Multi-tier **Approval Decision Engine** with auto-approvals, SLA monitors, and auto-escalations. |
| **Disconnected Systems** | Quotes exist in PDFs, pipeline in CRMs, inventory in ERPs, and billing in spreadsheets. | Unified **Single Source of Truth** connecting Catalog → Stock → Quote → Deal → Invoice. |
| **Black-Box Deal Health** | Executives discover stalled or slipping deals only at end-of-quarter reviews. | **Deal Health Engine** evaluating stall probability, delay risk, and behavioral anomalies. |

---

## 💡 The Solution

DEALFLOW360 replaces fragmented tooling with a closed-loop governance architecture:

```text
       ┌────────────────────────────────────────────────────────┐
       │                   DEAL DISCOVERY                       │
       │  Customer Profiling • Tiers • Historical Financials    │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             CATALOG & INVENTORY ALLOCATION             │
       │  Multi-Warehouse ATP • Stock Reservation • Backorders  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            DISCOUNT & MARGIN GOVERNANCE                │
       │  4-Tier Ceilings • Actor Limits • Decimal Margin Math  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             AI / ML REVENUE INTELLIGENCE               │
       │  50-Feature Risk Trees • Upsell/Cross-sell • Health    │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             APPROVAL ORCHESTRATION LAYER               │
       │  Auto-Approval • Manager/Director/VP/Finance • SLA     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            QUOTATION & CUSTOMER NEGOTIATION            │
       │  ReportLab Vector PDF • Portal Review • Counter-Offers │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             COMMERCIAL DEAL CONVERSION                 │
       │  Atomic Quote-to-Deal • Win Probability • Forecast     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             FULFILLMENT & BILLING SETTLEMENT           │
       │  Delivery State Machine • Invoicing • Subscriptions   │
       └────────────────────────────────────────────────────────┘
```

---

## 📊 Key Features & Implementation Status Matrix

Every capability listed below is verified directly against the underlying codebase:

| Category | Platform Capability | Repository Evidence | Status |
| :--- | :--- | :--- | :---: |
| **Authentication & RBAC** | Argon2id password hashing, JWT access & refresh token rotation | `app/core/security.py`, `app/models/user.py`, `app/models/refresh_token.py` | ✅ Implemented |
| **Multi-Tenancy** | Strict tenant isolation via `company_id` foreign keys & session filters | `app/api/v1/endpoints/deps.py`, `app/db/base.py` | ✅ Implemented |
| **Customer Intelligence** | Customer 360, tiers (Bronze/Silver/Gold), LTV, price sensitivity | `app/models/customer.py`, `app/services/customer_financial_intelligence.py` | ✅ Implemented |
| **Product Catalog** | Base pricing, unit cost, variants, attributes, recurring frequencies | `app/models/product.py`, `app/models/product_variant.py` | ✅ Implemented |
| **Multi-Warehouse Stock** | Multi-facility tracking, Available-to-Promise (ATP), row locking | `app/models/warehouse_stock.py`, `app/services/atp.py`, `stock_reservation.py` | ✅ Implemented |
| **Fulfillment & Delivery**| Priority allocation, auto-backorders, 5-stage delivery state machine | `app/models/fulfillment.py`, `app/models/backorder.py`, `fulfillment.py` | ✅ Implemented |
| **Discount Governance** | 4-tier ceilings (Company/Customer/Category/Product), Actor limits | `app/models/discount_configuration.py`, `app/services/discount_governance.py` | ✅ Implemented |
| **Margin Protection** | Exact Decimal financial math, negative margin detection, floor bounds | `app/services/discount_intelligence.py`, `app/services/deal.py` | ✅ Implemented |
| **Decision Automation** | Automated discount evaluation, rule engine, idempotency tracking | `app/services/discount_automation.py`, `app/models/applied_discount.py` | ✅ Implemented |
| **Tree-Based ML Risk** | Pure-Python 2nd-order Taylor XGBoost, LightGBM, Random Forest, SHAP | `app/services/ml_risk.py`, `app/api/v1/endpoints/ml_risk.py` | ✅ Implemented |
| **AI Upsell / Cross-Sell**| Collaborative & Content filtering, affinity mining, Next-Best-Product | `app/services/recommendations.py`, `app/models/recommendation_event.py` | ✅ Implemented |
| **Quotation Engine** | Line items, taxes, overall discounts, versioning, ReportLab PDF | `app/models/quotation.py`, `app/services/quotation.py` | ✅ Implemented |
| **Approval Engine** | Multi-level (Manager/Director/VP/Finance), auto-approval, SLA, escalations | `app/models/approval_execution.py`, `app/services/approval_execution.py` | ✅ Implemented |
| **Commercial Deals** | Atomic quote conversion, DealProduct, DealActivity, win probability | `app/models/customer_deal_history.py`, `app/models/deal.py`, `deal.py` | ✅ Implemented |
| **Deal Health Telemetry** | 0–100 health score, stall/delay risk, 8 alert triggers, nudges | `app/models/deal_health.py`, `app/services/deal_health.py` | ✅ Implemented |
| **Customer Portal** | Customer quote review, negotiation comments, counter-offers, acceptance | `app/models/portal.py`, `app/services/portal/`, `portal.py` | ✅ Implemented |
| **Subscriptions & Invoices**| Recurring billing plans, subscriptions, usage records, hybrid invoices | `app/models/billing.py`, `app/services/billing/`, `billing.py` | ✅ Implemented |
| **Realtime WebSockets** | Full-duplex WebSocket `/api/v1/ws`, JWT auth, topic channels, event bus | `app/api/v1/endpoints/ws.py`, `app/services/connection_manager.py` | ✅ Implemented |
| **AI Copilot & Tools** | LangChain-style Orchestrator, OpenAI/Grok provider, 13 domain tools | `app/ai/orchestrator.py`, `app/ai/tools.py`, `app/ai/providers/` | ✅ Implemented |
| **RAG Knowledge Base** | Vector search, document ingestion, cosine similarity, source citations | `app/rag/service.py`, `app/rag/models.py`, `app/api/v1/endpoints/knowledge.py` | ✅ Implemented |
| **Business Analytics** | Sales, Customer, Inventory, Approval reports, CSV/JSON exporters | `app/reporting/services.py`, `app/reporting/queries.py` | ✅ Implemented |
| **Payment Gateway** | Live payment gateway integration (Razorpay / Stripe webhooks) | *Internal settlement mocked via `PortalPaymentService`* | 📋 Planned |
| **Containerization** | Docker / Docker Compose containers | *Phase G25 explicitly implemented bare-metal Linux/Nginx/PM2* | 📋 Planned |

---

## 🔄 The Commercial Deal Lifecycle

Every deal in DEALFLOW360 follows an auditable lifecycle state machine:

```mermaid
flowchart TD
    NEW([Stage: NEW]) --> QUALIFIED([Stage: QUALIFIED])
    QUALIFIED --> PROPOSAL([Stage: PROPOSAL])
    PROPOSAL --> NEGOTIATION([Stage: NEGOTIATION])
    NEGOTIATION --> CLOSED_WON([Stage: CLOSED_WON])
    NEGOTIATION --> CLOSED_LOST([Stage: CLOSED_LOST])
    PROPOSAL --> CLOSED_LOST
    NEW --> CLOSED_LOST
    QUALIFIED --> CLOSED_LOST

    classDef stage fill:#0d1117,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef won fill:#052e16,stroke:#22c55e,stroke-width:2px,color:#fff;
    classDef lost fill:#450a0a,stroke:#ef4444,stroke-width:2px,color:#fff;
    class NEW,QUALIFIED,PROPOSAL,NEGOTIATION stage;
    class CLOSED_WON won;
    class CLOSED_LOST lost;
```

### Stage Transitions & Operational Milestones:
1. **`NEW`**: Opportunity identified. Account details and preliminary transaction scope recorded.
2. **`QUALIFIED`**: Customer profile verified against historical credit, payment reliability score, and relationship tier.
3. **`PROPOSAL`**: Line items configured. ATP inventory allocated, discount policy checks executed, and formal vector PDF quotation generated (`QT-YYYYMM-XXXX`).
4. **`NEGOTIATION`**: Customer reviews quote via Customer Portal. Real-time counter-offers or discount concession requests trigger internal Approval Engine workflows.
5. **`CLOSED_WON`**: Customer accepts agreement. Quotation atomically converts into an active commercial deal record (`CustomerDealHistory`), reserving inventory and scheduling billing.
6. **`CLOSED_LOST`**: Terminal outcome. Requires mandatory loss categorization reason code to train historical win/loss analytics.

---

## 💼 Deal Management Engine

Commercial deals are managed via the unified `CustomerDealHistory` entity (`app/models/customer_deal_history.py`) and associated child records:

* **Commercial Terms**: Deal Code, Title, Deal Value, Owner (Sales Rep), Quotation Lineage ID & Version.
* **Financial & Margin Precision**:
  * All monetary values utilize Python `Decimal` and PostgreSQL `Numeric(14, 2)` with `ROUND_HALF_UP` precision.
  * Reconciles `subtotal`, `discount_amount`, `discount_percent`, `tax_amount`, `total_cost`, `gross_profit`, and `margin_percentage`.
  * Categorizes margin health: `HEALTHY` ($\ge 40\%$), `MODERATE` ($25-39\%$), `THIN` ($10-24\%$), or `CRITICAL` ($<10\%$).
* **Product Line Items (`DealProduct`)**:
  * Line-item catalog snapshots preserving historical unit price, unit cost, line discounts, tax rates, and individual gross margin contributions.
* **Append-Only Activity Stream (`DealActivity`)**:
  * Audit-logged interactions: `NOTE`, `CALL`, `EMAIL`, `MEETING`, `TASK`, `FOLLOW_UP`, `STAGE_CHANGE`, `APPROVAL`, `QUOTE_SENT`, `QUOTE_ACCEPTED`, `QUOTE_REJECTED`.
* **Deterministic Win Probability & Forecasting**:
  * Win probability ($0-100\%$) evaluated deterministically using stage baselines, customer tier history, margin health, and activity recency.
  * Expected Revenue calculated as:
    $$\text{Expected Revenue} = \text{Deal Value} \times \left(\frac{\text{Probability}}{100}\right)$$

---

## 📋 Pipeline & Kanban Board

The Deals view (`frontend/src/pages/Deals.tsx`) provides high-velocity pipeline management:

* **Dual Display Modes**: Instant toggle between an interactive **Kanban Board** and a structured **Data Table**.
* **Stage Transitions**: Drag-and-drop or single-click stage updates with immediate backend synchronization via `PATCH /api/v1/deals/{id}/stage`.
* **Multi-Dimensional Filtering**: Search by deal title or customer name, filter by Stage (`NEW`, `QUALIFIED`, `PROPOSAL`, `NEGOTIATION`, `CLOSED_WON`, `CLOSED_LOST`), or filter by Sales Rep.
* **Dynamic Pipeline Metrics**:
  * Total Pipeline Volume & Value
  * Probability-Weighted Expected Revenue
  * Blended Gross Margin %
  * Active Win Rate %
* **Deal Detail Drawer**: Deep-dive into line-item catalogs, stage progression history, and active Deal Health signals.

---

## 🖥️ Operational Dashboards & Command Center

DEALFLOW360 delivers domain-specific command centers powered by Recharts:

1. **Command Center (`/command`)**: Executive overview showing total transaction volume, monthly revenue trajectory area charts, live action alerts, and recent deal velocity.
2. **Deals Pipeline Dashboard (`/deals`)**: Pipeline distribution across lifecycle stages, top opportunities by value, and margin exposure summaries.
3. **Inventory Dashboard (`/inventory`)**: Warehouse capacity, overall physical vs. reserved quantities, real-time ATP, low-stock alerts, and open backorder backlogs.
4. **Approval Governance Dashboard (`/approvals`)**: Pending review queues, average turnaround latency (minutes), SLA breach risk counts, and bottleneck heatmaps.
5. **AI Risk Dashboard (`/risk`)**: Pipeline risk tier distributions (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), model evaluation telemetry (ROC-AUC, PR-AUC, Brier score), and top contributing risk factors.
6. **Analytics & Reports (`/analytics`)**: Historical revenue recognition, conversion funnels, customer cohort performance, and scheduled automated reporting.

---

## 🤖 AI, Machine Learning & Revenue Intelligence

DEALFLOW360 avoids black-box claims by implementing **strictly verified, inspectable machine learning architectures**:

```text
       ┌────────────────────────────────────────────────────────┐
       │               POINT-IN-TIME DEAL DATA                  │
       │  Customer History • Applied Discounts • Line Margins   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             50-FEATURE VECTOR ENGINEERING              │
       │  Ceiling Utilization • Margin Compression • Tenure     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │           TOURNAMENT MODEL COMPARISON SUITE            │
       │   XGBoost (2nd-Order) • LightGBM • Random Forest       │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │           PLATT SCALING PROBABILITY CALIBRATION        │
       │    Calibrated Brier Score • 0–100 Scaled Risk Score    │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            SHAP TREE EXPLAINABILITY & FACTORS          │
       │  Marginal Feature Contributions • Prescribed Actions   │
       └────────────────────────────────────────────────────────┘
```

### 1. Pure-Python Tree-Based Risk Engine (`app/services/ml_risk.py`)
To ensure zero-dependency portability and runtime stability without brittle native C-extensions, DEALFLOW360 implements full tree-based ensembles in pure Python:
* **Feature Engineering (Phases 121–130)**: Extracts a 50-dimensional tabular feature vector spanning discount behavior, margin compression, customer reliability, and deal outlier ratios with strict anti-leakage guards.
* **Architectures Evaluated (Phases 131–135)**:
  * **XGBoost Classifier**: 2nd-order Taylor expansion tree optimizer minimizing logistic cross-entropy loss with L2 leaf regularization.
  * **LightGBM Classifier**: Leaf-wise (best-first) expansion strategy for complex non-linear boundary capture.
  * **Random Forest Baseline**: Bagging ensemble with bootstrap aggregation and random subspace feature selection ($m_{\text{try}}$).
* **Model Tournament & Evaluation**: Evaluates all candidate architectures on held-out test splits, measuring Accuracy, Precision, Recall, F1-Score, ROC-AUC, PR-AUC, and Brier Score.
* **Probability Calibration (Phase 139)**: Platt scaling logistic calibration to guarantee reliable probabilistic confidence.
* **SHAP Tree Explainability (Phase 143)**: Recursive tree-path traversal calculating exact marginal feature attributions for human-readable auditability.

### 2. AI Upsell & Cross-Sell Engine (`app/services/recommendations.py`)
* **Product Affinity Mining**: Calculates transactional co-occurrence matrices using Jaccard similarity coefficients.
* **Frequently Bought Together**: Mines association rules based on Support, Confidence, and Lift thresholds.
* **Collaborative & Content Filtering**: Blends customer neighborhood matrices with product attribute TF-IDF cosine similarities.
* **Margin-Aware Ranking**: Re-ranks recommendations to maximize blended gross margin contribution while respecting customer tier ceilings.

### 3. Deal Health Telemetry & Anomaly Analytics (`app/services/deal_health.py`)
* Evaluates point-in-time health ($0-100$) mapped into 4 governance tiers: `HEALTHY` (80–100), `WATCH` (60–79), `AT_RISK` (40–59), and `CRITICAL` (0–39).
* Proactively fires 8 alert triggers: `CRITICAL_HEALTH`, `HIGH_STALL_RISK`, `HIGH_DELAY_RISK`, `DISCOUNT_ANOMALY`, `APPROVAL_BOTTLENECK`, `DELIVERY_SLIPPAGE`, `SEVERE_INACTIVITY`, and `BEHAVIORAL_ANOMALY`.
* Dispatches automated corrective nudges to deal owners and triggers management escalations.

### 4. AI Copilot (`app/ai/orchestrator.py`)
* Connects to **OpenAI** (`gpt-4o-mini`, `gpt-4o`) or **xAI Grok** (`grok-2-latest`) via `LLM_API_KEY`. Falls back to deterministic simulated responses in offline/testing environments.
* **13 Verified Domain Tools**:
  `get_deal_summary`, `get_risk_explanation`, `get_discount_explanation`, `get_approval_explanation`, `get_upsell_explanation`, `get_deal_health`, `get_negotiation_summary`, `get_customer_summary`, `get_next_best_action`, `execute_analytics_query`, `generate_report`, `search_business_knowledge`, and `request_discount`.
* **Guarded Mutations & Security**:
  * `sanitize_untrusted_input()` blocks prompt injection attempts.
  * Mutating actions (such as `request_discount`) enforce **Human-in-the-Loop confirmation** before executing.
  * Full token consumption telemetry (`AIUsage`) and immutable audit trails (`AIAuditEvent`).

### 5. Enterprise RAG Knowledge Base (`app/rag/service.py`)
* Ingests authorized business guidelines, discount policies, and compliance documentation.
* Generates vector embeddings via OpenAI `text-embedding-ada-002` (1536 dimensions) or deterministic offline vectors.
* Performs cosine similarity vector search over PostgreSQL-persisted document chunks with explicit source citations.

---

## 🛡️ Approval Engine & Governance Workflow

When deal discounts or margin concessions breach standard policies, DEALFLOW360’s **Approval Decision Engine** routes the transaction through an immutable approval hierarchy:

```mermaid
flowchart TD
    Q[Quotation Submitted] --> CHK{Policy & Margin Check}
    CHK -- Safe Harbor Criteria Met --> AUTO[Auto-Approved]
    CHK -- Policy or Margin Breach --> DET[Detect Required Sign-offs]

    DET --> T1{Discount <= 15%?}
    T1 -- Yes --> MGR[Sales Manager Review]
    T1 -- No --> T2{Discount <= 25%?}

    T2 -- Yes --> DIR[Sales Director Review]
    T2 -- No --> VP[VP of Sales Review]

    CHK -- Margin < 20% --> FIN[Finance Authority Review]

    MGR --> DEC{Decision}
    DIR --> DEC
    VP --> DEC
    FIN --> DEC

    DEC -- Approved --> APP[Status: APPROVED]
    DEC -- Rejected --> REJ[Status: REJECTED]
    DEC -- Stipulations Added --> COND[Status: CONDITIONAL_APPROVAL]

    classDef proc fill:#0d1117,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef succ fill:#052e16,stroke:#22c55e,stroke-width:2px,color:#fff;
    classDef fail fill:#450a0a,stroke:#ef4444,stroke-width:2px,color:#fff;
    class Q,CHK,DET,T1,T2,MGR,DIR,VP,FIN,DEC proc;
    class AUTO,APP,COND succ;
    class REJ fail;
```

* **Multi-Tier Routing**:
  * **Sales Manager**: Concessions within first-line discretionary limits.
  * **Sales Director / VP**: Strategic enterprise volume exceptions.
  * **Finance**: Mandatory parallel sign-off whenever gross margin dips below target thresholds.
* **Auto-Approval Safe Harbor**: Instant approval for low-risk quotes that satisfy all ceiling and margin requirements.
* **SLA Monitoring & Auto-Escalation**: Configurable countdown timers trigger escalation to higher tiers when reviews stall.
* **Delegation**: Temporary authority delegation during out-of-office windows.
* **Structured Rejections**: Mandatory rejection taxonomies ensure explainability and prevent arbitrary vetoes.

---

## 🏭 Multi-Warehouse Inventory & Fulfillment

DEALFLOW360 natively prevents overselling through deterministic inventory tracking:

* **Available-to-Promise (ATP)**:
  $$\text{ATP} = \max(\text{Physical Quantity} - \text{Reserved Quantity}, 0)$$
* **Multi-Warehouse Allocation**: Sequentially searches facilities by deterministic priority order (`priority >= 1`).
* **Atomic Stock Reservation**: Employs database row-level pessimistic locking (`SELECT ... FOR UPDATE`) to eliminate race conditions during concurrent checkouts.
* **Automatic Backorders**: Automatically generates `Backorder` records for shortfalls without mutating active stock balances.
* **Delivery State Machine**: Tracks fulfillment progression:
  $$\text{NOT\_STARTED} \longrightarrow \text{READY} \longrightarrow \text{DISPATCHED} \longrightarrow \text{IN\_TRANSIT} \longrightarrow \text{DELIVERED}$$

---

## 🤝 Customer Negotiation Portal

Enterprise deals require collaborative iteration. The **Customer Portal** (`/portal`) gives clients a secure workspace:

* **Margin-Sanitized Views**: Customers review line items, totals, and terms with sensitive internal costs and margins stripped out.
* **Real-Time Commenting**: Direct messaging between buyer and seller attached directly to the quotation context.
* **Structured Counter-Offers**: Customers submit counter-requests (e.g., target discount or adjusted delivery milestones).
* **Intent Extraction Engine**: Parses counter-proposals and re-triggers internal approval workflows if requested terms breach policies.
* **Instant Digital Acceptance / Rejection**: Cryptographically attributed client acceptance or structured rejection with feedback.

---

## 💳 Subscriptions & Invoicing Engine

DEALFLOW360 bridges the gap between sales and finance with native billing orchestration:

* **Subscription Lifecycle**: Manage `SubscriptionPlan` tiers, recurring frequencies (Monthly, Quarterly, Annual), renewals, and cancellations.
* **Usage Records**: Ingest metered consumption logs linked to customer accounts.
* **Consolidated Invoicing**: Generates `Invoice` and `InvoiceLineItem` records supporting both one-off product lines and recurring subscription fees.
* **Mock Settlement Engine**: Internal settlement execution via `PortalPaymentService` simulating payment reconciliation without external gateway dependencies.

---

## ⚡ Real-time WebSockets & Event Bus

The platform provides a production WebSocket infrastructure:

* **Endpoint**: `/api/v1/ws?token=<JWT_TOKEN>`
* **Authentication**: Verified through query parameters or initial auth frames using `RealtimeAuthService`.
* **Topic Subscriptions**: Granular channel subscriptions for `deal:{id}`, `approvals`, `inventory`, and `notifications`.
* **Heartbeat Ping/Pong**: Automatic connection health checks and seamless client reconnection handling.
* **Internal Event Bus**: Decoupled asynchronous event broadcasting across backend services.

---

## 👥 User Roles & RBAC Matrix

DEALFLOW360 enforces canonical business roles across all backend API endpoints and frontend navigation routes:

| Role Name | Scope & Primary Capabilities |
| :--- | :--- |
| **Admin** | System-wide configuration, company settings, user management, global audit logs, full override authority. |
| **Sales Manager** | Deal review, manager-tier discount approvals, team quota tracking, approval escalation handling. |
| **Sales Representative** | Customer creation, quote drafting, deal pipeline management, discretionary discount granting up to limit. |
| **Finance** | Financial policy configuration, margin threshold enforcement, invoice creation, billing lifecycle management. |
| **Operations** | Warehouse facility configuration, stock level updates, fulfillment allocation, backorder resolution. |
| **Viewer** | Read-only observation across deals, products, customers, and analytics dashboards. |
| **Customer Portal** | External customer access to view quotes, submit counter-offers, and sign agreements. |

---

## 🔒 Security & Production Guardrails

DEALFLOW360 is engineered with a **zero-trust security posture**:

* **Cryptographic Password Hashing**: State-of-the-art **Argon2id** algorithm (`argon2-cffi`).
* **Stateless JWT Tokens**: PyJWT authentication with short-lived access tokens (30 min) and rotating refresh tokens (7 days).
* **Strict Multi-Tenant Isolation**: Every database entity enforces `company_id` foreign keys; all queries are isolated by tenant context.
* **Production Configuration Fail-Safes (`app/core/config.py`)**:
  * Rejects `DEBUG=true` in production mode.
  * Rejects default development secrets; enforces $\ge 32$-character cryptographically secure keys.
  * Rejects default development database URLs and wildcard CORS (`*`).
* **Prompt Injection Defense**: Sanitizes all AI Copilot prompts to block jailbreaks and malicious prompts.
* **Human-in-the-Loop Confirmation**: Mutating tools require explicit user confirmation before executing.
* **Append-Only Audit Logging**: Comprehensive `AuditLog` tracking actor attribution, client IP, and before/after mutation payloads.

---

## 🏗️ Technical System Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                                    │
│       React 19 • Vite • TypeScript • Tailwind CSS v4 • Framer Motion • Recharts  │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │  HTTPS / WSS (Port 8000)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             API GATEWAY & ROUTING                                │
│        FastAPI • Uvicorn • Pydantic v2 • Global Exception Filters • CORS         │
└───────┬────────────────────────────────┼─────────────────────────────────┬───────┘
        │                                │                                 │
        ▼                                ▼                                 ▼
┌───────────────────────┐  ┌─────────────────────────────┐  ┌───────────────────────┐
│   COMMERCIAL CORE     │  │   GOVERNANCE & RISK         │  │   AI & INTELLIGENCE   │
│  • Customer 360       │  │  • Discount Ceilings        │  │  • Pure-Python Trees  │
│  • Product Catalog    │  │  • Margin Floor Protection  │  │  • XGBoost / LightGBM │
│  • Quotation Engine   │  │  • Approval State Machine   │  │  • AI Copilot & Tools │
│  • Deal Management    │  │  • Deal Health Telemetry    │  │  • RAG Knowledge Base │
└───────────┬───────────┘  └─────────────┬───────────────┘  └───────────┬───────────┘
            │                            │                              │
            ▼                            ▼                            ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            PERSISTENCE & DATA LAYER                              │
│       PostgreSQL 15+ • SQLAlchemy 2.0 (Declarative ORM) • Alembic (28 Revisions) │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Interactive Mermaid Diagrams

### 1. System Request Architecture
```mermaid
flowchart TD
    Client[Web Client: React 19 / Vite] -->|HTTPS REST| FastAPI[FastAPI Backend: Port 8000]
    Client -->|WSS Realtime| WSEndpoint[/api/v1/ws]

    FastAPI --> AuthGuard{JWT & RBAC Guard}
    WSEndpoint --> ConnMgr[Connection Manager]

    AuthGuard -->|Authenticated| Router[API Router /api/v1]

    Router --> DealSvc[Deal Service]
    Router --> DiscSvc[Discount Engine]
    Router --> ApprSvc[Approval Engine]
    Router --> MLSvc[ML Risk Engine]
    Router --> AISvc[AI Copilot & RAG]

    DealSvc --> DB[(PostgreSQL Database)]
    DiscSvc --> DB
    ApprSvc --> DB
    MLSvc --> DB
    AISvc --> DB
```

### 2. Quotation-to-Deal Conversion Flow
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Enterprise Customer
    participant Portal as Customer Portal
    participant API as FastAPI Backend
    participant QuoteSvc as Quotation Engine
    participant DealSvc as Deal Engine
    participant InvSvc as Inventory Service
    participant DB as PostgreSQL DB

    Customer->>Portal: Review Quote (QT-2026-0042)
    Portal->>API: POST /api/v1/portal/quotes/{id}/accept
    API->>QuoteSvc: Validate Quote (Not Expired, Approved)
    QuoteSvc->>DB: Update QuotationStatus = ACCEPTED
    QuoteSvc->>DealSvc: convert_quote_to_deal(quotation_id)
    DealSvc->>DB: Create CustomerDealHistory (Stage: CLOSED_WON)
    DealSvc->>DB: Create DealProduct Snapshots
    DealSvc->>InvSvc: Lock & Allocate Stock (ATP)
    InvSvc->>DB: Commit Stock Reservation
    QuoteSvc->>DB: Update QuotationStatus = CONVERTED
    API-->>Portal: 200 OK (Deal Successfully Created)
    Portal-->>Customer: Confirmation & Agreement Receipt
```

### 3. Authentication & Session Flow
```mermaid
sequenceDiagram
    autonumber
    actor User as Sales Representative
    participant UI as React 19 UI
    participant API as FastAPI Backend
    participant DB as PostgreSQL DB

    User->>UI: Submit Email & Password
    UI->>API: POST /api/v1/auth/login
    API->>DB: Query User by Email
    API->>API: Verify Password with Argon2id
    API->>DB: Persist Rotating Refresh Token
    API->>API: Generate Access Token (JWT HS256, 30m)
    API-->>UI: { access_token, refresh_token, token_type: "bearer" }
    UI->>UI: Store Token in localStorage
    UI->>API: GET /api/v1/auth/me (Bearer Token)
    API-->>UI: User Profile, Assigned Roles & Permissions
    UI-->>User: Render Role-Aware AppShell
```

---

## 🛠️ Technology Stack

| Layer | Component | Version / Library | Rationale |
| :--- | :--- | :--- | :--- |
| **Frontend** | Framework | React 19 + Vite 8 | Ultra-fast HMR, concurrent features, modern module bundling. |
| | Language | TypeScript 5.7 | Strict type safety, shared API contracts across client. |
| | Styling | Tailwind CSS v4 | Next-gen utility engine, minimal CSS runtime bundle size. |
| | Motion & UI | Framer Motion 13 | Smooth hardware-accelerated drawer, modal, and tab animations. |
| | Data Visualization | Recharts 3.10 | Responsive SVG-based interactive charts and pipeline analytics. |
| **Backend** | Framework | FastAPI 0.110+ | Asynchronous Python framework with native OpenAPI schema generation. |
| | ASGI Server | Uvicorn (Standard) | High-concurrency async event loop worker. |
| | Validation | Pydantic v2.6+ | High-performance C-based schema validation and type parsing. |
| | Security | Argon2id + PyJWT | Memory-hard password hashing and cryptographically signed tokens. |
| | PDF Generation | ReportLab 4.0+ | Server-side vector PDF generation for quotations and invoices. |
| **Database** | Database | PostgreSQL 15+ / 16+ | ACID-compliant relational persistence with JSONB dialect support. |
| | ORM | SQLAlchemy 2.0 | Declarative mapped columns, strict type hints, and relationship cascading. |
| | Migrations | Alembic 1.13+ | 28 deterministic schema migration revisions. |
| | Drivers | `psycopg` & `psycopg2-binary` | Native PostgreSQL binary connectivity for async/sync execution. |
| **Intelligence**| ML Risk Engine | Pure-Python Trees | Custom 2nd-order XGBoost & LightGBM trees with zero native C-deps. |
| | LLM Integration | OpenAI / xAI Grok API | LLM Copilot orchestration with prompt injection guardrails. |
| | Embeddings & RAG | `text-embedding-ada-002` | Vector embeddings with cosine similarity search over PostgreSQL. |
| **DevOps** | Process Control | Systemd + PM2 | Multi-worker background process lifecycle management on Linux. |
| | Reverse Proxy | Nginx 1.24+ | TLS 1.3 termination, rate limiting, gzip, and unified routing. |
| | CI/CD | GitHub Actions | Automated multi-job test, lint, migration, and build verification. |

---

## 📂 Project Structure

```text
DealFlow360/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Unified multi-job GitHub Actions CI/CD pipeline
├── backend/
│   ├── alembic/
│   │   ├── versions/                  # 28 declarative Alembic migration revisions
│   │   └── env.py                     # Alembic migration runner bound to App Settings
│   ├── app/
│   │   ├── ai/                        # AI Copilot, providers (OpenAI/Grok), 13 domain tools
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/         # 31 domain endpoint routers
│   │   │       └── api.py             # Versioned API router aggregator
│   │   ├── core/                      # Configuration, error handlers, logging, security
│   │   ├── db/                        # Declarative base, session manager, master seed
│   │   ├── models/                    # 44 SQLAlchemy 2.0 domain model entities
│   │   ├── rag/                       # RAG models, chunking, embeddings, vector search
│   │   ├── reporting/                 # Analytical SQL queries, report scheduling, exporters
│   │   ├── schemas/                   # Pydantic request/response validation contracts
│   │   ├── services/                  # Domain business logic & calculation engines
│   │   └── main.py                    # FastAPI application initialization & middleware
│   ├── tests/                         # 43 test modules (452 automated test cases)
│   ├── .env.example                   # Backend environment template
│   ├── requirements.txt               # Pinned Python dependencies
│   ├── run.py                         # Local Uvicorn server launcher
│   └── seed_demo_users.py             # Demo user provisioning script
├── deploy/
│   ├── nginx/                         # Nginx edge reverse proxy configuration
│   ├── pm2/                           # PM2 cluster ecosystem manifest
│   ├── scripts/                       # Production startup & audit scripts
│   └── systemd/                       # Systemd service unit definitions
├── docs/
│   ├── architecture/
│   │   ├── ARCHITECTURE_REFERENCE.md
│   │   └── DealFlow360_End_to_End_Product_Flow.png
│   └── devops/                        # Deployment, branch strategy, and production audit guides
├── frontend/
│   ├── public/                        # Static assets, branding logos, and favicons
│   ├── src/
│   │   ├── assets/                    # Application logos and iconography
│   │   ├── components/                # Reusable UI components, modals, drawers, AppShell
│   │   ├── hooks/                     # Custom React hooks (useAuth, useRequests, useAI)
│   │   ├── lib/                       # Centralized typed API client & motion primitives
│   │   ├── mocks/                     # Local fallback mock datasets
│   │   ├── pages/                     # 20 operational page views (Deals, Quotes, Risk, etc.)
│   │   ├── services/                  # Frontend domain HTTP service wrappers
│   │   ├── types/                     # TypeScript domain interface definitions
│   │   ├── App.tsx                    # Root routing & authentication state switcher
│   │   ├── index.css                  # Core Tailwind CSS v4 styling rules
│   │   └── main.tsx                   # React 19 application entrypoint
│   ├── .env.example                   # Frontend environment template
│   ├── package.json                   # Dependencies & build scripts
│   ├── tsconfig.json                  # TypeScript compiler settings
│   └── vite.config.ts                 # Vite bundler configuration
├── .gitignore                         # Secret, cache, and artifact exclusions
├── .gitmessage                        # Conventional Commits template
└── README.md                          # Master product documentation
```

---

## 🗄️ Database Schema & Persistence Models

The data layer is structured across **44 mapped SQLAlchemy 2.0 entities** managed through **28 Alembic revisions**:

```text
               ┌───────────────┐
               │    Company    │ (Tenant Root)
               └───────┬───────┘
                       │
       ┌───────────────┼───────────────────────────────┐
       ▼               ▼                               ▼
┌──────────────┐ ┌──────────────┐             ┌─────────────────┐
│     User     │ │  Warehouse   │             │    Customer     │
└──────┬───────┘ └──────┬───────┘             └────────┬────────┘
       │                │                              │
       │                ▼                              ▼
       │         WarehouseStock               CustomerTier (Bronze/Silver/Gold)
       │                │                              │
       │                ▼                              ▼
       │         Backorder / Fulfillment      CustomerFinancialIntelligence
       │                                               │
       └───────────────────────┬───────────────────────┘
                               │
                               ▼
                        Quotation (Draft, Sent, Accepted, etc.)
                               │
                       ┌───────┴───────┐
                       ▼               ▼
            QuotationLineItem     QuotationVersion
                       │
                       ▼
            CustomerDealHistory (Deal: NEW -> WON / LOST)
                       │
       ┌───────────────┼───────────────────────────────┐
       ▼               ▼                               ▼
  DealProduct     DealActivity                  DealHealthSnapshot
                       │                               │
                       ▼                               ▼
                 ApprovalRequest               DealHealthAlert
                       │                               │
                       ▼                               ▼
                 Invoice / Billing             DealHealthNudge
```

* **Tenant Isolation**: Foreign key references to `companies.id` ensure absolute data compartmentalization.
* **Integrity Constraints**: Database-level check constraints enforce `quantity > 0`, `unit_price >= 0`, `discount_percent BETWEEN 0 AND 100`, and `margin_percentage` bounds.
* **Audit Lineage**: Every critical state transition appends an immutable record to `AuditLog`.

---

## 🔌 API Documentation & Verified Endpoints

FastAPI automatically serves interactive OpenAPI documentation at:
* **Interactive Swagger UI**: `http://localhost:8000/docs`
* **Alternative ReDoc UI**: `http://localhost:8000/redoc`
* **OpenAPI JSON Schema**: `http://localhost:8000/openapi.json`

### Key Endpoint Catalog

| Domain Router | HTTP Method | Endpoint Path | Description |
| :--- | :---: | :--- | :--- |
| **Authentication** | `POST` | `/api/v1/auth/register` | Register new user account within tenant. |
| | `POST` | `/api/v1/auth/login` | Authenticate credentials; return JWT access & refresh tokens. |
| | `GET` | `/api/v1/auth/me` | Fetch authenticated user profile, roles, and permissions. |
| **Customers** | `GET` | `/api/v1/customers` | Paginated customer directory with search and filtering. |
| | `GET` | `/api/v1/customers/{id}/financial-intelligence` | Retrieve customer LTV, payment risk, and baseline discount. |
| **Products & Stock** | `GET` | `/api/v1/products` | Catalog listing with variants, pricing, and gross margins. |
| | `GET` | `/api/v1/warehouses/stock/availability` | Deterministic stock availability and ATP per warehouse. |
| | `POST` | `/api/v1/warehouses/stock/reserve` | Atomic, pessimistic row-locked stock reservation. |
| **Governance** | `POST` | `/api/v1/governance/discounts/validate` | Verify requested discount against active multi-tier ceilings. |
| | `POST` | `/api/v1/governance/discounts/automation/evaluate-decision` | Run discount decision engine for automated approval/escalation. |
| **ML Risk Engine** | `POST` | `/api/v1/ml/models/compare` | Execute tournament comparison across XGBoost, LightGBM, and RF. |
| | `POST` | `/api/v1/ml/predict` | Generate calibrated 0–100 risk score and SHAP feature attributions. |
| **Quotations** | `POST` | `/api/v1/quotations` | Create formal quotation with line items, taxes, and margins. |
| | `POST` | `/api/v1/quotations/{id}/pdf` | Stream server-side ReportLab vector PDF document. |
| | `POST` | `/api/v1/quotations/{id}/submit-approval` | Submit quote to Approval Engine for multi-stakeholder review. |
| **Commercial Deals**| `GET` | `/api/v1/deals` | List deals with stage filtering and financial aggregates. |
| | `POST` | `/api/v1/deals/from-quote` | Transactionally convert accepted quotation into commercial deal. |
| | `PATCH` | `/api/v1/deals/{id}/stage` | Transition deal stage with transition validator and audit trail. |
| **Deal Health** | `POST` | `/api/v1/deal-health/evaluate/{deal_id}` | Compute point-in-time health score, stall risk, and alert triggers. |
| **Customer Portal** | `GET` | `/api/v1/portal/quotes/{id}` | Retrieve customer-facing sanitized quotation. |
| | `POST` | `/api/v1/portal/quotes/{id}/negotiations`| Submit structured customer counter-offer / negotiation request. |
| **AI Copilot** | `POST` | `/api/v1/ai/query` | Submit prompt to AI Orchestrator with tool-calling capabilities. |
| **Realtime** | `WS` | `/api/v1/ws` | Full-duplex WebSocket for deal updates and notifications. |

---

## 💻 API Example: Creating a Deal from an Accepted Quote

### 1. Request
```bash
curl -X POST "http://localhost:8000/api/v1/deals/from-quote" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "quotation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "title": "Acme Corp — Enterprise Infrastructure & AI Fleet Expansion",
    "notes": "Annual enterprise contract with premium support SLA."
  }'
```

### 2. Response (`201 Created`)
```json
{
  "id": "7b1c4e92-3a81-429d-9d7a-12e84d62b901",
  "company_id": "c1a93e82-1234-4567-89ab-cdef01234567",
  "customer_id": "d2b84f93-5678-4321-ba98-fedcba987654",
  "deal_code": "DEAL-202609-0014",
  "title": "Acme Corp — Enterprise Infrastructure & AI Fleet Expansion",
  "deal_value": 2850000.00,
  "status": "WON",
  "stage": "CLOSED_WON",
  "subtotal": 3000000.00,
  "discount_amount": 150000.00,
  "discount_percent": 5.00,
  "tax_amount": 0.00,
  "total_cost": 1710000.00,
  "gross_profit": 1140000.00,
  "margin_percentage": 40.00,
  "probability": 100,
  "expected_revenue": 2850000.00,
  "quotation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "quotation_version": 1,
  "created_at": "2026-09-06T05:22:18Z"
}
```

---

## ⚙️ Installation & Getting Started

### System Prerequisites
* **Node.js**: `v18.0.0+` (tested with Node.js 20 LTS & 22)
* **Python**: `3.11+` (tested with Python 3.11.9)
* **PostgreSQL**: `15+` or `16+` running locally or accessible via network
* **Git**: `2.30+`

### 1. Clone Repository
```bash
git clone https://github.com/Dharshan-05/DealFlow360.git
cd DealFlow360
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your local PostgreSQL credentials
```

### 3. Database Migration & Seeding
```bash
# Run all 28 Alembic migrations
alembic upgrade head

# Seed master catalog, tiers, warehouses, and authority limits
python -m app.db.seed

# Provision demo accounts
python seed_demo_users.py
```

### 4. Frontend Setup
```bash
cd ../frontend

# Install frontend dependencies
npm install

# Configure environment
cp .env.example .env.local
```

---

## 🔑 Environment Configuration

### Backend Environment Variables (`backend/.env`)

| Variable | Description | Required | Default / Safe Placeholder |
| :--- | :--- | :---: | :--- |
| `ENVIRONMENT` | Operating environment (`development`, `testing`, `production`) | Yes | `development` |
| `DEBUG` | Enable debug mode (must be `false` in production) | Yes | `true` |
| `PORT` | Uvicorn server port | No | `8000` |
| `DATABASE_URL` | PostgreSQL connection URI | Yes | `postgresql+psycopg://postgres:postgres@localhost:5432/dealflow360` |
| `JWT_SECRET_KEY` | Cryptographic key for signing HS256 tokens ($\ge 32$ chars) | Yes | `<generate-via-openssl-rand-hex-32>` |
| `CORS_ORIGINS` | Permitted cross-origin origins (comma-separated) | Yes | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173` |
| `LLM_API_KEY` | OpenAI or xAI Grok API key for Copilot intelligence | Optional | `sk-...` or `xai-...` *(falls back to simulation)* |
| `LLM_MODEL` | Preferred model name | Optional | `gpt-4o-mini` / `grok-2-latest` |
| `OPENAI_API_KEY` | OpenAI key for RAG vector embeddings | Optional | `sk-...` *(falls back to deterministic test vectors)* |

### Frontend Environment Variables (`frontend/.env.local`)

| Variable | Description | Required | Default |
| :--- | :--- | :---: | :--- |
| `VITE_API_BASE_URL` | Base HTTP URI of backend API | No | `http://localhost:8000` |
| `VITE_APP_ENV` | Client environment descriptor | No | `development` |

---

## 🚀 Running Locally

### Start Backend API Server
```bash
cd backend
.venv\Scripts\activate
python run.py
```
* Backend API live at: `http://localhost:8000`
* Interactive API Documentation: `http://localhost:8000/docs`

### Start Frontend Application
```bash
cd frontend
npm run dev
```
* Frontend client live at: `http://localhost:5173` (or configured dev port)

### Demo Credentials
Log into the platform using pre-seeded accounts:
* **Internal Sales / Admin Account**:
  * **Email**: `arjun.sharma@dealflow360.io`
  * **Password**: `password123`
  * **Access**: Command Center, Deals Kanban, Quote Workspace, Approvals, AI Copilot, Audit Center
* **Customer Portal Account**:
  * **Email**: `rajesh@acme.com`
  * **Password**: `password123`
  * **Access**: Customer Negotiation Portal (Sanitized quote review, counter-offers, acceptance)

---

## 🚢 DevOps & Production Deployment (Without Docker)

Phase Group G25 (Phases 456–470) intentionally implemented an enterprise **DevOps Without Docker** architecture designed for high-performance Linux instances (Ubuntu 22.04 LTS / Debian):

```text
┌────────────────────────────────────────────────────────────┐
│                    EDGE NGINX PROXY                        │
│   TLS 1.3 • Rate Limiting • Gzip • Static Caching • HSTS   │
└──────────────┬──────────────────────────────┬──────────────┘
               │                              │
               ▼                              ▼
      ┌─────────────────┐            ┌─────────────────┐
      │   PORT 3000     │            │   PORT 8000     │
      │   Frontend PM2  │            │   Backend Pool  │
      │  Next/Vite SSR  │            │  Systemd Uvicorn│
      └─────────────────┘            └────────┬────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ PostgreSQL 15+  │
                                     │  Unix Socket    │
                                     └─────────────────┘
```

* **Process Management**:
  * Backend: Managed via systemd service unit (`deploy/systemd/dealflow360-backend.service`) with sandbox isolation and automatic restart policies.
  * Frontend: Managed via PM2 cluster mode (`deploy/pm2/ecosystem.config.js`).
* **Reverse Proxy**:
  * Nginx reverse proxy configuration (`deploy/nginx/dealflow360.conf`) with TLS 1.3, rate-limiting zones (`api_limit`, `auth_limit`), proxy buffering, and WebSocket upgrade headers.
* **Production Readiness Verification**:
  ```bash
  python deploy/scripts/verify_production_readiness.py
  ```
  Automated script validating environment guardrails, database connectivity, pending migrations, systemd units, and Nginx configurations before deployment.

---

## 🧪 Testing & Quality Assurance

DEALFLOW360 maintains a **100% passing automated test suite**:

### Backend Test Suite
The backend contains **452 automated tests** across **43 distinct test modules**:

```bash
cd backend
.venv\Scripts\activate
pytest tests -v --durations=10
```

Coverage areas include:
* `test_auth.py` & `test_authorization.py`: Authentication, JWT expiration, Argon2id hashing, and RBAC permissions.
* `test_g18_warehouses.py` & `test_g19_warehouse_allocation.py`: Stock ATP calculations, pessimistic row locking, and fulfillment allocation.
* `test_g21_discount_governance.py` & `test_g22_discount_governance_engine.py`: 4-tier ceiling evaluations and actor limit boundaries.
* `test_g23_discount_intelligence.py` & `test_g24_discount_automation.py`: Decimal margin math and automated decision engine rules.
* `test_b01_ml_risk_features.py` to `test_b04_ml_risk_pipeline_and_api.py`: 50-feature engineering, XGBoost/LightGBM model training, and Platt calibration.
* `test_b05_approval_routing.py` & `test_b06_approval_execution.py`: Multi-level approval hierarchies, SLA timers, and escalations.
* `test_b07_recommendations.py` & `test_b08_recommendations.py`: Collaborative and content-based recommendation scoring.
* `test_b09_quotations.py` & `test_b10_quotation_lifecycle.py`: Quotation state transitions, ReportLab PDF, and deal conversion.
* `test_b11_deals.py` & `test_b12_deal_health.py`: Commercial deal calculations, probability forecasting, and health telemetry alerts.
* `test_g19_realtime.py`: WebSocket connection management, channel topics, and message serialization.

### Frontend Validation & Build
```bash
cd frontend
# TypeScript compiler validation
npm run build
```
Builds client production bundles with **1070 modules transformed** without type errors.

---

## 🎬 End-to-End Demo Walkthrough

Experience the full DEALFLOW360 deal lifecycle in 10 steps:

1. **Authenticate**: Log in as Sales Representative Arjun Sharma (`arjun.sharma@dealflow360.io`).
2. **Review Command Center**: Inspect current pipeline value, monthly deal velocity, and active health notifications.
3. **Draft a Quote**: Navigate to **Requests / Quotes** (`/quotes`) and initiate a new quotation for *Acme Corporation*.
4. **Configure Line Items**: Add hardware appliances and platform licenses. Notice how unit costs, gross margins, and customer tier ceilings calculate automatically.
5. **Request Concession**: Input an 18% discretionary discount. The **Discount Governance Engine** alerts you that the requested discount breaches your 10% authority limit.
6. **Trigger Approval Routing**: Submit the quotation. The **Approval Engine** evaluates margin exposure and automatically routes the request to the Sales Director and Finance.
7. **Approve Request**: In **Approvals** (`/approvals`), review the ML risk factors and approve the concession with binding margin stipulations.
8. **Engage Customer Portal**: Log in as customer Rajesh Kumar (`rajesh@acme.com`). Review the sanitized quote and digitally accept the agreement.
9. **Atomic Deal Conversion**: The accepted quote converts into a commercial deal (`CustomerDealHistory`), transitions stage to `CLOSED_WON`, locks warehouse stock, and logs an activity event.
10. **Analyze Revenue Impact**: Visit **Analytics & Reports** (`/analytics`) to observe updated win rates, pipeline forecast distribution, and generated invoices.

---

## 🎯 Enterprise Use Cases

* **High-Tech & SaaS Enterprises**: Orchestrate hybrid contracts combining upfront appliance hardware with recurring multi-year platform subscriptions.
* **Capital Equipment & Industrial Manufacturing**: Manage multi-facility inventory allocation across regional warehouses without risking stockouts on long-lead SKUs.
* **Corporate Deal Desks**: Centralize commercial review workflows to eliminate shadow discounting and guarantee compliance with corporate margin targets.
* **Wholesale & Distribution**: Provide self-service negotiation portals for wholesale partners to collaborate on high-volume commercial bids.

---

## 💎 Competitive Differentiation

| Architectural Dimension | Traditional CRM (e.g., Salesforce / HubSpot) | Standalone CPQ | DEALFLOW360 |
| :--- | :--- | :--- | :--- |
| **Margin Enforcement** | Post-facto reporting in dashboards. | Static discount lookup tables. | **Continuous runtime governance** with strict Decimal margin protection and negative-margin blocking. |
| **Inventory Synchronization**| Decoupled; relies on delayed batch sync from ERP. | Blind to physical stock availability. | **Real-time Available-to-Promise (ATP)** evaluation with database pessimistic row locking. |
| **Risk Assessment** | Uncalibrated heuristic lead scoring. | Absent. | **Calibrated Tree-based ML Risk Engine** (XGBoost / LightGBM) with SHAP factor explainability. |
| **Approval Workflow** | Static email notifications with frequent delays. | Isolated approval chains. | **Multi-stakeholder dynamic routing** with SLA countdown timers, auto-escalations, and safe-harbor approvals. |
| **Customer Collaboration** | Static PDF attachments over email. | Separate proprietary portals. | **Integrated Customer Negotiation Portal** with real-time comments, counter-offers, and instant sign-off. |
| **Deal Conversion** | Manual opportunity stage updating. | Disconnected handoff to billing. | **Atomic transactional conversion** from quote to deal, reserving inventory and creating billing records. |

---

## 🧭 Product Philosophy

> **"Every deal must have an accountable owner, an explicit state, full operational context, deterministic safety guardrails, and a measurable financial outcome."**

DEALFLOW360 rejects the premise that enterprise software must choose between sales velocity and financial control. By embedding intelligence and policy verification directly into the quotation workflow, sales representatives close deals faster while executive leadership maintains continuous margin assurance.

---

## 🗺️ Implementation Roadmap

### Phase 1: Core Foundation & Commercial Engine
* [x] Monorepo architecture, FastAPI backend, React 19 / Vite frontend
* [x] PostgreSQL database schema, SQLAlchemy 2.0 ORM, and 28 Alembic migrations
* [x] Argon2id password hashing, JWT authentication, and Canonical RBAC
* [x] Customer 360, customer tiers, and historical financial intelligence
* [x] Product catalog, variants, attributes, and unit economics

### Phase 2: Warehouse, Governance & Decision Automation
* [x] Multi-warehouse facility management and deterministic stock ATP calculation
* [x] Pessimistic row-locked stock reservation and automated backorder engine
* [x] 4-tier discount governance ceilings (Company, Customer, Category, Product)
* [x] Sales Representative, Manager, and Finance authority limits
* [x] Decimal margin protection engine and automated discount application

### Phase 3: AI Intelligence, Approvals & Quotations
* [x] 50-feature tabular vector extraction and anti-leakage ML dataset pipeline
* [x] Pure-Python 2nd-order XGBoost, LightGBM, and Random Forest models
* [x] Platt scaling probability calibration and SHAP tree explainability
* [x] Multi-level approval decision engine with SLA monitoring and auto-escalations
* [x] Quotation lifecycle state machine and ReportLab vector PDF generation
* [x] AI Upsell / Cross-sell recommendation engine and Next-Best-Product scoring

### Phase 4: Deals, Telemetry & Customer Collaboration
* [x] Atomic quotation-to-deal conversion (`CustomerDealHistory` & `DealProduct`)
* [x] Commercial deals pipeline with Table and Kanban views
* [x] Deal Health Engine (0–100 health scoring, 8 alert triggers, and automated nudges)
* [x] Customer Negotiation Portal with counter-offers and sanitized quote review
* [x] AI Copilot with 13 domain tools, prompt sanitization, and human-in-the-loop actions
* [x] Full-duplex WebSockets (`/api/v1/ws`) and in-memory event bus
* [x] Enterprise RAG business knowledge base with source citations

### Phase 5: Future Enhancements (Planned)
* [ ] Live payment gateway webhooks (Razorpay / Stripe)
* [ ] Docker containerization and Kubernetes Helm charts
* [ ] Advanced multi-currency exchange rate synchronization
* [ ] Native electronic signature provider integrations (DocuSign / Adobe Sign)

---

## 🔍 Known Limitations & Transparency

In adherence to strict technical credibility, the following boundaries reflect the current codebase state:
1. **Payment Settlement**: Invoicing and payment status tracking are fully implemented; however, third-party payment gateways (such as Razorpay or Stripe webhooks) operate via an internal mock settlement engine (`PortalPaymentService`).
2. **Containerization**: The project does not currently include Dockerfiles or Docker Compose configurations. In accordance with Phase Group G25, the deployment architecture is optimized for bare-metal Linux instances utilizing Nginx, systemd, and PM2.
3. **RAG Vector Search**: In development and testing environments without an active `OPENAI_API_KEY`, the RAG knowledge base automatically falls back to deterministic mathematical vectors rather than live OpenAI embeddings.

---

## 🌿 Responsible AI & Governance Principles

* **Human-in-the-Loop Authority**: AI Copilot tools never execute mutating financial operations without explicit user confirmation.
* **Deterministic Financial Bounds**: Machine learning models advise on deal risk and recommendations; however, hard policy ceilings and margin floors are strictly enforced by deterministic Decimal rule engines.
* **Explainability over Black Boxes**: All risk scores are decomposed into human-readable SHAP feature contributions and contextual business explanations.
* **Tenant Data Privacy**: Enterprise documents and transaction histories are strictly scoped to the originating company; data is never leaked across tenants or utilized for shared model training.

---

## 🤝 Contributing Guidelines

We welcome contributions to DEALFLOW360. Please adhere to the following workflow:

### 1. Branch Strategy
Follow our branch naming conventions:
* `feature/<feature-name>`: New capabilities
* `fix/<bug-description>`: Bug fixes and patches
* `docs/<doc-update>`: Documentation enhancements

### 2. Commit Standards
All commits must strictly follow the **Conventional Commits v1.0.0** specification:
```text
feat(deals): implement probability-weighted revenue forecasting
fix(approvals): enforce director sign-off on discounts exceeding 20%
test(inventory): add pessimistic concurrency reservation test
```

### 3. Pull Request Checklist
* [ ] Code adheres to existing PEP 8 (Python) and TypeScript standards.
* [ ] All 452 backend automated tests pass (`pytest tests`).
* [ ] Frontend compiles without type errors (`npm run build`).
* [ ] Any new API endpoints include OpenAPI response models and unit tests.

---

## 📄 License & Acknowledgments

* **License**: DEALFLOW360 is currently distributed under proprietary source-available terms. License information will be updated upon public release.
* **Author & Architecture**: Built with modern software architecture standards, clean hexagonal domain boundaries, and zero-compromise margin governance.

---

## 🏆 Hackathon Evaluator Summary

For judges, hackathon evaluators, and technical recruiters reviewing DEALFLOW360:

* **The Problem**: B2B companies hemorrhage revenue through uncoordinated discounting, out-of-stock commitments, and opaque approval delays.
* **The Technical Innovation**: A unified platform that pairs CRM pipeline management with **real-time Decimal margin governance**, **multi-warehouse ATP reservation**, and **tree-based ML risk scoring**.
* **AI with Substance**: Rather than superficial chatbot wrappers, DEALFLOW360 implements a pure-Python ML tournament suite (XGBoost, LightGBM, Random Forest), Platt-calibrated probabilities, SHAP explainability, and 13 permission-guarded Copilot tools.
* **Engineering Rigor**: 44 database models, 28 Alembic migrations, 452 passing backend tests, and a production-ready DevOps architecture built on Linux systemd and Nginx.
* **Business Impact**: Closes the loop from quotation to cash, protecting enterprise operating margins while accelerating deal velocity.
