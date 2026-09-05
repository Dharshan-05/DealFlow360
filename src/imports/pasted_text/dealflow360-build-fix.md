STRICT BUILD + FIX TASK — SCREENS 09–13 ONLY.

IMPORTANT:
Screens 01–08 are APPROVED and FROZEN.

DO NOT:

* modify Screens 01–08
* redesign Screens 01–08
* overwrite existing components
* duplicate existing components unnecessarily
* change the established DealFlow360 design system
* change existing navigation, typography, spacing, colors, buttons, cards, tables, badges, or interaction patterns

INHERIT the exact design language from Screens 01–08.

Build and complete ONLY:

09 → Subscriptions List
10 → Subscription Detail
11 → Customer Portal
12 → Invoices List
13 → Invoice Detail

==================================================
GLOBAL DESIGN DIRECTION
=======================

DealFlow360 is a premium enterprise B2B SaaS platform.

Maintain the established visual system:

* Black + white as the primary foundation
* Restrained accent color, approximately 10%
* Premium enterprise appearance
* Minimal and clean
* Strong information hierarchy
* High-density but readable data
* Professional tables
* Consistent cards
* Consistent status badges
* Subtle borders
* Minimal shadows
* No unnecessary gradients
* No excessive glassmorphism
* No random colors
* No unrelated visual styles

Reuse existing components from Screens 01–08.

==================================================
09 — SUBSCRIPTIONS LIST
=======================

Create the Subscriptions List using the existing application shell.

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

Subscriptions must be ACTIVE using the existing active-navigation treatment.

Page header:

Subscriptions

Create a professional subscription management table.

Columns:

Subscription
Customer
Plan
Amount
Billing Cycle
Status
Next Billing
Owner

Use realistic example data:

SUB-2041
Acme Corp
Enterprise
$2,400
Monthly
Active
Sep 30

SUB-2037
Nova Retail
Growth
$950
Monthly
Active
Oct 02

SUB-2029
Beta Industries
Enterprise
$4,800
Annual
At Risk
Oct 15

==================================================
SUBSCRIPTION STATUS
===================

Support:

Active
Trial
Paused
Cancelled
Past Due
At Risk

Status must be understandable without relying only on color.

Include:

* status badge
* search
* status filter
* customer filter
* billing-cycle filter
* date filter
* * New Subscription

Every subscription row must be clickable.

Click row:

Subscriptions List
→ Subscription Detail

==================================================
10 — SUBSCRIPTION DETAIL
========================

Create a detailed subscription workspace.

Header:

SUB-2041
Acme Corp

Show summary information:

Plan
Enterprise

Status
Active

MRR
$2,400

Billing Cycle
Monthly

Next Billing
Sep 30

Create a clear subscription overview.

==================================================
SUBSCRIPTION DETAILS
====================

Include sections:

Plan Details

Products / Services

Billing Information

Payment Method

Usage

Invoices

Activity

Keep sections visually organized without excessive cards.

==================================================
SUBSCRIPTION LIFECYCLE
======================

Show:

Trial
↓
Active
↓
Renewed
↓
Paused
↓
Cancelled

Do not imply every subscription must pass through every state.

Clearly identify:

* current status
* previous status
* next possible action

==================================================
SUBSCRIPTION ACTIONS
====================

Include:

Edit Subscription
Pause
Cancel
Change Plan

Use appropriate confirmation UI for destructive actions.

Pause:
→ confirmation

Cancel:
→ confirmation + cancellation reason

Change Plan:
→ plan selection/change interface

==================================================
11 — CUSTOMER PORTAL
====================

Create the customer-facing portal.

IMPORTANT:

This is NOT an internal admin screen.

The portal must use the same DealFlow360 visual language but provide a simpler customer-focused experience.

Customer portal navigation:

My Quotation
Messages
Profile

Do not expose internal-only:

* approval controls
* internal risk information
* internal audit data
* internal pricing governance
* warehouse controls
* security administration

==================================================
MY QUOTATION
============

Show:

Quotation ID
Q-1042

Customer:
Acme Corp

Quotation status:

Draft
Under Review
Negotiation
Approved
Confirmed

Show quotation line items:

Product
Quantity
Price
Discount
Total

Provide:

Accept

Request Changes

Send Message

Actions must be clearly visible.

==================================================
CUSTOMER MESSAGING
==================

Create a Messages interface.

Show conversation:

Customer
↔
Sales Team

Include:

* message history
* sender
* timestamp
* unread state
* message composer
* send action
* attachment indicator

Keep the messaging interface simple and professional.

==================================================
CUSTOMER PROFILE
================

Create:

Company Name
Contact Name
Email
Phone
Billing Information

Allow:

Edit Profile

Save Changes

Use existing input components.

==================================================
CUSTOMER PORTAL PERMISSIONS
===========================

The customer must only see customer-relevant information.

Customer should be able to:

View quotation
Review quotation
Accept quotation
Request changes
Send messages
View profile

Do NOT expose:

Internal risk scores
Internal approval notes
Internal audit history
Internal discount limits
Internal warehouse data

==================================================
12 — INVOICES LIST
==================

Create the Invoices List.

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

Invoices must be ACTIVE.

Header:

Invoices

Create a professional invoice table.

Columns:

Invoice
Customer
Amount
Issue Date
Due Date
Status

Use:

INV-3012
Acme Corp
$2,400
Sep 01
Sep 30
Pending

INV-3008
Nova Retail
$950
Aug 28
Sep 28
Paid

INV-3001
Beta Industries
$4,800
Aug 15
Sep 15
Overdue

==================================================
INVOICE STATUS
==============

Support:

Draft
Pending
Paid
Overdue
Cancelled

Do not communicate status using color alone.

Include:

* search
* status filter
* customer filter
* date filter
* export action

Every invoice row must open:

Invoices List
→ Invoice Detail

==================================================
13 — INVOICE DETAIL
===================

Create a detailed invoice workspace.

Header:

INV-3012
Acme Corp

Show:

Invoice Status
Pending

Issue Date
Sep 01

Due Date
Sep 30

==================================================
BILLING DETAILS
===============

Show:

Bill To

Customer information

Billing address

Payment terms

Invoice reference

==================================================
LINE ITEMS
==========

Create:

Product / Service
Qty
Unit Price
Discount
Tax
Total

Use clean financial formatting.

==================================================
FINANCIAL SUMMARY
=================

Show:

Subtotal

Discount

Tax

Total

The final total must be visually prominent.

==================================================
PAYMENT INFORMATION
===================

Show:

Payment Status

Payment Method

Transaction Reference

Payment Date when applicable

==================================================
INVOICE ACTIONS
===============

Include:

Download Invoice

Send Invoice

Record Payment

Use appropriate confirmation states.

For:

Pending:
show payment action.

Paid:
show successful payment state.

Overdue:
show clear overdue state and payment action.

Cancelled:
disable inappropriate payment actions.

==================================================
INVOICE ACTIVITY
================

Create a timeline:

Invoice Created

Invoice Sent

Payment Reminder

Payment Received

Show only relevant events for the current invoice.

Include:

* timestamp
* event
* actor/system

==================================================
CROSS-MODULE CONNECTION
=======================

Maintain the business relationship:

Quotation
↓
Approval
↓
Fulfillment
↓
Subscription
↓
Invoice
↓
Payment

Where relevant, show references between entities.

For example:

Invoice INV-3012
Related Subscription: SUB-2041
Related Customer: Acme Corp

Do not create unnecessary navigation complexity.

==================================================
INTERACTION STATES
==================

For Screens 09–13 include appropriate:

Default
Hover
Focus
Selected
Loading
Empty
Error
Success
Disabled
Confirmation

Do not add unnecessary animations.

==================================================
RESPONSIVE DESIGN
=================

Support:

Desktop
Tablet
Mobile

Desktop:

* full application navigation
* tables
* detailed workspaces

Tablet:

* compact layout
* responsive tables

Mobile:

* collapsible navigation
* stacked summary cards
* readable list rows
* usable filters
* customer portal optimized for mobile
* invoice details remain readable
* primary actions remain accessible

Avoid broken horizontal layouts.

==================================================
ACCESSIBILITY
=============

Ensure:

* strong contrast
* visible focus states
* readable typography
* status communicated with text
* clear button labels
* logical heading hierarchy
* keyboard-friendly controls

==================================================
DESIGN CONSISTENCY
==================

Screens 09–13 must visually belong to the SAME DealFlow360 product as Screens 01–08.

Reuse:

* existing navigation
* existing active-tab treatment
* existing typography
* existing buttons
* existing inputs
* existing tables
* existing cards
* existing badges
* existing modal/dialog patterns
* existing spacing
* existing responsive behavior

Do NOT introduce a new visual language.

==================================================
FINAL STRICT AUDIT
==================

Before finishing, verify:

[ ] 09 Subscriptions List exists
[ ] Subscription table exists
[ ] Exact example data exists
[ ] Subscription filters exist
[ ] Subscription statuses exist
[ ] Subscription rows are clickable

[ ] 10 Subscription Detail exists
[ ] Plan information exists
[ ] MRR exists
[ ] Billing cycle exists
[ ] Next billing exists
[ ] Subscription lifecycle exists
[ ] Subscription actions exist
[ ] Confirmation states exist

[ ] 11 Customer Portal exists
[ ] My Quotation exists
[ ] Messages exists
[ ] Profile exists
[ ] Accept action exists
[ ] Request Changes exists
[ ] Send Message exists
[ ] Customer permissions are respected
[ ] Internal-only information is hidden

[ ] 12 Invoices List exists
[ ] Invoice table exists
[ ] Exact invoice example data exists
[ ] Invoice filters exist
[ ] Invoice statuses exist
[ ] Invoice rows are clickable

[ ] 13 Invoice Detail exists
[ ] Invoice status exists
[ ] Billing information exists
[ ] Line items exist
[ ] Financial summary exists
[ ] Payment information exists
[ ] Download Invoice exists
[ ] Send Invoice exists
[ ] Record Payment exists
[ ] Invoice activity exists

[ ] Navigation is consistent
[ ] Responsive layouts exist
[ ] Accessibility is considered
[ ] Screens 01–08 remain completely unchanged
[ ] No duplicate components were unnecessarily created

FINAL INSTRUCTION:

This is a STRICT BUILD + FIX task.

Do not redesign existing approved screens.

Do not modify Screens 01–08.

Do not create unrelated features.

Do not simplify away required business information.

ONLY complete Screens 09–13.
