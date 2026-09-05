STRICT IMPLEMENTATION TASK — COMPLETE SCREENS 01–04 ONLY.

You are working inside an existing DealFlow360 Figma design.

IMPORTANT:
Do NOT redesign the existing visual identity.
Do NOT randomly change colors, typography, spacing, navigation, components, or layout patterns that already exist.
Use the existing Figma design as the PRIMARY DESIGN SYSTEM.

GOAL:
Complete and polish these four connected screens:

01 → Login / Signup
02 → Sales Dashboard
03 → Quotations List
04 → Quotation Detail

==================================================
GLOBAL DESIGN RULES
===================

DealFlow360 is a premium enterprise B2B SaaS application.

Visual direction:

* Black and white are the primary foundation.
* Black backgrounds with white typography where appropriate.
* White surfaces with black typography where appropriate.
* Use accent color very selectively, approximately 10% of the interface.
* Premium, minimal, modern enterprise SaaS aesthetic.
* High information density without visual clutter.
* Strong hierarchy.
* Clean grids.
* Consistent spacing.
* Subtle borders.
* Restrained shadows.
* Professional data tables.
* No unnecessary gradients.
* No excessive rounded cards.
* No decorative elements that reduce usability.

Use the existing navigation/sidebar/header system.
The active module must use the existing white-highlight treatment.

Maintain:

* Existing typography
* Existing buttons
* Existing inputs
* Existing cards
* Existing table style
* Existing status badges
* Existing modal/drawer style
* Existing spacing system
* Existing responsive behavior

Reuse components instead of creating visually different duplicates.

==================================================
01 — LOGIN / SIGNUP
===================

Create a polished authentication entry screen.

Include:

* DealFlow360 branding
* Log In / Sign Up tabs
* Email field
* Password field
* Show/hide password
* Remember me
* Forgot Password
* Primary Log In button
* Sign Up flow
* Basic validation states
* Error state
* Loading state
* Success state

For Sign Up include:

* Name
* Email
* Password
* Confirm Password
* Account type:
  Internal User / Customer
* Company/team selector where applicable
* Create Account button

Authentication behavior concept:

Internal user → Sales Dashboard

Customer → Customer Portal

Keep the screen visually consistent with the rest of DealFlow360.

==================================================
02 — SALES DASHBOARD
====================

Create the central sales operations dashboard.

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

Dashboard must be active.

Header:
Sales Dashboard
Home

Include KPI cards:

Pending Approvals
4

Open Quotations
12

At-Risk Deals
3

Include primary actions:

* New Quotation
  View Approvals

Include Recent Activity:

Acme Corp quotation approved by Finance

Beta Industries requested discount change

East Depot stock updated for Order #2291

Also include useful enterprise dashboard sections:

* quotation pipeline summary
* approval status
* fulfillment status
* deal risk overview
* recent activity

Do not overload the page.

==================================================
03 — QUOTATIONS LIST
====================

Create the quotation management list.

Header:
Quotations

Subtitle:
Every quotation, one row per quote. Click a row to open.

Actions:

* New Quotation
  Switch to Table View

Show quotation pipeline/status sections:

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

Also provide a professional table view containing:

Quotation ID
Customer
Amount
Stage
Risk
Owner
Last Updated
Status
Actions

Every row must be clickable.

Use realistic enterprise SaaS empty/loading/error states.

==================================================
04 — QUOTATION DETAIL
=====================

Create the detailed quotation workspace.

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

Line-item table:

Product | Qty | Price | Discount | Limit | Status

Laptop Pro 14
2
$1,200
12%
15%
OK

Onsite Setup Service
1
$450
18%
10%
OVER (+8pt)

Extended Warranty
1
$180
10%
15%
OK

CRITICAL BUSINESS RULE:

Discount must be checked LIVE against each individual line item's own discount limit.

Do NOT only validate on form submission.

If discount exceeds limit:

* visually highlight the affected row
* show clear OVER status
* show exact variance
* show contextual warning
* preserve the rest of the quotation

Add banner:

"Discount checked live against each line's own limit."

==================================================
UPSELL / CROSS-SELL
===================

Include a recommendation section:

Wireless Mouse
Margin +$18

Docking Station
Promo 12% off

Care Plan 2yr
Margin +$46

Recommendations should feel AI-assisted but remain professional and actionable.

Actions:

Save Draft
Submit for Approval

Include:

* success state
* validation state
* unsaved changes state
* approval-required state

==================================================
INTERACTION / NAVIGATION
========================

Connect the screens conceptually:

Login
↓
Sales Dashboard
↓
Quotations List
↓
Quotation Detail

Clicking a quotation row opens Quotation Detail.

Clicking Dashboard returns to Sales Dashboard.

Clicking Quotations opens Quotations List.

Maintain the same shell across authenticated screens.

==================================================
RESPONSIVE DESIGN
=================

Design for:

* Desktop
* Tablet
* Mobile

On mobile:

* collapse navigation
* convert tables into readable cards/stacked rows
* preserve primary actions
* maintain hierarchy
* avoid horizontal overflow where possible

==================================================
FINAL QUALITY CHECK
===================

Before finishing:

1. Verify all four screens exist.
2. Verify navigation consistency.
3. Verify typography consistency.
4. Verify spacing consistency.
5. Verify black/white visual foundation.
6. Keep accent color restrained.
7. Verify quotation data exactly.
8. Verify live discount-limit visualization.
9. Verify quotation list → detail flow.
10. Do not redesign existing DealFlow360 components unnecessarily.

This is an implementation/completion task, NOT a creative redesign task.
