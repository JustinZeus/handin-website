import sqlite3
from pathlib import Path

from app.database import get_connection, init_db


def test_init_db_creates_tables(tmp_data_dir: Path) -> None:
    db_path = tmp_data_dir / "handin.db"
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "site" in tables
    assert "segments" in tables


def test_init_db_idempotent(tmp_data_dir: Path) -> None:
    db_path = tmp_data_dir / "handin.db"
    init_db(db_path)
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "site" in tables
    assert "segments" in tables


def test_wal_mode_enabled(tmp_data_dir: Path) -> None:
    db_path = tmp_data_dir / "handin.db"
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    conn.close()

    assert mode == "wal"


def test_get_connection_busy_timeout(db: Path) -> None:
    conn = get_connection(db)
    cursor = conn.execute("PRAGMA busy_timeout")
    timeout = cursor.fetchone()[0]
    conn.close()

    assert timeout == 5000


def test_segments_table_schema(db: Path) -> None:
    conn = sqlite3.connect(db)
    cursor = conn.execute("PRAGMA table_info(segments)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    expected = {
        "id",
        "type",
        "sort_order",
        "title",
        "content",
        "metadata",
        "page_id",
        "created_at",
        "updated_at",
    }
    assert columns == expected


def test_site_table_schema(db: Path) -> None:
    conn = sqlite3.connect(db)
    cursor = conn.execute("PRAGMA table_info(site)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    assert columns == {"key", "value"}
