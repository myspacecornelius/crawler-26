# Brief 12 — Outreach Integration Page (Instantly / SmartLead)

**Priority:** HIGH (Direct revenue multiplier — lets users act on leads immediately)
**Commercial Impact:** Without outreach, users export CSV and may never come back. Integrated outreach creates a sticky workflow loop: crawl → enrich → email → track opens → repeat. This is the #1 upsell lever for Pro/Scale tiers.

---

## Problem

The backend has a full outreach router (`api/routers/outreach.py`) with 5 endpoints:
- `POST /outreach/launch` — Launch outreach campaign from LeadFactory campaign leads
- `POST /outreach/start` — Activate a paused outreach campaign
- `POST /outreach/pause` — Pause an active outreach campaign
- `GET /outreach/stats/{provider}/{id}` — Get campaign analytics (opens, replies, bounces)
- `GET /outreach/templates` — List available email sequence templates by vertical

None of these are surfaced in the dashboard. There is no outreach page, no sidebar nav link, and no API client functions.

## Scope

### Files to CREATE
- `dashboard/app/dashboard/outreach/page.tsx` — Outreach hub: launch, monitor, manage
- `dashboard/app/dashboard/outreach/[id]/page.tsx` — Single outreach campaign detail + stats

### Files to MODIFY
- `dashboard/lib/api.ts` — Add outreach API functions
- `dashboard/components/Sidebar.tsx` — Add "Outreach" nav link

### Files NOT to touch
- Any Python files or API routers

---

## Implementation

### 1. `dashboard/lib/api.ts` — Add outreach functions

```typescript
// Outreach
export async function launchOutreach(data: {
  name: string;
  provider: string;
  campaign_id: string;
  from_email?: string;
  from_name?: string;
  min_score?: number;
  tiers?: string[];
  api_key?: string;
  custom_vars?: Record<string, string>;
}) {
  return fetchAPI('/outreach/launch', { method: 'POST', body: JSON.stringify(data) });
}

export async function startOutreach(provider: string, providerCampaignId: string, apiKey?: string) {
  return fetchAPI('/outreach/start', {
    method: 'POST',
    body: JSON.stringify({ provider, provider_campaign_id: providerCampaignId, api_key: apiKey }),
  });
}

export async function pauseOutreach(provider: string, providerCampaignId: string, apiKey?: string) {
  return fetchAPI('/outreach/pause', {
    method: 'POST',
    body: JSON.stringify({ provider, provider_campaign_id: providerCampaignId, api_key: apiKey }),
  });
}

export async function getOutreachStats(provider: string, providerCampaignId: string) {
  return fetchAPI(`/outreach/stats/${provider}/${providerCampaignId}`);
}

export async function listOutreachTemplates() {
  return fetchAPI('/outreach/templates');
}
```

### 2. `dashboard/components/Sidebar.tsx` — Add nav link

Add to the `nav` array, after Campaigns:
```typescript
{ href: '/dashboard/outreach', label: 'Outreach', icon: '📨' },
```

### 3. `dashboard/app/dashboard/outreach/page.tsx` — Outreach Hub

#### Layout
- **Header:** "Outreach" title + "Launch Campaign" button
- **Section 1: Launch Form** (collapsible card, expanded by default if no campaigns exist)
  - Provider selector: radio buttons for "Instantly" and "SmartLead"
  - Source campaign: dropdown of completed LeadFactory campaigns (fetch via `listCampaigns`)
  - Campaign name: text input
  - From email: text input
  - From name: text input  
  - Targeting:
    - Min score slider (0–100)
    - Tier checkboxes (HOT, WARM, COOL)
  - Provider API key: password input with "Use saved key" toggle
  - Template preview: fetch templates via `listOutreachTemplates()`, show steps as accordion
  - **Launch button** → calls `launchOutreach()`, shows success toast with provider campaign ID

- **Section 2: Active Campaigns** (table)
  - Columns: Name, Provider, Status, Leads, Sent, Opens, Replies, Actions
  - Actions: Start, Pause, View Stats
  - **Note:** The backend doesn't persist outreach campaigns in our DB — stats come from the provider API. For now, store launched campaign IDs in localStorage as a lightweight tracking mechanism:
    ```typescript
    interface OutreachRecord {
      provider: string;
      provider_campaign_id: string;
      name: string;
      source_campaign_id: string;
      launched_at: string;
    }
    ```
  - On page load, iterate stored records and fetch stats for each via `getOutreachStats()`

#### Visual Design
- Match existing dashboard style: white cards, gray-200 borders, rounded-xl
- Provider selector: card-style radio (like vertical selector in campaign wizard)
- Stats use the same `StatsCard` component
- Template preview: accordion with step number, subject line, and body preview

### 4. `dashboard/app/dashboard/outreach/[id]/page.tsx` — Campaign Detail

- Fetch stats via `getOutreachStats(provider, id)`
- Display:
  - Stats grid: Total Leads, Emails Sent, Opens (with rate), Replies (with rate), Bounces, Clicks
  - Start/Pause toggle button
  - "Back to Outreach" link
- Keep it simple — this is a read-only stats view

---

## Acceptance Criteria

1. Sidebar shows "Outreach" link with 📨 icon between Campaigns and Verticals
2. `/dashboard/outreach` page renders with launch form and (empty) campaigns table
3. Launch form has provider selector, campaign picker, targeting filters, API key input
4. Template preview loads and shows email sequence steps
5. Launch button calls `POST /outreach/launch` with correct payload
6. Launched campaigns stored in localStorage and stats fetched on page load
7. Campaign detail page shows analytics from provider API
8. Start/Pause buttons call correct endpoints
9. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Navigate to /dashboard/outreach
# Verify launch form renders with all fields
# Select a provider, pick a campaign, set targeting
# Click Launch (will fail if no API key — verify error message shows)
# Check that localStorage tracking works
```
