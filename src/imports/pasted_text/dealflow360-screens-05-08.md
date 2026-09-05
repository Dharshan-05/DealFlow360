STRICT IMPLEMENTATION TASK — COMPLETE SCREENS 05–08 ONLY.

DealFlow360 Screens 01–04 are APPROVED and FROZEN.

DO NOT:

* modify Screens 01–04
* redesign Screens 01–04
* duplicate existing components
* replace the established design system
* change existing typography, colors, spacing, navigation, buttons, cards, or interaction patterns

Instead, INHERIT the exact visual language and reusable components from Screens 01–04.

Your task is to build and complete ONLY:

05 → Approvals List
06 → Approval Detail
07 → Fulfillment List
08 → Fulfillment Detail

==================================================
GLOBAL PRODUCT CONTEXT
======================

DealFlow360 is a premium enterprise B2B SaaS platform connecting:

Quotations
→ Discounts
→ Risk
→ Approvals
→ Inventory
→ Fulfillment
→ Billing
→ Subscriptions
→ Customer Portal
→ Analytics

Screens 05–08 must feel like a natural continuation of Screens 01–04.

Design foundation:

* Black and white first
* Restrained accent color
* Premium enterprise SaaS
* Clean information hierarchy
* High-density but readable data
* Professional tables
* Clear status indicators
* Minimal decoration
* No unnecessary gradients
* No excessive glassmorphism
* No random colors

Use existing DealFlow360 components wherever possible.

==================================================
05 — APPROVALS LIST
===================

Create the Approvals List.

Global navigation:

Dashboard
Quotations
Approvals
Fulfillment
Subscriptions
Invoices
Deal Health
Reports
Product

Approvals must be the ACTIVE module using the existing active-tab treatment.

Page header:

Approvals

Subtitle:

Every quotation that needed, needs, or is going through discount approval.

==================================================
SUMMARY / FILTERS
=================

Create compact status filters:

3 Pending
1 Returned
12 Approved

Add:

Pending Only

Also provide:

* search
* status filter
* risk filter
* assigned-to filter
* customer filter

Filters must match the existing DealFlow360 UI.

==================================================
APPROVAL TABLE
==============

Create a professional enterprise table.

Columns:

Quotation
Customer
Blended Risk
Stage
Assigned To

Use this exact data:

Q-1042
Acme Corp
HIGH
Sales Manager
M. Shah

Q-1039
Beta Industries
MEDIUM
Finance
R. Iyer

Q-1035
Nova Retail
LOW
Auto-Approved

Each row must be clickable.

Click row:

Approvals List
→ Approval Detail

==================================================
APPROVAL INFORMATION
====================

Risk must be immediately understandable.

Use:

HIGH
MEDIUM
LOW

Do not rely only on color.

Use text + badge/icon/indicator where appropriate.

Add a banner:

"Click a row for full approval detail, risk breakdown, and audit trail."

==================================================
06 — APPROVAL DETAIL
====================

Create the detailed approval workspace.

Header:

Q-1042
Acme Corp

Show:

Blended Risk
HIGH

Customer Tier
Gold

Clearly communicate that this quotation requires approval.

==================================================
WHY FLAGGED
===========

Create a detailed table:

Line
Discount
Allowed Limit
Variance
Status

Laptop Hardware
12%
15%
0 pt
OK

Setup Service
18%
10%
+8 pt
OVER

Use the same visual language as Screen 04's live discount validation.

CRITICAL:

The approval screen must connect directly to the per-line discount validation from Quotation Detail.

The user should immediately understand:

Which line caused the problem?
How far over the limit?
Why does approval exist?

==================================================
EXPLANATION BANNER
==================

Include:

"The worst single line plus the overall pattern determines the blended score. One bad line can require approval."

Make this visually prominent but not oversized.

==================================================
APPROVAL PROGRESSION
====================

Create a clear approval workflow:

Submitted
↓
Sales Manager
↓
Finance
↓
Confirmed

Show:

* completed steps
* current step
* pending steps

The current step must be visually obvious.

==================================================
AUDIT HISTORY
=============

Create a chronological audit timeline/table.

Entry 1:

J. Rao
Submitted
Aug 20
Initial 12% discount

Entry 2:

M. Shah
Returned
Aug 21
Requested justification

Entry 3:

J. Rao
Resubmitted
Aug 22
Added margin note

Show timestamps and actions clearly.

==================================================
APPROVAL ACTIONS
================

Primary actions:

Approve

Return for Revision

Reject

Each action must have appropriate interaction states.

For destructive/reversible actions, provide confirmation UI.

Return for Revision should allow the reviewer to enter a reason.

Reject should require confirmation.

Approve should show success confirmation.

==================================================
07 — FULFILLMENT LIST
=====================

Create the Fulfillment and Stock management screen.

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

Fulfillment must be ACTIVE.

Header:

Fulfillment and Stock

Subtitle:

Live stock per warehouse + every order needing fulfillment.

==================================================
INVENTORY TABLE
===============

Columns:

Warehouse
Product
In Stock
Reserved
Available

Use EXACT data:

Main Warehouse
Laptop Pro 14
40
18
22

East Depot
Laptop Pro 14
10
6
4

Main Warehouse
Docking Station
65
12
53

Make the Available quantity easy to understand.

Formula concept:

Available = In Stock - Reserved

==================================================
STOCK STATUS
============

Include clear states:

Available
Low Stock
Out of Stock

Do not rely only on color.

Show useful stock warnings where appropriate.

Add:

* warehouse filter
* product filter
* search
* stock status filter

==================================================
ORDERS AWAITING FULFILLMENT
===========================

Create a second section:

Orders Awaiting Fulfillment

Columns:

Order
Customer
Status
Warehouses

Rows should be clickable.

Clicking an order:

Fulfillment List
→ Fulfillment Detail

==================================================
08 — FULFILLMENT DETAIL
=======================

Create a detailed fulfillment workspace.

Show:

Order ID

Customer

Quotation Reference

Fulfillment Status

==================================================
ORDER ITEMS
===========

Create a line-item table:

Product
Quantity
Warehouse
Available
Reserved
Fulfillment Status

Show realistic examples connected to the inventory data.

Example:

Laptop Pro 14
2
Main Warehouse
22
2
Reserved

Docking Station
1
Main Warehouse
53
0
Pending

==================================================
WAREHOUSE ALLOCATION
====================

Show where each item is being fulfilled from.

Allow the user to conceptually:

* reserve stock
* change warehouse
* split fulfillment
* check availability

If inventory is insufficient, show a clear warning.

==================================================
FULFILLMENT WORKFLOW
====================

Create the status progression:

Pending
↓
Reserved
↓
Packed
↓
Shipped
↓
Delivered

Clearly show:

* completed state
* current state
* next available action

==================================================
FULFILLMENT ACTIONS
===================

Actions should change according to status.

Examples:

Reserve Stock
Change Warehouse
Mark Packed
Mark Shipped
Mark Delivered

Do not display every action as equally primary.

Use one clear primary action and secondary actions.

==================================================
AUDIT / ACTIVITY
================

Include an activity timeline.

Example:

Order Created

Stock Reserved

Warehouse Assigned

Package Prepared

Shipment Created

Delivered

Show timestamps and responsible user/system where appropriate.

==================================================
CROSS-MODULE CONNECTION
=======================

Maintain the product relationship:

Quotation
→ Approval
→ Fulfillment

Example:

Q-1042 Acme Corp
↓
Discount Approval
↓
Approved
↓
Order Created
↓
Fulfillment

The UI should make this relationship understandable.

==================================================
INTERACTION STATES
==================

For Screens 05–08 include:

Default
Hover
Focus
Selected
Loading
Empty
Error
Success
Confirmation
Disabled

Do not create excessive animations.

==================================================
RESPONSIVE DESIGN
=================

Support:

Desktop
Tablet
Mobile

Desktop:

* full navigation
* tables
* detailed workspace

Tablet:

* compact navigation
* responsive tables

Mobile:

* collapsible navigation
* stacked information cards
* readable tables
* horizontally scroll only when absolutely necessary
* sticky primary action where appropriate

==================================================
ACCESSIBILITY
=============

Ensure:

* sufficient text contrast
* visible focus states
* status communicated through text, not color alone
* readable typography
* logical information hierarchy
* buttons have clear labels

==================================================
STRICT DESIGN PRESERVATION
==========================

IMPORTANT:

Screens 01–04 are already approved.

DO NOT TOUCH THEM.

Reuse their:

* navigation
* typography
* buttons
* inputs
* cards
* badges
* tables
* spacing
* border treatment
* active navigation treatment
* responsive behavior

Screens 05–08 must look like they belong to the SAME PRODUCT.

Do not create a new visual language.

==================================================
FINAL AUDIT
===========

Before finishing, verify:

[ ] 05 Approvals List exists
[ ] Approval filters exist
[ ] Approval table exists
[ ] Exact approval data is present
[ ] Rows are clickable
[ ] 06 Approval Detail exists
[ ] Blended Risk is visible
[ ] Customer Tier is visible
[ ] Why Flagged table exists
[ ] Exact +8 pt variance is visible
[ ] Approval progression exists
[ ] Audit history exists
[ ] Approve action exists
[ ] Return for Revision exists
[ ] Reject exists

[ ] 07 Fulfillment List exists
[ ] Inventory table exists
[ ] Exact inventory values are present
[ ] Available quantity is clear
[ ] Orders Awaiting Fulfillment exists
[ ] Search/filter controls exist
[ ] Rows are clickable

[ ] 08 Fulfillment Detail exists
[ ] Order information exists
[ ] Product allocation exists
[ ] Warehouse allocation exists
[ ] Stock reservation exists
[ ] Fulfillment progression exists
[ ] Fulfillment actions exist
[ ] Activity timeline exists

[ ] Navigation is consistent
[ ] Responsive layouts exist
[ ] Accessibility is considered
[ ] Screens 01–04 remain unchanged

FINAL INSTRUCTION:

This is a STRICT BUILD + FIX task.

Do not redesign.
Do not simplify away required information.
Do not invent unrelated features.
Do not modify Screens 01–04.

ONLY complete Screens 05–08.
