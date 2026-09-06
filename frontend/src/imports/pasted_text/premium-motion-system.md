## MODULE 2 — PREMIUM MOTION SYSTEM & INTERACTIVE ANIMATIONS

Continue from the existing DealFlow360 implementation.

DO NOT redesign the existing UI.

DO NOT change the existing black/white visual identity, layouts, navigation structure, pages, components, or business logic.

The goal of this module is to implement a complete, reusable, production-quality animation system across the existing application.

### REQUIRED STACK

Use only the existing project stack:

* Next.js 15
* React 19
* TypeScript
* Tailwind CSS
* shadcn/ui
* Radix UI
* Lucide React
* Framer Motion
* Recharts
* TanStack Query
* Zustand
* React Hook Form
* Zod

Use Framer Motion for application animations.

Use Recharts native animation capabilities for charts.

Do not introduce another animation library.

---

# 1. CREATE A GLOBAL MOTION SYSTEM

Create a centralized motion configuration.

Define reusable:

* durations
* easing curves
* spring configurations
* page transitions
* fade animations
* slide animations
* stagger animations
* hover animations
* tap animations

Recommended motion behavior:

FAST:
120–180ms

NORMAL:
200–300ms

COMPLEX:
300–500ms

Animations must feel fast and responsive.

Never make normal UI interactions feel slow.

---

# 2. CREATE REUSABLE ANIMATION COMPONENTS

Create reusable components/utilities instead of duplicating animation code throughout every page.

Create:

### FadeIn

Simple opacity entrance.

### SlideUp

Opacity + translateY entrance.

### SlideIn

Opacity + horizontal translation.

### StaggerContainer

Controls staggered children.

### StaggerItem

Individual animated child.

### PageTransition

Used when changing between major application pages.

### RevealOnScroll

Animation triggered when the element enters the viewport.

### AnimatedNumber

Smoothly animate numerical values.

Example:

100 → 250 → 500 → 1,000

### HoverCard

Subtle card hover movement.

### Pressable

Small scale-down interaction when clicking buttons.

### AnimatedPresence

Handle mounting/unmounting elements smoothly.

### TypingIndicator

Three-dot animated AI typing indicator.

### SkeletonLoader

Premium loading skeleton animation.

All components must be strongly typed with TypeScript.

---

# 3. APPLICATION PAGE TRANSITIONS

Implement smooth transitions between:

Command Center
Products
Quote Workspace
Approvals
Risk Center
Customers
Deals
Billing
Analytics
AI Copilot

Use:

opacity
+
small translateY

Example behavior:

Old page:
opacity 1 → 0

New page:
opacity 0 → 1

Keep the movement extremely subtle.

Do not use dramatic page transitions.

---

# 4. SIDEBAR ANIMATION

Improve the existing collapsible sidebar.

Expanded:

* smooth width transition
* labels fade/slide into view
* icons remain stable

Collapsed:

* labels disappear smoothly
* icons remain centered
* active indicator remains visible

Navigation active state:

The active indicator should smoothly move from one navigation item to another.

Use Framer Motion layout/layoutId where appropriate.

---

# 5. TOPBAR ANIMATIONS

Animate:

* Breadcrumb changes
* Notification dropdown
* User menu
* Search interface
* Command menu if available

Dropdown behavior:

opacity
+
translateY(-4px → 0)

Keep it subtle.

---

# 6. COMMAND CENTER

Animate the dashboard when it loads.

### KPI CARDS

Cards appear sequentially.

Example:

Card 1 → Card 2 → Card 3 → Card 4

Use stagger.

### KPI NUMBERS

Use AnimatedNumber.

Example:

Revenue:

$0 → $10K → $25K → $50K

Do not instantly display the final number.

### REVENUE CHART

Use Recharts animation.

The chart should progressively appear when entering the viewport.

### AI ACTION QUEUE

Each AI action should appear sequentially.

Use:

opacity
+
translateX

### DEAL TABLE

Rows should gently fade in.

Hovering a row should create a subtle background transition.

Do not move the entire table row dramatically.

---

# 7. PRODUCTS

Implement:

### Product Grid

Cards appear using stagger animation.

### Product Hover

On hover:

* subtle translateY
* slight scale
* border/background transition

Keep movement extremely small.

### Add To Quote

When clicking:

* button changes state
* loading indicator
* success state
* cart/quote count updates smoothly

### Grid/List Toggle

Animate the layout between grid and list using Framer Motion layout animations.

---

# 8. QUOTE WORKSPACE

This page should feel highly interactive.

When adding a line item:

* new row slides/fades in

When removing:

* row exits smoothly

When changing quantity:

* price updates smoothly

When changing discount:

* total value animates

Use AnimatedNumber for:

Subtotal
Discount
Tax
Final Total

### AI INTELLIGENCE PANEL

When opened:

slide in from the right.

When closed:

smoothly slide out.

### RISK ANALYSIS

Risk indicators should appear progressively.

Critical/high-risk elements can use subtle pulse animations.

Do not continuously animate every element.

---

# 9. APPROVALS

### APPROVAL TABLE

Rows appear with a small stagger.

### DETAIL DRAWER

Opening:

translateX(100%) → translateX(0)

Closing:

translateX(0) → translateX(100%)

### TIMELINE

Timeline items reveal sequentially.

### APPROVE

When approved:

* button loading state
* success transition
* status changes from Pending → Approved
* approval timestamp appears

### REJECT

Same behavior but with a clear rejection state.

Do not use large celebration animations.

---

# 10. RISK CENTER

Animate:

* Risk lanes
* Deal cards
* Risk matrix
* Category charts

Cards should enter their corresponding lane using subtle movement.

Risk severity:

Critical
High
Medium
Low

Use animation only where it communicates status.

Critical risks may have a very subtle pulse.

Avoid aggressive flashing.

---

# 11. CUSTOMERS

### CRM TABLE

Rows fade in sequentially.

### HEALTH BARS

Health bars should animate from:

0 → actual percentage

Example:

0% → 82%

### CUSTOMER PROFILE

Opening profile:

smooth width/height expansion

AI insights:

appear using stagger animation.

---

# 12. DEALS

### PIPELINE

Pipeline stages should progressively appear.

### DEAL CARDS

Cards use stagger animation.

### DEAL STATUS

When moving:

Lead → Qualified → Proposal → Negotiation → Closed

animate the status transition.

### DEAL TIMELINE

Timeline events should reveal one by one.

Completed stages should receive subtle visual feedback.

---

# 13. BILLING

Animate:

### Revenue KPIs

Use AnimatedNumber.

### Invoice Table

Stagger rows.

### Payment Status

Smoothly transition between:

Pending
Paid
Overdue

### Charts

Use Recharts animation.

Bars should grow from the baseline.

Lines should progressively render.

---

# 14. ANALYTICS

Create polished chart interactions.

Animate:

* Revenue
* Pipeline
* Win Rate
* AI Impact
* Conversion metrics

When changing filters/date ranges:

Old data should transition smoothly into the new state.

Avoid hard visual jumps.

Tooltips should appear smoothly.

KPI numbers should animate between values.

---

# 15. AI COPILOT

This is one of the most important animated experiences.

### USER MESSAGE

Message appears immediately with subtle fade/slide.

### AI RESPONSE

Show:

TypingIndicator

Then simulate a natural response appearance.

### TYPING INDICATOR

Three dots:

dot 1
dot 2
dot 3

Animate continuously but subtly.

### AI RESPONSE

Use a streaming-style reveal effect where appropriate.

### QUICK ACTIONS

Hover:

slight elevation

Press:

small scale-down

### AI SUGGESTIONS

Suggestion cards appear using stagger.

AI-specific accent color should remain limited.

---

# 16. MODALS / DRAWERS / DROPDOWNS

All Radix/shadcn dialogs, popovers, sheets, dropdowns and tooltips should have consistent motion.

Modal:

fade backdrop

Content:

opacity + scale + translateY

Drawer:

slide from edge

Dropdown:

opacity + translateY

Do not create separate animation styles for every component.

Create reusable variants.

---

# 17. LOADING STATES

Add premium skeleton loading states.

Use subtle shimmer animation.

Apply to:

* Dashboard cards
* Tables
* Product cards
* Customer profiles
* Analytics
* AI Copilot

Do not use spinners everywhere.

Use skeletons when content is loading.

---

# 18. MICRO INTERACTIONS

Add subtle interaction feedback to:

Buttons
Cards
Inputs
Tabs
Navigation
Badges
Checkboxes
Switches
Dropdowns
Pagination
Filters

Button behavior:

Hover → subtle visual change

Press → scale slightly down

Release → return smoothly

Keep all interactions under approximately 200ms where possible.

---

# 19. SCROLL REVEAL

Use viewport-triggered animations for:

Landing page sections
Feature sections
Analytics sections
AI Copilot sections
Large dashboard blocks

Do not animate every small element based on scrolling.

Only major content groups should use scroll reveal.

---

# 20. REDUCED MOTION SUPPORT

Respect:

prefers-reduced-motion

When reduced motion is enabled:

* remove large transforms
* minimize stagger
* disable decorative floating animations
* keep opacity transitions minimal

The application must remain fully usable.

---

# 21. PERFORMANCE REQUIREMENTS

Animations must not negatively affect application performance.

Prefer:

transform
opacity
layout animations

Avoid unnecessary animation of:

width
height
top
left
margin
box-shadow
filters

Do not create hundreds of continuously running animations.

Only animate what improves UX.

---

# 22. RESPONSIVE BEHAVIOR

Animations must work correctly on:

Desktop
Laptop
Tablet
Mobile

On mobile:

* reduce large movement
* reduce stagger where necessary
* keep drawers and sheets responsive
* avoid heavy decorative animation

---

# 23. ACCESSIBILITY

Animations must not interfere with:

Keyboard navigation
Focus states
Screen readers
Reduced motion
Touch interaction

Never hide important content permanently because of animation.

---

# 24. CODE QUALITY

Keep the existing architecture clean.

Do not put large animation configurations directly inside every component.

Centralize reusable animation variants.

Use TypeScript types.

Avoid:

any

unnecessary duplicated code

unused animation components

unused imports

console errors

---

# 25. FINAL QUALITY BAR

After implementation, verify:

* No React errors
* No hydration errors
* No Framer Motion errors
* No duplicate React instances
* No console warnings caused by animations
* No broken routes
* No broken interactions
* No layout shifts
* No animation blocking clicks
* No excessive animation
* No performance regression

Run the TypeScript check and production build.

The final DealFlow360 experience should feel like a premium enterprise SaaS product:

FAST
SMOOTH
MINIMAL
INTELLIGENT
RESPONSIVE
PROFESSIONAL

The animation should be noticeable when interacting with the application, but it should never distract from the data or business workflow.

Think:

Linear-level motion quality
+
Attio-style premium SaaS feel
+
DealFlow360's black/white enterprise identity.
