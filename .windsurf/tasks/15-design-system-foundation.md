# Brief 15 — Design System Foundation

**Priority:** CRITICAL — Every other UI brief depends on this
**Commercial Impact:** A professional design system is the difference between "side project" and "enterprise SaaS". This brief establishes the visual foundation that all subsequent UI work builds on.

---

## Audit — Current Problems

1. **Emoji icons everywhere** — Sidebar, StatsCard, nav all use 📊🚀📨 instead of proper SVG icons. Lucide is installed but barely used (only in CampaignWizard).
2. **No shared UI primitives** — Every page hand-rolls its own buttons, inputs, badges, cards with raw Tailwind. Styles are inconsistent across pages.
3. **No proper font** — Using system defaults. No `@next/font` or Google Fonts integration.
4. **No CSS custom properties** — Colors are hardcoded Tailwind classes. No dark mode path. No theming.
5. **No loading skeletons** — All pages show "Loading..." text strings with `animate-pulse`.
6. **No toast/notification system** — Uses `alert()` for errors (CRM page, campaign actions).
7. **No tooltips** — Complex UIs have no contextual help.
8. **Inconsistent focus rings** — Some inputs use `focus:ring-brand-500`, others `focus:ring-blue-500`.

---

## Scope

### Files to CREATE
- `dashboard/components/ui/Button.tsx`
- `dashboard/components/ui/Badge.tsx`
- `dashboard/components/ui/Input.tsx`
- `dashboard/components/ui/Select.tsx`
- `dashboard/components/ui/Card.tsx`
- `dashboard/components/ui/Skeleton.tsx`
- `dashboard/components/ui/Toast.tsx`
- `dashboard/components/ui/Tooltip.tsx`
- `dashboard/components/ui/Dialog.tsx`
- `dashboard/components/ui/index.ts` (barrel export)
- `dashboard/lib/cn.ts` (clsx + twMerge utility)

### Files to MODIFY
- `dashboard/app/layout.tsx` — Add Inter font via `next/font/google`, add ToastProvider
- `dashboard/app/globals.css` — Add CSS custom properties for colors, add font smoothing
- `dashboard/tailwind.config.ts` — Extend with CSS variable references, add animations
- `dashboard/package.json` — Add `@radix-ui/react-toast`, `@radix-ui/react-tooltip`, `@radix-ui/react-dialog`

### Files NOT to touch
- No page files in this brief — those are updated in Briefs 16–20
- No Python/API files

---

## Implementation

### 1. `dashboard/lib/cn.ts` — Utility

```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 2. `dashboard/app/layout.tsx` — Font + Providers

```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/Toast';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'LeadFactory',
  description: 'Multi-vertical lead generation platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
```

### 3. `dashboard/app/globals.css` — Design Tokens

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 98%;
    --foreground: 220 14% 10%;
    --card: 0 0% 100%;
    --card-foreground: 220 14% 10%;
    --primary: 226 70% 55.5%;
    --primary-foreground: 0 0% 100%;
    --secondary: 220 14% 96%;
    --secondary-foreground: 220 14% 10%;
    --muted: 220 14% 96%;
    --muted-foreground: 220 8% 46%;
    --accent: 220 14% 96%;
    --accent-foreground: 220 14% 10%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --border: 220 13% 91%;
    --input: 220 13% 91%;
    --ring: 226 70% 55.5%;
    --radius: 0.625rem;
    --success: 160 84% 39%;
    --warning: 38 92% 50%;
  }
}

body {
  @apply bg-[hsl(var(--background))] text-[hsl(var(--foreground))] antialiased;
  font-feature-settings: "cv02", "cv03", "cv04", "cv11";
}
```

### 4. `dashboard/tailwind.config.ts` — Extended Config

Extend with:
- CSS variable color references (e.g. `primary: 'hsl(var(--primary))'`)
- Font family: `sans: ['var(--font-inter)', ...defaultTheme.fontFamily.sans]`
- Keyframe animations: `fadeIn`, `slideUp`, `slideDown`, `scaleIn`
- Border radius using `--radius` variable

### 5. UI Components

#### `Button.tsx`
- Variants: `default`, `secondary`, `outline`, `ghost`, `destructive`, `link`
- Sizes: `sm`, `default`, `lg`, `icon`
- Loading state with spinner
- Uses `cn()` for class merging
- Forwards ref

#### `Badge.tsx`
- Variants: `default`, `success`, `warning`, `destructive`, `outline`
- Sizes: `sm`, `default`

#### `Input.tsx`
- Consistent focus ring using `--ring` variable
- Error state styling
- Left/right icon slot
- Forwards ref

#### `Select.tsx`
- Styled wrapper around native `<select>`
- Consistent with Input styling
- Chevron icon

#### `Card.tsx`
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
- Compound component pattern

#### `Skeleton.tsx`
- Animated pulse skeleton for text, circle, card shapes
- `SkeletonText`, `SkeletonCircle`, `SkeletonCard`

#### `Toast.tsx`
- Based on Radix UI Toast primitive
- Variants: `default`, `success`, `error`, `warning`
- Auto-dismiss with configurable duration
- `useToast()` hook for imperative usage
- `<Toaster />` provider component

#### `Tooltip.tsx`
- Based on Radix UI Tooltip primitive
- Consistent styling
- `<Tooltip content="..."><TriggerElement /></Tooltip>` API

#### `Dialog.tsx`
- Based on Radix UI Dialog primitive
- `Dialog`, `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter`
- Overlay with backdrop blur
- Keyboard accessible (Esc to close)

---

## Acceptance Criteria

1. `npm run build` passes with zero errors
2. All UI primitives exported from `@/components/ui`
3. Inter font loads correctly on all pages
4. `cn()` utility available at `@/lib/cn`
5. CSS variables defined for all design tokens
6. Toast system works — `useToast()` can show success/error toasts
7. Skeleton components render animated placeholders
8. No visual regressions on existing pages (this brief only ADDS, doesn't modify pages)

## Dependencies

```bash
npm install @radix-ui/react-toast @radix-ui/react-tooltip @radix-ui/react-dialog
```

## Testing

```bash
cd dashboard && npm run build
# Zero errors, 15/15 pages generated
```

---

## Notes for Sub-Agent
- Do NOT modify any existing page files — those are covered in Briefs 16–20
- DO create all component files even if no page uses them yet
- Use the shadcn/ui pattern (Radix primitives + Tailwind) but hand-build, do NOT run `npx shadcn-ui init`
- Every component must be a named export AND default export for flexibility
