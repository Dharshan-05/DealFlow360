STRICT FIX AND COMPLETION TASK — DO NOT REDESIGN.

You have already implemented part of DealFlow360 Screens 01–04.

Current implementation already includes:

* Login / Signup tabs
* Password visibility
* Validation
* Account type selection
* Customer portal entry
* Quotations List
* Search
* Stage filters
* Clickable quotation rows
* Existing Quotation Detail workspace
* Updated quotation data
* Per-line discount-limit validation
* Clear OVER / OK states
* Live discount-validation banner

DO NOT REMOVE OR REBUILD these working features.

DO NOT create duplicate screens.

DO NOT change the established DealFlow360 design system.

Your task is ONLY to audit, fix, and complete Screens 01–04.

==================================================
01 — LOGIN / SIGNUP
===================

Keep the existing implementation.

Verify and fix:

* Log In / Sign Up tabs work correctly.
* Email validation.
* Password validation.
* Show/hide password.
* Forgot Password.
* Remember Me.
* Account Type:
  Internal User
  Customer.
* Company/team selector where required.
* Loading state.
* Invalid credentials/error state.
* Successful login state.

Navigation must be:

Internal User
→ Sales Dashboard

Customer
→ Customer Portal

Make sure the authentication screen visually matches the existing DealFlow360 system.

Do not redesign it.

==================================================
02 — SALES DASHBOARD — COMPLETE THIS SCREEN
===========================================

This is the main missing piece.

Create/fix the Sales Dashboard using the existing DealFlow360 application shell.

Navigation:

Dashboard
Quotations
Approvals
Fulfillment
Subscriptions
Invoices
Deal Health
Reports
Product

Dashboard must have the active white-highlight treatment already used by the application.

Header:

Sales Dashboard

Breadcrumb:
Home

Purpose:
The dashboard is the central hub connecting all sales operations.

==================================================
KPI CARDS
=========

Create these KPI cards with the exact values:

Pending Approvals
4

Open Quotations
12

At-Risk Deals
3

Cards must be clean, compact, and enterprise-grade.

Do not use excessive colors.

==================================================
PRIMARY ACTIONS
===============

Add:

* New Quotation

View Approvals

Actions must look like the existing DealFlow360 buttons.

Navigation:

New Quotation
→ Quotation Detail / Quotation creation workspace

View Approvals
→ Approvals List

==================================================
RECENT ACTIVITY
===============

Create a Recent Activity section containing:

Acme Corp quotation approved by Finance

Beta Industries requested discount change

East Depot stock updated for Order #2291

Each activity should include:

* meaningful timestamp
* activity type/status
* relevant customer/order
* clean visual hierarchy

==================================================
DASHBOARD SUPPORTING SECTIONS
=============================

Add compact business overview sections for:

Quotation Pipeline

Approval Status

Fulfillment Status

Deal Risk

These should summarize information without making the dashboard unnecessarily crowded.

Use simple charts/progress indicators only where useful.

==================================================
03 — QUOTATIONS LIST
====================

The existing quotation list is working.

DO NOT rebuild it.

Audit and fix the current implementation.

Required:

Header:
Quotations

Subtitle:
Every quotation, one row per quote. Click a row to open.

Actions:

* New Quotation

Switch to Table View

Required quotation data:

DRAFT

Acme Corp — $12,400

Delta LLC — $3,200

PENDING APPROVAL

Beta Industries — $28,900

APPROVED

Nova Retail — $9,750

NEGOTIATION

Zenith Co — $15,300

CONFIRMED

Orion Ltd — $41,000

Make sure search and stage filtering work visually.

Every quotation row must open:

→ Quotation Detail

Do not duplicate the quotation workspace.

==================================================
04 — QUOTATION DETAIL
=====================

The existing quotation workspace must be preserved.

Audit and fix it.

Header:

Q-1042
Acme Corp

Subtitle:

Add products, apply discounts, review upsells.

Fields:

Customer
Acme Corp

Price List
Default Price List

Line items:

Laptop Pro 14
Qty: 2
Price: $1,200
Discount: 12%
Limit: 15%
Status: OK

Onsite Setup Service
Qty: 1
Price: $450
Discount: 18%
Limit: 10%
Status: OVER (+8pt)

Extended Warranty
Qty: 1
Price: $180
Discount: 10%
Limit: 15%
Status: OK

==================================================
CRITICAL DISCOUNT RULE
======================

Maintain TRUE PER-LINE validation.

Each line must compare:

Line Discount
vs
That Line's Own Discount Limit

Example:

Laptop Pro 14:
12% <= 15%
→ OK

Onsite Setup Service:
18% > 10%
→ OVER (+8pt)

Extended Warranty:
10% <= 15%
→ OK

Validation must happen LIVE while the user changes the discount.

Do NOT validate only when clicking Submit.

The affected row must immediately show the OVER state.

==================================================
LIVE VALIDATION BANNER
======================

Keep the existing banner explaining:

Discount is checked live against each line's own limit.

Make sure the message is visible but not intrusive.

==================================================
UPSELL / CROSS-SELL
===================

Ensure the quotation workspace includes:

Wireless Mouse
Margin +$18

Docking Station
Promo 12% off

Care Plan 2yr
Margin +$46

These should appear as professional AI-assisted recommendations.

Actions:

Add
Dismiss
View Details

Keep the AI styling restrained.

==================================================
QUOTATION ACTIONS
=================

Ensure these actions exist:

Save Draft

Submit for Approval

If any line exceeds its discount limit:

Show clear approval-required state.

Do not silently allow the user to assume the quotation is approved.

==================================================
INTERACTION STATES
==================

Add/fix:

Default state

Hover state

Focus state

Loading state

Validation error state

Success state

Unsaved changes state

Approval required state

Do not create unnecessary animations.

==================================================
NAVIGATION FLOW
===============

The flow must work conceptually:

01 Login
↓
02 Sales Dashboard
↓
03 Quotations List
↓
04 Quotation Detail

Dashboard:
Quotations → Quotations List

Quotations List:
Click row → Quotation Detail

Quotation Detail:
Submit for Approval → Approvals flow

Dashboard:
View Approvals → Approvals List

==================================================
DESIGN SYSTEM — STRICT
======================

Use the existing DealFlow360 visual system.

Primary foundation:

Black
White

Accent color:
Approximately 10% maximum.

Use accent only where it communicates:

* status
* risk
* important action
* AI intelligence
* alerts

Do not introduce random colors.

Do not introduce a completely new dashboard style.

Do not use excessive gradients.

Do not use excessive glassmorphism.

Do not use oversized decorative cards.

Keep it:
Premium
Minimal
Enterprise
Professional
Data-focused

==================================================
RESPONSIVE
==========

Verify:

Desktop
Tablet
Mobile

Mobile requirements:

* collapsible navigation
* stacked KPI cards
* readable quotation rows
* usable filters
* no broken tables
* quotation detail remains usable
* primary actions remain accessible

==================================================
FINAL AUDIT
===========

Before finishing, check every requirement:

[ ] Login / Signup complete
[ ] Authentication states complete
[ ] Internal → Dashboard
[ ] Customer → Portal
[ ] Sales Dashboard complete
[ ] KPI values correct
[ ] Dashboard actions correct
[ ] Recent Activity present
[ ] Quotations List complete
[ ] Search works
[ ] Stage filters present
[ ] Clickable quotation rows
[ ] Quotation Detail preserved
[ ] Exact quotation data present
[ ] Per-line discount validation
[ ] OVER / OK states
[ ] Live validation
[ ] Upsell / cross-sell section
[ ] Save Draft
[ ] Submit for Approval
[ ] Approval-required state
[ ] Navigation connected
[ ] Responsive layouts
[ ] Existing design system preserved

IMPORTANT:

This is a FIX + COMPLETE task.

Do not redesign working components.
Do not delete existing working functionality.
Do not duplicate existing screens.
Do not modify Screens 05–15 yet.

ONLY finish and polish Screens 01–04.
