# Brief 11 — Enhanced Campaign Creation Wizard

**Priority:** HIGH (Core revenue path — self-serve campaign creation is the #1 conversion driver)
**Commercial Impact:** The wizard exists but is minimal (name + vertical). Users need filtering, targeting, and estimated lead counts to feel confident hitting "Run." This is the difference between a demo tool and a paid product.

---

## Problem

The current `/dashboard/campaigns/new` page only collects a campaign name and vertical. Users cannot configure:
- Target tiers (HOT/WARM/COOL filtering)
- Minimum score threshold
- Sector/stage/geography targeting
- Estimated lead count before running (no "preview" step)
- CSV import as an alternative to crawling

The `createCampaign` API accepts a `config` JSON blob but the frontend passes `{}`.

## Scope

### Files to MODIFY
- `dashboard/app/dashboard/campaigns/new/page.tsx` — Replace with multi-step wizard
- `dashboard/lib/api.ts` — Add `importCSV()` function, add `previewCampaign()` if needed

### Files to CREATE
- `dashboard/components/CampaignWizard.tsx` — Reusable wizard component with steps

### Files NOT to touch
- Any Python files or API routers (the backend already accepts config via `CampaignCreate.config`)

---

## Implementation

### Multi-Step Wizard Flow

**Step 1: Name & Vertical** (already exists — keep this)
- Campaign name input
- Vertical card selector (fetched from `/verticals`)

**Step 2: Targeting Configuration**
- **Min Score** — slider from 0–100, default 0
- **Tiers** — multi-select checkboxes: HOT, WARM, COOL (default: all)
- **Sectors** — tag input (free-text, comma-separated), e.g. "AI, SaaS, Fintech"
- **Stage** — dropdown: Pre-Seed, Seed, Series A, Series B, Growth, Any
- **Geography** — text input for HQ filter, e.g. "US", "SF Bay Area"
- **Check Size** — text input, e.g. "$1M–$5M"

All these map to the `config` JSON blob sent to `createCampaign()`:
```typescript
const config = {
  min_score: minScore,
  tiers: selectedTiers,
  sectors: sectors.split(',').map(s => s.trim()).filter(Boolean),
  stage: stage || undefined,
  hq: geography || undefined,
  check_size: checkSize || undefined,
};
```

**Step 3: Review & Launch**
- Summary card showing: vertical, targeting criteria, estimated scope
- "Create Campaign" button → calls `createCampaign(name, vertical, config)`
- On success → redirect to campaign detail page
- Show credit cost estimate: "This campaign will use approximately X credits"

### Wizard Component Structure

```tsx
// dashboard/components/CampaignWizard.tsx
interface WizardStep {
  title: string;
  description: string;
}

const steps: WizardStep[] = [
  { title: 'Basics', description: 'Name your campaign and pick a vertical' },
  { title: 'Targeting', description: 'Configure lead filters and criteria' },
  { title: 'Review', description: 'Confirm and launch' },
];
```

Visual design:
- Horizontal step indicator at top (1 → 2 → 3) with active/completed states
- Each step is a card with back/next navigation
- Step 3 shows a summary table of all configured options
- Use existing Tailwind classes consistent with the rest of the dashboard
- "Back" button is gray outline, "Next"/"Launch" is brand-600

### CSV Import (Alternative Flow)

Add a toggle at the top of Step 1: **"Start from scratch"** vs **"Import existing CSV"**

If import mode:
- Show a file upload dropzone (drag & drop or click to browse)
- Accept `.csv` files only
- Show preview of first 5 rows after upload
- POST to a new frontend helper that reads the file and sends it

For the API call, add to `dashboard/lib/api.ts`:
```typescript
export async function importCSV(campaignId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/campaigns/${campaignId}/import`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) throw new Error('Import failed');
  return res.json();
}
```

**Note:** The backend import endpoint may not exist yet. If so, create a stub response in the frontend that shows "CSV import coming soon" with the upload UI disabled but visible. Do NOT create backend endpoints.

---

## Acceptance Criteria

1. Wizard has 3 steps with horizontal progress indicator
2. Step 2 shows all targeting fields: min_score, tiers, sectors, stage, geography, check_size
3. Step 3 shows a review summary of all configured options
4. `createCampaign` is called with the full `config` object
5. CSV import toggle is visible (can be stubbed if backend endpoint missing)
6. Back/Next navigation works, validation prevents advancing without required fields
7. Responsive layout — works on mobile (stack steps vertically)
8. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Navigate to /dashboard/campaigns/new
# Verify 3-step wizard renders
# Fill out Step 1, advance to Step 2
# Configure targeting, advance to Step 3
# Verify summary shows all options
# Click Create — verify API call includes config blob
```
