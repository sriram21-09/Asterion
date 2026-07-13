# Asterion Platform — UI User Documentation

> **Version:** v0.2.0 — Week 2 Sprint  
> **Stack:** React 19, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS v4, Sonner

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Layout & Navigation](#layout--navigation)
4. [Pages Reference](#pages-reference)
   - [Dashboard](#dashboard)
   - [Case Management](#case-management)
   - [Scenario Configurator](#scenario-configurator)
   - [Reports](#reports)
   - [Settings](#settings)
5. [UI Component Library](#ui-component-library)
6. [Theme System](#theme-system)
7. [Keyboard Shortcuts & Accessibility](#keyboard-shortcuts--accessibility)
8. [Error Handling & Feedback](#error-handling--feedback)
9. [Known Limitations](#known-limitations)

---

## Overview

The Asterion frontend is a single-page React application providing the investigation and engineering workspace for RF-based device localization. It communicates with the FastAPI backend via a centralized Axios client (`/api/v1`).

**Key architectural decisions:**
- **TanStack Query v5** — all server state (cases, scenarios) is managed via query/mutation hooks with automatic cache invalidation
- **Zustand** — lightweight client-only state for theme, sidebar, and app settings
- **Sonner** — toast notifications for all async feedback (success, error)
- **Tailwind CSS v4** with a custom design token system via `@theme` — all colors, shadows, and animations are defined as CSS custom properties

---

## Getting Started

### Local Development

```bash
cd frontend
cp .env.example .env          # set VITE_API_URL if backend is not on port 8000
npm install
npm run dev                   # starts on http://localhost:3000
```

### Production Build

```bash
npm run build                 # TypeScript compile (tsc -b) + Vite bundle → dist/
npm run preview               # preview the production bundle locally
```

### Linting

```bash
npm run lint                  # oxlint — zero-warning policy
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Full base URL for the backend API |

---

## Layout & Navigation

### Shell Layout

The `DashboardLayout` renders a two-column shell:

```
┌─────────────────────────────────────┐
│  SIDEBAR (256px, fixed on desktop)  │
│  ─────────────────────────────────  │
│  • ASTERION logo                    │
│  • Dashboard                        │
│  • Cases                            │
│  • Scenarios                        │
│  • Reports                          │
│  • Settings                         │
│  ─────────────────────────────────  │
│  Researcher Mode footer             │
├─────────────────────────────────────┤
│  HEADER (64px, full-width)          │
│  Breadcrumb        Theme · Status · │
│  ─────────────────────────────────  │
│  MAIN CONTENT (scrollable)          │
│                                     │
└─────────────────────────────────────┘
```

**Mobile:** The sidebar slides in from the left on hamburger tap. A backdrop overlay closes it. The hamburger button exposes `aria-expanded` linked to actual sidebar state.

### Active Route Highlighting

The sidebar uses `useLocation()` to highlight the currently active route with a left accent bar and brand-primary text color.

---

## Pages Reference

### Dashboard

**Route:** `/`  
**Title:** `Dashboard — Asterion`

The landing page provides:

| Section | Description |
|---|---|
| **Hero Banner** | Version badge (`v0.2.0`), platform name, and summary |
| **Quick Stats** | Live counts from the API: Active Cases, Scenarios, Localizations (placeholder), System Status |
| **Platform Modules** | Grid of 4 feature cards with shipped/in-progress states |

**Quick Stats** are driven by the `useCases()` and `useScenarios()` hooks. Active cases excludes `closed` and `archived` statuses.

**Platform Module card states:**

| State | Border | Icon Background | Badge |
|---|---|---|---|
| Shipped | `success/20` green | `success/10` | Green `Shipped ✓` |
| In Progress | `border-primary` blue | `surface-secondary` | Muted `Week 2 — In Progress` |

---

### Case Management

**Route:** `/cases`  
**Title:** `Cases — Asterion`

Full CRUD interface for investigation cases.

#### Views

| View | Toggle | Description |
|---|---|---|
| **List** (default) | `≡` icon | Sortable table with ID, title, status badge, date, and action buttons |
| **Grid** | `⊞` icon | Card grid showing title, description preview, status, date |

The view toggle only appears when at least one case exists.

#### Case Fields

| Field | Required | Values |
|---|---|---|
| **Title** | ✅ Yes | Free text |
| **Status** | No (default: `open`) | `open`, `in_progress`, `closed`, `archived` |
| **Description** | No | Free text (optional) |

#### Status Colors

| Status | Color |
|---|---|
| `open` | Green |
| `in_progress` | Blue |
| `closed` | Gray |
| `archived` | Amber |

#### User Flows

**Create a Case:**
1. Click **Create Case** (top-right)
2. Fill in title (required), status, and optional description
3. Click **Create Case** in the modal — success toast confirms creation

**Delete a Case:**
1. Click the 🗑️ trash icon on any row/card
2. Confirm in the **Delete Case** dialog
3. Success toast confirms deletion; the list refreshes automatically

---

### Scenario Configurator

**Route:** `/scenarios`  
**Title:** `Scenarios — Asterion`

Manages RF simulation scenario configurations. Functionally mirrors the Cases page.

#### Scenario Fields

| Field | Required | Description |
|---|---|---|
| **Name** | ✅ Yes | Human-readable scenario identifier |
| **Description** | No | Terrain conditions, objectives, notes |

#### User Flows

**Create a Scenario:**
1. Click **Add Scenario**
2. Enter name and optional description
3. Click **Create Scenario** — success toast + list refresh

**Delete a Scenario:**
1. Click 🗑️ on any row/card
2. Confirm in dialog — this permanently removes all transmitter/signal configurations

---

### Reports

**Route:** `/reports`  
**Title:** `Reports — Asterion`

Placeholder page for upcoming sprint. Report compilation, export formats, and mathematical analytics summaries are scheduled for Week 2+.

---

### Settings

**Route:** `/settings`  
**Title:** `Settings — Asterion`

Placeholder page. The `useAppSettingsStore` (Zustand, persisted) already scaffolds:
- `apiBaseUrl` — backend endpoint override
- `mapTileProvider` — `osm` | `carto-dark` | `carto-light`
- `defaultMapCenter` — `[lat, lng]` (default: center of India)
- `defaultMapZoom` — integer zoom level

The Settings UI to edit these will be wired in a future sprint.

---

## UI Component Library

All components are exported from `@/components/ui` for import convenience.

### `<Button>`

A polymorphic, accessible button with 4 variants and 3 sizes.

```tsx
import { Button } from '@/components/ui'

<Button variant="primary" size="md" isLoading={false} leftIcon={<Plus />}>
  Create Case
</Button>
```

| Prop | Type | Default | Description |
|---|---|---|---|
| `variant` | `'primary' \| 'secondary' \| 'ghost' \| 'danger'` | `'primary'` | Visual style |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Button size |
| `isLoading` | `boolean` | `false` | Shows spinner, disables button |
| `leftIcon` | `ReactNode` | — | Icon rendered before children |
| `rightIcon` | `ReactNode` | — | Icon rendered after children |

---

### `<Badge>`

Compact status chip with optional dot indicator.

```tsx
<Badge variant="success" dot>Open</Badge>
<Badge variant="danger">Archived</Badge>
```

**Variants:** `default` | `success` | `warning` | `danger` | `info` | `muted`

---

### `<LoadingSpinner>`

Accessible animated spinner for inline and overlay use.

```tsx
<LoadingSpinner size="md" label="Fetching cases…" />
```

**Sizes:** `xs` | `sm` | `md` | `lg` | `xl`

---

### `<LoadingPage>`

Full-screen loading view for route-level suspense or initial app load.

```tsx
<LoadingPage label="Loading Asterion…" />
```

Renders the brand `Radio` icon with a pulse ring and a spinner below it.

---

### `<SkeletonCard>` / `<SkeletonGrid>`

Shimmer placeholder cards displayed while data is fetching.

```tsx
// Single card
<SkeletonCard lines={3} showHeader showBadge />

// Grid of N cards
<SkeletonGrid count={6} />
```

`SkeletonGrid` renders a responsive 3-column grid of `SkeletonCard` components.

---

### `<ErrorCard>`

Inline error state with retry button.

```tsx
<ErrorCard
  title="Error loading cases"
  message={error.message}
  onRetry={refetch}
/>
```

| Prop | Type | Description |
|---|---|---|
| `title` | `string` | Bold red error title |
| `message` | `string` | Descriptive explanation |
| `onRetry` | `() => void` | If provided, shows a "Try again" button |

---

### `<ConfirmDialog>`

Accessible modal replacing `window.confirm()`.

```tsx
<ConfirmDialog
  title="Delete Case"
  message="This action cannot be undone."
  confirmLabel="Delete Case"
  isDangerous
  isLoading={deleteCase.isPending}
  onConfirm={handleDeleteConfirm}
  onCancel={() => setDeleteTarget(null)}
/>
```

**Accessibility features:**
- Auto-focuses the Cancel button on mount (safe default)
- `Escape` key closes the dialog
- Clicking the backdrop closes the dialog
- Uses `role="dialog"` and `aria-modal="true"`

---

## Theme System

Asterion uses a **dual-mode design token system** built on CSS custom properties via Tailwind v4's `@theme` directive.

### Switching Themes

Click the **☀/🌙** icon in the top-right header. The chosen theme is persisted to `localStorage` under the key `asterion-theme` and restored on next load (no flash of unstyled content).

The store applies the theme class to `<html>`:
- `html.dark` — dark mode (default)
- `html.light` — light mode

### Token Reference

| Token | Dark | Light | Usage |
|---|---|---|---|
| `surface-base` | `#0e1117` | `#f6f7fb` | Page background |
| `surface-primary` | `#121722` | `#ffffff` | Cards, panels |
| `surface-secondary` | `#171e2e` | `#f0f2f8` | Inputs, table headers |
| `brand-primary` | Purple `oklch(0.585 0.233 264)` | Slightly darker | CTAs, active states |
| `brand-secondary` | Lighter purple | Darker | Icons, labels |
| `content-primary` | Near-white | Near-black | Main text |
| `content-tertiary` | Muted gray | Muted gray | Labels, placeholders |
| `success` | Green | Green | Open status, success toasts |
| `danger` | Red | Red | Errors, delete actions |
| `warning` | Amber | Amber | Warnings, archived status |

### Smooth Theme Transitions

The `DashboardLayout` applies a `theme-transition` class to the root `<div>` for 400ms whenever the theme changes. This class adds CSS transitions to `background-color`, `border-color`, and `color` across all children for a smooth crossfade — then removes itself to avoid transition cost on every render.

---

## Keyboard Shortcuts & Accessibility

| Interaction | Behavior |
|---|---|
| `Escape` | Closes any open modal (CaseForm, ScenarioForm, ConfirmDialog) |
| `Tab` | Focus-trapped inside modals |
| Sidebar hamburger | `aria-expanded` reflects actual open state |
| Error dialogs | `role="alert"` so screen readers announce them |
| Loading spinners | `role="status"` + `aria-label` for screen readers |
| Skeleton cards | `aria-busy="true"` + `aria-label="Loading…"` |
| Confirm dialog | Auto-focuses Cancel button (safe default prevents accidental destructive action) |

---

## Error Handling & Feedback

### API Error Normalization

`src/lib/api.ts` contains a response interceptor that normalizes all backend errors into a human-readable `error.message`:

| Backend Response | Normalized To |
|---|---|
| `{ error: { message: "..." } }` | Uses `error.message` directly |
| `{ detail: "string" }` | FastAPI plain detail |
| `{ detail: [{ msg: "..." }, ...] }` | FastAPI 422 — joined with `;` |
| No response (network error) | `"Unable to reach the backend. Is the server running?"` |

All TanStack Query `onError` handlers in `useCases.ts` and `useScenarios.ts` call `toast.error(error.message)` — the normalized message surfaces automatically.

### APIResponse Unwrapping

The interceptor automatically detects the backend's `{ success: true, data: [...] }` envelope format and unwraps it so hooks receive the raw array/object directly.

### Toast Notifications

All user-facing feedback uses **Sonner** toasts (top-right, 4 second duration):

| Event | Toast Type |
|---|---|
| Case/Scenario created | ✅ Success |
| Case/Scenario deleted | ✅ Success |
| Create failed | ❌ Error with message |
| Delete failed | ❌ Error with message |

---

## Known Limitations

| Area | Limitation | Planned Fix |
|---|---|---|
| Settings page | UI controls not yet wired to `useAppSettingsStore` | Week 3 sprint |
| Reports page | Placeholder only — no data export | Week 2+ sprint |
| Cases — View Details | Eye button visible but no detail route exists | Pending case detail page |
| Scenarios — View Details | Same — no detail route | Pending scenario detail page |
| Leaflet map | Installed but not yet rendered in any page | Week 2 localization view |
| Auth | No login/token flow — all endpoints open | Future sprint |
