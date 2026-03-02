# Slice 4: Asset Service + Routes + Docker

## Role

You are a backend Python developer implementing the asset upload/delete service, asset API routes, and Docker deployment for a FastAPI-based academic submission website. You follow TDD strictly: write all tests first, then implement until they pass.

## Objective

Create three production files (`services/asset_service.py`, `routes/assets.py`, `Dockerfile`, `docker-compose.yml`) and modify one (`main.py`). Create one test file (`tests/test_assets.py`). All tests must pass. All production files must pass `mypy --strict`.

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
- Use `Annotated[..., Depends(...)]` type aliases to satisfy ruff B008 (no function calls in default arguments)

## Step 0: Verify Previous Slices

Before writing any new code, verify that slices 1–3 are healthy. Run:

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

### `backend/app/auth.py`
```python
from fastapi import HTTPException, Request

from app.config import get_settings


def require_admin(request: Request) -> None:
    token = request.query_params.get("token")
    if token is None:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")

    if token is None or token != get_settings().admin_token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
```

### `backend/app/routes/segments.py` (for `get_db_path` and type alias patterns)
```python
import threading
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth import require_admin
from app.config import get_settings
from app.database import init_db
from app.models import (
    ReorderRequest,
    SegmentCreateRequest,
    SegmentResponse,
    SegmentUpdateRequest,
)
from app.services import segment_service

router = APIRouter(prefix="/api/segments", tags=["segments"])

# Serialize writes to prevent sort_order race conditions in SQLite
_write_lock = threading.Lock()


def get_db_path() -> Path:
    data_dir = get_settings().data_dir
    db_path = Path(data_dir) / "handin.db"
    init_db(db_path)
    return db_path


DbPath = Annotated[Path, Depends(get_db_path)]
Admin = Annotated[None, Depends(require_admin)]

# ... endpoints follow using DbPath and Admin type aliases ...
```

### `backend/app/main.py`
```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.config import get_settings
from app.database import init_db
from app.routes.auth import router as auth_router
from app.routes.segments import router as segments_router
from app.routes.site import router as site_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    db_path = Path(get_settings().data_dir) / "handin.db"
    init_db(db_path)
    yield


app = FastAPI(title="Handin Website", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(segments_router)
app.include_router(site_router)


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

### `pyproject.toml`
```toml
[project]
name = "handin-website"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.135.1",
    "uvicorn[standard]==0.41.0",
    "pydantic==2.12.5",
    "pydantic-settings==2.13.1",
    "python-multipart==0.0.22",
]

[dependency-groups]
dev = [
    "pytest==9.0.2",
    "httpx==0.28.1",
    "ruff==0.15.4",
    "mypy==1.19.1",
]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]

[tool.ruff]
target-version = "py312"
line-length = 99
src = ["backend"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]

[tool.ruff.lint.isort]
known-first-party = ["app"]

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

- Assets are uploaded as multipart files and stored as `data/assets/<uuid>.<ext>`
- Original filename is NOT used on disk (prevents path traversal and collisions)
- The extension is extracted from the original filename, validated against `Settings.allowed_upload_types`
- File size is validated against `Settings.max_upload_bytes`
- Assets are served via FastAPI's `StaticFiles` mount at `/api/assets`
- Upload and delete endpoints require admin auth
- The asset service is a pure function layer — it receives `assets_dir: Path` and operates on the filesystem
- Docker: multi-stage build (Node frontend build → Python backend), single container serves everything

## Step 1: Write Tests

Write ALL tests FIRST, before any production code. Use the `client` fixture from conftest.

### `backend/tests/test_assets.py`

**Helper constants at module level:**
```python
from tests.conftest import TEST_ADMIN_TOKEN

BEARER_HEADERS = {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}
```

**Asset route tests:**

1. **`test_upload_asset`** — `POST /api/assets` with `BEARER_HEADERS` and a multipart file upload (`file` field, filename `test.pdf`, content `b"fake pdf content"`, content type `application/pdf`). Assert `201`. Response JSON has `filename` key. The `filename` value should NOT equal `test.pdf` (it's UUID-based). The `filename` should end with `.pdf`.

2. **`test_upload_asset_file_exists_on_disk`** — Upload a file via POST. Extract the returned `filename`. Use the `client` fixture's app settings to derive the assets directory (`Path(get_settings().data_dir) / "assets"`). Assert the file exists on disk at `assets_dir / filename`. Assert the file content matches what was uploaded.

3. **`test_upload_asset_disallowed_type`** — Upload a file with filename `malware.exe`. Assert `415` (Unsupported Media Type).

4. **`test_upload_asset_too_large`** — Upload a file larger than `max_upload_bytes`. Since the default is 100MB and creating that in a test is impractical, temporarily set `HANDIN_MAX_UPLOAD_BYTES` to a small value (e.g. `"100"`) in the test environment, clear and rebuild settings, then upload a file larger than 100 bytes. Assert `413` (Request Entity Too Large). Restore the environment after the test. Alternatively, use a fixture or monkeypatch approach — the key is that the test must verify the size limit works.

5. **`test_upload_asset_unauthorized`** — `POST /api/assets` without auth headers. Assert `401`.

6. **`test_delete_asset`** — Upload a file, extract the `filename`. Then `DELETE /api/assets/{filename}` with `BEARER_HEADERS`. Assert `204`. Verify the file no longer exists on disk.

7. **`test_delete_asset_not_found`** — `DELETE /api/assets/nonexistent.pdf` with `BEARER_HEADERS`. Assert `404`.

8. **`test_delete_asset_unauthorized`** — `DELETE /api/assets/somefile.pdf` without auth. Assert `401`.

9. **`test_serve_asset`** — Upload a file via the API. Then `GET /api/assets/{filename}` (no auth needed — public). Assert `200`. Assert the response body matches the uploaded content.

**Test conventions:**
- Each test function takes `client: TestClient` as parameter (from fixture)
- No mocking — use real HTTP calls via TestClient against real filesystem on temp directories
- Use `from app.config import get_settings` within tests where you need `data_dir`

## Step 2: Implement `backend/app/services/asset_service.py`

Two functions:

### `save_asset(assets_dir: Path, filename: str, content: bytes, allowed_types: str, max_bytes: int) -> str`
- Extract extension from `filename` (lowercase, without the dot)
- Validate extension is in `allowed_types` (comma-separated string) — raise `ValueError("Unsupported file type")` if not
- Validate `len(content)` does not exceed `max_bytes` — raise `ValueError("File too large")` if it does
- Generate a UUID-based filename: `f"{uuid4()}.{ext}"`
- Ensure `assets_dir` exists (`mkdir(parents=True, exist_ok=True)`)
- Write `content` to `assets_dir / new_filename`
- Return `new_filename`

### `delete_asset(assets_dir: Path, filename: str) -> bool`
- Construct full path: `assets_dir / filename`
- Validate the resolved path is within `assets_dir` (prevent path traversal) — return `False` if not
- If the file exists, delete it and return `True`
- Return `False` if the file doesn't exist

## Step 3: Implement `backend/app/routes/assets.py`

Create a FastAPI `APIRouter` with `prefix="/api/assets"` and `tags=["assets"]`.

**Shared dependency:**

### `get_assets_dir() -> Path`
- Reads `data_dir` from `get_settings()`
- Returns `Path(data_dir) / "assets"`

Use `Annotated` type aliases for dependencies (same pattern as `segments.py`).

**Endpoints:**

### `POST /` → `dict[str, str]` (status 201)
- Admin only (`Depends(require_admin)`)
- Accepts `file: UploadFile` parameter
- Reads the file content: `content = await file.read()`
- Calls `asset_service.save_asset(assets_dir, file.filename or "upload", content, settings.allowed_upload_types, settings.max_upload_bytes)`
- Catches `ValueError` — if message contains "File too large" return `413`, if "Unsupported file type" return `415`
- Returns `{"filename": saved_filename}` with status `201`

### `DELETE /{filename}` → `Response` (status 204)
- Admin only
- Calls `asset_service.delete_asset(assets_dir, filename)`
- Returns `204` if deleted, raises `HTTPException(404)` if not found

## Step 4: Modify `backend/app/main.py`

Update `main.py` to:

- Import and register the `assets_router`
- Mount `StaticFiles` at `/api/assets` to serve uploaded files. This mount must be registered **after** the assets API router (so POST/DELETE are handled by the router, and GET falls through to StaticFiles)
- The lifespan should also ensure the `assets` directory exists on startup (`(Path(data_dir) / "assets").mkdir(parents=True, exist_ok=True)`)

**Important:** The `StaticFiles` mount for assets serves files from `{data_dir}/assets/`. The API router handles POST and DELETE at `/api/assets`. To avoid conflicts, mount `StaticFiles` at a path like `/api/assets/file` or use a different strategy. One clean approach: register the assets API router with routes for upload (`POST /api/assets`) and delete (`DELETE /api/assets/{filename}`), then mount `StaticFiles(directory=assets_path)` at `/api/assets/file` for serving. Alternatively, keep the router at `/api/assets` and mount static files at `/api/assets` — FastAPI checks routers first, so `POST` and `DELETE` will be handled by the router, while `GET` requests for specific files will fall through to the static mount. Test which approach works and go with it.

## Step 5: Create `Dockerfile`

Multi-stage Dockerfile at the project root:

### Stage 1: Frontend build
```dockerfile
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build
```

### Stage 2: Python backend + built frontend
```dockerfile
FROM python:3.12-slim AS production

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ backend/
COPY --from=frontend-build /build/dist static/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
```

## Step 6: Create `docker-compose.yml`

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HANDIN_ADMIN_TOKEN=${HANDIN_ADMIN_TOKEN:?Set HANDIN_ADMIN_TOKEN}
      - HANDIN_DATA_DIR=/data
    volumes:
      - handin-data:/data

volumes:
  handin-data:
```

## Verification

After implementation, run these commands and ensure they all succeed:

```bash
uv run pytest backend/tests/test_assets.py -v
uv run mypy --strict backend/app/services/asset_service.py backend/app/routes/assets.py backend/app/main.py
uv run ruff check backend/app/services/asset_service.py backend/app/routes/assets.py backend/app/main.py
```

Then run the **full** verification suite to ensure nothing is broken:

```bash
uv run pytest backend/tests/ -v
uv run mypy --strict backend/app/ backend/tests/
uv run ruff check backend/
```

All tests must pass (~56 total: 6 database + 15 service + 24 route + 2 concurrency + 9 asset). Zero mypy errors. Zero ruff errors.

Optionally verify Docker builds (only if Docker is available):

```bash
docker compose build
```

## Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `backend/tests/test_assets.py` |
| CREATE | `backend/app/services/asset_service.py` |
| CREATE | `backend/app/routes/assets.py` |
| CREATE | `Dockerfile` |
| CREATE | `docker-compose.yml` |
| MODIFY | `backend/app/main.py` |
