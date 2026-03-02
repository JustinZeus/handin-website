# Slice 6: Admin UI

## Role

You are a frontend TypeScript/Vue developer adding admin functionality to an existing read-only academic submission website. The backend API and read-only frontend are complete — you are adding token-based authentication, inline editing, asset upload, and drag-and-drop reorder.

## Objective

Create the full admin experience: token entry, inline segment editing (create/update/delete), asset uploading, and drag-and-drop segment reorder. Admin controls must be invisible when no token is active. All files must pass `vue-tsc --noEmit` (strict TypeScript).

## Architecture Reference

Read [PLAN.md](../PLAN.md) for full architecture context. **However, note these deviations from PLAN.md that were made during Slice 5 implementation:**

### Layout Change (IMPORTANT)

The layout was changed from a **sidebar** to a **horizontal top bar with tabs**:

- **Title bar:** `bg-primary-300` (golden yellow) with dark text, full width at top.
- **Tab navigation:** Horizontal tab bar below the title, with `border-b-2 border-primary-400` on the active tab. Visible on `md+` screens.
- **Mobile:** Hamburger dropdown (not slide-out sidebar). Opens a vertical list from the top with backdrop.
- **Content area:** Centered `max-w-4xl` on white background.

The component **file names** from PLAN.md are preserved but their implementations differ:
- `SidebarNav.vue` is actually a **horizontal tab bar** (desktop).
- `MobileHeader.vue` is a **hamburger dropdown** (mobile).
- `AppShell.vue` composes the title bar + tab nav + mobile header + main content slot.

### Backend Route Trailing Slashes

Backend collection routes use **trailing slashes**. Always include them in fetch URLs:
- `GET /api/site/` — not `/api/site`
- `GET /api/segments/` — not `/api/segments`
- `POST /api/segments/` — not `/api/segments`
- `POST /api/assets/` — not `/api/assets`
- `PUT /api/segments/reorder` — no trailing slash (path route, not collection)
- `GET /api/auth/verify` — no trailing slash
- `PATCH /api/segments/{id}` — no trailing slash (uses PATCH, not PUT)
- `DELETE /api/segments/{id}` — no trailing slash
- `DELETE /api/assets/{filename}` — no trailing slash

Omitting trailing slashes on collection routes causes **307 redirects** which break in the Docker proxy setup (CORS errors).

## UI Decision-Making Policy

**When you encounter any ambiguity in visual design, layout, spacing, interaction patterns, or component behavior — use `AskUserQuestion` BEFORE implementing.** Do not guess or pick defaults for subjective UI choices. Examples:
- How the "Add Segment" form should look (modal vs inline vs dropdown)
- Editor layout for different segment types
- Confirmation dialogs for delete actions
- Token input styling and placement
- Admin toolbar positioning relative to the top bar
- Drag handle icon/style

Only proceed without asking when this prompt gives an unambiguous, specific instruction.

## Coding Standards (mandatory)

- Vue 3 `<script setup lang="ts">` single-file components
- Strict TypeScript — no `any`, all props/emits typed
- Tailwind CSS v4 utility classes (no separate CSS files per component)
- Composables use `ref`/`computed`/`onMounted` from Vue — no Options API
- Components are small and focused — one responsibility per file
- Use `@/` path alias for imports (configured in vite.config.ts as `src/`)
- No external state management library — use composables with reactive state
- Use native `fetch()` — no axios

## Step 0: Verify Existing Setup

```bash
cd frontend && npm run build
```

Must exit cleanly. If it fails, fix before proceeding.

## Context: Backend API

### Auth Mechanism

- Single shared token set via `HANDIN_ADMIN_TOKEN` env var (in `.env` file, value: `changeme`).
- Token accepted via `?token=<token>` query param OR `Authorization: Bearer <token>` header.
- `GET /api/auth/verify` — returns `{ "valid": true }` if token is valid, 401 otherwise.
- All write endpoints require the token (POST, PATCH, PUT, DELETE on segments/assets/site).

### API Endpoints Used by This Slice

```
AUTH:
  GET    /api/auth/verify              → { "valid": true } or 401

SEGMENTS (admin):
  POST   /api/segments/               → SegmentResponse (201)
         Body: { "type": SegmentType, "title": string, "content"?: string, "metadata"?: object }

  PATCH  /api/segments/{id}            → SegmentResponse
         Body: { "title"?: string, "content"?: string, "metadata"?: object }
         NOTE: PATCH not PUT — only send changed fields

  DELETE /api/segments/{id}            → 204 No Content

  PUT    /api/segments/reorder         → SegmentResponse[]
         Body: { "segment_ids": string[] }

ASSETS (admin):
  POST   /api/assets/                  → { "filename": "uuid.ext" } (201)
         Body: multipart/form-data with "file" field

  DELETE /api/assets/{filename}        → 204 No Content

SITE (admin):
  PUT    /api/site/                    → { "title": string }
         Body: { "title": string }
```

### Existing Frontend Types

```typescript
// frontend/src/types/segment.ts
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

### Existing Composable: useSegments

```typescript
// frontend/src/composables/useSegments.ts
// Returns: { segments, siteTitle, loading, error, refresh }
// refresh() re-fetches both /api/site/ and /api/segments/
// Call refresh() after any admin mutation to sync the UI
```

### Existing Layout Structure

```
AppShell.vue
├── <header> — yellow title bar (bg-primary-300), shows siteTitle
├── SidebarNav.vue — horizontal tab bar (hidden below md)
├── MobileHeader.vue — hamburger dropdown (hidden at md+)
└── <main> — slot for page content (max-w-4xl centered)
```

### Existing Segment List

```vue
<!-- SegmentList.vue renders each segment as: -->
<section :id="segment.id" class="rounded-lg bg-white p-6 shadow-sm">
  <h2>{{ segment.title }}</h2>
  <SegmentRenderer :segment="segment" />
</section>
```

## Step 1: Create `useAdmin` Composable

### `frontend/src/composables/useAdmin.ts`

Manages admin authentication state. Exports a composable `useAdmin()` that returns:

- `token: Ref<string | null>` — current token (persisted in `sessionStorage`)
- `isAdmin: Ref<boolean>` — true when token is verified
- `verifying: Ref<boolean>` — true during verification request
- `login(token: string): Promise<boolean>` — verify token via `GET /api/auth/verify`, persist if valid
- `logout(): void` — clear token and admin state
- `authHeaders: ComputedRef<Record<string, string>>` — returns `{ "Authorization": "Bearer <token>" }` when authenticated, empty object otherwise
- `authQuery: ComputedRef<string>` — returns `?token=<token>` or empty string (useful for asset URLs)

On creation, check `sessionStorage` for an existing token and re-verify it silently.

**Important:** This composable must use module-level reactive state (defined outside the function) so that all components share the same auth state. The function just returns references to the shared state.

## Step 2: Create `useAssetUpload` Composable

### `frontend/src/composables/useAssetUpload.ts`

Handles file uploads. Exports `useAssetUpload()` that returns:

- `uploading: Ref<boolean>`
- `error: Ref<string | null>`
- `upload(file: File, authHeaders: Record<string, string>): Promise<string | null>` — uploads file to `POST /api/assets/`, returns the filename on success or null on failure

Use `FormData` with native `fetch()`. Set `error` on failure with the server's error message.

## Step 3: Create Admin Components

### `frontend/src/components/admin/TokenPrompt.vue`

The entry point for admin access. When no token is active:
- Show a small, subtle lock icon in the top bar (inside AppShell's header area)
- Clicking it reveals an inline token input field with a submit button
- On successful login, the input disappears and admin controls appear

Props: none (uses `useAdmin` composable directly).

Emits:
- `authenticated` — fired when login succeeds

### `frontend/src/components/admin/AdminToolbar.vue`

A thin bar shown below the tab nav when admin is authenticated. Contains:
- An "Editing" badge (subtle indicator)
- An "Add Segment" button that triggers segment creation
- A "Logout" button

Props: none (uses `useAdmin` composable directly).

Emits:
- `add-segment` — when "Add Segment" is clicked
- `logout` — when "Logout" is clicked

### `frontend/src/components/admin/SegmentEditor.vue`

Inline editor that appears below a segment card when editing. Handles:
- Editing title (text input)
- Editing content based on segment type:
  - `markdown`: textarea for raw markdown
  - `pdf`, `video`, `audio`: file upload (via AssetUploader) or URL input showing current asset
  - `iframe`: URL text input
  - `gallery`: file upload for multiple images, display current images with remove buttons
- Save and Cancel buttons
- Delete button (with confirmation)

Props:
- `segment: Segment`

Emits:
- `save(updates: { title?: string; content?: string; metadata?: Record<string, unknown> })` — partial update
- `cancel` — close editor
- `delete` — delete this segment

### `frontend/src/components/admin/AssetUploader.vue`

Drag-and-drop file upload zone. Features:
- Dashed border drop zone
- Click to select file
- Shows upload progress/status
- Returns the uploaded filename

Props:
- `accept?: string` — file type filter (e.g., `"application/pdf"`, `"image/*"`)
- `label?: string` — descriptive text inside the zone

Emits:
- `uploaded(filename: string)` — when upload completes successfully

## Step 4: Integrate Admin into Existing Components

### Modify `AppShell.vue`

- Add `TokenPrompt` to the title bar header (when not authenticated)
- Add `AdminToolbar` below the tab nav (when authenticated)
- Pass admin state down or let child components use `useAdmin` directly

### Modify `SegmentList.vue`

When admin is active:
- Show a small edit icon (pencil) on each segment card header (next to the title)
- Clicking the edit icon toggles `SegmentEditor` inline below that segment
- Show drag handles on each card for reorder (use `vuedraggable`)
- After drag-and-drop reorder, call `PUT /api/segments/reorder` with the new ID order, then `refresh()`

The `vuedraggable` package is already installed (`"vuedraggable": "4.1.0"` in package.json). Import it as:
```typescript
import draggable from "vuedraggable";
```

Note: `vuedraggable` 4.x may not have TypeScript declarations. If `vue-tsc` complains, create a type declaration file `frontend/src/types/vuedraggable.d.ts`:
```typescript
declare module "vuedraggable" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent;
  export default component;
}
```

### Modify `HomePage.vue`

- Wire up the "Add Segment" flow: when `AdminToolbar` emits `add-segment`, show a creation form (could be a simple modal or inline form at the top/bottom of the segment list)
- After creating a segment, call `refresh()` to reload the list
- After editing/deleting a segment, call `refresh()`
- Handle logout: call `useAdmin().logout()`

## Step 5: Segment Creation Flow

When "Add Segment" is clicked, the user needs to:
1. Choose a segment type (dropdown or button group)
2. Enter a title
3. Provide initial content (type-dependent: text for markdown, URL for iframe, file upload for pdf/video/audio, etc.)
4. Submit → `POST /api/segments/` with auth header → `refresh()`

## Step 6: Wire Up All Mutations

All admin mutations must:
1. Include auth headers from `useAdmin().authHeaders`
2. Call `useSegments().refresh()` after success to sync the UI
3. Handle errors gracefully (show error message, don't lose user input)

### Mutation summary:

| Action | Method | Endpoint | Auth | After |
|--------|--------|----------|------|-------|
| Create segment | POST | `/api/segments/` | Bearer header | refresh() |
| Update segment | PATCH | `/api/segments/{id}` | Bearer header | refresh() |
| Delete segment | DELETE | `/api/segments/{id}` | Bearer header | refresh() |
| Reorder segments | PUT | `/api/segments/reorder` | Bearer header | refresh() |
| Upload asset | POST | `/api/assets/` | Bearer header | use filename |
| Delete asset | DELETE | `/api/assets/{filename}` | Bearer header | refresh() |
| Update site title | PUT | `/api/site/` | Bearer header | refresh() |

## Verification

After implementation, run:

```bash
cd frontend && npm run build
```

Must succeed with zero errors. Then verify functionally:

```bash
cd frontend && npm run dev
```

Or with Docker:
```bash
docker compose up --build
# Visit http://localhost:5174
```

Check:
1. **No admin UI visible** without token — only the lock icon in the header
2. Click lock icon → enter token `changeme` → admin controls appear
3. Admin toolbar shows with "Add Segment" and "Logout" buttons
4. Create a markdown segment → appears in the list
5. Edit a segment's title and content → saves correctly
6. Delete a segment → removed from list (after confirmation)
7. Drag-and-drop reorder segments → order persists after refresh
8. Upload an asset (PDF, image) → segment displays it
9. Logout → all admin UI disappears, read-only view restored
10. No TypeScript errors (`npm run type-check`)

## Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `frontend/src/composables/useAdmin.ts` |
| CREATE | `frontend/src/composables/useAssetUpload.ts` |
| CREATE | `frontend/src/components/admin/TokenPrompt.vue` |
| CREATE | `frontend/src/components/admin/AdminToolbar.vue` |
| CREATE | `frontend/src/components/admin/SegmentEditor.vue` |
| CREATE | `frontend/src/components/admin/AssetUploader.vue` |
| CREATE | `frontend/src/types/vuedraggable.d.ts` (if needed for type-check) |
| MODIFY | `frontend/src/components/layout/AppShell.vue` |
| MODIFY | `frontend/src/components/segments/SegmentList.vue` |
| MODIFY | `frontend/src/views/HomePage.vue` |
