Enhance the existing DealFlow360 enterprise SaaS design with a premium, modern animation system.

DO NOT redesign the existing UI, layout, navigation, information architecture, or visual hierarchy. Keep the current black-and-white design language and existing screens. Only enhance the experience with sophisticated motion and micro-interactions.

### DESIGN DIRECTION

DealFlow360 should feel like a premium enterprise SaaS product inspired by the smoothness and polish of Linear and Attio.

Primary visual system:

* Black background
* White typography and UI surfaces where appropriate
* Very limited accent color usage, around 10%
* Clean typography
* High contrast
* Minimal, professional, enterprise-focused
* Avoid excessive gradients, bouncing animations, cartoon effects, or flashy transitions

### FRONTEND STACK

Build the experience using:

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

### ANIMATION SYSTEM

Use Framer Motion as the primary animation library.

Create a consistent motion system:

* Fast micro-interactions: 120–180ms
* Standard UI transitions: 200–300ms
* Larger panel/page transitions: 300–500ms
* Use ease-out/ease-in-out curves
* Prefer opacity + transform animations
* Avoid unnecessary scale animations
* Respect prefers-reduced-motion

### LANDING PAGE

Add premium entrance animations:

* Hero headline fades and slides upward
* Supporting text appears with a small stagger
* CTA buttons fade in after the hero content
* Dashboard preview enters with a subtle scale + opacity animation
* Dashboard preview has a very subtle floating/parallax effect
* KPI cards inside the dashboard preview animate sequentially
* Charts draw themselves progressively
* Feature sections reveal while scrolling
* Feature cards use staggered reveal animations
* AI Copilot demo should simulate live activity
* CTA section should smoothly reveal when entering the viewport

Use viewport-based scroll reveal animations rather than animating everything immediately.

### LOGIN PAGE

Keep the Linear-inspired minimal authentication design.

Add:

* Smooth page entrance
* Logo fade-in
* Login card slide-up + fade
* Input focus micro-interactions
* Button hover/press animation
* Google SSO button subtle hover animation
* Loading state with elegant spinner
* Successful login transition into the application shell

### APPLICATION SHELL

Add:

* Smooth sidebar expand/collapse
* Sidebar navigation items highlight with an animated active indicator
* Icons subtly transition on hover
* Breadcrumb transitions when changing pages
* Notification dropdown slides/fades from the top-right
* User menu opens with scale + opacity
* Main content uses subtle page transitions

Do not make page transitions slow.

### COMMAND CENTER

Animate:

* KPI cards entering with stagger
* KPI numbers count up smoothly
* Revenue chart progressively draws on mount
* AI action queue items appear sequentially
* Live deal table rows fade/slide in
* Approval queue cards reveal smoothly
* Status badges use subtle pulse animation only when representing live activity

### PRODUCTS

Add:

* Product cards stagger into the grid
* Grid/list switching uses smooth layout animation
* Category filter transitions smoothly
* Product cards slightly lift on hover
* Product card content transitions naturally
* AI insight badges appear with subtle fade/scale
* "Add to Quote" button has press feedback
* Avoid excessive card movement

### QUOTE WORKSPACE

Add:

* Line items animate when added or removed
* Quantity changes smoothly update totals
* Discount changes animate the price summary
* AI intelligence panel slides in smoothly
* Risk analysis indicators reveal progressively
* Price summary numbers animate when values change
* Buttons have subtle hover and tap feedback

### APPROVALS

Add:

* Approval table rows stagger on initial load
* Detail drawer slides smoothly from the side
* Timeline events reveal sequentially
* AI reasoning content fades in
* Approve/reject actions have clear success/error micro-interactions
* After approval, update the status with a smooth transition instead of an abrupt change

### RISK CENTER

Create animated risk visualization:

* Risk lanes reveal progressively
* Deal cards smoothly enter each lane
* Risk matrix points animate into position
* Critical/high-risk indicators can use a very subtle pulse
* Category breakdown chart animates on load
* Filtering between risk levels should use layout transitions

### CUSTOMERS

Add:

* CRM table rows stagger in
* Health bars animate from 0 to their actual value
* Customer profile panel expands/collapses smoothly
* AI insights reveal sequentially
* Customer status changes animate smoothly

### DEALS

Add:

* Pipeline stages animate when loaded
* Deal cards enter with stagger
* Pipeline progress smoothly transitions when deal status changes
* Deal timeline animates step-by-step
* Completed stages receive subtle visual feedback
* Avoid overly dramatic animations

### BILLING

Add:

* Revenue KPI count-up animation
* Invoice rows fade in sequentially
* Payment status indicators transition smoothly
* Recharts bar/line charts animate naturally
* Payment status changes use subtle transitions

### ANALYTICS

Use Recharts with polished animation:

* Line charts animate progressively
* Bar charts grow from the baseline
* Data points appear subtly
* Tooltip appears smoothly
* KPI values count up
* Switching date ranges should animate chart transitions
* Avoid excessive animation that distracts from data

### AI COPILOT

Make the AI Copilot feel alive.

Add:

* Chat messages appear with smooth fade + slide
* Typing indicator with three subtle animated dots
* Simulated streaming response effect
* Quick action chips animate on hover
* AI suggestion sidebar slides/fades into view
* AI insight cards appear sequentially
* Contextual responses should feel instantaneous but polished
* Use subtle glowing/accent effects only for AI-specific elements

### GLOBAL MICRO-INTERACTIONS

Apply consistently across the entire application:

Buttons:

* Hover → slight scale/brightness change
* Press → subtle scale down
* Loading → animated loading state
* Success → subtle confirmation animation

Cards:

* Hover → very small elevation/transform
* Focus → accessible focus ring
* Loading → skeleton shimmer

Navigation:

* Active indicator smoothly moves between items
* Hover states transition smoothly

Modals:

* Fade backdrop
* Scale + fade modal content
* Smooth closing animation

Dropdowns:

* Opacity + translate animation
* Smooth opening/closing

Tables:

* Row hover transitions
* Staggered initial appearance
* Smooth status changes

Forms:

* Animated validation feedback
* Smooth error/success messages
* Focus transitions

### PAGE TRANSITIONS

Create a reusable page transition system using Framer Motion.

Every major application view should transition using:

opacity + slight translateY

Keep transitions fast and professional.

Do NOT use:

* dramatic zooms
* spinning pages
* excessive bouncing
* large movements
* distracting particle effects

### PERFORMANCE

Animations must be production-ready.

Use:

* transform
* opacity
* layout animations where appropriate
* AnimatePresence
* viewport-triggered animations
* reduced-motion support

Avoid animating expensive CSS properties such as width, height, top, left, box-shadow, or filters unless necessary.

Use GPU-friendly transforms whenever possible.

### COMPONENT ARCHITECTURE

Create reusable animation utilities/components such as:

* FadeIn
* SlideUp
* StaggerContainer
* StaggerItem
* PageTransition
* AnimatedNumber
* AnimatedCard
* AnimatedPresence wrapper
* HoverScale
* RevealOnScroll
* TypingIndicator
* SkeletonLoader

Keep animations reusable rather than writing separate animation logic for every screen.

### FINAL EXPERIENCE

The finished DealFlow360 application should feel:

Premium
Fast
Smooth
Professional
Enterprise-grade
Minimal
AI-powered
Modern

The animation should enhance usability and hierarchy rather than becoming the main visual element.

Maintain the existing black-and-white visual identity and use accent colors sparingly for AI states, success states, warnings, and important interactions.
