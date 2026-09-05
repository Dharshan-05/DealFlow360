# DealFlow360 — Complete Figma Design Prompt

Design the remaining 15 screens for **DealFlow360**, an enterprise B2B sales, quotation, approval, fulfillment, billing, subscription, risk intelligence, and analytics platform.

## IMPORTANT — EXISTING DESIGN MUST BE PRESERVED

The first 9 modules of DealFlow360 have already been designed in Figma.

Treat the existing Figma design as the **single source of truth** for:

* Visual language
* Typography
* Spacing
* Layout
* Navigation
* Components
* Cards
* Tables
* Buttons
* Inputs
* Badges
* Icons
* Borders
* Radius
* Shadows
* Motion direction
* Information hierarchy

**DO NOT redesign the existing visual identity.**

Create these 15 new screens so they look like they are part of the exact same product.

---

# 1. DESIGN LANGUAGE

DealFlow360 uses a premium enterprise SaaS visual style.

### Primary visual system

* Dominant black and white interface
* Black as the primary background where appropriate
* White as primary text on dark surfaces
* White/light surfaces where appropriate
* Approximately 10% accent color usage
* Accent colors should communicate status and intelligence, not decorate the entire interface
* High contrast
* Clean typography
* Strong hierarchy
* Minimal visual noise
* Premium enterprise appearance
* Dense but readable information layouts
* Subtle borders
* Restrained shadows
* Consistent spacing
* Consistent corner radius

The design should feel inspired by modern products such as Attio, Linear, Stripe, and high-end enterprise SaaS products, while remaining distinctly **DealFlow360**.

Do not copy any competitor branding.

---

# 2. GLOBAL APPLICATION STRUCTURE

For internal-user screens, maintain the existing DealFlow360 application shell.

### Left Sidebar

Use the existing sidebar structure and component style.

Navigation:

* Dashboard
* Quotations
* Approvals
* Fulfillment
* Subscriptions
* Invoices
* Deal Health
* Reports
* Products

The currently active module must have the existing white-highlight/active treatment from the current Figma design.

### Top Navigation

Maintain the existing:

* Breadcrumb
* Page title
* Page description
* Search where appropriate
* Notifications
* User profile
* Context/company selector where appropriate

### General interaction model

Every entity should follow:

**List → click row → Detail**

Examples:

Quotations List → Quotation Detail

Approvals List → Approval Detail

Fulfillment List → Fulfillment Detail

Subscriptions List → Subscription Detail

Invoices List → Invoice Detail

---

# 3. SCREEN 01 — LOGIN / SIGNUP

Frame name:

**1. Login / Signup**

Create a premium authentication experience.

### Layout

Use a clean split or centered authentication layout consistent with the existing DealFlow360 visual language.

Include:

* DealFlow360 logo
* Short product statement
* Log In / Sign Up tabs
* Email field
* Password field
* Password visibility control
* Forgot Password?
* Primary Log In button
* Sign Up link
* Company/team selector for multi-team environments
* Validation messages
* Loading state
* Error state

### Login behavior concept

After login:

* Internal users → Sales Dashboard
* Customers → Customer Portal

Include subtle supporting text explaining this behavior.

Keep the screen minimal and premium.

---

# 4. SCREEN 02 — SALES DASHBOARD

Frame name:

**2. Sales Dashboard**

This is the central internal-user hub.

### Header

Title:

**Sales Dashboard**

Subtitle:

**Central hub for quotations, approvals, fulfillment, subscriptions, invoices and deal health.**

### KPI cards

Create premium KPI cards for:

* Pending Approvals — 4
* Open Quotations — 12
* At-Risk Deals — 3
* Revenue
* Deal Value
* Conversion
* Margin
* Fulfillment

Use the existing KPI/card system.

### Primary actions

* * New Quotation
* View Approvals

### Recent Activity

Show activity such as:

* Acme Corp quotation approved by Finance
* Beta Industries requested a discount change
* East Depot stock updated for Order #2291

### Additional widgets

Include:

* Recent Quotations
* Pending Approvals
* Risk Alerts
* Inventory Alerts
* Deal Health
* Revenue Trend

Keep the dashboard information-dense but organized.

---

# 5. SCREEN 03 — QUOTATIONS LIST

Frame name:

**3. Quotations List**

### Header

Title:

**Quotations**

Subtitle:

**Every quotation in the system. Click a row to open the quotation.**

### Actions

* * New Quotation
* Search
* Filter
* Sort
* Switch to Table View

### Status pipeline

Display quotation states:

* Draft
* Pending Approval
* Approved
* Negotiation
* Confirmed

Example records:

Draft:

* Acme Corp — $12,400
* Delta LLC — $3,200

Pending Approval:

* Beta Industries — $28,900

Approved:

* Nova Retail — $9,750

Negotiation:

* Zenith Co — $15,300

Confirmed:

* Orion Ltd — $41,000

### Table information

Include:

* Quote ID
* Customer
* Value
* Status
* Discount
* Margin
* Risk
* Owner
* Updated
* Actions

Rows must clearly look clickable.

---

# 6. SCREEN 04 — QUOTATION DETAIL

Frame name:

**4. Quotation Detail**

Title:

**Quotation Detail: Q-1042**

Customer:

**Acme Corp**

Subtitle:

**Add products, apply discounts, review upsells and submit for approval.**

### Header actions

* Save Draft
* Submit for Approval
* More

### Quote information

Fields:

* Customer
* Price List
* Quote Status
* Owner
* Created Date
* Expiry Date

### Line items table

Columns:

* Product
* Qty
* Price
* Discount
* Limit
* Margin
* Status
* Actions

Example:

Laptop Pro 14

* Qty: 2
* Price: $1,200
* Discount: 12%
* Limit: 15%
* Status: OK

Onsite Setup Service

* Qty: 1
* Price: $450
* Discount: 18%
* Limit: 10%
* Status: OVER +8pt

Extended Warranty

* Qty: 1
* Price: $180
* Discount: 10%
* Limit: 15%
* Status: OK

### Important UX

Discount validation must appear **live while entering the discount**.

Show:

* Requested Discount
* Allowed Discount
* Difference
* Margin Impact
* Risk

### Upsell / Cross-sell section

Create recommendation cards:

* Wireless Mouse — Margin +$18
* Docking Station — Promo: 12% off
* Care Plan 2yr — Margin +$46

Each recommendation should have:

* Product
* Reason
* Margin impact
* Confidence
* Add button

### Summary

Show:

* Subtotal
* Total Discount
* Tax
* Cost
* Margin
* Grand Total
* Risk Status
* Approval Status

---

# 7. SCREEN 05 — APPROVALS LIST

Frame name:

**5. Approvals List**

Title:

**Approvals**

Subtitle:

**Every quotation requiring or going through discount approval.**

### Filter badges

* 3 Pending
* 1 Returned
* 12 Approved

### Table

Columns:

* Quotation
* Customer
* Blended Risk
* Stage
* Requested Discount
* Margin
* Assigned To
* Updated

Example:

Q-1042 — Acme Corp — HIGH — Sales Manager — M. Shah

Q-1039 — Beta Industries — MEDIUM — Finance — R. Iyer

Q-1035 — Nova Retail — LOW — Auto-Approved

### Actions

* Search
* Filter
* Sort
* Pending Only

Rows must open Approval Detail.

---

# 8. SCREEN 06 — APPROVAL DETAIL

Frame name:

**6. Approval Detail**

Title:

**Approval Detail: Q-1042**

Customer:

**Acme Corp**

### Status

Show:

* Blended Risk: HIGH
* Customer Tier: Gold
* Approval Required

### Why this quote was flagged

Table:

| Line            | Discount | Limit |    Over By |
| --------------- | -------: | ----: | ---------: |
| Laptop Hardware |      12% |   15% |  0 pt — OK |
| Setup Service   |      18% |   10% | +8 pt OVER |

### Explanation

Clearly explain:

The worst single line combined with the overall order pattern determines the blended approval risk.

### Approval progression

Create a visual progression:

**Submitted → Sales Manager → Finance → Confirmed**

Clearly highlight the current stage.

### AI Risk explanation

Include:

* Risk Score
* Risk Classification
* Risk Factors
* AI Explanation
* Recommended Action

### Audit Trail

Timeline/table:

* J. Rao — Submitted — Aug 20 — Initial 12% discount
* M. Shah — Returned — Aug 21 — Requested justification
* J. Rao — Resubmitted — Aug 22 — Added margin note

### Actions

* Approve
* Return for Revision
* Reject

Make destructive actions visually clear.

---

# 9. SCREEN 07 — FULFILLMENT LIST

Frame name:

**7. Fulfillment List**

Title:

**Fulfillment & Stock**

Subtitle:

**Live stock by warehouse and orders awaiting fulfillment.**

### Inventory table

Columns:

* Warehouse
* Product
* In Stock
* Reserved
* Available
* ATP
* Status

Example:

Main Warehouse — Laptop Pro 14 — 40 — 18 — 22

East Depot — Laptop Pro 14 — 10 — 6 — 4

Main Warehouse — Docking Station — 65 — 12 — 53

### Orders awaiting fulfillment

Columns:

* Order
* Customer
* Status
* Warehouses
* Items
* Delivery
* Risk

Include stock alerts and fulfillment status.

---

# 10. SCREEN 08 — FULFILLMENT DETAIL

Frame name:

**8. Fulfillment Detail**

Create a detailed fulfillment workspace.

### Header

Show:

* Order ID
* Customer
* Order Status
* Fulfillment Status
* Delivery Status

### Order summary

Display:

* Products
* Quantities
* Required Date
* Customer
* Delivery Address
* Priority

### Warehouse allocation

Create a clear allocation visualization.

Example:

Laptop Pro 14 — Qty 20

Main Warehouse:

* Available: 22
* Allocate: 18

East Depot:

* Available: 4
* Allocate: 2

Total allocated: 20

### Actions

* Auto Allocate
* Manual Override
* Reserve Stock
* Create Delivery
* Split Fulfillment
* Create Backorder

### Timeline

Show:

Order Confirmed
→ Stock Reserved
→ Warehouse Allocated
→ Delivery Created
→ Shipped
→ Delivered

Include warnings for:

* Insufficient stock
* Warehouse delay
* Partial fulfillment
* Backorder

---

# 11. SCREEN 09 — SUBSCRIPTIONS LIST

Frame name:

**9. Subscriptions List**

Title:

**Subscriptions**

Subtitle:

**Manage recurring customer subscriptions and billing cycles.**

### KPI cards

* Active Subscriptions
* Monthly Recurring Revenue
* Upcoming Renewals
* Failed Payments

### Table

Columns:

* Subscription
* Customer
* Plan
* Status
* Billing Cycle
* Amount
* Next Billing
* Renewal
* Actions

Statuses:

* Active
* Trial
* Past Due
* Cancelled
* Paused

Include:

* Search
* Filter
* Sort
* Create Subscription

---

# 12. SCREEN 10 — SUBSCRIPTION DETAIL

Frame name:

**10. Subscription Detail**

Create a complete subscription management screen.

### Header

Show:

* Subscription ID
* Customer
* Plan
* Status
* Monthly/Annual value

### Subscription information

* Billing Cycle
* Next Billing Date
* Start Date
* Renewal Date
* Payment Method
* Amount

### Products

Show subscribed products/services.

### Actions

* Upgrade
* Downgrade
* Modify
* Pause
* Cancel
* Renew

### Billing

Show:

* Current Amount
* Proration
* Next Invoice
* Payment Status

### Timeline

Show:

Created
→ Activated
→ Modified
→ Renewed
→ Upcoming Billing

Include confirmation dialogs for cancellation and financial actions.

---

# 13. SCREEN 11 — CUSTOMER PORTAL

Frame name:

**11. Customer Portal**

This is a customer-facing experience and should be visually simpler than the internal application.

### Navigation

* My Quotations
* Messages
* Orders
* Invoices
* Subscriptions
* Profile

### Customer dashboard

Show:

* Active Quotations
* Pending Negotiations
* Orders
* Outstanding Invoices
* Subscription Status

### My Quotation

Customer can:

* Open quote
* Review products
* View pricing
* Request discount change
* Request delivery change
* Accept
* Reject
* Send message

### Negotiation workspace

Include:

* Quote summary
* Current discount
* Counter discount input
* Customer message
* Sales response
* Negotiation status
* Timeline

### Messages

Create a clean conversation interface.

### Profile

Include:

* Customer information
* Company
* Contact details
* Billing information

Ensure this screen feels like a professional customer portal rather than an internal admin dashboard.

---

# 14. SCREEN 12 — INVOICES LIST

Frame name:

**12. Invoices List**

Title:

**Invoices**

Subtitle:

**Track invoices, payments and billing status.**

### KPI cards

* Total Invoiced
* Paid
* Outstanding
* Overdue

### Table

Columns:

* Invoice
* Customer
* Amount
* Status
* Payment Status
* Due Date
* Created
* Actions

Statuses:

* Draft
* Sent
* Paid
* Partially Paid
* Overdue
* Cancelled

Include:

* Search
* Filter
* Sort
* Date Range
* Export

Clicking a row opens Invoice Detail.

---

# 15. SCREEN 13 — INVOICE DETAIL

Frame name:

**13. Invoice Detail**

Create a professional invoice detail workspace.

### Header

Show:

* Invoice Number
* Customer
* Invoice Status
* Payment Status
* Due Date

### Invoice document section

Include:

* Company information
* Customer information
* Invoice date
* Due date
* Line items
* Quantity
* Unit price
* Discount
* Tax
* Subtotal
* Total

### Payment section

Show:

* Amount Due
* Amount Paid
* Remaining
* Payment Method
* Payment Timeline

### Actions

* Download Invoice
* Send Invoice
* Record Payment
* Retry Payment
* Refund
* View Audit

### Payment timeline

Created
→ Sent
→ Payment Attempt
→ Paid / Failed
→ Reconciled

Use clear financial-status indicators.

---

# 16. SCREEN 14 — DEAL HEALTH

Frame name:

**14. Deal Health**

Create an intelligence-focused command center.

### Header

Title:

**Deal Health**

Subtitle:

**Monitor deal risk, conversion probability, anomalies and recommended actions.**

### Health score

Large central score:

**78 / 100 — Healthy**

Support states:

* Healthy
* Warning
* Critical

### Metrics

Display:

* Conversion Probability
* Stall Probability
* Delay Probability
* Discount Anomaly
* Deal Value Anomaly
* Approval Bottleneck
* Fulfillment Delay
* Negotiation Risk

### Risk visualization

Include:

* Risk trend
* Health history
* Risk timeline
* Anomaly feed

### AI recommendation

Create an AI recommendation panel:

**Recommended Next Action**

Example:

“Follow up with Acme Corp because the deal has been inactive for 5 days and the approval stage is approaching its SLA.”

Show:

* Recommendation
* Reason
* Confidence
* Suggested action

### Actions

* Follow Up
* Escalate
* Review Quote
* Open Approval
* Open Customer

---

# 17. SCREEN 15 — REPORTS

Frame name:

**15. Reports**

Create an executive analytics and reporting workspace.

### Header

Title:

**Reports**

Subtitle:

**Business intelligence across sales, revenue, margin, risk and operations.**

### KPI section

Include:

* Revenue
* Margin
* Discount
* Conversion
* Approval Rate
* Upsell Revenue
* Fulfillment Performance
* Risk Exposure

### Charts

Create premium enterprise charts for:

* Revenue Trend
* Deal Trend
* Margin Trend
* Discount Trend
* Conversion Trend
* Approval Trend
* Fulfillment Trend
* Subscription Revenue

### Filters

* Date Range
* Customer
* Product
* Warehouse
* Sales Representative
* Status

### Report actions

* Create Report
* Save Report
* Export
* Download

### Saved Reports

Display reusable reports with:

* Report Name
* Owner
* Last Updated
* Date Range
* Actions

---

# 18. RESPONSIVE DESIGN

Every screen must be designed for:

### Desktop

Primary design target.

### Tablet

Adapt:

* Sidebar
* Tables
* Cards
* Charts
* Detail panels

### Mobile

Use responsive transformations:

* Collapsible navigation
* Stacked cards
* Horizontally scrollable tables where necessary
* Bottom actions where appropriate
* Full-width forms
* Collapsible sections

Do not simply shrink the desktop design.

---

# 19. COMPONENT REUSE

Reuse existing DealFlow360 components wherever possible.

Do not create separate versions of the same component.

Reuse:

* Buttons
* Inputs
* Tables
* Cards
* Badges
* Tabs
* Dropdowns
* Drawers
* Dialogs
* Tooltips
* Toasts
* Stat cards
* Metric cards
* Charts
* Timelines
* Activity feeds
* Status indicators

Maintain consistent component behavior across every screen.

---

# 20. STATUS SYSTEM

Use restrained accent colors only when communicating state.

Examples:

* Success → approved / paid / healthy
* Warning → approaching limit / pending / delayed
* Critical → high risk / overdue / blocked
* Neutral → draft / inactive
* AI → subtle dedicated accent treatment

Never turn the entire UI into a colorful dashboard.

---

# 21. AI UX

AI features must feel integrated into the business workflow.

Use AI panels for:

* Risk explanation
* Discount recommendation
* Upsell recommendation
* Deal health
* Approval explanation
* Negotiation summary

Each AI result should show:

* Recommendation
* Explanation
* Confidence where applicable
* Relevant business context
* Suggested action

Avoid unnecessary futuristic graphics.

AI should feel like a powerful enterprise assistant, not a chatbot demo.

---

# 22. DATA UX

Tables should support:

* Search
* Filtering
* Sorting
* Pagination
* Row actions
* Status badges
* Empty states
* Loading states
* Error states

Detail pages should use:

* Clear hierarchy
* Sticky important actions where useful
* Summary cards
* Tabs/sections
* Activity timelines
* Audit information

---

# 23. INTERACTION STATES

For important components create appropriate states:

* Default
* Hover
* Active
* Focus
* Disabled
* Loading
* Success
* Warning
* Error
* Empty

Financial and destructive actions should require confirmation.

---

# 24. ACCESSIBILITY

Ensure:

* Strong contrast
* Keyboard navigation
* Visible focus states
* Proper labels
* Clear validation messages
* Accessible buttons
* Accessible tables
* Non-color-only status communication

---

# 25. FINAL FLOW

The completed Figma design must communicate this complete business journey:

**Login / Signup**

↓

**Sales Dashboard**

↓

**Quotations List**

↓

**Quotation Detail**

↓

**Discount Validation + AI Upsell + Risk**

↓

**Approvals List**

↓

**Approval Detail**

↓

**Fulfillment List**

↓

**Fulfillment Detail**

↓

**Subscriptions List**

↓

**Subscription Detail**

↓

**Customer Portal / Negotiation**

↓

**Invoices List**

↓

**Invoice Detail**

↓

**Deal Health**

↓

**Reports**

The complete experience should feel like **one connected enterprise platform**, not 15 unrelated screens.

## FINAL REQUIREMENT

Do not redesign existing DealFlow360 screens.

Extend the current Figma design system.

Maintain the existing black/white visual identity with restrained accent color.

Maintain consistent navigation, typography, spacing, components, status patterns and information hierarchy.

The final result should look like a polished, production-ready enterprise SaaS application suitable for a serious hackathon demonstration and real-world B2B sales operations.
