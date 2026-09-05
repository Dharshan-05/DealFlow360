IMPORTANT: ONLY ADD THE MISSING WORKFLOW DETAILS TO THE EXISTING DEALFLOW360 DESIGN.

DO NOT redesign anything.
DO NOT change the existing UI.
DO NOT change existing screens, layouts, colors, typography, navigation, tables, components, labels, data, or existing functionality.
DO NOT remove anything.
DO NOT restructure the current application.

Only add the missing details/states/actions listed below.
If something already exists, KEEP IT AS-IS and do not duplicate it.

==================================================
MISSING DETAILS TO ADD
==================================================

1. QUOTATION DETAIL — Q-1042

Add the missing quotation lifecycle states/actions if they are not already present:

- Draft
- Sent to Customer
- Customer Negotiation
- Customer Accepted
- Customer Requested Changes
- Customer Rejected
- Pending Approval
- Approved
- Approval Rejected
- Ready for Fulfillment

Add only the necessary status/action controls to the existing Quotation Detail screen.

Required actions where applicable:
- Send to Customer
- Edit Quote
- Submit for Approval
- Accept
- Reject
- Request Changes

Do not modify the existing quotation design.


==================================================
2. CUSTOMER NEGOTIATION

On the existing Customer Portal / Negotiation screen, add the missing outcomes:

- Customer Accepts Quote
- Customer Requests Changes
- Customer Rejects Quote

When "Request Changes" is selected, show a simple:
- Change request/comment
- Submit Changes button

When accepted:
Customer Accepted → continue to the existing approval/fulfillment workflow.

When changes are requested:
Customer Requested Changes → return to the existing Quotation Detail.

When rejected:
Customer Rejected → mark the deal/quotation as Lost/Rejected.

Do not redesign the Customer Portal.


==================================================
3. APPROVAL DETAIL — Q-1042

Keep the existing Approval Detail screen exactly as it is.

Only add missing approval outcomes if absent:

- Approve
- Reject
- Request Changes

Add corresponding statuses:

Pending
Approved
Rejected
Changes Requested

If rejected:
Approval Rejected → return to existing Quotation Detail.

If changes requested:
Changes Requested → return to existing Quotation Detail.

If approved:
Approved → continue to existing Fulfillment workflow.

Also show, where space/components already allow:

- Approval reason
- Discount requested
- Approval threshold
- Approver
- Comments
- Approval history

Do not replace the existing approval UI.


==================================================
4. FULFILLMENT & STOCK

Keep the existing Fulfillment & Stock List and Fulfillment Detail designs.

Only add missing stock/fulfillment states:

- Pending
- Stock Check
- Stock Available
- Allocated
- Partially Fulfilled
- Fulfilled
- Insufficient Stock
- Backordered
- Cancelled

If stock is insufficient, show an exception state instead of allowing the workflow to silently proceed.

Show these quantities where appropriate:

- Ordered
- Available
- Allocated
- Backordered

Do not redesign the fulfillment screens.


==================================================
5. SUBSCRIPTION / BILLING

Keep the existing Subscription List and Billing Detail screens.

Only add missing subscription/billing states if absent:

Subscription:
- Pending
- Active
- Suspended
- Cancelled
- Expired

Billing:
- Pending
- Active
- Payment Pending
- Payment Failed
- Paid
- Overdue

Make sure Billing can lead to the existing Invoice workflow.

Do not create a new billing design if an existing screen can contain the state.


==================================================
6. INVOICE DETAIL — INV-1042

Keep the existing Invoice List and Invoice Detail screens.

Only add missing invoice/payment states:

Invoice:
- Draft
- Issued
- Pending Payment
- Paid
- Overdue
- Cancelled

Payment:
- Pending
- Processing
- Successful
- Failed

Add the minimum necessary action/state:

[Pay / Record Payment]

Payment Successful:
→ Invoice becomes Paid
→ Deal can become Completed

Payment Failed:
→ Invoice remains unpaid
→ show Retry Payment

Payment Pending:
→ keep invoice in Pending Payment

Do not redesign the invoice screens.


==================================================
7. PAYMENT RESULT

If a separate Payment screen/state does not currently exist, add ONLY the minimum required payment state/modal/page using the existing visual style.

It must support:

Payment Pending
Payment Successful
Payment Failed

Failed payment must have:

[Retry Payment]

Successful payment must update:

Invoice → Paid
Billing → Paid/Active as appropriate
Deal → Completed

Do not add unnecessary payment functionality.


==================================================
8. DISCOUNT / APPROVAL CONNECTION

Keep the existing:

Product Catalog
Product & Pricelist
Discount Tiers & Approval Chains

Do not modify their existing UI.

Only make the missing logical relationship visible:

Product
→ Price
→ Discount
→ Approval Threshold
→ Approval Required / Not Required
→ Quotation

If discount exceeds the configured approval threshold:

Quotation → Pending Approval

If discount does not require approval:

Quotation → continue to the existing next step.


==================================================
9. DEAL HEALTH & ANOMALY DASHBOARD

Keep the existing Deal Health & Anomaly Dashboard exactly as designed.

Only add missing anomaly types if absent:

- Approval Overdue
- Excessive Discount
- Insufficient Stock
- Fulfillment Delayed
- Payment Failed
- Invoice Overdue
- Subscription Renewal Risk

Each anomaly should point to the already-existing relevant screen.

Examples:

Approval Overdue → Approval Detail
Excessive Discount → Approval Detail
Insufficient Stock → Fulfillment Detail
Payment Failed → Invoice Detail
Invoice Overdue → Invoice Detail

Do not redesign the dashboard.


==================================================
10. ADMIN / REPORTING

Keep the existing Admin / Reporting Dashboard.

Only add missing reporting visibility if absent:

- Pending Approvals
- Rejected Approvals
- Fulfillment Exceptions
- Active Subscriptions
- Pending Payments
- Failed Payments
- Overdue Invoices
- Paid Invoices
- Completed Deals

Do not change the existing dashboard structure.


==================================================
11. CROSS-SCREEN STATUS CONSISTENCY

Do NOT redesign any screen.

Only ensure the existing records reflect the correct status after an action.

For the existing example:

Quotation: Q-1042
Customer: Acme Corp
Invoice: INV-1042

The same deal should remain connected across:

Q-1042
→ Customer Negotiation
→ Approval
→ Fulfillment
→ Subscription/Billing
→ INV-1042
→ Payment
→ Completed

Do not create duplicate records.


==================================================
12. IMPORTANT MISSING EDGE CASES

Add only these missing states if they do not already exist:

- Customer Requests Changes
- Customer Rejects
- Approval Rejects
- Approval Requests Changes
- Approval Overdue
- Insufficient Stock
- Partial Fulfillment
- Backorder
- Invoice Overdue
- Payment Pending
- Payment Failed
- Payment Retry
- Subscription Cancelled
- Deal Lost


==================================================
FINAL INSTRUCTION

THIS IS AN ADDITIVE FIX ONLY.

Preserve 100% of the existing DealFlow360 design and functionality.

DO NOT:
- redesign screens
- change layouts
- change colors
- change navigation
- rename existing screens
- remove components
- remove existing workflow
- replace existing tables
- change existing sample data
- create unnecessary new pages
- alter existing functionality

ONLY add the missing states, actions, edge cases, and workflow connections listed above.

If a requested item already exists, leave it untouched.

The final result should look like the SAME existing DealFlow360 application, but with the missing workflow details completed.