# Brief 16 — Layout & Navigation Overhaul

**Priority:** CRITICAL — This is the first thing users see and interact with
**Commercial Impact:** Navigation quality directly correlates with user retention. A collapsible sidebar with proper icons, mobile support, and breadcrumbs signals "real product" vs "hackathon project".
**Depends on:** Brief 15 (design system primitives must exist)

---

## Audit — Current Problems

1. **Emoji nav icons** — Sidebar uses 📊🚀📨🔗🏢📁⚙️ instead of proper Lucide SVG icons
2. **Fixed sidebar, no collapse** — Always 240px, no toggle, wastes screen real estate
3. **No mobile support** — Sidebar is `fixed left-0 w-60` with no responsive handling. Unusable on mobile.
4. **Empty header** — Left side of header is literally `<div />`. No breadcrumbs, no page context.
5. **No global search** — No Cmd+K command palette for quick navigation
6. **No notification bell** — No way to surface crawl completion, campaign results, etc.
7. **User avatar is a letter circle** — No gravatar, no proper dropdown menu
8. **Active state is weak** — Only a subtle bg tint distinguishes active nav from inactive

---

## Scope

### Files to CREATE

- `dashboard/components/layout/AppSidebar.tsx` — New collapsible sidebar with Lucide icons
- `dashboard/components/layout/MobileNav.tsx` — Slide-out drawer for mobile
- `dashboard/components/layout/Breadcrumbs.tsx` — Auto-generated breadcrumb trail
- `dashboard/components/layout/CommandPalette.tsx` — Cmd+K search/navigation
- `dashboard/components/layout/UserMenu.tsx` — Avatar dropdown (profile, settings, sign out)
- `dashboard/components/layout/NotificationBell.tsx` — Notification indicator
- `dashboard/contexts/SidebarContext.tsx` — Collapse state provider (persisted to localStorage)

### Files to MODIFY

- `dashboard/app/dashboard/layout.tsx` — Wire up new sidebar, header, providers
- `dashboard/components/Sidebar.tsx` — REPLACE with import from `AppSidebar`

### Files NOT to touch

- No page content files (those are Briefs 17–20)
- No Python/API files

---

## Implementation

### 1. Nav Icon Mapping

Replace every emoji with Lucide icon:

| Current | Route | New Icon |
|---------|-------|----------|
| 📊 | Overview | `LayoutDashboard` |
| 🚀 | Campaigns | `Rocket` |
| 📨 | Outreach | `Send` |
| 🔗 | CRM | `Link` |
| 🏢 | Verticals | `Building2` |
| 📁 | Portfolio | `Briefcase` |
| ⚙️ | Settings | `Settings` |

### 2. `AppSidebar.tsx` — Collapsible Sidebar

```
Structure:
┌──────────────────────┐
│  Logo + Collapse btn │  ← Brand area (clickable logo → /dashboard)
├──────────────────────┤
│  🔍 Search shortcut  │  ← "Search..." label, Cmd+K hint, opens CommandPalette
├──────────────────────┤
│  Nav items           │  ← Icon + label (label hidden when collapsed)
│  · Overview          │
│  · Campaigns         │
│  · Outreach          │
│  · CRM              │
│  · Verticals         │
│  · Portfolio         │
├──────────────────────┤
│  ── separator ──     │
│  · Settings          │
├──────────────────────┤
│  User profile row    │  ← Avatar, name, plan badge (collapsed = avatar only)
│  Sign out            │
└──────────────────────┘
```

Key behaviors:
- **Collapsed state:** Icons only, 64px wide, tooltips on hover
- **Expanded state:** Icons + labels, 240px wide
- **Toggle button:** Chevron at top-right of sidebar, or hamburger on mobile
- **Persistence:** Collapse state saved to `localStorage('sidebar_collapsed')`
- **Transition:** `transition-all duration-200` for smooth width change
- **Active indicator:** Left border accent bar (3px brand-500) + bg tint + bold text

### 3. `MobileNav.tsx` — Mobile Drawer

- Triggered by hamburger icon in header (visible only < md breakpoint)
- Full-screen overlay with slide-in from left
- Same nav items as sidebar
- Close on route change, Escape key, or overlay click
- Uses Radix Dialog under the hood

### 4. `Breadcrumbs.tsx` — Contextual Navigation

- Auto-generates from pathname
- Maps route segments to human-readable labels:
  - `/dashboard` → "Overview"
  - `/dashboard/campaigns` → "Overview / Campaigns"
  - `/dashboard/campaigns/new` → "Overview / Campaigns / New Campaign"
  - `/dashboard/campaigns/[id]` → "Overview / Campaigns / {campaign name}"
  - `/dashboard/outreach/[id]` → "Overview / Outreach / Campaign Details"
- Each segment is a clickable link except the last (current page)
- Rendered in the header bar, left side (replaces the empty `<div />`)

### 5. `CommandPalette.tsx` — Quick Navigation

- Opens with Cmd+K (Mac) / Ctrl+K (Windows)
- Search input at top
- Sections:
  - **Navigation** — All sidebar routes
  - **Quick Actions** — "New Campaign", "Push to CRM", etc.
  - **Recent** — Last 5 visited pages (stored in localStorage)
- Arrow key navigation, Enter to select
- Uses Radix Dialog + Combobox pattern
- Closes on selection or Escape

### 6. `UserMenu.tsx` — Header User Dropdown

Replace the current static avatar with:
- Clickable avatar + name
- Dropdown menu:
  - User name + email (non-clickable header)
  - Plan badge (e.g. "Pro" in brand color)
  - "Settings" link
  - "Billing" link
  - Separator
  - "Sign out" button
- Uses Radix DropdownMenu or a simple state-toggled div

### 7. Updated `dashboard/layout.tsx`

```
<SidebarProvider>
  <div className="min-h-screen bg-background">
    <AppSidebar />           {/* Desktop sidebar */}
    <MobileNav />            {/* Mobile drawer */}
    <main className="transition-all duration-200" style={{ marginLeft: collapsed ? 64 : 240 }}>
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <MobileMenuButton />  {/* Hamburger, visible < md */}
          <Breadcrumbs />
        </div>
        <div className="flex items-center gap-3">
          <NotificationBell />
          <UserMenu user={user} />
        </div>
      </header>
      <div className="p-6 lg:p-8">
        {children}
      </div>
    </main>
    <CommandPalette />
  </div>
</SidebarProvider>
```

---

## Acceptance Criteria

1. Sidebar uses Lucide icons — zero emojis in navigation
2. Sidebar collapses to icon-only mode (64px) and remembers state
3. Mobile: hamburger menu opens a full-screen drawer with nav
4. Breadcrumbs show correct path on every page
5. Cmd+K opens command palette with navigation search
6. User menu dropdown has profile, settings, sign out
7. Smooth transitions on sidebar collapse/expand
8. `npm run build` passes with zero errors
9. No visual regressions — all existing page content still renders correctly

## Testing

```bash
cd dashboard && npm run build
# Zero errors

npm run dev
# Desktop: click collapse button → sidebar shrinks to icons
# Desktop: Cmd+K → command palette opens
# Mobile (resize to < 768px): hamburger appears, sidebar hidden, drawer opens on click
# Navigate to /dashboard/campaigns/new → breadcrumb shows "Overview / Campaigns / New Campaign"
# Click user avatar → dropdown with settings + sign out
```
