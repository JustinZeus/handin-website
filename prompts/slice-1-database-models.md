# Slice 1: Database + Models

## Role

You are a backend Python developer implementing the SQLite persistence layer and Pydantic models for a FastAPI-based academic submission website. You follow TDD strictly: write all tests first, then implement until they pass.

## Objective

Create two production files (`database.py`, `models.py`) and one test file (`test_database.py`). All tests must pass. Both production files must pass `mypy --strict`.

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
- Pydantic models use `PascalCase` + suffix convention (e.g., `SegmentCreateRequest`, `SegmentResponse`)
- Comments explain WHY, not WHAT

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

### `backend/tests/conftest.py`
```python
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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
def settings(_env_settings: None) -> "Settings":  # noqa: F821
    from app.config import Settings, get_settings

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

### Existing empty `__init__.py` files
- `backend/app/__init__.py`
- `backend/app/routes/__init__.py`
- `backend/app/services/__init__.py`
- `backend/tests/__init__.py`

## Step 1: Write Tests (`backend/tests/test_database.py`)

Write these tests FIRST, before any production code. Use the `db` and `tmp_data_dir` fixtures from conftest.

**Required test cases:**

1. **`test_init_db_creates_tables`** — Call `init_db` on a fresh path. Connect and verify both `site` and `segments` tables exist (query `sqlite_master`).

2. **`test_init_db_idempotent`** — Call `init_db` twice on the same path. No error raised. Tables still exist with correct schema.

3. **`test_wal_mode_enabled`** — After `init_db`, connect and run `PRAGMA journal_mode`. Assert the result is `"wal"`.

4. **`test_get_connection_busy_timeout`** — Call `get_connection`. Run `PRAGMA busy_timeout` on the returned connection. Assert the value is `5000`.

5. **`test_segments_table_schema`** — After init, verify the `segments` table has all expected columns: `id`, `type`, `sort_order`, `title`, `content`, `metadata`, `created_at`, `updated_at`.

6. **`test_site_table_schema`** — After init, verify the `site` table has columns: `key`, `value`.

**Test conventions:**
- Each test function takes `tmp_data_dir: Path` as parameter (from fixture)
- Tests call `init_db` and `get_connection` directly (imported from `app.database`)
- Use the `db` fixture where a pre-initialized database is needed
- No mocking — use real SQLite on temp directories

## Step 2: Implement `backend/app/database.py`

**Required functions:**

### `init_db(db_path: Path) -> None`
- Takes a `Path` to the SQLite database file
- Creates parent directories if they don't exist (`db_path.parent.mkdir(parents=True, exist_ok=True)`)
- Connects to SQLite at `db_path`
- Sets `PRAGMA journal_mode=WAL`
- Sets `PRAGMA busy_timeout=5000`
- Creates tables with `CREATE TABLE IF NOT EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS site (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS segments (
    id         TEXT PRIMARY KEY,
    type       TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL DEFAULT '',
    metadata   TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_segments_order ON segments(sort_order);
```

- Closes the connection when done

### `get_connection(db_path: Path) -> sqlite3.Connection`
- Returns a `sqlite3.Connection` with `row_factory = sqlite3.Row`
- Sets `PRAGMA busy_timeout=5000` on each new connection
- Does NOT set WAL mode (that's a one-time setup in `init_db`)

## Step 3: Implement `backend/app/models.py`

**Required models:**

### Enums
```python
class SegmentType(StrEnum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    IFRAME = "iframe"
    GALLERY = "gallery"
```

### Domain Models
- **`Segment`** — `id: UUID`, `type: SegmentType`, `sort_order: int`, `title: str`, `content: str = ""`, `metadata: dict[str, object] = Field(default_factory=dict)`, `created_at: datetime`, `updated_at: datetime`

### Request Models
- **`SegmentCreateRequest`** — `type: SegmentType`, `title: str`, `content: str = ""`, `metadata: dict[str, object] = Field(default_factory=dict)`
- **`SegmentUpdateRequest`** — `title: str | None = None`, `content: str | None = None`, `metadata: dict[str, object] | None = None`
- **`ReorderRequest`** — `segment_ids: list[UUID]`
- **`SiteUpdateRequest`** — `title: str`

### Response Models
- **`SegmentResponse`** — `id: UUID`, `type: SegmentType`, `sort_order: int`, `title: str`, `content: str`, `metadata: dict[str, object]`, `created_at: datetime`, `updated_at: datetime`
- **`SiteResponse`** — `title: str`

Use `Field(default_factory=...)` where needed. Use `from __future__ import annotations` if it helps with forward references, but prefer Python 3.12+ syntax.

## Verification

After implementation, run these commands and ensure they all succeed:

```bash
uv run pytest backend/tests/test_database.py -v
uv run mypy --strict backend/app/models.py backend/app/database.py
uv run ruff check backend/app/models.py backend/app/database.py
```

All tests must pass. Zero mypy errors. Zero ruff errors.

## Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `backend/tests/test_database.py` |
| CREATE | `backend/app/database.py` |
| CREATE | `backend/app/models.py` |

Do NOT modify any other files. Do NOT modify `conftest.py`, `config.py`, or `main.py`.
