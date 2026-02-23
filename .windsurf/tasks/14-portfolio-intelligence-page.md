# Brief 14 — Portfolio Intelligence Page

**Priority:** LOW (Differentiation feature — "wow factor" for demos, not a direct revenue driver)
**Commercial Impact:** Portfolio data enriches the sales narrative ("we don't just find investors, we map their portfolios") but doesn't directly drive conversion or retention. Useful for enterprise demos and content marketing. Ship last.

---

## Problem

The backend has a portfolio endpoint (`GET /funds/{fund}/portfolio`) that returns portfolio companies for a fund with sector/stage/year filters. The dashboard has no page to surface this. Users can't explore which companies a fund has invested in, which is valuable context for personalized outreach.

## Scope

### Files to CREATE
- `dashboard/app/dashboard/portfolio/page.tsx` — Portfolio explorer

### Files to MODIFY
- `dashboard/lib/api.ts` — Add portfolio API function
- `dashboard/components/Sidebar.tsx` — Add "Portfolio" nav link

### Files NOT to touch
- Any Python files or API routers

---

## Implementation

### 1. `dashboard/lib/api.ts` — Add portfolio function

```typescript
// Portfolio
export async function getFundPortfolio(fund: string, params: Record<string, string> = {}) {
  const searchParams = new URLSearchParams(params);
  return fetchAPI(`/funds/${encodeURIComponent(fund)}/portfolio?${searchParams}`);
}
```

### 2. `dashboard/components/Sidebar.tsx` — Add nav link

Add to `nav` array after CRM:
```typescript
{ href: '/dashboard/portfolio', label: 'Portfolio', icon: '📁' },
```

### 3. `dashboard/app/dashboard/portfolio/page.tsx` — Portfolio Explorer

#### Layout

**Search Bar** (top)
- Large search input: "Search fund name (e.g. Sequoia, a16z, Benchmark)..."
- On enter or click search → calls `getFundPortfolio(fundName)`
- Debounced search with 300ms delay

**Results Section**
- Fund name as heading with company count badge
- Filter bar:
  - Sector dropdown (populated from results)
  - Stage dropdown (populated from results)  
  - Year range (min/max inputs)
- Company grid: responsive cards (3 columns on desktop, 1 on mobile)
  - Each card shows:
    - Company name (bold)
    - Sector badge (colored pill)
    - Stage badge
    - Year of investment
    - Description (truncated to 2 lines)
    - Website link (if available)

**Empty State**
- Illustration/icon + "Search for a fund to explore their portfolio"
- Suggested funds: show 4-5 well-known fund names as clickable chips

#### Visual Design
- Search bar: large, prominent, centered at top with subtle shadow
- Company cards: white bg, rounded-xl, hover shadow transition
- Sector badges: use distinct colors per sector (AI=purple, SaaS=blue, Fintech=green, Health=red, etc.)
- Stage badges: gray outline pills
- Match dashboard styling throughout

---

## Acceptance Criteria

1. Sidebar shows "Portfolio" link with 📁 icon
2. Search bar allows fund name input
3. Results display as filterable card grid
4. Sector/stage/year filters work client-side on loaded results
5. Empty state shows suggested fund names as clickable chips
6. Pagination works if >100 results (use API's page/per_page params)
7. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Navigate to /dashboard/portfolio
# Verify search bar and empty state render
# Search for a fund name → verify API call made
# Check cards render with company data
# Test filters narrow results
```
