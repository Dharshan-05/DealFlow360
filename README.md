# DealFlow360

> **"DealFlow360 doesn't just record a sale. It continuously governs the deal from quotation to cash."**

DealFlow360 is an enterprise deal orchestration and discount governance platform designed to guide deals end-to-end—from initial quotation, dynamic policy and margin protection, multi-warehouse fulfillment, and customer negotiation, through to automated billing and payment settlement.

---

#### Current Status: B11 Complete (Phases 001–215, 456–470)

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
- **G22 (Phases 106–110 Discount Governance Engine)**:
  - **Phase 106**: Manager Authority Limit (`ManagerAuthorityLimit` entity managing Sales Manager maximum discount approval and granting thresholds, partial unique index, self-modification check).
  - **Phase 107**: Finance Authority Limit (`FinanceAuthorityLimit` entity managing Finance officer discount limits; Sales Reps forbidden from configuring Finance limits [403]).
  - **Phase 108**: Discount Policy Engine (`DiscountPolicyEngine` evaluating active Company, Customer, Category, Product ceilings and actor authority limits at unified UTC timestamp; computes effective ceiling as `MIN(ceilings)`).
  - **Phase 109**: Discount Validation Service (`DiscountValidationService` verifying tenant isolation, input boundaries [0–100], and executing policy checks).
  - **Phase 110**: Discount Violation Detection (Explicit taxonomy: `COMPANY_DISCOUNT_CEILING`, `CUSTOMER_DISCOUNT_CEILING`, `CATEGORY_DISCOUNT_CEILING`, `PRODUCT_DISCOUNT_CEILING`, `SALES_REP_AUTHORITY_LIMIT`, `MANAGER_AUTHORITY_LIMIT`, `FINANCE_AUTHORITY_LIMIT`).
- **G23 (Phases 111–115 Discount Intelligence Foundation)**:
  - **Phase 111**: Recommended Discount Engine (`DiscountRecommendationEngine` generating optimal, explainable recommendations clamped to safe boundaries with structured reason codes).
  - **Phase 112**: Maximum Safe Discount (`MaximumSafeDiscountEngine` deterministically evaluating upper safe bounds intersecting policy ceilings, margin limits, and actor authority).
  - **Phase 113**: Margin Protection Engine (`MarginProtectionEngine` preventing profit erosion using exact Decimal arithmetic, handling cost >= price, zero price, and insufficient buffer).
  - **Phase 114**: Historical Discount Analysis (`DiscountHistoryAnalysisService` aggregating tenant-isolated historical discounts, sample size, mean, min, max, and latest grants).
  - **Phase 115**: Customer Discount Analysis (`CustomerDiscountAnalysisService` evaluating customer-specific discount behavior against active ceilings and relationship profile).
- **G24 (Phases 116–120 Discount Intelligence -> Inventory / Deal / Risk / Decision / Automation)**:
  - **Phase 116**: Inventory-Aware Discount (`InventoryAwareDiscountService` evaluating multi-warehouse ATP, physical, reserved stock and backorders to produce inventory signals `EXCESS_AVAILABLE`, `HEALTHY_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `BACKORDERED` and stock-sensitive discount multipliers).
  - **Phase 117**: Deal-Value-Aware Discount (`DealValueAwareDiscountService` sizing deals into transaction volume tiers `LOW_VALUE`, `STANDARD_VALUE`, `HIGH_VALUE`, `ENTERPRISE_TIER` and calculating volume incentive multipliers).
  - **Phase 118**: Discount Risk Calculation (`DiscountRiskCalculationService` deterministically computing 0–100 composite risk score across 5 weighted dimensions: `GOVERNANCE_OVERRUN`, `MARGIN_EROSION`, `INVENTORY_SCARCITY`, `CUSTOMER_PROFILE`, `DEAL_EXPOSURE` and risk levels `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - **Phase 119**: Discount Decision Engine (`DiscountDecisionEngine` orchestrating deterministic precedence rules across Governance, Actor Authority, Maximum Safe Discount, Margin Protection, and Risk Scoring to produce outcomes `APPROVED`, `ADJUSTED`, `ESCALATION_REQUIRED`, `REJECTED`).
  - **Phase 120**: Automated Discount Application (`AutomatedDiscountApplicationService` executing server-side re-verified discount application, guaranteeing idempotency via `deal_reference`, persisting `AppliedDiscount`, updating customer history, and logging immutable `AuditLog` domain events).
- **B01 (Phases 121–125 AI/ML Risk Engine Foundation)**:
  - **Phase 121**: ML Dataset Preparation (`MLDatasetPreparationService` orchestrating data extraction, record validation, missing value imputation, sanitization, and deterministic dataset manifests).
  - **Phase 122**: Historical Deal Dataset (`HistoricalDealDatasetExtractor` extracting point-in-time deal records combining `CustomerDealHistory`, `AppliedDiscount`, and historical customer metrics without future leakage).
  - **Phase 123**: Feature Engineering (`FeatureEngineeringService` converting raw deal records into ML-ready tabular feature vectors with log transforms and flat export).
  - **Phase 124**: Discount Features (`DiscountFeatureEngineer` calculating ceiling utilization ratios, historical customer baseline deviations, tier utilization, and breach indicators).
  - **Phase 125**: Margin Features (`MarginFeatureEngineer` evaluating gross profit, discounted margin amount/percentage, margin compression ratio, and zero-cost/zero-price edge cases using Decimal arithmetic).
- **B02 (Phases 126–130 AI/ML Risk Engine Feature Engineering & Foundation)**:
  - **Phase 126**: Customer Features (`CustomerFeatureEngineer` computing relationship tenure days, tier codes, lifetime orders, revenue, settled amounts, average order value, payment default ratio, payment reliability score, and price sensitivity).
  - **Phase 127**: Deal Value Features (`DealValueFeatureEngineer` deriving nominal scale, log transform `log(deal_value + 1)`, transaction size category `MICRO`, `SMALL`, `MEDIUM`, `LARGE`, `ENTERPRISE`, deal-to-AOV ratio, and statistical outlier flags).
  - **Phase 128**: Approval Features (`ApprovalFeatureEngineer` quantifying historical governance approval requests, escalations, rejections, approval rate, escalation rate, rejection rate, threshold proximity, and escalation required indicators).
  - **Phase 129**: Negotiation Features (`NegotiationFeatureEngineer` evaluating prior deal negotiations, concession deal counts, concession frequency, average concession magnitude, max concession, volatility, trend slope, and repeated negotiation indicators).
  - **Phase 130**: Fulfillment Features (`FulfillmentFeatureEngineer` evaluating customer fulfillment history, fulfilled order counts, fulfillment success rate, fulfillment exceptions, backorder indicators, and warehouse stock availability ratios; with ML target infrastructure managed by `RiskTargetGenerator` without target leakage).
- **B03 (Phases 131–135 AI/ML Risk Engine Models & Comparison)**:
  - **Phase 131**: Risk Dataset Pipeline (`RiskDatasetPipelineService` extracting deterministic, leak-free 50-feature matrices with label encodings and stratified train/val/test splits).
  - **Phase 132**: XGBoost Model (`XGBoostRiskModelService` implementing 2nd-order gradient boosted trees minimizing logistic loss with L2 regularization, feature importances, and artifact serialization).
  - **Phase 133**: LightGBM Model (`LightGBMRiskModelService` implementing leaf-wise best-first tree growth on gradient residuals, probability calibration bounds, and feature importances).
  - **Phase 134**: Random Forest Baseline (`RandomForestRiskModelService` implementing bagging ensemble with bootstrap sampling, random feature sub-selection `m_try`, and Gini impurity optimization).
  - **Phase 135**: Model Comparison (`ModelComparisonService` evaluating all 3 architectures on identical test splits, generating Wilcoxon-Mann-Whitney ROC-AUC, PR-AUC, F1, accuracy, Brier scores, and automated winner selection).
- **B04 (Phases 136–145 AI/ML Risk Engine Pipeline, Calibration, Scoring & Dashboard)**:
  - **Phase 136**: Model Selection (`ModelSelectionService` evaluating candidate models deterministically across held-out test splits with composite scoring formula and full selection justification).
  - **Phase 137**: Model Training Pipeline (`ModelTrainingPipelineService` orchestrating end-to-end dataset extraction, candidate model tournament, held-out evaluation, and tenant registry caching).
  - **Phase 138**: Model Evaluation (`ModelMetricsEvaluator` computing out-of-sample held-out test split accuracy, precision, recall, F1, ROC-AUC, PR-AUC, and Brier score).
  - **Phase 139**: Probability Calibration (`ProbabilityCalibrationService` fitting Platt scaling logistic calibration on validation split and verifying Brier score improvement).
  - **Phase 140**: Risk Prediction API (`RiskPredictionInferenceService` serving sub-millisecond inference using cached champion models without retraining).
  - **Phase 141**: Risk Score 0–100 (`RiskPredictionInferenceService.compute_risk_score` mapping calibrated probabilities into an integer 0–100 risk scale).
  - **Phase 142**: Risk Classification (`RiskPredictionInferenceService.classify_risk` mapping scores into 4 distinct governance tiers: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - **Phase 143**: SHAP Explainability (`TreeExplainabilityService` traversing tree structures to compute exact marginal signed feature contributions and impact percentages).
  - **Phase 144**: Risk Factors (`RiskFactorExtractionService` translating mathematical feature attributions into contextual business explanations and severity tiers).
  - **Phase 145**: AI Risk Dashboard (`AIRiskDashboardService` executive KPIs, pipeline risk distribution, model performance telemetry, and active deal risk rankings at `/risk-dashboard`).
- **B05 (Phases 146–155 Approval Engine Routing & Policy)**:
  - **Phase 146**: Approval Matrix (`ApprovalMatrix` policy entity configuring approval tiers, thresholds, and routing hierarchies).
  - **Phase 147**: Approval Rules (`ApprovalRule` entity defining condition trees, discount boundaries, and margin thresholds).
  - **Phase 148**: Approval Trigger Detection (`ApprovalTriggerDetector` detecting discount overruns, margin breaches, negative profitability, and ML risk triggers).
  - **Phase 149**: Auto-Approval Engine (`AutoApprovalEngine` evaluating low-risk, safe-harbor deals for instant policy approval without manual latency).
  - **Phase 150**: Manager Approval (`ApprovalDecisionEngine` routing tier-1 discount concessions to Sales Management).
  - **Phase 151**: Director Approval (`ApprovalDecisionEngine` routing high-value, deep-discount exceptions to Director governance).
  - **Phase 152**: VP Approval (`ApprovalDecisionEngine` routing strategic enterprise concessions to VP executive review).
  - **Phase 153**: Finance Approval (`ApprovalDecisionEngine` parallel finance authority enforcement on margin-sensitive deals).
  - **Phase 154**: Parallel Approval (`ParallelApprovalService` orchestrating concurrent multi-stakeholder governance reviews).
  - **Phase 155**: Sequential Approval (`SequentialApprovalService` managing structured step-by-step hierarchical sign-offs).
- **B06 (Phases 156–165 Approval Engine Lifecycle, Audit & Delegation)**:
  - **Phase 156**: Approval Request CRUD (`ApprovalRequest` entity, tenant isolation, request states `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`).
  - **Phase 157**: Approval Action (`ApprovalActionService` recording immutable approve/reject actions with required reasoning).
  - **Phase 158**: Approval History (`ApprovalHistory` append-only audit trail capturing full review lifecycles and actor attribution).
  - **Phase 159**: SLA Engine (`ApprovalSLAService` monitoring review deadlines, calculating SLA breach timers, and flagging at-risk requests).
  - **Phase 160**: Escalation Engine (`ApprovalEscalationService` auto-escalating overdue reviews to higher authority tiers).
  - **Phase 161**: Delegation Engine (`ApprovalDelegation` entity managing temporary authority delegation during out-of-office periods).
  - **Phase 162**: Rejection Reason Engine (`RejectionReasonCode` taxonomy and structured justification capture).
  - **Phase 163**: Conditional Approval (`ConditionalApprovalService` attaching binding stipulations and discount caps to approvals).
  - **Phase 164**: Approval Notifications (`ApprovalNotificationService` real-time alerting for requests, decisions, and escalations).
  - **Phase 165**: Approval Dashboard (`ApprovalDashboardService` metrics on pending reviews, turnaround times, SLA compliance, and bottlenecks).
- **B07 (Phases 166–175 AI Upsell / Cross-Sell Engine)**:
  - **Phase 166**: AI Upsell Engine (`AIUpsellEngine` evaluating product upgrade tiers, higher-capacity SKUs, and premium alternative recommendations).
  - **Phase 167**: AI Cross-Sell Engine (`AICrossSellEngine` analyzing complementary category bundles, accessories, and warranty attachments).
  - **Phase 168**: Customer Purchase Pattern Analysis (`PurchasePatternAnalysisService` analyzing historical order frequency, seasonal cycles, and recurring reorder intervals).
  - **Phase 169**: Product Affinity Analysis (`ProductAffinityService` computing Jaccard co-occurrence coefficients and item affinity matrices across transactions).
  - **Phase 170**: Frequently Bought Together (`FrequentlyBoughtTogetherService` mining transactional co-purchases with support, confidence, and lift thresholds).
  - **Phase 171**: Rule-Based Recommendation Engine (`RuleBasedRecommendationEngine` deterministic fallback rules for mandatory attachments, accessories, and warranties).
  - **Phase 172**: Collaborative Filtering (`CollaborativeFilteringService` user-item and item-item interaction matrices for customer neighborhood recommendations).
  - **Phase 173**: Content-Based Filtering (`ContentBasedFilteringService` TF-IDF and attribute vector cosine similarity for product feature matching).
  - **Phase 174**: Hybrid Recommendation Engine (`HybridRecommendationEngine` ensemble model blending collaborative, content, rule-based, and affinity signals).
  - **Phase 175**: Margin-Aware Recommendations (`MarginAwareRecommendationService` profit-filtering recommendations to maximize gross margin contribution).
- **B08 (Phases 176–185 AI Upsell / Cross-Sell Engine — Scoring, Ranking, Tracking & Analytics)**:
  - **Phase 176**: Upsell Score (`UpsellScoringService.calculate_upsell_score` deterministic 0–100 composite scoring across customer tier, margin, and purchase patterns).
  - **Phase 177**: Cross-Sell Score (`CrossSellScoringService.calculate_cross_sell_score` deterministic 0–100 composite scoring across affinity, bought-together, and tenure).
  - **Phase 178**: Recommendation Ranking (`RecommendationRankingService.rank_recommendations` multi-criteria ranking algorithm balancing score, margin, inventory, and historical conversion).
  - **Phase 179**: AI Next-Best-Product (`NextBestProductEngine.get_next_best_products` unified upsell/cross-sell evaluation per customer).
  - **Phase 180**: Upsell Explanation (`RecommendationExplanationService.generate_explanation` structured human-readable justification without hallucination).
  - **Phase 181**: Add-to-Quote Recommendation (`RecommendationQuoteIntegrationService.add_recommendation_to_quote` line-item quote addition, product status validation, and automated lifecycle event generation).
  - **Phase 182**: Real-Time Margin Update (`RealTimeMarginService.calculate_margins` strict Decimal financial arithmetic recalculating gross profit and margin percentages without floating-point inaccuracies).
  - **Phase 183**: Upsell Acceptance Tracking (`RecommendationEvent` entity, Alembic migration, `RecommendationTrackingService` tracking `GENERATED`, `VIEWED`, `SELECTED`, `ADDED_TO_QUOTE`, `ACCEPTED`, `REJECTED`, `DISMISSED` with 5-second idempotency deduplication).
  - **Phase 184**: Recommendation Analytics (`RecommendationAnalyticsService.get_analytics` lifecycle funnels, acceptance conversion rates, and product conversion leaderboards with date filtering and zero-denominator protection).
- **B09 (Phases 186–195 Quotation Engine)**:
  - **Phase 186**: Quotation CRUD (`Quotation` & `QuotationLineItem` entities, lifecycle management: `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `SENT`, `ACCEPTED`, `EXPIRED`, `CANCELLED`, tenant-isolated CRUD endpoints).
  - **Phase 187**: Quote Number Generation (`QuotationNumberGenerator` producing deterministic, sequential, company-scoped `QT-YYYYMM-XXXX` numbers with collision protection).
  - **Phase 188**: Customer Selection (Tenant-isolated customer verification, rejection of cross-tenant customer IDs, inclusion of customer metadata in quotation DTOs).
  - **Phase 189**: Product Selection (Catalog validation, rejection of inactive/non-sellable products, product base pricing inheritance).
  - **Phase 190**: Quantity Management (Positive quantity validation, Decimal-safe precision, automatic recalculation of line and grand totals).
  - **Phase 191**: Unit Price (Product base price inheritance, authorized unit price overrides, monetary precision preservation).
  - **Phase 192**: Tax Calculation (Per-line tax calculation on net discounted base, zero-tax cases support, consolidated tax scaling under overall discounts).
  - **Phase 193**: Line Discount (Percentage-based line discount, boundaries validation `[0, 100]`, net line subtotal recalculation).
  - **Phase 194**: Overall Discount (Quotation-level discount, interaction with line discounts, net taxable base and grand total recalculation).
  - **Phase 195**: Real-Time Margin (Product cost vs selling price, gross profit amount, margin %, negative/zero margin detection, Decimal financial arithmetic).
- **B10 (Phases 196–205 Quotation Lifecycle, Versioning, Approval, PDF, Email & Deal Conversion)**:
  - **Phase 196**: Quotation Status (`QuotationStatus` lifecycle state machine: `DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `SENT`, `VIEWED`, `ACCEPTED`, `REJECTED`, `EXPIRED`, `CONVERTED`, `CANCELLED`; `QuotationStatusTransitionValidator` enforcing immutable transitions, terminal state guards, and AuditLog event tracking).
  - **Phase 197**: Quote Versioning (`QuotationVersion` entity & `QuotationVersioningService` capturing immutable historical revisions in `quotation_versions`, sequential `v1, v2...` versioning, full Decimal snapshot preservation, and active version management).
  - **Phase 198**: Quote Expiration (`QuotationExpirationService` deterministic UTC timestamp evaluation against `valid_until`, manual expiration trigger, expired quote acceptance/send rejection, and idempotent evaluation).
  - **Phase 199**: Quote Approval Integration (`QuotationApprovalService` direct integration with B05/B06 `ApprovalDecisionEngine.submit_for_approval`, auto-approval vs multi-level routing, and linkage via `approval_request_id`).
  - **Phase 200**: Quote PDF Generation (`QuotationPdfService` ReportLab vector PDF generation with company legal branding, customer details, line item tables, monetary totals, margins, and tenant-isolated `application/pdf` streaming).
  - **Phase 201**: Quote Email (`QuotationEmailService` email dispatch abstraction with safe development transport, PDF attachment, recipient validation, and delivery state `SENT`).
  - **Phase 202**: Quote Send Tracking (`QuotationSendLog` entity & `QuotationSendTrackingService` tracking send logs, unique tracking tokens, recipient view events, and automatic transitions to `VIEWED`).
  - **Phase 203**: Quote Acceptance (`QuotationAcceptanceService` acceptance workflow, unapproved and expired quotation guards, and idempotent re-acceptance).
  - **Phase 204**: Quote Rejection (`QuotationRejectionService` mandatory rejection reason, status transition to `REJECTED`, terminal state protection, and audit logging).
  - **Phase 205**: Quote Conversion to Deal (`QuotationDealConversionService` transactional atomic conversion of `ACCEPTED` quotation into existing `CustomerDealHistory` entity, copying commercial terms, setting `CONVERTED` status, and duplicate conversion prevention).
- **B11 (Phases 206–215 Commercial Deals Pipeline & Management)**:
  - **Phase 206**: Deal Creation from Quote (`DealCreationService` transactional conversion of `ACCEPTED` quotation into `CustomerDealHistory` deal record with line-item `DealProduct` generation, `EXPIRED`/unaccepted guards, idempotency, and status `WON` in stage `CLOSED_WON`).
  - **Phase 207**: Deal Product Linking (`DealProduct` entity & `DealProductService` managing line-item catalog linking to deals, quantities, unit prices, costs, discounts, taxes, and margins with duplicate prevention and closed deal mutation guards).
  - **Phase 208**: Deal Value Calculation (`DealCalculationEngine` centralized Decimal financial arithmetic using `ROUND_HALF_UP` precision, reconciling subtotals, line discounts, taxes, total costs, gross profit, and deal values).
  - **Phase 209**: Deal Margin Calculation (`DealMarginService` computing exact gross margin %, discounted margin relative to list subtotal, and risk categorization: `HEALTHY`, `MODERATE`, `THIN`, `CRITICAL` with negative margin detection).
  - **Phase 210**: Deal Stage Management (`DealStageManagementService` lifecycle state machine: `NEW`, `QUALIFIED`, `PROPOSAL`, `NEGOTIATION`, `CLOSED_WON`, `CLOSED_LOST`; enforcing permitted stage transitions, terminal state guards, and AuditLog event tracking).
  - **Phase 211**: Deal Probability (`DealProbabilityService` deterministic 0–100% win probability calculation with business signal breakdowns across stage baselines, quote status, customer tiers, margin health, and sales activity recency).
  - **Phase 212**: Deal Forecasting (`DealForecastingService` computing probability-weighted expected revenue `deal_value * probability / 100`, company-wide pipeline aggregations, and multi-stage forecast distributions).
  - **Phase 213**: Deal Activity Tracking (`DealActivity` entity & `DealActivityService` append-only interaction tracking for `NOTE`, `CALL`, `EMAIL`, `MEETING`, `TASK`, `FOLLOW_UP`, and `STAGE_CHANGE` with actor accountability and tenant isolation).
  - **Phase 214**: Deal Timeline (`DealTimelineService` unified chronological event stream aggregating deal creation, activities, quotation lifecycle events, and send/view tracking).
  - **Phase 215**: Deal Dashboard (`DealDashboardService` executive pipeline KPI aggregation: pipeline value, expected revenue, win rate, open/won/lost deal counts, average deal size, stage distributions, recent activities, and top deals).
- **G25 (Phases 456–470 DevOps Without Docker)**:
  - **Phase 456**: Production Environment Config (Pydantic v2 fail-safes, strict type coercion, rejection of debug/weak secrets/default DB in production).
  - **Phase 457**: Git Branch Strategy (Trunk-based development, branch naming conventions, protected main branch).
  - **Phase 458**: Git Commit Standards (Conventional Commits v1.0.0, scope enforcement, structured `.gitmessage` template).
  - **Phase 459**: GitHub Repository Cleanup (Comprehensive `.gitignore`, removal of untracked artifacts, log/sock hygiene).
  - **Phase 460**: GitHub Actions Foundation (Unified `.github/workflows/ci.yml` multi-job pipeline).
  - **Phase 461**: Backend CI (Python 3.11, PostgreSQL 15 service container, Alembic migrations, database seed, test runner).
  - **Phase 462**: Frontend CI (Node 20, npm ci, TypeScript strict typecheck, Next.js production build).
  - **Phase 463**: Automated Tests in CI (Regression test validation covering all 265 backend test suites).
  - **Phase 464**: Build Validation (Artifact generation, standalone Next.js bundle validation).
  - **Phase 465**: Environment Secret Management (Decoupled `.env.production.example`, key rotation runbooks, zero secret leaks).
  - **Phase 466**: Nginx Reverse Proxy (Edge TLS 1.3, rate limiting, HSTS, gzip, static asset caching, unified routing).
  - **Phase 467**: Backend Process Management (systemd service unit `dealflow360-backend.service`, Uvicorn multi-worker pool, sandbox hardening).
  - **Phase 468**: Frontend Process Management (systemd service unit `dealflow360-frontend.service`, PM2 `ecosystem.config.js` manifest).
  - **Phase 469**: Deployment Documentation (19-section operational manual `docs/devops/DEPLOYMENT_GUIDE.md`).
  - **Phase 470**: Production Readiness Audit (Zero-trust audit report `docs/devops/PRODUCTION_READINESS_AUDIT.md`, automated verification script).

### ⏳ Not Yet Implemented (Scheduled for Future Authorized Phases)
- Phase 216+ (Deal Negotiation Engine / Contract Management)
- Pricing Engine & Dynamic Discount Matrix
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
