# Brief 19 — Campaign, Outreach & CRM Page Polish

**Priority:** MEDIUM — These are the core workflow pages that power users spend 80% of their time on
**Commercial Impact:** Professional workflow pages reduce churn. If the CRM page looks like a form dump, users won't trust it with their Salesforce credentials. If campaigns look flat, users won't see the value of paying for more.
**Depends on:** Brief 15 (UI primitives), Brief 16 (layout), Brief 17 (charts), Brief 18 (tables)

---

## Audit — Current Problems

### Campaigns

1. **Campaign detail page** — Missing charts. Just stats cards + lead table. No visualization of lead quality, email status breakdown, or scoring distribution.
2. **Campaign list** — Plain table only. No card view toggle. No campaign status timeline.
3. **Campaign wizard** — Functional but transitions between steps are instant (no animation). Step indicator could be more polished.

### Outreach

1. **Visual hierarchy is flat** — All sections have equal weight. The launch form and active campaigns table compete for attention.
2. **Provider selection** — Basic buttons. Should look like integration cards with logos.
3. **Template preview** — No actual template rendering. Just says "Template preview will appear here."
4. **Stats display** — Just numbers in a table. Should be visual (mini charts).

### CRM

1. **748 lines in one file** — Massively overloaded component. Should be decomposed.
2. **Provider cards** — Use emoji circles (🟠 🔵) instead of real logos or icons.
3. **Form is overwhelming** — All options visible at once. Field mapping, custom fields, targeting, test mode — too much cognitive load.
4. **Push history uses alert()** — `alert(JSON.stringify(result, null, 2))` for status check.

---

## Scope

### Files to CREATE

- `dashboard/components/campaign/CampaignStatsPanel.tsx` — Chart-enhanced stats for campaign detail
- `dashboard/components/campaign/LeadScoreDistribution.tsx` — Histogram of lead scores
- `dashboard/components/outreach/ProviderCard.tsx` — Integration card for Instantly/SmartLead
- `dashboard/components/outreach/OutreachStatsChart.tsx` — Mini stats visualization
- `dashboard/components/crm/CRMProviderSetup.tsx` — Extracted provider connection cards
- `dashboard/components/crm/CRMPushForm.tsx` — Extracted push form
- `dashboard/components/crm/CRMPushHistory.tsx` — Extracted push history table

### Files to MODIFY

- `dashboard/app/dashboard/campaigns/[id]/page.tsx` — Add charts, improve layout
- `dashboard/app/dashboard/campaigns/page.tsx` — Card view option, better empty state
- `dashboard/components/CampaignWizard.tsx` — Add step transition animations
- `dashboard/app/dashboard/outreach/page.tsx` — Restructure with visual hierarchy
- `dashboard/app/dashboard/crm/page.tsx` — Decompose into sub-components, collapsible sections

### Files NOT to touch

- No Python/API files
- No Brief 15–18 component files (use them, don't modify them)

---

## Implementation

### 1. Campaign Detail Enhancement (`campaigns/[id]/page.tsx`)

Current layout: 4 StatsCards + LeadTable

New layout:

```
┌─────────────────────────────────────────────────┐
│  Campaign: "Q1 VC Outreach"    [Run] [Export ▼] │
│  Status: ● Running  |  Created: Feb 23, 2026    │
├────────────┬───────────┬───────────┬────────────┤
│  Total     │  Emails   │  Verified │  Avg Score │
│  Leads     │  Found    │  Rate     │            │
│  5,108     │  4,990    │  0%       │  43.4      │
├────────────┴───────────┴───────────┴────────────┤
│  ┌─────────────────────┐ ┌────────────────────┐ │
│  │ Lead Score           │ │ Email Status       │ │
│  │ Distribution         │ │ Breakdown          │ │
│  │ (Histogram)          │ │ (Donut)            │ │
│  └─────────────────────┘ └────────────────────┘ │
│                                                  │
│  ┌─────────────────────────────────────────────┐│
│  │ Leads Table (with DataTable from Brief 18)  ││
│  │ Sortable, selectable, exportable            ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

- `LeadScoreDistribution.tsx` — Recharts bar histogram showing count of leads in score buckets (0–20, 20–40, 40–60, 60–80, 80–100)
- Reuse `EmailStatusDonut` from Brief 17

### 2. Campaign List Enhancement (`campaigns/page.tsx`)

- Add view toggle: "Table" (current) | "Cards" (grid of campaign cards)
- Card view: each campaign as a card with name, status badge, lead count, mini progress bar, created date
- Better empty state with illustration icon + CTA
- Status filter tabs at top: All | Running | Completed | Pending

### 3. Campaign Wizard Animation (`CampaignWizard.tsx`)

- Add `framer-motion` (or CSS-only) slide transition between steps
- Steps slide left when advancing, right when going back
- Step indicator: connected line animates fill as you progress
- Add subtle fade-in for step content

### 4. Outreach Page Restructure (`outreach/page.tsx`)

New layout with clear visual hierarchy:

```
┌─────────────────────────────────────────────────┐
│  Outreach Hub                                    │
│  Launch and monitor email outreach campaigns     │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─── Launch New Campaign ────────────────────┐ │
│  │ Provider:  [Instantly ▣] [SmartLead ▣]     │ │
│  │                                            │ │
│  │ Source Campaign: [dropdown]                │ │
│  │ API Key: [••••••••]                        │ │
│  │ Template: [dropdown] → preview panel       │ │
│  │                                            │ │
│  │ Targeting: [collapsible section]           │ │
│  │                                            │ │
│  │ [Launch Campaign →]                        │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌─── Active Campaigns ──────────────────────┐  │
│  │ 3 active campaigns                         │ │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐      │ │
│  │ │ Camp 1  │ │ Camp 2  │ │ Camp 3  │      │ │
│  │ │ 150 sent│ │ 89 sent │ │ 45 sent │      │ │
│  │ │ 23% open│ │ 18% open│ │ 31% open│      │ │
│  │ └─────────┘ └─────────┘ └─────────┘      │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

- `ProviderCard.tsx` — Cards with provider icon (Lucide `Mail` for Instantly, `Zap` for SmartLead), name, description, connected status
- Active campaigns shown as stat cards instead of a flat table
- Each card links to the detail page

### 5. CRM Page Decomposition (`crm/page.tsx`)

Break the 748-line monolith into:

**`CRMProviderSetup.tsx`** (~120 lines)
- HubSpot and Salesforce connection cards
- Replace emoji circles with Lucide icons (`CircleDot` orange for HubSpot, `Cloud` blue for Salesforce)
- Each card is self-contained with credential inputs + test button
- Show connection indicator (green dot when connected)

**`CRMPushForm.tsx`** (~200 lines)
- Provider toggle, source campaign, targeting
- Collapsible "Advanced" section for field mapping and custom fields
- Field mapping defaults collapsed, opens in a slide-down panel
- Test mode toggle moved to footer next to push button

**`CRMPushHistory.tsx`** (~100 lines)
- Table with status badges
- Replace `alert(JSON.stringify(...))` with a Dialog that shows formatted status
- Add "Sync Again" action button

Main `crm/page.tsx` becomes a thin orchestrator (~50 lines) that renders:
```tsx
<CRMProviderSetup ... />
<CRMPushForm ... />
<CRMPushHistory ... />
```

### 6. Collapsible Section Pattern

All three pages benefit from a consistent collapsible section:

```tsx
<CollapsibleSection title="Advanced Targeting" defaultOpen={false} badge="3 filters">
  {/* content */}
</CollapsibleSection>
```

This can be a simple component using `useState` + CSS transition for height, or use Radix Collapsible.

---

## Acceptance Criteria

1. Campaign detail page shows score histogram + email donut chart
2. Campaign list has status filter tabs and card view toggle
3. Campaign wizard has smooth step transitions
4. Outreach page has clear launch form → active campaigns hierarchy
5. CRM page is decomposed into 3 sub-components (< 100 lines each for child components)
6. Zero `alert()` calls remain in any of these pages
7. All provider icons use Lucide (no emojis)
8. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Campaign detail: score histogram + email donut render
# Campaign list: toggle between table and card view
# Campaign wizard: step transitions animate
# Outreach: provider cards render with icons
# CRM: sections are collapsible, push history uses dialog not alert
# grep -r "alert(" dashboard/app/ → zero results
```
