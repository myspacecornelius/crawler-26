# Brief 18 — Table & Data Components Upgrade

**Priority:** MEDIUM-HIGH — Tables are the core data interaction surface
**Commercial Impact:** Buyers evaluate data products by how well they can explore the data. Sortable, selectable, exportable tables with proper loading states are table stakes (pun intended) for enterprise SaaS.
**Depends on:** Brief 15 (UI primitives), Brief 16 (layout)

---

## Audit — Current Problems

1. **No column sorting** — LeadTable, campaign tables, CRM history — none are sortable
2. **No row selection** — Cannot select leads for bulk actions (export, push to CRM, delete)
3. **No column visibility toggle** — All columns always visible, clutters narrow screens
4. **Filter bar wraps poorly** — LeadTable has 6 inline filters that overflow on smaller screens
5. **No CSV export button** — Users must use API to export data
6. **`alert()` for errors** — CRM page and campaigns page use `alert()` instead of toast
7. **Plain text loading** — All tables show "Loading..." text, no skeleton rows
8. **Pagination is basic** — Just Prev/Next, no page number indicators or jump-to-page
9. **No empty state illustrations** — Empty tables just say "No leads found" in gray text

---

## Scope

### Files to CREATE

- `dashboard/components/DataTable/DataTable.tsx` — Reusable table component with sorting, selection, pagination
- `dashboard/components/DataTable/TableSkeleton.tsx` — Skeleton loading rows
- `dashboard/components/DataTable/ColumnToggle.tsx` — Column visibility popover
- `dashboard/components/DataTable/BulkActions.tsx` — Floating action bar for selected rows
- `dashboard/components/DataTable/ExportButton.tsx` — CSV download button
- `dashboard/components/DataTable/FilterBar.tsx` — Collapsible filter section
- `dashboard/components/EmptyState.tsx` — Reusable empty state with icon + message + action

### Files to MODIFY

- `dashboard/components/LeadTable.tsx` — Refactor to use new DataTable components
- `dashboard/app/dashboard/campaigns/page.tsx` — Use DataTable, replace alert() with toast
- `dashboard/app/dashboard/crm/page.tsx` — Replace alert() with toast in push history
- `dashboard/app/dashboard/outreach/page.tsx` — Use DataTable for outreach records

### Files NOT to touch

- No Python/API files
- No layout files (Brief 16 handles those)

---

## Implementation

### 1. `DataTable.tsx` — Core Reusable Table

Props interface:

```typescript
interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
  className?: string;
  hidden?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  total: number;
  page: number;
  perPage: number;
  loading?: boolean;
  selectable?: boolean;
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
  onPageChange: (page: number) => void;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
  emptyMessage?: string;
  emptyAction?: React.ReactNode;
  rowKey: (row: T) => string;
}
```

Features:

- **Sortable headers** — Click column header to sort. Shows up/down chevron icon. Calls `onSort` callback.
- **Row selection** — Checkbox column on left. Header checkbox for select-all. Selection state managed by parent via `selectedIds`.
- **Hover highlight** — Subtle row hover effect.
- **Sticky header** — Table header stays visible when scrolling vertically within the card.
- **Responsive** — Horizontal scroll on overflow with scroll shadow indicators.

### 2. `TableSkeleton.tsx`

- Takes `columns: number` and `rows: number` props
- Renders animated skeleton rectangles matching table cell dimensions
- Varying widths to look natural (e.g., name column wider than score)

### 3. `ColumnToggle.tsx`

- Button with columns icon that opens a popover
- Checklist of all columns — toggle visibility
- "Reset" button to show all columns
- Persists preferences to localStorage per table ID

### 4. `BulkActions.tsx`

- Floating bar that appears when rows are selected
- Shows selection count: "{n} leads selected"
- Action buttons:
  - "Export Selected" — downloads CSV of selected rows
  - "Push to CRM" — navigates to CRM page with pre-selected leads
  - "Deselect All" — clears selection
- Slides up from bottom with animation
- Fixed position at bottom of viewport

### 5. `ExportButton.tsx`

- Button that generates a CSV from the current table data
- Uses `Blob` + `URL.createObjectURL` for client-side download
- Shows toast on success
- Props: `data`, `columns`, `filename`

### 6. `FilterBar.tsx`

- Collapsible filter section (collapsed by default, button to expand)
- Responsive grid layout (wraps properly on narrow screens)
- "Clear all" button when any filter is active
- Active filter count badge on the toggle button
- Renders filter inputs passed as children or via config

### 7. `EmptyState.tsx`

```typescript
interface EmptyStateProps {
  icon: React.ReactNode;        // Lucide icon
  title: string;
  description?: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}
```

- Centered layout with large icon, title, description, optional CTA button
- Used in all tables, search results, and list pages

### 8. Updated `LeadTable.tsx`

Refactor to compose the new primitives:

```
┌────────────────────────────────────────────────────┐
│  Leads  [🔍 Search...]  [Filters ▼ (3)]  [⬇ CSV] │
├────────────────────────────────────────────────────┤
│  Filter bar (collapsible):                         │
│  [Tier ▼] [Stage ▼] [Sector] [Geography] [Email ▼]│
├────────────────────────────────────────────────────┤
│  ☐  Name      Email        Role    Fund  Score Tier│
│  ☐  John...   john@...     Partner ABC   85   HOT  │
│  ☑  Jane...   jane@...     VP      XYZ   72   WARM │
│  ☑  Bob...    bob@...      Dir     DEF   61   COOL │
├────────────────────────────────────────────────────┤
│  Showing 1–20 of 5,108   [1] [2] [3] ... [256] [→]│
└────────────────────────────────────────────────────┘

┌─ Floating bulk actions (when rows selected) ──────┐
│  2 leads selected  [Export Selected] [Push to CRM] │
│  [Deselect All]                                    │
└────────────────────────────────────────────────────┘
```

### 9. Enhanced Pagination

Replace simple Prev/Next with:

- Page number buttons (show first, last, current ± 2)
- Ellipsis for gaps
- "Showing X–Y of Z" label
- Optional "per page" selector (20 / 50 / 100)

### 10. Replace all `alert()` calls

Grep and replace every `alert(...)` with `toast.error(...)` or `toast.success(...)` using the toast system from Brief 15.

Files with `alert()`:
- `dashboard/app/dashboard/campaigns/page.tsx` (lines 51, 61)
- `dashboard/app/dashboard/crm/page.tsx` (line 257)
- `dashboard/app/dashboard/settings/page.tsx` (lines 48, 59, 72)

---

## Acceptance Criteria

1. LeadTable uses new DataTable with sortable columns
2. Row selection works with select-all checkbox
3. Bulk actions bar appears when rows are selected
4. CSV export downloads a file with selected (or all) leads
5. Filter bar is collapsible and shows active filter count
6. Empty states have icon + message + CTA button
7. Skeleton loading replaces all "Loading..." text
8. Pagination shows page numbers (not just Prev/Next)
9. Zero `alert()` calls remain — all replaced with toast
10. `npm run build` passes with zero errors

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Navigate to /dashboard/campaigns → click column header → sorts
# Navigate to campaign detail → lead table: check rows → bulk bar appears
# Click "Export CSV" → file downloads
# Click "Filters" → filter bar expands with grid layout
# Empty campaign → shows illustration empty state
# grep -r "alert(" dashboard/app/ → should return zero results
```
