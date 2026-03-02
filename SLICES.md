# Implementation Slices

Each slice is a self-contained unit of work. Implement sequentially — each slice builds on the previous. Every slice follows TDD: write tests first, then implement until tests pass.

**Reference:** See [PLAN.md](PLAN.md) for full architecture context, color system, layout details, and project structure.

**Prompt files:** Each slice has a corresponding prompt in `prompts/` that can be handed to an agent for autonomous execution.

---

## Slice 0: Project Scaffold ✅

**Goal:** Set up the project skeleton so all subsequent slices have a working dev environment.

**Deliverables:**
- `pyproject.toml` — Python 3.12+, managed with `uv`. Deps: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-multipart`. Dev deps (via `[dependency-groups]`): `pytest`, `httpx`, `ruff`, `mypy`. Ruff + mypy config sections included.
- `backend/app/__init__.py` (empty)
- `backend/app/config.py` — `Settings` class via `pydantic-settings` with fields: `admin_token: str`, `data_dir: str = "./data"`, `max_upload_bytes: int = 100_000_000`, `allowed_upload_types: str = "pdf,png,jpg,jpeg,gif,mp4,webm,mp3,wav,ogg,webp"`. Env prefix `HANDIN_`.
- `backend/tests/__init__.py` (empty)
- `backend/tests/conftest.py` — fixtures: `tmp_data_dir` (creates temp dir with `assets/` subdir), `settings` (overrides `data_dir` and `admin_token`), `db` (initializes SQLite in temp dir), `client` (FastAPI `TestClient`).
- `frontend/package.json` — deps: `vue`, `marked`, `vuedraggable`. Dev deps: `vite`, `@vitejs/plugin-vue`, `typescript`, `vue-tsc`, `tailwindcss`, `@tailwindcss/vite`, `@tailwindcss/typography`. Pin exact versions.
- `frontend/tsconfig.json`, `frontend/vite.config.ts` (with `@tailwindcss/vite` plugin).
- `frontend/src/main.ts`, `frontend/src/App.vue` (minimal), `frontend/src/style.css` (Tailwind directives).
- `frontend/index.html`
- `.gitignore` — Python, Node, data dir, IDE files.

**Verify:** `uv run pytest backend/tests/ -v` runs (0 tests collected, no errors). `cd frontend && npm install && npm run build` succeeds.

---

## Slice 1: Database + Models ✅

**Prompt:** `prompts/slice-1-database-models.md`

**Goal:** SQLite persistence layer with schema initialization and Pydantic models.

**Tests first (`backend/tests/test_database.py`):**
- Test: `init_db` creates tables (`site`, `segments`) in a fresh DB.
- Test: calling `init_db` twice is idempotent.
- Test: WAL mode is enabled after init.
- Test: `get_connection` returns a connection with `busy_timeout` set.

**Implement:**
- `backend/app/database.py` — `init_db(db_path)` creates schema with `CREATE TABLE IF NOT EXISTS`. Sets `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000`. `get_connection(db_path)` returns a `sqlite3.Connection` with row factory.
- `backend/app/models.py` — `SegmentType(StrEnum)`, `Segment(BaseModel)`, `SegmentCreateRequest`, `SegmentUpdateRequest`, `ReorderRequest`, `SegmentResponse`, `SiteResponse`, `SiteUpdateRequest`.

**Verify:** `uv run pytest backend/tests/test_database.py -v` — all pass. `uv run mypy --strict backend/app/models.py backend/app/database.py` — clean.

---

## Slice 2: Segment & Site Service Layer ✅

**Prompt:** `prompts/slice-2-segment-service.md`

**Goal:** Business logic + persistence for segments and site metadata.

**Tests first (`backend/tests/test_services.py`):**
- 12 segment service tests (create, auto-increment sort_order, list empty/ordered, get found/not found, update title/not found, delete found/not found, reorder valid/invalid)
- 3 site service tests (default title, update + get, overwrite)

**Implement:**
- `backend/app/services/segment_service.py` — `create_segment`, `list_segments`, `get_segment`, `update_segment`, `delete_segment`, `reorder_segments`, `_row_to_segment`.
- `backend/app/services/site_service.py` — `get_site_title`, `update_site_title`.

**Verify:** 15 service tests pass. Zero mypy/ruff errors.

---

## Slice 3: Auth + API Routes + Concurrency

**Prompt:** `prompts/slice-3-api-routes.md`

**Goal:** Complete the backend — auth dependency, all API route handlers, concurrent write safety.

**Covers (from original plan):** Auth (PLAN slice 2), Segment CRUD routes (3), Reorder route (4), Site routes (6), Concurrency tests (7).

**Tests first:**
- `backend/tests/test_routes.py` — ~19 HTTP-level tests for segments, site, and auth (CRUD, reorder, unauthorized access, not-found cases)
- `backend/tests/test_concurrent.py` — 2 concurrency tests (parallel creates, concurrent create + reorder)

**Implement:**
- `backend/app/auth.py` — `require_admin` dependency. Checks `?token=` query param first, falls back to `Authorization: Bearer` header.
- `backend/app/routes/auth.py` — `GET /api/auth/verify` endpoint.
- `backend/app/routes/segments.py` — CRUD + reorder at `/api/segments`. Public: GET list, GET by id. Admin: POST, PATCH, DELETE, PUT reorder.
- `backend/app/routes/site.py` — GET + PUT at `/api/site`. Public: GET. Admin: PUT.
- `backend/app/main.py` — register routers, wire lifespan with `init_db`.

**Verify:** All backend tests pass (~40 total). Zero mypy/ruff errors across entire backend.

---

## Slice 4: Asset Service + Docker

**Prompt:** `prompts/slice-4-assets-docker.md`

**Goal:** File upload/serve/delete and containerized deployment.

**Covers (from original plan):** Asset Upload + Serve (5), Docker (13).

**Tests first (`backend/tests/test_assets.py`):**
- 8 tests: upload valid file, file exists on disk, disallowed type → 415, too large → 413, no auth → 401, delete file, delete not found → 404, serve via StaticFiles.

**Implement:**
- `backend/app/services/asset_service.py` — `save_asset`, `delete_asset`.
- `backend/app/routes/assets.py` — POST upload, DELETE by filename.
- Mount `StaticFiles` at `/api/assets` in `main.py`.
- `Dockerfile` — multi-stage build (Node → Python).
- `docker-compose.yml` — single service, volume mount, env vars.

**Verify:** All backend tests pass. `docker compose up --build` serves at localhost:8000.

---

## Slice 5: Frontend Shell + Renderers

**Prompt:** `prompts/slice-5-frontend-shell.md`

**Goal:** Read-only frontend — app shell, sidebar nav, mobile layout, all segment renderers.

**Covers (from original plan):** Frontend Shell + Tailwind Theme (8), Segment Renderers (9).

**Deliverables:**
- `style.css` — Tailwind v4 with `@theme` block for primary palette.
- `types/segment.ts` — TypeScript types matching backend models.
- Layout components: `AppShell.vue`, `SidebarNav.vue`, `MobileHeader.vue`.
- `composables/useSegments.ts` — fetch segments + site title.
- `views/HomePage.vue` — main page rendering.
- Segment components: `SegmentRenderer.vue`, `SegmentList.vue`, plus renderers for markdown, PDF, video, audio, iframe, gallery.

**Verify:** `npm run build` succeeds. Dev server renders sidebar + segments correctly on desktop and mobile.

---

## Slice 6: Admin UI ✅

**Prompt:** `prompts/slice-6-admin-ui.md`

**Goal:** Full admin experience — token entry, inline editing, asset upload, drag-and-drop reorder.

**Covers (from original plan):** Admin Token + Toolbar (10), Segment Editor + CRUD (11), Asset Upload + Drag-and-Drop Reorder (12).

**Deliverables:**
- `composables/useAdmin.ts` — token management via module-level reactive state, auth headers, verify/login/logout, sessionStorage persistence.
- `composables/useAssetUpload.ts` — file upload via FormData + native fetch.
- `components/admin/TokenPrompt.vue` — subtle lock icon in title bar → inline token input.
- `components/admin/AdminToolbar.vue` — thin editing bar below tabs with "Editing" badge + "Add Segment" + "Logout".
- `components/admin/SegmentEditor.vue` — inline editor below each segment card, type-aware content editing, custom styled delete confirmation modal.
- `components/admin/AssetUploader.vue` — drag-and-drop file upload zone with click-to-browse.
- `components/admin/AddSegmentModal.vue` — modal dialog with button-group type selector for creating new segments.
- `types/vuedraggable.d.ts` — type declaration for vuedraggable 4.x.
- Drag-and-drop reorder via `vuedraggable` in `SegmentList.vue` with grip-dot handles.
- Modified `AppShell.vue` — TokenPrompt in header, AdminToolbar below tabs (when authenticated).
- Modified `SegmentList.vue` — pencil edit icons, inline editors, draggable reorder (admin), plain rendering (read-only).
- Modified `HomePage.vue` — wires all admin mutations (create/PATCH/DELETE/reorder) with auth headers + refresh().
- **New segment type: `link`** — nav-only external links. Renders as `<a target="_blank">` in SidebarNav/MobileHeader, excluded from content area. Backend `SegmentType` enum and frontend type updated.

**Verify:** `npm run build` passes with zero errors. Full admin flow works end-to-end. No admin UI visible without token.

---

## Slice 7: Polish + Final Validation

**Prompt:** `prompts/slice-7-polish.md`

**Goal:** End-to-end sweep, edge cases, visual polish.

**Tasks:**
- Run full backend test suite: `uv run pytest backend/tests/ -v`.
- Run `uv run ruff check backend/` + `uv run mypy --strict backend/app/`.
- Run `npm run lint` + `npm run type-check` in frontend.
- Test mobile layout on narrow viewport (sidebar collapses, touch-friendly targets).
- Test all segment types render correctly in read-only mode.
- Test admin flow end-to-end: enter token, add each segment type, upload assets, reorder, delete, logout.
- Test concurrent edits: two browser tabs editing simultaneously.
- Verify no admin UI leaks in read-only mode.
