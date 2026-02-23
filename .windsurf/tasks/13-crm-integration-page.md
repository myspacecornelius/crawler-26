# Brief 13 — CRM Integration Page (HubSpot / Salesforce)

**Priority:** MEDIUM (Enterprise unlock — required to justify Pro/Scale/Enterprise pricing tiers)
**Commercial Impact:** CRM push transforms LeadFactory from a standalone tool into a platform embedded in the customer's workflow. Key for enterprise sales, SOC2 discussions, and reducing "export CSV and forget" churn. Second to outreach because CRM push is a one-time sync, not an ongoing engagement loop.

---

## Problem

The backend has a complete CRM router (`api/routers/crm.py`) with 4 endpoints:
- `POST /crm/push` — Push leads to HubSpot or Salesforce
- `POST /crm/status` — Check status of pushed CRM records
- `GET /crm/fields/{provider}` — Get CRM field definitions (for mapping UI)
- `GET /crm/field-mapping/defaults` — Get default lead→CRM field mapping

None are surfaced in the dashboard.

## Scope

### Files to CREATE
- `dashboard/app/dashboard/crm/page.tsx` — CRM integration hub

### Files to MODIFY
- `dashboard/lib/api.ts` — Add CRM API functions
- `dashboard/components/Sidebar.tsx` — Add "CRM" nav link

### Files NOT to touch
- Any Python files or API routers

---

## Implementation

### 1. `dashboard/lib/api.ts` — Add CRM functions

```typescript
// CRM
export async function pushToCRM(data: {
  provider: string;
  campaign_id: string;
  test_mode?: boolean;
  min_score?: number;
  tiers?: string[];
  field_mapping?: Record<string, string>;
  custom_fields?: Record<string, string>;
  api_key?: string;
  sf_client_id?: string;
  sf_client_secret?: string;
  sf_instance_url?: string;
  sf_access_token?: string;
}) {
  return fetchAPI('/crm/push', { method: 'POST', body: JSON.stringify(data) });
}

export async function getCRMStatus(data: {
  provider: string;
  crm_ids: string[];
  test_mode?: boolean;
  api_key?: string;
}) {
  return fetchAPI('/crm/status', { method: 'POST', body: JSON.stringify(data) });
}

export async function getCRMFields(provider: string, testMode = true) {
  return fetchAPI(`/crm/fields/${provider}?test_mode=${testMode}`);
}

export async function getDefaultFieldMapping() {
  return fetchAPI('/crm/field-mapping/defaults');
}
```

### 2. `dashboard/components/Sidebar.tsx` — Add nav link

Add to `nav` array after Outreach:
```typescript
{ href: '/dashboard/crm', label: 'CRM', icon: '🔗' },
```

### 3. `dashboard/app/dashboard/crm/page.tsx` — CRM Hub

#### Layout: 3 Sections

**Section 1: Provider Setup** (always visible)
- Two provider cards side by side: HubSpot (orange accent) and Salesforce (blue accent)
- Each card shows:
  - Provider logo/icon and name
  - Connection status indicator (connected/not connected)
  - Credentials input:
    - **HubSpot:** API Key (private app token) — single password input
    - **Salesforce:** Instance URL, Client ID, Client Secret OR Access Token — collapsible form
  - "Test Connection" button → calls `getCRMFields(provider)` — if it returns fields, show green "Connected ✓"
  - Store credentials in localStorage (keys: `crm_hubspot_api_key`, `crm_sf_*`)
  - ⚠️ Show security note: "Credentials are stored in your browser only. For production use, configure via environment variables on the server."

**Section 2: Push Leads** (card below provider setup)
- **Source campaign** dropdown — fetch completed campaigns via `listCampaigns()`
- **Provider** — auto-selected from Section 1, or radio toggle
- **Targeting:**
  - Min score slider (0–100)
  - Tier checkboxes (HOT, WARM, COOL)
- **Field Mapping** — expandable accordion:
  - Fetch defaults via `getDefaultFieldMapping()`
  - Show table: LeadFactory Field → CRM Field
  - Each row has a dropdown for the CRM field (populated from `getCRMFields()`)
  - Allow overriding defaults
- **Custom Fields** — key/value pairs, "Add field" button
- **Test Mode** toggle — "Validate mapping without pushing to CRM"
- **Push button** → calls `pushToCRM()`:
  - While running: show spinner + "Pushing X leads..."
  - On success: show summary card — created / updated / failed counts
  - On error: show error message from API

**Section 3: Push History** (below push section)
- Table of recent pushes (store in localStorage similar to outreach):
  ```typescript
  interface CRMPushRecord {
    provider: string;
    campaign_id: string;
    campaign_name: string;
    pushed_at: string;
    total: number;
    created: number;
    updated: number;
    failed: number;
  }
  ```
- Columns: Date, Campaign, Provider, Total, Created, Updated, Failed, Status
- "Check Status" button on each row → calls `getCRMStatus()` with stored CRM IDs

#### Visual Design
- Provider cards: white bg, colored left border (orange for HubSpot, blue for Salesforce)
- Field mapping table: compact, monospace font for field names
- Push result summary: green for success, amber for partial, red for failure
- Match dashboard styling: rounded-xl cards, gray-200 borders

---

## Acceptance Criteria

1. Sidebar shows "CRM" link with 🔗 icon
2. Provider setup cards render for HubSpot and Salesforce
3. Test Connection button validates credentials via `getCRMFields()`
4. Push form shows campaign picker, targeting, field mapping, and custom fields
5. Field mapping table loads defaults and allows CRM field override via dropdown
6. Test mode toggle works — shows "test mode" badge on push
7. Push button calls `POST /crm/push` with full payload including field_mapping
8. Push result summary shows created/updated/failed counts
9. Push history persists in localStorage and renders in table
10. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Navigate to /dashboard/crm
# Verify provider cards render
# Click "Test Connection" on HubSpot (will fail without key — verify error shows)
# Toggle test_mode ON, select a campaign, click Push
# Verify API call is made with test_mode=true
# Check push history table updates
```
