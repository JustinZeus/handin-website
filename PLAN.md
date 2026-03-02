# Academic Group Submission Website — Architecture Plan

> **Implementation guide:** See [SLICES.md](SLICES.md) for the step-by-step slice-based implementation order.

## Context

Build a lightweight, containerized CMS for academic group submissions. The site aggregates multimodal content (PDFs, video, audio, markdown, embeds, galleries) into a single web page. Admin access is gated by a shared token — no user accounts. Multiple students may edit concurrently. All data persists in SQLite + uploaded assets on a Docker volume.

**Stack:** Python 3.12+ / FastAPI, Vue 3 / TypeScript / Tailwind CSS, SQLite (stdlib), single Docker container.

---

## Project Structure

```
handin-website/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .gitignore
├── coding-style.md
├── PLAN.md                      # This file — architecture reference
├── SLICES.md                    # Slice-based implementation guide
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, static mounts, lifespan
│   │   ├── config.py            # pydantic-settings: token, paths, limits
│   │   ├── auth.py              # require_admin dependency (token via query/header)
│   │   ├── models.py            # Pydantic models for requests/responses
│   │   ├── database.py          # SQLite connection, schema init, WAL mode
│   │   ├── routes/
│   │   │   ├── segments.py      # CRUD + reorder endpoints
│   │   │   └── assets.py        # Upload + delete endpoints
│   │   └── services/
│   │       ├── segment_service.py
│   │       └── asset_service.py
│   └── tests/
│       ├── conftest.py          # Fixtures: test client, temp DB, temp asset dir
│       ├── test_auth.py
│       ├── test_segments.py
│       ├── test_assets.py
│       └── test_concurrent.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts            # Includes @tailwindcss/vite plugin
│   ├── index.html
│   └── src/
│       ├── App.vue
│       ├── main.ts
│       ├── style.css            # Tailwind directives + custom theme
│       ├── types/segment.ts
│       ├── types/vuedraggable.d.ts  # Type declarations for vuedraggable 4.x
│       ├── composables/
│       │   ├── useSegments.ts
│       │   ├── useAdmin.ts
│       │   └── useAssetUpload.ts
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppShell.vue       # Sidebar + main content layout
│       │   │   ├── SidebarNav.vue     # Segment nav, collapses on mobile
│       │   │   └── MobileHeader.vue   # Hamburger menu for mobile
│       │   ├── segments/
│       │   │   ├── SegmentRenderer.vue
│       │   │   ├── SegmentList.vue
│       │   │   ├── MarkdownSegment.vue
│       │   │   ├── PdfSegment.vue
│       │   │   ├── VideoSegment.vue
│       │   │   ├── AudioSegment.vue
│       │   │   ├── IframeSegment.vue
│       │   │   └── GallerySegment.vue
│       │   └── admin/
│       │       ├── AdminToolbar.vue
│       │       ├── SegmentEditor.vue
│       │       ├── AssetUploader.vue
│       │       ├── AddSegmentModal.vue  # Modal for creating new segments
│       │       └── TokenPrompt.vue
│       └── views/
│           └── HomePage.vue
└── data/                        # Docker volume mount
    ├── handin.db                # SQLite database
    └── assets/                  # Uploaded files
```

---

## Data Persistence — SQLite

SQLite with WAL mode for concurrent student edits. Single portable file, no external service.

### Schema

```sql
CREATE TABLE site (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE segments (
    id         TEXT PRIMARY KEY,           -- UUID as text
    type       TEXT NOT NULL,              -- markdown|pdf|video|audio|iframe|gallery
    sort_order INTEGER NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL DEFAULT '',
    metadata   TEXT NOT NULL DEFAULT '{}', -- JSON string
    created_at TEXT NOT NULL,              -- ISO 8601
    updated_at TEXT NOT NULL               -- ISO 8601
);
CREATE INDEX idx_segments_order ON segments(sort_order);
```

**Segment types:** `markdown`, `pdf`, `video`, `audio`, `iframe`, `gallery`, `link`.

> **`link` type:** Nav-only segment — renders as an external `<a target="_blank">` in the tab bar and mobile menu. Does not appear in the main content area. The `content` field stores the destination URL.

### Database layer (`database.py`)

- WAL mode: `PRAGMA journal_mode=WAL` for concurrent read/write.
- `PRAGMA busy_timeout=5000` so concurrent writers wait instead of failing.
- Schema auto-created on startup via `CREATE TABLE IF NOT EXISTS`.
- Connection managed per-request via FastAPI dependency.

### Assets

Uploaded files stored as `data/assets/<uuid>.<ext>`. Original filename preserved only in segment metadata (prevents path traversal and collisions).

---

## Auth

- Single token set via `HANDIN_ADMIN_TOKEN` env var.
- Accepted via `?token=` query param or `Authorization: Bearer` header.
- `require_admin` FastAPI dependency on all write endpoints.
- Public endpoints (GET) require no auth.
- `GET /api/auth/verify` for frontend token validation on load.

---

## API Endpoints

```
PUBLIC:
  GET  /api/site/                   Site metadata (title)
  GET  /api/segments/               All segments, ordered by sort_order
  GET  /api/segments/{id}           Single segment
  GET  /api/assets/{filename}       Served via StaticFiles

NOTE: Collection routes use trailing slashes. Omitting them causes 307 redirects.

ADMIN (token required):
  PUT    /api/site/                 Update site title
  POST   /api/segments/             Create segment
  PATCH  /api/segments/{id}         Update segment (partial — send only changed fields)
  DELETE /api/segments/{id}         Delete segment
  PUT    /api/segments/reorder      Reorder (body: ordered UUID list)
  POST   /api/assets/               Upload file (multipart)
  DELETE /api/assets/{filename}     Delete asset
  GET    /api/auth/verify           Validate token
```

**Note:** Register `/reorder` route before `/{id}` to avoid path conflict.

---

## UI Design — Tailwind + #ffcd00 Theme

### Color System

Primary color `#ffcd00` (golden yellow). Tailwind extended palette:

| Token        | Hex       | Usage                           |
|-------------|-----------|----------------------------------|
| primary-50  | `#fffbeb` | Backgrounds, hover states        |
| primary-100 | `#fff3c4` | Editor panel borders             |
| primary-200 | `#fce588` | Subtle highlights                |
| primary-300 | `#ffcd00` | **Brand color** — accents, active states |
| primary-400 | `#e6b800` | Hover on primary elements        |
| primary-500 | `#cc9900` | Text on light backgrounds        |
| primary-600 | `#997300` | Dark accent text                 |
| primary-700 | `#664d00` | Darkest accent                   |

Neutrals: Tailwind `slate` for text and backgrounds. Dark sidebar (`slate-900`), light main content.

### Layout — Top Bar with Tabs

> **Note:** The original plan specified a sidebar layout. Implementation changed to a horizontal top bar with tabs (Slice 5). Component **file names** from the original plan are preserved but their implementations differ.

**Desktop (≥768px `md+`):**
- **Title bar:** `bg-primary-300` (golden yellow) full-width at top, dark text, lock icon (admin entry) on the right.
- **Tab navigation:** Horizontal tab bar below the title bar, `border-b-2 border-primary-400` on the active tab.
- **Content area:** Centered `max-w-4xl` on white background.

**Mobile (<768px):**
- Title bar still visible. Tab bar hidden.
- `MobileHeader.vue` shows hamburger icon → dropdown from top with backdrop overlay.
- Segments stack vertically, full-width, comfortable touch targets.

**Component mapping:**
- `SidebarNav.vue` → horizontal tab bar (desktop, hidden below `md`).
- `MobileHeader.vue` → hamburger dropdown (mobile, hidden at `md+`).
- `AppShell.vue` → composes title bar + TokenPrompt + tab nav + mobile header + AdminToolbar + main content slot.

### Admin Integration (Minimal Interference)

No separate admin page. Controls blend into the existing UI:

- **Token active:** subtle edit icons on segment cards (pencil, muted → `primary-300` on hover). Drag handles in sidebar nav. Thin `primary-300` top bar with "Editing" badge + "Add Segment" button.
- **Segment editing:** inline — editor panel expands below the card. Same card styling, `primary-100` border.
- **Asset upload:** dashed-border drag-and-drop zone matching card aesthetics.
- **Token inactive:** zero admin UI visible.

---

## Dependencies

**Backend:** `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-multipart`
**Backend dev:** `pytest`, `httpx`, `ruff`, `mypy`
**Frontend runtime:** `vue`, `marked`, `vuedraggable`
**Frontend dev:** `vite`, `@vitejs/plugin-vue`, `typescript`, `vue-tsc`, `tailwindcss`, `@tailwindcss/vite`, `@tailwindcss/typography`

---

## Docker Strategy

Multi-stage Dockerfile:
1. **Stage 1** (`node:20-alpine`): `npm ci && npm run build` → `dist/`.
2. **Stage 2** (`python:3.12-slim`): `uv sync --frozen --no-dev`, copy backend + built frontend to `/app/static/`.

FastAPI serves:
- API routes at `/api/*` (registered first)
- Uploaded assets at `/api/assets` via `StaticFiles`
- Vue SPA at `/` via `StaticFiles(directory="/app/static", html=True)` (registered last, catch-all)

`docker-compose.yml`: named volume for `/data`, `HANDIN_ADMIN_TOKEN` from environment.

---

## Verification

1. `uv run pytest backend/tests/ -v` — all pass
2. `uv run ruff check backend/` + `uv run mypy --strict backend/app/` — clean
3. `docker compose up --build` — serves at `localhost:8000`
4. No-token visit: read-only, sidebar nav works, mobile responsive
5. Token visit: admin controls appear inline, CRUD + reorder works
6. Concurrent edits from two browsers: no corruption
7. Container restart: data persists
