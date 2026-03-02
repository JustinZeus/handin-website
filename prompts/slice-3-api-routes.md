# Slice 3: Auth + API Routes + Concurrency

## Role

You are a backend Python developer implementing the auth dependency, all API route handlers, and concurrency tests for a FastAPI-based academic submission website. You follow TDD strictly: write all tests first, then implement until they pass.

## Objective

Create five production files (`auth.py`, `routes/auth.py`, `routes/segments.py`, `routes/site.py`) and modify one (`main.py`). Create two test files (`tests/test_routes.py`, `tests/test_concurrent.py`). All tests must pass. All production files must pass `mypy --strict`.

## Coding Standards (mandatory)

- Python 3.12+ features (type parameter syntax, `StrEnum`, `list[X]` not `List[X]`)
- All function signatures must have type hints (params and return)
- Use `UUID` from `uuid` for ID fields, `datetime` from `datetime` for timestamps
- Max 50 lines per function; extract helpers if longer
- Guard clauses before logic (fail early, no nested conditionals)
- No `else` after `return`/`raise`
- Max 3 levels of indentation
- Imports grouped: stdlib → third-party → local (absolute imports only: `from app.module import ...`)
- No `Any` types. No `# type: ignore` without explanation
- Comments explain WHY, not WHAT

## Step 0: Verify Previous Slices

Before writing any new code, verify that slices 1 and 2 are healthy. Run:

```bash
uv run pytest backend/tests/ -v
uv run mypy --strict backend/app/
uv run ruff check backend/
```

**All commands must exit cleanly with zero errors.** If any fail, fix the issues before proceeding. Do NOT continue to Step 1 with a broken baseline.

## Context: Existing Files

### `backend/app/config.py`
```python
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    admin_token: str
    data_dir: str = "./data"
    max_upload_bytes: int = 100_000_000
    allowed_upload_types: str = "pdf,png,jpg,jpeg,gif,mp4,webm,mp3,wav,ogg,webp"

    model_config = {"env_prefix": "HANDIN_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### `backend/app/database.py`
```python
import sqlite3
from pathlib import Path


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS site (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS segments (
                id         TEXT PRIMARY KEY,
                type       TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL DEFAULT '',
                metadata   TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_segments_order ON segments(sort_order)"
        )
        conn.commit()
    finally:
        conn.close()


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn
```

### `backend/app/models.py`
```python
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class SegmentType(StrEnum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    IFRAME = "iframe"
    GALLERY = "gallery"


class Segment(BaseModel):
    id: UUID
    type: SegmentType
    sort_order: int
    title: str
    content: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class SegmentCreateRequest(BaseModel):
    type: SegmentType
    title: str
    content: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class SegmentUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    metadata: dict[str, object] | None = None


class ReorderRequest(BaseModel):
    segment_ids: list[UUID]


class SiteUpdateRequest(BaseModel):
    title: str


class SegmentResponse(BaseModel):
    id: UUID
    type: SegmentType
    sort_order: int
    title: str
    content: str
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class SiteResponse(BaseModel):
    title: str
```

### `backend/app/services/segment_service.py`
```python
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.database import get_connection
from app.models import Segment, SegmentCreateRequest, SegmentType, SegmentUpdateRequest


def _row_to_segment(row: sqlite3.Row) -> Segment:
    return Segment(
        id=UUID(row["id"]),
        type=SegmentType(row["type"]),
        sort_order=row["sort_order"],
        title=row["title"],
        content=row["content"],
        metadata=json.loads(row["metadata"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def create_segment(db_path: Path, request: SegmentCreateRequest) -> Segment:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order) + 1, 0) AS next_order FROM segments"
        ).fetchone()
        sort_order: int = row["next_order"] if row else 0

        segment_id = uuid4()
        now = datetime.now(UTC).isoformat()
        metadata_json = json.dumps(request.metadata)

        cols = "id, type, sort_order, title, content, metadata, created_at, updated_at"
        conn.execute(
            f"INSERT INTO segments ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(segment_id), request.type.value, sort_order, request.title,
             request.content, metadata_json, now, now),
        )
        conn.commit()

        return Segment(
            id=segment_id,
            type=request.type,
            sort_order=sort_order,
            title=request.title,
            content=request.content,
            metadata=request.metadata,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )
    finally:
        conn.close()


def list_segments(db_path: Path) -> list[Segment]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM segments ORDER BY sort_order ASC"
        ).fetchall()
        return [_row_to_segment(row) for row in rows]
    finally:
        conn.close()


def get_segment(db_path: Path, segment_id: UUID) -> Segment | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM segments WHERE id = ?", (str(segment_id),)
        ).fetchone()
        if row is None:
            return None
        return _row_to_segment(row)
    finally:
        conn.close()


def update_segment(
    db_path: Path, segment_id: UUID, request: SegmentUpdateRequest
) -> Segment | None:
    conn = get_connection(db_path)
    try:
        existing = conn.execute(
            "SELECT * FROM segments WHERE id = ?", (str(segment_id),)
        ).fetchone()
        if existing is None:
            return None

        now = datetime.now(UTC).isoformat()
        title = request.title if request.title is not None else existing["title"]
        content = request.content if request.content is not None else existing["content"]
        metadata_json = (
            json.dumps(request.metadata) if request.metadata is not None
            else existing["metadata"]
        )

        conn.execute(
            """UPDATE segments SET title = ?, content = ?, metadata = ?, updated_at = ?
               WHERE id = ?""",
            (title, content, metadata_json, now, str(segment_id)),
        )
        conn.commit()

        return get_segment(db_path, segment_id)
    finally:
        conn.close()


def delete_segment(db_path: Path, segment_id: UUID) -> bool:
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM segments WHERE id = ?", (str(segment_id),)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def reorder_segments(db_path: Path, segment_ids: list[UUID]) -> list[Segment]:
    conn = get_connection(db_path)
    try:
        existing_ids = {
            row["id"]
            for row in conn.execute("SELECT id FROM segments").fetchall()
        }
        requested_ids = {str(sid) for sid in segment_ids}
        missing = requested_ids - existing_ids
        if missing:
            raise ValueError(f"Segment IDs not found: {missing}")

        now = datetime.now(UTC).isoformat()
        for index, sid in enumerate(segment_ids):
            conn.execute(
                "UPDATE segments SET sort_order = ?, updated_at = ? WHERE id = ?",
                (index, now, str(sid)),
            )
        conn.commit()

        return list_segments(db_path)
    finally:
        conn.close()
```

### `backend/app/services/site_service.py`
```python
from pathlib import Path

from app.database import get_connection


def get_site_title(db_path: Path) -> str:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT value FROM site WHERE key = ?", ("title",)
        ).fetchone()
        if row is None:
            return "Untitled Site"
        return str(row["value"])
    finally:
        conn.close()


def update_site_title(db_path: Path, title: str) -> str:
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO site (key, value) VALUES (?, ?)",
            ("title", title),
        )
        conn.commit()
        return title
    finally:
        conn.close()
```

### `backend/app/main.py`
```python
from fastapi import FastAPI

app = FastAPI(title="Handin Website")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

### `backend/tests/conftest.py`
```python
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings

TEST_ADMIN_TOKEN = "test-secret-token"


@pytest.fixture
def tmp_data_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        (data_dir / "assets").mkdir()
        yield data_dir


@pytest.fixture
def _env_settings(tmp_data_dir: Path) -> Generator[None, None, None]:
    original_env = os.environ.copy()
    os.environ["HANDIN_ADMIN_TOKEN"] = TEST_ADMIN_TOKEN
    os.environ["HANDIN_DATA_DIR"] = str(tmp_data_dir)

    from app.config import get_settings

    get_settings.cache_clear()
    yield
    os.environ.clear()
    os.environ.update(original_env)
    get_settings.cache_clear()


@pytest.fixture
def settings(_env_settings: None) -> Settings:
    from app.config import get_settings

    s = get_settings()
    assert isinstance(s, Settings)
    return s


@pytest.fixture
def db(tmp_data_dir: Path) -> Path:
    """Return path to an initialized SQLite database in the temp dir."""
    from app.database import init_db

    db_path = tmp_data_dir / "handin.db"
    init_db(db_path)
    return db_path


@pytest.fixture
def client(_env_settings: None) -> TestClient:
    from app.main import app

    return TestClient(app)
```

### `pyproject.toml` (relevant sections)
```toml
[tool.mypy]
strict = true
python_version = "3.12"
mypy_path = "backend"
packages = ["app"]
plugins = ["pydantic.mypy"]
```

### Existing empty `__init__.py` files
- `backend/app/__init__.py`
- `backend/app/routes/__init__.py`
- `backend/app/services/__init__.py`
- `backend/tests/__init__.py`

## Architecture Notes

- The routes layer is thin: parse request → call service → return response
- Authentication uses a shared token (`Settings.admin_token`) checked via a FastAPI dependency
- Auth accepts token via **two methods**: `?token=` query param (checked first) OR `Authorization: Bearer <token>` header (fallback)
- All admin endpoints (create, update, delete, reorder segments; update site title) require auth
- Public endpoints (list segments, get segment, get site title, health) require no authentication
- The database path is derived from `Settings.data_dir` via a FastAPI dependency
- The `main.py` lifespan must call `init_db()` to ensure the database exists on startup
- Register the `/reorder` route **before** `/{segment_id}` to avoid path conflict

## Step 1: Write Tests

Write ALL tests FIRST, before any production code. Use the `client` fixture from conftest.

### `backend/tests/test_routes.py`

**Helper constants at module level:**
```python
from tests.conftest import TEST_ADMIN_TOKEN

BEARER_HEADERS = {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}
```

**Segment route tests:**

1. **`test_list_segments_empty`** — `GET /api/segments` returns `200` with an empty JSON list.

2. **`test_create_segment`** — `POST /api/segments` with `BEARER_HEADERS` and body `{"type": "markdown", "title": "Intro"}`. Assert `201`, response has `id`, `title == "Intro"`, `type == "markdown"`, `sort_order == 0`.

3. **`test_create_segment_unauthorized`** — `POST /api/segments` without auth headers. Assert `401`.

4. **`test_create_segment_wrong_token`** — `POST /api/segments` with `Authorization: Bearer wrong-token`. Assert `401`.

5. **`test_create_segment_via_query_param`** — `POST /api/segments?token={TEST_ADMIN_TOKEN}` (no headers). Assert `201`.

6. **`test_get_segment`** — Create a segment via POST, then `GET /api/segments/{id}`. Assert `200` and matching data.

7. **`test_get_segment_not_found`** — `GET /api/segments/{random_uuid}`. Assert `404`.

8. **`test_update_segment`** — Create a segment, then `PATCH /api/segments/{id}` with `BEARER_HEADERS` and `{"title": "Updated"}`. Assert `200` and `title == "Updated"`.

9. **`test_update_segment_not_found`** — `PATCH /api/segments/{random_uuid}` with `BEARER_HEADERS`. Assert `404`.

10. **`test_update_segment_unauthorized`** — `PATCH /api/segments/{id}` without auth. Assert `401`.

11. **`test_delete_segment`** — Create a segment, then `DELETE /api/segments/{id}` with `BEARER_HEADERS`. Assert `204`. Confirm `GET /api/segments/{id}` returns `404`.

12. **`test_delete_segment_not_found`** — `DELETE /api/segments/{random_uuid}` with `BEARER_HEADERS`. Assert `404`.

13. **`test_delete_segment_unauthorized`** — `DELETE /api/segments/{id}` without auth. Assert `401`.

14. **`test_reorder_segments`** — Create three segments (A, B, C). `PUT /api/segments/reorder` with `BEARER_HEADERS` and `{"segment_ids": [C.id, A.id, B.id]}`. Assert `200`. List segments and verify new order is C, A, B.

15. **`test_reorder_segments_invalid_ids`** — `PUT /api/segments/reorder` with `BEARER_HEADERS` and a non-existent UUID in the list. Assert `400`.

16. **`test_reorder_segments_unauthorized`** — `PUT /api/segments/reorder` without auth. Assert `401`.

**Site route tests:**

17. **`test_get_site_title_default`** — `GET /api/site`. Assert `200` and `title == "Untitled Site"`.

18. **`test_update_site_title`** — `PUT /api/site` with `BEARER_HEADERS` and `{"title": "My Course"}`. Assert `200` and `title == "My Course"`. Then `GET /api/site` confirms it.

19. **`test_update_site_title_unauthorized`** — `PUT /api/site` without auth. Assert `401`.

**Auth route tests:**

20. **`test_auth_verify_valid_bearer`** — `GET /api/auth/verify` with `BEARER_HEADERS`. Assert `200` and body `{"valid": true}`.

21. **`test_auth_verify_valid_query_param`** — `GET /api/auth/verify?token={TEST_ADMIN_TOKEN}`. Assert `200` and body `{"valid": true}`.

22. **`test_auth_verify_invalid`** — `GET /api/auth/verify` with wrong token. Assert `401`.

23. **`test_auth_verify_no_token`** — `GET /api/auth/verify` with no auth. Assert `401`.

**Health test:**

24. **`test_health`** — `GET /api/health`. Assert `200` and `status == "ok"`.

**Test conventions:**
- Each test function takes `client: TestClient` as parameter (from fixture)
- No mocking — use real HTTP calls via TestClient against real SQLite on temp directories
- Create segments via `client.post(...)` within tests rather than calling service functions directly

### `backend/tests/test_concurrent.py`

Use the `client` fixture. Import `TEST_ADMIN_TOKEN` from conftest.

1. **`test_concurrent_creates`** — Use `concurrent.futures.ThreadPoolExecutor` to fire 10 concurrent `POST /api/segments` requests (all with auth). Assert all 10 return `201`. Assert `GET /api/segments` returns 10 segments with 10 unique IDs and `sort_order` values `0` through `9` (no gaps, no duplicates).

2. **`test_concurrent_create_and_reorder`** — Create 3 segments sequentially. Then concurrently: create 2 more segments AND reorder the original 3. Assert no errors (all requests return 2xx). Assert final DB state is consistent (5 total segments, all have valid `sort_order` values).

**Test conventions:**
- Use `concurrent.futures.ThreadPoolExecutor(max_workers=10)` for thread-based concurrency
- Each thread gets its own `TestClient` call (the underlying SQLite handles concurrency via WAL + busy_timeout)

## Step 2: Implement `backend/app/auth.py`

**Single function (used as FastAPI dependency):**

### `require_admin(request: Request) -> None`
- First check for `token` query parameter in `request.query_params`
- If not present, check `Authorization` header for `Bearer <token>` format
- Compare extracted token against `get_settings().admin_token`
- Raise `HTTPException(status_code=401, detail="Invalid or missing token")` if:
  - No token found in either location
  - Token doesn't match
- Import `Request` from `fastapi`, `HTTPException` from `fastapi`

## Step 3: Implement `backend/app/routes/auth.py`

Create a FastAPI `APIRouter` with `prefix="/api/auth"` and `tags=["auth"]`.

### `GET /verify` → `dict[str, bool]`
- Depends on `require_admin` (if the dependency passes, token is valid)
- Returns `{"valid": True}`

## Step 4: Implement `backend/app/routes/segments.py`

Create a FastAPI `APIRouter` with `prefix="/api/segments"` and `tags=["segments"]`.

**Shared dependency (define in this file):**

### `get_db_path() -> Path`
- A FastAPI dependency (use `Depends`)
- Reads `data_dir` from `get_settings()`
- Computes `db_path = Path(data_dir) / "handin.db"`
- Calls `init_db(db_path)` to ensure the database is initialized
- Returns the `db_path`

**Endpoints (register `/reorder` BEFORE `/{segment_id}`):**

### `GET /` → `list[SegmentResponse]`
- Public (no auth required)
- Calls `segment_service.list_segments(db_path)`
- Returns `200` with list of `SegmentResponse`

### `POST /` → `SegmentResponse`
- Admin only (`Depends(require_admin)`)
- Accepts `SegmentCreateRequest` as JSON body
- Calls `segment_service.create_segment(db_path, request)`
- Returns `201` with the created `SegmentResponse`

### `PUT /reorder` → `list[SegmentResponse]`
- Admin only
- Accepts `ReorderRequest` as JSON body
- Calls `segment_service.reorder_segments(db_path, request.segment_ids)`
- Catches `ValueError` and returns `400` with error detail
- Returns `200` with the reordered list on success

### `GET /{segment_id}` → `SegmentResponse`
- Public (no auth required)
- Calls `segment_service.get_segment(db_path, segment_id)`
- Returns `200` if found, raises `HTTPException(404)` if not

### `PATCH /{segment_id}` → `SegmentResponse`
- Admin only
- Accepts `SegmentUpdateRequest` as JSON body
- Calls `segment_service.update_segment(db_path, segment_id, request)`
- Returns `200` if found and updated, raises `HTTPException(404)` if not

### `DELETE /{segment_id}` → `None`
- Admin only
- Calls `segment_service.delete_segment(db_path, segment_id)`
- Returns `204` if deleted, raises `HTTPException(404)` if not found

## Step 5: Implement `backend/app/routes/site.py`

Create a FastAPI `APIRouter` with `prefix="/api/site"` and `tags=["site"]`.

Reuse `get_db_path` from `segments.py` (or extract to a shared location if preferred).

### `GET /` → `SiteResponse`
- Public (no auth required)
- Calls `site_service.get_site_title(db_path)`
- Returns `200` with `SiteResponse`

### `PUT /` → `SiteResponse`
- Admin only (`Depends(require_admin)`)
- Accepts `SiteUpdateRequest` as JSON body
- Calls `site_service.update_site_title(db_path, request.title)`
- Returns `200` with `SiteResponse`

## Step 6: Modify `backend/app/main.py`

Update `main.py` to:

- Add a **lifespan** context manager that calls `init_db()` on startup (compute `db_path` from `get_settings().data_dir`)
- Import and register all three routers: `auth_router`, `segments_router`, `site_router`
- Keep the existing `/api/health` endpoint

## Verification

After implementation, run these commands and ensure they all succeed:

```bash
uv run pytest backend/tests/test_routes.py -v
uv run pytest backend/tests/test_concurrent.py -v
uv run mypy --strict backend/app/auth.py backend/app/routes/auth.py backend/app/routes/segments.py backend/app/routes/site.py backend/app/main.py
uv run ruff check backend/app/auth.py backend/app/routes/ backend/app/main.py
```

Then run the **full** verification suite to ensure nothing is broken:

```bash
uv run pytest backend/tests/ -v
uv run mypy --strict backend/app/ backend/tests/
uv run ruff check backend/
```

All tests must pass (~40 total: 6 database + 15 service + 24 route + 2 concurrency). Zero mypy errors. Zero ruff errors.

## Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `backend/tests/test_routes.py` |
| CREATE | `backend/tests/test_concurrent.py` |
| CREATE | `backend/app/auth.py` |
| CREATE | `backend/app/routes/auth.py` |
| CREATE | `backend/app/routes/segments.py` |
| CREATE | `backend/app/routes/site.py` |
| MODIFY | `backend/app/main.py` |

Do NOT modify any other files. Do NOT modify `conftest.py`, `config.py`, `database.py`, `models.py`, or the service files.
