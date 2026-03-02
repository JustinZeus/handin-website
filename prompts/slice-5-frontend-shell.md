# Slice 5: Frontend Shell + Segment Renderers

## Role

You are a frontend TypeScript/Vue developer building the read-only public UI for a FastAPI-based academic submission website. The backend is complete — you are building the Vue 3 / Tailwind CSS v4 frontend that consumes its API.

## Objective

Create the read-only frontend shell: sidebar navigation, responsive layout, data fetching composable, TypeScript types, and all segment renderers. No admin functionality in this slice. All files must pass `vue-tsc --noEmit` (strict TypeScript).

## Architecture Reference

Read [PLAN.md](../PLAN.md) before starting. It contains the full architecture context: color system, layout specs, component hierarchy, and design decisions. Use it as the source of truth for any details not covered in this prompt.

## UI Decision-Making Policy

**When you encounter any ambiguity in visual design, layout, spacing, interaction patterns, or component behavior — use `AskUserQuestion` BEFORE implementing.** This is the prioritized method of resolution. Do not guess or pick defaults for subjective UI choices. Examples of when to ask:
- Exact spacing/padding values not specified in the prompt
- Animation/transition details (duration, easing, direction)
- Empty state presentation (what to show when no segments exist)
- Icon choices (hamburger style, close button style)
- Typography sizing not explicitly stated
- Any "or" choices in the prompt (e.g., "`<iframe>` or `<embed>`")
- Hover/focus state details beyond what's specified

Only proceed without asking when the prompt or PLAN.md gives an unambiguous, specific instruction.

## Coding Standards (mandatory)

- Vue 3 `<script setup lang="ts">` single-file components
- Strict TypeScript — no `any`, all props/emits typed
- Tailwind CSS v4 utility classes (no separate CSS files per component)
- Composables use `ref`/`computed`/`onMounted` from Vue — no Options API
- Components are small and focused — one responsibility per file
- Use `@/` path alias for imports (configured in vite.config.ts as `src/`)
- No external state management library — use composables with reactive state

## Step 0: Verify Existing Setup

Before writing any code, verify the frontend builds:

```bash
cd frontend && npm run build
```

Must exit cleanly. If it fails, fix before proceeding.

## Context: Backend API

The backend is running at `http://localhost:8000` (proxied via Vite dev server at `/api`).

### API Endpoints Used by This Slice

```
GET /api/site          → { "title": string }
GET /api/segments      → Array of SegmentResponse
GET /api/assets/{file} → Static file (binary)
```

### SegmentResponse Shape (from backend `models.py`)

```json
{
  "id": "uuid-string",
  "type": "markdown" | "pdf" | "video" | "audio" | "iframe" | "gallery",
  "sort_order": 0,
  "title": "Section Title",
  "content": "markdown text or URL or empty",
  "metadata": {},
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

**Content conventions by type:**
- `markdown` — `content` is raw markdown text
- `pdf` — `content` is the asset URL (e.g., `/api/assets/uuid.pdf`)
- `video` — `content` is the asset URL (e.g., `/api/assets/uuid.mp4`)
- `audio` — `content` is the asset URL (e.g., `/api/assets/uuid.mp3`)
- `iframe` — `content` is the embed URL (any external URL)
- `gallery` — `metadata` contains `{ "images": ["/api/assets/uuid.png", ...] }`

### Existing Frontend Files

**`frontend/src/style.css`** (already has theme):
```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";

@theme {
  --color-primary-50: #fffbeb;
  --color-primary-100: #fff3c4;
  --color-primary-200: #fce588;
  --color-primary-300: #ffcd00;
  --color-primary-400: #e6b800;
  --color-primary-500: #cc9900;
  --color-primary-600: #997300;
  --color-primary-700: #664d00;
}
```

**`frontend/vite.config.ts`** — has `@` alias to `src/`, API proxy to `localhost:8000`.

**`frontend/src/main.ts`** — mounts `App.vue` at `#app`.

**`frontend/src/App.vue`** — placeholder, will be replaced.

## UI Design Reference

### Color System
- Primary: golden yellow `#ffcd00` (primary-300) for accents and active states
- Neutrals: Tailwind `slate` — dark sidebar (`slate-900`), light content area (`slate-50`)
- Active nav item: `primary-300` left border + subtle bg highlight

### Layout — Sidebar Navigation

**Desktop (≥1024px):**
- Fixed left sidebar, `w-64`, `bg-slate-900`, full height
- Sidebar header: site title styled in `primary-300`, font bold
- Nav items: segment titles as anchor links, `text-slate-300` default, `text-white` on hover
- Active segment: `border-l-2 border-primary-300 bg-slate-800` + `text-white`
- Main content: `ml-64`, scrollable, segments as full-width cards on `bg-slate-50`

**Tablet (768–1023px):**
- Sidebar off-screen by default, toggle button to slide it in as overlay

**Mobile (<768px):**
- No sidebar visible. `MobileHeader` with hamburger icon at top
- Hamburger opens slide-out overlay nav (full-height, `bg-slate-900`)
- Close button or tap-outside to dismiss
- Segments stack vertically, full-width

## Step 1: Create TypeScript Types

### `frontend/src/types/segment.ts`

```typescript
export type SegmentType = "markdown" | "pdf" | "video" | "audio" | "iframe" | "gallery";

export interface Segment {
  id: string;
  type: SegmentType;
  sort_order: number;
  title: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SiteInfo {
  title: string;
}
```

## Step 2: Create Data Fetching Composable

### `frontend/src/composables/useSegments.ts`

Exports a composable function `useSegments()` that returns:
- `segments: Ref<Segment[]>` — list of segments, ordered by `sort_order`
- `siteTitle: Ref<string>` — site title (default: `"Handin"`)
- `loading: Ref<boolean>` — true while initial fetch is in progress
- `error: Ref<string | null>` — error message if fetch fails
- `refresh: () => Promise<void>` — re-fetch both endpoints

On mount (`onMounted`), fetch both `GET /api/site` and `GET /api/segments` in parallel using `Promise.all`. Use native `fetch()` — no axios.

## Step 3: Create Layout Components

### `frontend/src/components/layout/AppShell.vue`

Top-level layout component. Structure:
- Contains `SidebarNav` (desktop) and `MobileHeader` (mobile)
- Main content area as a `<slot />`
- Uses CSS breakpoints: sidebar visible `lg:block`, hidden below `lg`
- Mobile header visible below `lg`, hidden at `lg+`

### `frontend/src/components/layout/SidebarNav.vue`

Props:
- `segments: Segment[]`
- `siteTitle: string`
- `activeId: string | null`

Emits:
- `navigate(id: string)` — when a nav item is clicked

Renders:
- Site title in header area (`text-primary-300 font-bold text-lg`)
- List of segment titles as clickable items
- Active item has left border accent and bg highlight
- Scroll overflow if many segments

### `frontend/src/components/layout/MobileHeader.vue`

Props:
- `siteTitle: string`
- `segments: Segment[]`
- `activeId: string | null`

Manages its own open/closed state for the slide-out menu. Contains:
- Top bar with site title and hamburger button
- Slide-out overlay with same nav items as `SidebarNav`
- Click outside or close button dismisses the overlay

## Step 4: Create Segment Renderers

### `frontend/src/components/segments/SegmentRenderer.vue`

Props: `segment: Segment`

A switch component that renders the correct sub-renderer based on `segment.type`. Use a `v-if`/`v-else-if` chain or a dynamic component approach.

### `frontend/src/components/segments/SegmentList.vue`

Props: `segments: Segment[]`

Renders a vertical list of segments, each wrapped in a card-like container. Each segment card:
- Has an `id` attribute matching the segment ID (for anchor scroll)
- White background, rounded, subtle shadow
- Title as heading, then the renderer below

### Individual Renderers

Each takes a `segment: Segment` prop:

**`MarkdownSegment.vue`**
- Render `segment.content` as HTML using `marked` library
- Wrap output in a `prose` class div (Tailwind typography plugin)
- Use `v-html` with the parsed markdown

**`PdfSegment.vue`**
- Render an `<iframe>` or `<embed>` pointing to `segment.content` (the PDF URL)
- Full-width, reasonable height (e.g., `h-[600px]` or `aspect-[4/3]`)

**`VideoSegment.vue`**
- Render a `<video>` element with `controls`, `src` pointing to `segment.content`
- Full-width, responsive

**`AudioSegment.vue`**
- Render an `<audio>` element with `controls`, `src` pointing to `segment.content`
- Full-width

**`IframeSegment.vue`**
- Render an `<iframe>` with `src` from `segment.content`
- Full-width, reasonable height, border-none
- Add `sandbox` and `allow` attributes for security

**`GallerySegment.vue`**
- Read image URLs from `segment.metadata.images` (cast to `string[]`)
- Render as a responsive grid of `<img>` elements
- Grid: 2 columns on mobile, 3 on tablet, 4 on desktop
- Images have `object-cover`, rounded corners

## Step 5: Create HomePage View

### `frontend/src/views/HomePage.vue`

Wires everything together:
- Uses `useSegments()` composable
- Tracks `activeId` (string or null) — updates on scroll or nav click
- Shows loading spinner/skeleton while `loading` is true
- Shows error message if `error` is set
- Renders `AppShell` with `SegmentList` in the main slot

**Scroll tracking:** Use `IntersectionObserver` to detect which segment is currently visible and update `activeId` for sidebar highlighting.

## Step 6: Update App.vue

Replace the placeholder `App.vue` with:

```vue
<script setup lang="ts">
import HomePage from "@/views/HomePage.vue";
</script>

<template>
  <HomePage />
</template>
```

## Verification

After implementation, run:

```bash
cd frontend && npm run build
```

Must succeed with zero errors. Then verify visually:

```bash
cd frontend && npm run dev
```

Check:
1. Sidebar renders with site title and segment nav items (populate via backend or verify empty state)
2. Desktop: sidebar fixed left, content scrolls independently
3. Mobile (narrow viewport): hamburger menu, slide-out nav works
4. Each segment type renders correctly when data is present
5. Active segment highlights in sidebar on scroll
6. No TypeScript errors (`npm run type-check`)

## Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `frontend/src/types/segment.ts` |
| CREATE | `frontend/src/composables/useSegments.ts` |
| CREATE | `frontend/src/components/layout/AppShell.vue` |
| CREATE | `frontend/src/components/layout/SidebarNav.vue` |
| CREATE | `frontend/src/components/layout/MobileHeader.vue` |
| CREATE | `frontend/src/components/segments/SegmentRenderer.vue` |
| CREATE | `frontend/src/components/segments/SegmentList.vue` |
| CREATE | `frontend/src/components/segments/MarkdownSegment.vue` |
| CREATE | `frontend/src/components/segments/PdfSegment.vue` |
| CREATE | `frontend/src/components/segments/VideoSegment.vue` |
| CREATE | `frontend/src/components/segments/AudioSegment.vue` |
| CREATE | `frontend/src/components/segments/IframeSegment.vue` |
| CREATE | `frontend/src/components/segments/GallerySegment.vue` |
| CREATE | `frontend/src/views/HomePage.vue` |
| MODIFY | `frontend/src/App.vue` |
