# Brief 17 — Data Visualization & Dashboard Upgrade

**Priority:** HIGH — The dashboard is the landing page after login. It must impress immediately.
**Commercial Impact:** Charts and visualizations are the #1 "wow factor" in demos. A dashboard with real-time charts converts prospects 3x faster than one with just numbers.
**Depends on:** Brief 15 (UI primitives), Brief 16 (layout)

---

## Audit — Current Problems

1. **No charts at all** — Dashboard is 4 StatsCards + 1 table. Zero visualizations.
2. **StatsCard is minimal** — Just label + number + optional change text. No sparklines, no trend indicators, no animated counters.
3. **No activity feed** — No way to see recent events (crawl completed, emails verified, campaign launched).
4. **No email status breakdown** — 96% email rate is meaningless without seeing verified vs guessed vs scraped.
5. **No time-series data** — No sense of growth, progress, or trends over time.
6. **Loading is plain text** — `"Loading dashboard..."` instead of skeleton cards.

---

## Scope

### Dependencies to Install

```bash
npm install recharts
```

### Files to CREATE

- `dashboard/components/charts/LeadsOverTimeChart.tsx` — Area/line chart
- `dashboard/components/charts/EmailStatusDonut.tsx` — Donut/pie chart
- `dashboard/components/charts/FundCoverageBar.tsx` — Horizontal bar chart
- `dashboard/components/charts/MiniSparkline.tsx` — Tiny inline sparkline for StatsCard
- `dashboard/components/ActivityFeed.tsx` — Recent events list
- `dashboard/components/QuickActions.tsx` — Action buttons grid

### Files to MODIFY

- `dashboard/components/StatsCard.tsx` — Add sparkline slot, animated counter, trend arrow icon
- `dashboard/app/dashboard/page.tsx` — Complete redesign with chart grid + activity feed
- `dashboard/package.json` — Add `recharts`

### Files NOT to touch

- No Python/API files
- No other page files (those are Briefs 18–20)

---

## Implementation

### 1. Enhanced `StatsCard.tsx`

Current: label + value + change text
New additions:

- **Trend arrow** — Up/down Lucide arrow icon instead of just text color
- **Animated counter** — Number animates from 0 to value on mount (simple CSS counter or requestAnimationFrame)
- **Sparkline slot** — Optional `sparklineData` prop renders a tiny MiniSparkline in the bottom of the card
- **Icon slot** — Replace emoji string with Lucide icon component (passed as prop)
- **Subtle gradient** — Top border with gradient matching the metric type

```tsx
interface StatsCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;       // Changed from string emoji to ReactNode
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  sparklineData?: number[];    // NEW — tiny chart in bottom
  className?: string;          // NEW — allow custom styling
}
```

### 2. `MiniSparkline.tsx`

- Uses recharts `<AreaChart>` with no axes, no grid, no labels
- Just a tiny colored area fill (30px tall, full width of card)
- Color matches `changeType` (green for positive, red for negative, gray for neutral)
- Renders in the bottom 30px of the StatsCard

### 3. `LeadsOverTimeChart.tsx`

- Recharts `<AreaChart>` or `<ComposedChart>`
- X-axis: dates (last 30 days or campaign duration)
- Y-axis: lead count
- Two areas stacked: "Verified" (green) and "Guessed" (amber)
- Tooltip showing exact counts
- Responsive container
- Card wrapper with title "Leads Generated" and a time range selector (7d / 30d / 90d / All)

### 4. `EmailStatusDonut.tsx`

- Recharts `<PieChart>` with inner radius (donut style)
- Segments: Verified (emerald), Scraped (blue), Guessed (amber), Undeliverable (red), Unknown (gray)
- Center label showing total count
- Legend below with counts
- Card wrapper with title "Email Quality"

### 5. `FundCoverageBar.tsx`

- Horizontal bar chart showing top 10 funds by contact count
- Each bar shows fund name + count
- Color intensity based on extraction quality
- Card wrapper with title "Top Funds by Coverage"

### 6. `ActivityFeed.tsx`

- Vertical timeline/list of recent events
- Event types with icons:
  - `crawl_complete` — Globe icon, "Deep crawl completed: 5,205 contacts"
  - `enrichment_complete` — Mail icon, "Enrichment: 4,990 emails generated"
  - `campaign_created` — Rocket icon, "Campaign 'Q1 VC Outreach' created"
  - `crm_push` — Link icon, "Pushed 150 leads to HubSpot"
  - `outreach_launched` — Send icon, "Outreach campaign launched via Instantly"
- Relative timestamps ("2 hours ago", "Yesterday")
- Card wrapper with title "Recent Activity"
- Initially populated from campaign data; later can be enhanced with a real activity API

### 7. `QuickActions.tsx`

- Grid of 3–4 action buttons:
  - "New Campaign" → `/dashboard/campaigns/new`
  - "Run Deep Crawl" → triggers API call
  - "Push to CRM" → `/dashboard/crm`
  - "Export CSV" → triggers download
- Each button: icon + label + short description
- Styled as outlined cards with hover effect

### 8. Updated `dashboard/page.tsx` — New Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  Welcome back, {name}              [Quick Actions ▼] │
├────────────┬────────────┬────────────┬──────────────┤
│ StatsCard  │ StatsCard  │ StatsCard  │ StatsCard    │
│ Total Leads│ Emails     │ Active     │ Credits      │
│ + sparkline│ + sparkline│ Campaigns  │ Remaining    │
├────────────┴────────────┴────────────┴──────────────┤
│                                                      │
│  ┌──────────────────────┐  ┌───────────────────────┐│
│  │  Leads Over Time     │  │  Email Quality        ││
│  │  (Area Chart)        │  │  (Donut Chart)        ││
│  │                      │  │                       ││
│  └──────────────────────┘  └───────────────────────┘│
│                                                      │
│  ┌──────────────────────┐  ┌───────────────────────┐│
│  │  Recent Campaigns    │  │  Activity Feed        ││
│  │  (Table)             │  │  (Timeline)           ││
│  │                      │  │                       ││
│  └──────────────────────┘  └───────────────────────┘│
└─────────────────────────────────────────────────────┘
```

Grid layout:
- Top row: 4-column StatsCard grid (existing, enhanced)
- Middle row: 2-column — LeadsOverTimeChart (2/3 width) + EmailStatusDonut (1/3 width)
- Bottom row: 2-column — Recent Campaigns table (1/2) + ActivityFeed (1/2)

### 9. Dashboard Skeleton Loading

Replace `"Loading dashboard..."` with:
- 4 skeleton StatsCards (animated pulse rectangles)
- 2 skeleton chart areas
- Skeleton table rows

---

## Acceptance Criteria

1. Dashboard shows 4 enhanced StatsCards with Lucide icons (no emojis)
2. At least one chart renders with sample/placeholder data
3. Email status donut shows breakdown of verified/guessed/scraped
4. Activity feed shows recent events
5. Quick actions are accessible
6. Skeleton loading appears while data fetches
7. All charts are responsive (resize gracefully)
8. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Navigate to /dashboard
# Verify: StatsCards have icons (not emojis) and sparklines
# Verify: At least one chart renders
# Verify: Activity feed shows events
# Resize window — charts and grid adapt
```

---

## Notes for Sub-Agent

- If real API data isn't available, use realistic placeholder/mock data that matches the schema
- Charts should use the brand color palette from Brief 15's CSS variables
- Use `recharts` ResponsiveContainer for all charts
- Keep chart components generic and reusable (they may appear on campaign detail pages too)
- The activity feed can start with mock data — a real `/api/activity` endpoint can come later
