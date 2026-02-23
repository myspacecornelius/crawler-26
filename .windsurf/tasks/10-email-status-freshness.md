# Brief 10 — Email Status Badges + Freshness Panel in Dashboard

**Priority:** HIGH (Trust & retention — users must see verified vs guessed to trust product)
**Commercial Impact:** Users who can't distinguish email quality churn fast. This is the #1 signal that the data pipeline improvements (briefs 07-09) actually worked.

---

## Problem

The `LeadTable` component currently shows a simple boolean ✓ for `email_verified`, but the backend now tracks granular `email_status` values: `scraped`, `guessed`, `verified`, `catch_all`, `undeliverable`, `unknown`. The freshness endpoint (`/leads/campaign/{id}/freshness`) exists but is not surfaced anywhere. Users have no way to assess data quality at a glance.

## Scope

### Files to MODIFY (frontend only — no backend changes)
- `dashboard/components/LeadTable.tsx` — Add email status badge column, add email_status filter
- `dashboard/app/dashboard/campaigns/[id]/page.tsx` — Add freshness panel, update Stats interface
- `dashboard/lib/api.ts` — Add `getFreshness()` function

### Files NOT to touch
- Any Python files, API routers, or backend code

---

## Implementation

### 1. `dashboard/lib/api.ts` — Add freshness API call

```typescript
export async function getFreshness(campaignId: string) {
  return fetchAPI(`/leads/campaign/${campaignId}/freshness`);
}
```

### 2. `dashboard/components/LeadTable.tsx` — Email status badges

#### 2a. Update the `Lead` interface
Replace `email_verified: boolean` with:
```typescript
email_status: 'scraped' | 'guessed' | 'verified' | 'catch_all' | 'undeliverable' | 'unknown';
```

#### 2b. Add status badge color map
```typescript
const emailStatusColors: Record<string, string> = {
  verified: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  scraped: 'bg-blue-100 text-blue-700 border-blue-200',
  guessed: 'bg-amber-100 text-amber-700 border-amber-200',
  catch_all: 'bg-purple-100 text-purple-700 border-purple-200',
  undeliverable: 'bg-red-100 text-red-700 border-red-200',
  unknown: 'bg-gray-100 text-gray-500 border-gray-200',
};
```

#### 2c. Replace the email cell rendering
Replace the simple ✓ checkmark with a badge showing the status. Show the badge inline next to the email address:
```tsx
{lead.email_status && lead.email_status !== 'unknown' && (
  <span className={`ml-1.5 inline-block px-1.5 py-0.5 text-[10px] font-medium rounded border ${emailStatusColors[lead.email_status] || emailStatusColors.unknown}`}>
    {lead.email_status}
  </span>
)}
```

#### 2d. Add email status filter dropdown
Add after the existing Tier filter dropdown:
```tsx
<select
  value={emailStatusFilter}
  onChange={(e) => { setEmailStatusFilter(e.target.value); setTimeout(handleSearch, 0); }}
  className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
>
  <option value="">All Email Status</option>
  <option value="verified">Verified</option>
  <option value="scraped">Scraped</option>
  <option value="guessed">Guessed</option>
  <option value="catch_all">Catch-All</option>
  <option value="undeliverable">Undeliverable</option>
</select>
```

Add `email_status` to the filters object in `handleSearch`:
```typescript
if (emailStatusFilter) filters.email_status = emailStatusFilter;
```

### 3. `dashboard/app/dashboard/campaigns/[id]/page.tsx` — Freshness panel

#### 3a. Add freshness state and fetch
```typescript
const [freshness, setFreshness] = useState<any>(null);

// In the useEffect Promise.all, add:
getFreshness(id).catch(() => null),

// Destructure:
.then(([c, s, f]) => {
  setCampaign(c);
  setStats(s);
  setFreshness(f);
  ...
```

#### 3b. Add freshness card to the stats grid
Add a 5th StatsCard:
```tsx
<StatsCard
  label="Data Freshness"
  value={`${freshness?.freshness_pct ?? 0}%`}
  icon="🔄"
  change={`${freshness?.verified_last_7d ?? 0} verified this week`}
  changeType={freshness?.freshness_pct > 70 ? 'positive' : 'neutral'}
/>
```

#### 3c. Update Stats interface to include `verified_emails`
The `verified_emails` field from the stats endpoint should be shown:
```tsx
<StatsCard label="Verified" value={stats.verified_emails} icon="✅" change={`${Math.round(stats.verified_emails / stats.total_leads * 100)}% rate`} />
```

---

## Acceptance Criteria

1. LeadTable shows colored badges: verified (green), scraped (blue), guessed (amber), catch_all (purple), undeliverable (red)
2. Email status dropdown filter works — selecting "verified" only shows verified leads
3. Campaign detail page shows freshness % and verified-this-week count
4. No backend changes — all data already available from existing API endpoints
5. Existing tests still pass (run `npm run build` in dashboard/)

## Testing

```bash
cd dashboard && npm run build
# Should compile with zero errors

# Visual test: start dev server
npm run dev
# Navigate to a campaign detail page — verify badges appear
# Filter by email_status — verify filter works
# Check freshness card appears in stats grid
```
