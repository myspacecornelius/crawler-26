# Brief 20 — Landing Page, Login & Settings Premium Treatment

**Priority:** MEDIUM — These are the first-impression and monetization surfaces
**Commercial Impact:** The landing page is the conversion funnel entry point. The login page sets trust expectations. The settings/billing page directly drives revenue through plan upgrades. All three must look premium.
**Depends on:** Brief 15 (UI primitives), Brief 16 (layout)

---

## Audit — Current Problems

### Landing Page (Currently Non-Existent)

1. **Root `/` just redirects to `/dashboard`** — No marketing page, no value proposition, no social proof. Visitors who aren't logged in see nothing.
2. **No way for visitors to understand what LeadFactory does** before signing up.

### Login Page

3. **Generic login form** — White card on dark gradient. No social proof, no product preview, no trust indicators.
4. **No "forgot password"** — Basic auth flow.
5. **No visual identity** — Just text logo, no imagery.

### Settings Page

6. **Pricing cards look like a template** — Plain white boxes, no feature comparison table, no visual hierarchy between plans.
7. **Credit packs are bare** — Just name + price + button. No value proposition.
8. **Account section is sparse** — Just 4 text fields in a grid. No avatar upload, no edit capability.
9. **`any` types everywhere** — `useState<any>(null)` used 3 times. Type-unsafe.
10. **`alert()` for errors** — Lines 48, 59, 72 use `alert()`.

---

## Scope

### Files to CREATE

- `dashboard/app/(marketing)/page.tsx` — New landing page (replaces the redirect)
- `dashboard/app/(marketing)/layout.tsx` — Marketing layout (no sidebar, different header)
- `dashboard/components/landing/Hero.tsx` — Hero section
- `dashboard/components/landing/Features.tsx` — Feature grid
- `dashboard/components/landing/Pricing.tsx` — Pricing section (reused in settings)
- `dashboard/components/landing/SocialProof.tsx` — Stats + logos
- `dashboard/components/landing/Footer.tsx` — Marketing footer
- `dashboard/components/settings/PricingTable.tsx` — Enhanced pricing comparison
- `dashboard/components/settings/AccountCard.tsx` — Account info card
- `dashboard/components/settings/CreditUsage.tsx` — Enhanced credit display

### Files to MODIFY

- `dashboard/app/page.tsx` — Remove redirect, render landing page (or route group)
- `dashboard/app/login/page.tsx` — Add split layout with product preview
- `dashboard/app/dashboard/settings/page.tsx` — Use new sub-components, fix types, replace alert()

### Files NOT to touch

- No Python/API files
- No dashboard page files (those are Briefs 17–19)

---

## Implementation

### 1. Landing Page — Route Group `(marketing)`

Use Next.js route groups to separate marketing pages (no sidebar) from dashboard pages:

```
app/
├── (marketing)/
│   ├── layout.tsx      ← Marketing layout (navbar + footer, no sidebar)
│   └── page.tsx        ← Landing page
├── dashboard/
│   ├── layout.tsx      ← Dashboard layout (sidebar + header)
│   └── ...
├── login/
│   └── page.tsx
└── layout.tsx          ← Root layout (font, providers)
```

### 2. `(marketing)/layout.tsx` — Marketing Layout

- Sticky transparent navbar that becomes white on scroll
- Logo on left, nav links in center (Features, Pricing, Docs), CTA button on right ("Get Started" → /login)
- No sidebar
- Footer at bottom

### 3. `Hero.tsx` — Landing Hero

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│   Multi-Vertical Lead Generation                        │
│   at Scale                                              │
│                                                          │
│   Find decision-makers at 500+ VC firms, PE funds, and  │
│   family offices. Verified emails, scored leads,         │
│   direct to your CRM.                                   │
│                                                          │
│   [Get Started Free]  [See Demo →]                      │
│                                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │  Dashboard screenshot / product preview          │   │
│   │  (use a CSS mockup of the dashboard)             │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
│   5,200+ contacts  •  96% email coverage  •  400+ funds │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

- Gradient text for headline
- Animated background (subtle gradient mesh or dots)
- Stats bar below the CTA buttons with real numbers from the crawl
- Product screenshot mockup (can be a styled div mimicking the dashboard)

### 4. `Features.tsx` — Feature Grid

6 features in a 3x2 grid:

| Icon | Title | Description |
|------|-------|-------------|
| `Globe` | Deep Web Crawling | Automated extraction from 500+ fund websites with Playwright |
| `Mail` | Email Discovery | 96% email coverage through pattern matching and SMTP verification |
| `BarChart3` | Lead Scoring | AI-powered scoring based on role, seniority, and fund characteristics |
| `Send` | Outreach Integration | Launch campaigns directly through Instantly or SmartLead |
| `Link` | CRM Sync | One-click push to HubSpot or Salesforce with field mapping |
| `Briefcase` | Portfolio Intelligence | Explore fund portfolios with sector and stage filters |

Each feature card: Lucide icon in a colored circle + title + 1-line description.

### 5. `Pricing.tsx` / `PricingTable.tsx` — Shared Pricing Component

Used on both landing page and settings page. A proper comparison table:

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Starter    │     Pro      │    Scale     │  Enterprise  │
│    Free      │   $49/mo     │   $149/mo    │   Custom     │
│              │  POPULAR ★   │              │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 500 credits  │ 5K credits   │ 25K credits  │ Unlimited    │
│ 1 vertical   │ All verts    │ All verts    │ Custom verts │
│ CSV export   │ CSV + API    │ Priority     │ White-label  │
│ —            │ Email verify │ Outreach     │ SLA          │
│ —            │ —            │ Ded. support │ Ded. infra   │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ [Current]    │ [Upgrade →]  │ [Upgrade →]  │ [Contact →]  │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

- "Popular" badge on Pro plan
- Current plan highlighted with brand border
- Feature rows with checkmark/dash icons
- Hover effect on cards
- Annual/monthly toggle (if applicable)

### 6. `SocialProof.tsx`

- Stats bar: "Trusted by X companies" or real numbers
- Logo row: placeholder company logos or "As seen in" (can be generic placeholder logos initially)
- Testimonial quote (can be placeholder: "LeadFactory cut our prospecting time by 80%")

### 7. `Footer.tsx`

- 4-column footer: Product, Company, Legal, Connect
- Product: Features, Pricing, Docs, API
- Legal: Privacy, Terms, Opt-out
- Connect: Twitter, LinkedIn, Email
- Bottom: © 2026 LeadFactory. All rights reserved.

### 8. Enhanced Login Page

Split layout:

```
┌────────────────────────┬────────────────────────────────┐
│                        │                                 │
│   LeadFactory          │   ┌─────────────────────────┐  │
│                        │   │                         │  │
│   "Find the right      │   │   Sign in               │  │
│    investors,          │   │                         │  │
│    10x faster."        │   │   Email: [............] │  │
│                        │   │   Pass:  [............] │  │
│   ─────────────        │   │                         │  │
│                        │   │   [Sign in]             │  │
│   ● 5,200+ contacts   │   │                         │  │
│   ● 96% email rate     │   │   Don't have an acct?  │  │
│   ● 400+ funds         │   │   [Register]           │  │
│                        │   │                         │  │
│   "LeadFactory helped  │   └─────────────────────────┘  │
│    us close 3 deals    │                                 │
│    in Q1."             │                                 │
│    — Demo User         │                                 │
│                        │                                 │
└────────────────────────┴────────────────────────────────┘
```

- Left panel: dark bg, brand messaging, stats, testimonial
- Right panel: white bg, auth form (existing functionality)
- Mobile: stack vertically (form on top, social proof below)

### 9. Enhanced Settings Page

- Replace `any` types with proper interfaces
- Replace `alert()` with toast
- Use `PricingTable` component (shared with landing page)
- `AccountCard` — Editable fields with save button
- `CreditUsage` — Visual credit bar with gradient, usage breakdown, refill date countdown
- Credit packs: Add "Most Popular" badge, savings percentage

---

## Acceptance Criteria

1. Landing page renders at `/` with hero, features, pricing, footer
2. Landing page is NOT behind auth — anyone can see it
3. Login page has split layout with social proof panel
4. Settings page uses shared PricingTable component
5. Zero `alert()` calls in settings page
6. Zero `any` types in settings page
7. Marketing layout has navbar + footer (no sidebar)
8. Dashboard layout still has sidebar (no regression)
9. Mobile: all pages render correctly on 375px width
10. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors, new pages generated

npm run dev
# Visit / (not logged in) → landing page with hero, features, pricing
# Click "Get Started" → /login with split layout
# Log in → /dashboard (with sidebar, not marketing layout)
# Navigate to /dashboard/settings → PricingTable renders, no alert() usage
# Mobile test: resize to 375px → all sections stack correctly
```

---

## Notes for Sub-Agent

- The landing page should feel like a REAL SaaS landing page — study Vercel, Linear, Resend for inspiration
- Use CSS gradient mesh or subtle dot pattern for hero background — no external images needed
- Product screenshot in hero can be a styled div that mimics the dashboard UI (no actual screenshot)
- The pricing component MUST be shared between landing page and settings — do not duplicate
- For the login split layout, the left panel content (stats, testimonial) can use the same data as the landing page hero stats
