# Slice 7: Polish + Final Validation

## Role

You are a senior developer performing a final quality sweep on an academic group submission website. The backend (FastAPI + SQLite) and frontend (Vue 3 + TypeScript + Tailwind CSS v4) are fully implemented through Slices 0–6. Your job is to run every verification check, fix any issues found, and ensure the app works end-to-end.

## Objective

Run the full verification suite, fix any failures, and validate the complete user flow. The app must pass all automated checks with zero errors and work correctly in Docker.

## Architecture Reference

Read [PLAN.md](../PLAN.md) for full architecture context. Key deviations from the original plan:

### Layout
The layout uses a **horizontal top bar with tabs** (not a sidebar):
- `AppShell.vue` — sticky header (title bar `bg-primary-300` + nav bar) + dark mode toggle + TokenPrompt + AdminToolbar + back-to-top button + main content slot
- `SidebarNav.vue` — horizontal tab bar (desktop, `md+`)
- `MobileHeader.vue` — hamburger dropdown (mobile, `<md`)
- The entire header (title bar + nav) is `sticky top-0 z-20` — always visible when scrolling
- A floating back-to-top button appears after scrolling 300px (bottom-right, `bg-primary-300`)

### Backend Routes
- Collection routes use **trailing slashes** (`/api/segments/`, `/api/site/`, `/api/assets/`)
- Single-resource routes have **no trailing slash** (`/api/segments/{id}`, `/api/auth/verify`)
- Segment updates use **PATCH** (not PUT) — partial updates only

### Segment Types
Seven types: `markdown`, `pdf`, `video`, `audio`, `iframe`, `gallery`, `link`.
- `link` is nav-only — appears in tab bar/mobile menu as an external `<a target="_blank">`, not in the content area.

### Site Title
- Configurable via `HANDIN_SITE_TITLE` env var (default: `"Untitled Site"`)
- Stored in `config.py` as `Settings.site_title`, passed to `site_service.get_site_title()` as `default` kwarg
- Can also be overridden at runtime via `PUT /api/site/` (stored in DB, takes precedence over env var)

### Admin UI
- Lock icon in title bar → inline token input → admin controls appear
- Header icons (lock, dark mode toggle) use `text-slate-700` in both light and dark mode (yellow header stays consistent)
- AdminToolbar below tabs: "Editing" badge + "Add Segment" (modal) + "Logout"
- Inline SegmentEditor below each card with type-aware editing
- Grip-dot drag handles for reorder via `vuedraggable`
- Custom styled delete confirmation modal (not browser `confirm()`)

## Step 1: Backend Verification

Run these checks and fix any failures:

```bash
# Tests
uv run pytest backend/tests/ -v

# Linting
uv run ruff check backend/

# Type checking
uv run mypy --strict backend/app/
```

All must pass with zero errors. If any tests fail:
1. Read the failing test to understand what it expects
2. Read the relevant source code
3. Fix the source (not the test) unless the test itself is wrong
4. Re-run until clean

### Known Backend Files
```
backend/app/
├── main.py
├── config.py            # Settings: admin_token, site_title, data_dir, etc.
├── auth.py
├── models.py            # SegmentType enum includes LINK = "link"
├── database.py
├── routes/
│   ├── auth.py
│   ├── segments.py
│   ├── site.py          # Passes settings.site_title as default to service
│   └── assets.py
└── services/
    ├── segment_service.py
    ├── site_service.py  # get_site_title(db_path, *, default=DEFAULT_SITE_TITLE)
    └── asset_service.py
```

## Step 2: Frontend Verification

```bash
cd frontend && npm run build
```

This runs `vue-tsc --noEmit && vite build`. Must succeed with zero errors.

### Known Frontend Files
```
frontend/src/
├── composables/
│   ├── useSegments.ts
│   ├── useAdmin.ts       # Module-level reactive state, sessionStorage
│   ├── useAssetUpload.ts
│   └── useDarkMode.ts    # Class-based dark mode, localStorage persistence, system preference fallback
├── types/
│   ├── segment.ts        # SegmentType includes "link"
│   └── vuedraggable.d.ts
├── components/
│   ├── layout/
│   │   ├── AppShell.vue      # Sticky header, back-to-top button, scroll listener
│   │   ├── SidebarNav.vue    # Actually horizontal tab bar
│   │   └── MobileHeader.vue  # Hamburger dropdown
│   ├── segments/
│   │   ├── SegmentList.vue   # Draggable (admin) or plain (read-only), filters out link segments from content
│   │   ├── SegmentRenderer.vue
│   │   ├── MarkdownSegment.vue
│   │   ├── PdfSegment.vue
│   │   ├── VideoSegment.vue
│   │   ├── AudioSegment.vue
│   │   ├── IframeSegment.vue
│   │   └── GallerySegment.vue
│   └── admin/
│       ├── TokenPrompt.vue
│       ├── AdminToolbar.vue
│       ├── SegmentEditor.vue
│       ├── AssetUploader.vue
│       └── AddSegmentModal.vue
└── views/
    └── HomePage.vue
```

## Step 3: Docker Build + Smoke Test

```bash
docker compose up --build -d
```

Must build and start without errors. Then verify:

```bash
# Health check — site loads
curl -s http://localhost:8000/api/site/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)"

# Auth verify works
curl -s http://localhost:8000/api/auth/verify -H "Authorization: Bearer changeme" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['valid']==True; print('Auth OK')"

# Create a test segment
curl -s -X POST http://localhost:8000/api/segments/ \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"type":"markdown","title":"Test","content":"# Hello"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Created segment {d[\"id\"]}')"

# Create a link segment
curl -s -X POST http://localhost:8000/api/segments/ \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"type":"link","title":"GitHub","content":"https://github.com"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Created link {d[\"id\"]}')"

# List segments
curl -s http://localhost:8000/api/segments/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} segments')"

# Frontend loads
curl -s http://localhost:8000/ | head -5
```

Clean up test data after verification:
```bash
docker compose down
```

## Step 4: Edge Case Review

Check these specific scenarios and fix if broken:

1. **Empty state**: With no segments, the page should show "No content yet" (not crash or show blank).
2. **Link segments in read-only mode**: Should appear in nav tabs but NOT in the content area.
3. **Link segments in admin mode**: Should appear in the draggable list with URL displayed, editable via SegmentEditor.
4. **Gallery segment with no images**: Should not crash — show empty state or just the upload zone.
5. **Admin toolbar visibility**: Must be completely hidden when not authenticated.
6. **Token persistence**: After page reload, if token was valid, admin state should restore from sessionStorage.
7. **Concurrent safety**: Two simultaneous segment creates should not corrupt sort_order.
8. **Site title env var**: With `HANDIN_SITE_TITLE=MyCourseName`, the default title should be "MyCourseName" (not "Untitled Site"). Once overridden via `PUT /api/site/`, the DB value takes precedence.

## Step 5: Visual Polish Check

Review the Tailwind classes in these components for consistency:

1. **Spacing**: All segment cards should have consistent padding (`p-6`), gap between cards (`space-y-6`).
2. **Colors**: Primary color usage should be consistent — `bg-primary-300` for brand, `primary-50`/`primary-100` for editor backgrounds, `primary-400` for hover states. The header bar keeps its yellow `bg-primary-300` in both light and dark mode (university branding).
3. **Typography**: Title bar uses `text-xl font-bold`, segment titles use `text-xl font-semibold`, body text uses default size.
4. **Responsive**: Tab bar hidden on mobile, mobile hamburger hidden on desktop. Content area is `max-w-6xl` centered.
5. **Shadows**: Segment cards use `shadow-md` (+ `dark:shadow-slate-950/30` in dark mode).
6. **Dark mode**: All components have `dark:` variant classes. Toggle is a sun/moon icon in the title bar. Uses class-based dark mode via `@custom-variant dark (&:where(.dark, .dark *))` in style.css. Preference stored in localStorage, falls back to system preference.
7. **Sticky header**: Entire header (title bar + nav) sticks to top on scroll. Back-to-top button appears after 300px scroll.
8. **Admin controls**: Edit pencil icons should be `text-slate-300 hover:text-primary-300` (muted by default). Drag handles should match.
9. **Header icons**: Lock icon and dark mode toggle use `text-slate-700` (no dark: overrides) since they sit on the always-yellow header.

## Verification Checklist

All of these must be true when you're done:

- [ ] `uv run pytest backend/tests/ -v` — all pass
- [ ] `uv run ruff check backend/` — clean
- [ ] `uv run mypy --strict backend/app/` — clean
- [ ] `cd frontend && npm run build` — zero errors
- [ ] `docker compose up --build` — builds and runs
- [ ] Dark mode toggle works, persists across reload, respects system preference on first visit
- [ ] Header bar stays yellow (`bg-primary-300`) in both light and dark mode
- [ ] Sticky header stays visible when scrolling, back-to-top button appears
- [ ] `HANDIN_SITE_TITLE` env var sets the default site title
- [ ] Read-only mode shows zero admin UI (only lock icon + dark mode toggle in header)
- [ ] Admin mode: all CRUD operations work
- [ ] Link segments appear in nav only
- [ ] Drag-and-drop reorder persists after refresh

## Files You May Modify

Any file in the project. Prefer minimal, targeted fixes. Do not refactor working code unnecessarily.
