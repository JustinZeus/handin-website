# Slice 2: Segment & Site Service Layer

## Role

You are a backend Python developer implementing the service layer (business logic + persistence) for a FastAPI-based academic submission website. You follow TDD strictly: write all tests first, then implement until they pass.

## Objective

Create two production files (`services/segment_service.py`, `services/site_service.py`) and one test file (`tests/test_services.py`). All tests must pass. Both production files must pass `mypy --strict`.

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

## Step 0: Verify Previous Slice

Before writing any new code, verify that the slice-1 implementation is healthy. Run:

```bash
uv run pytest backend/tests/ -v
uv run mypy --strict backend/app/database.py backend/app/models.py backend/app/config.py
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

### `backend/app/main.py`
```python
from fastapi import FastAPI

app = FastAPI(title="Handin Website")


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
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

## Step 1: Write Tests (`backend/tests/test_services.py`)

Write these tests FIRST, before any production code. Use the `db` fixture from conftest.

**Required test cases for segment service:**

1. **`test_create_segment`** — Create a segment via `create_segment(db_path, request)`. Assert it returns a `Segment` with a valid UUID, `sort_order == 0`, matching title/type/content, and `created_at == updated_at`.

2. **`test_create_segment_auto_increments_sort_order`** — Create three segments. Assert their `sort_order` values are `0`, `1`, `2` respectively.

3. **`test_list_segments_empty`** — On a fresh DB, `list_segments` returns an empty list.

4. **`test_list_segments_ordered`** — Create three segments, then list. Assert they come back in `sort_order` ascending order.

5. **`test_get_segment_found`** — Create a segment, then retrieve it by ID with `get_segment`. Assert it matches.

6. **`test_get_segment_not_found`** — Call `get_segment` with a random UUID. Assert it returns `None`.

7. **`test_update_segment_title`** — Create a segment, then update only its title via `update_segment(db_path, id, request)`. Assert title changed, content unchanged, and `updated_at > created_at`.

8. **`test_update_segment_not_found`** — Call `update_segment` with a random UUID. Assert it returns `None`.

9. **`test_delete_segment`** — Create a segment, delete it with `delete_segment(db_path, id)`. Assert returns `True`. Assert `get_segment` returns `None`.

10. **`test_delete_segment_not_found`** — Call `delete_segment` with a random UUID. Assert returns `False`.

11. **`test_reorder_segments`** — Create three segments (A, B, C). Call `reorder_segments(db_path, [C.id, A.id, B.id])`. List segments and assert the new sort order is C=0, A=1, B=2.

12. **`test_reorder_segments_invalid_ids`** — Call `reorder_segments` with a list containing a non-existent UUID. Assert it raises `ValueError`.

**Required test cases for site service:**

13. **`test_get_site_title_default`** — On a fresh DB, `get_site_title(db_path)` returns `"Untitled Site"`.

14. **`test_update_and_get_site_title`** — Call `update_site_title(db_path, "My Course")`. Then call `get_site_title`. Assert it returns `"My Course"`.

15. **`test_update_site_title_overwrites`** — Update title twice with different values. Assert `get_site_title` returns the second value.

**Test conventions:**
- Each test function takes `db: Path` as parameter (from fixture)
- Import functions from `app.services.segment_service` and `app.services.site_service`
- No mocking — use real SQLite on temp directories
- Use `time.sleep(0.01)` before update operations to ensure `updated_at` differs from `created_at`

## Step 2: Implement `backend/app/services/segment_service.py`

**Required functions:**

### `create_segment(db_path: Path, request: SegmentCreateRequest) -> Segment`
- Generate a new `uuid4()` for the segment ID
- Compute `sort_order` as the current max `sort_order + 1` (or `0` if no segments exist)
- Set `created_at` and `updated_at` to `datetime.now(UTC)` formatted as ISO 8601 strings
- Insert into the `segments` table (serialize `metadata` as JSON)
- Return a `Segment` model instance

### `list_segments(db_path: Path) -> list[Segment]`
- Query all segments ordered by `sort_order ASC`
- Deserialize `metadata` from JSON string to dict
- Return a list of `Segment` model instances

### `get_segment(db_path: Path, segment_id: UUID) -> Segment | None`
- Query by ID
- Return `Segment` if found, `None` otherwise
- Deserialize `metadata` from JSON string to dict

### `update_segment(db_path: Path, segment_id: UUID, request: SegmentUpdateRequest) -> Segment | None`
- Fetch existing segment first; return `None` if not found
- Only update fields that are not `None` in the request
- Always update `updated_at` to `datetime.now(UTC)`
- If `metadata` is provided, serialize it as JSON
- Return the updated `Segment`

### `delete_segment(db_path: Path, segment_id: UUID) -> bool`
- Delete the row by ID
- Return `True` if a row was deleted, `False` otherwise

### `reorder_segments(db_path: Path, segment_ids: list[UUID]) -> list[Segment]`
- Validate that all provided IDs exist in the database; raise `ValueError` if any are missing
- Update `sort_order` for each segment to match its index in the provided list
- Update `updated_at` for all reordered segments
- Use a transaction (all updates succeed or none do)
- Return the newly ordered list of segments

**Helper function (private):**

### `_row_to_segment(row: sqlite3.Row) -> Segment`
- Convert a `sqlite3.Row` to a `Segment` model instance
- Parse `metadata` from JSON string
- Parse `created_at` and `updated_at` from ISO 8601 strings
- Parse `id` from string to `UUID`
- Parse `type` from string to `SegmentType`

## Step 3: Implement `backend/app/services/site_service.py`

**Required functions:**

### `get_site_title(db_path: Path) -> str`
- Query the `site` table for `key = "title"`
- Return the value if found, `"Untitled Site"` if not

### `update_site_title(db_path: Path, title: str) -> str`
- Upsert (INSERT OR REPLACE) the `title` key in the `site` table
- Return the new title

## Verification

After implementation, run these commands and ensure they all succeed:

```bash
uv run pytest backend/tests/test_services.py -v
uv run mypy --strict backend/app/services/segment_service.py backend/app/services/site_service.py
uv run ruff check backend/app/services/segment_service.py backend/app/services/site_service.py
```

Then run the **full** verification suite to ensure nothing is broken and all files pass strict checks:

```bash
uv run pytest backend/tests/ -v
uv run mypy --strict backend/app/ backend/tests/
uv run ruff check backend/
```

All tests must pass. Zero mypy errors across the entire backend. Zero ruff errors.

## Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `backend/tests/test_services.py` |
| CREATE | `backend/app/services/segment_service.py` |
| CREATE | `backend/app/services/site_service.py` |

Do NOT modify any other files. Do NOT modify `conftest.py`, `config.py`, `main.py`, `database.py`, or `models.py`.
