import sqlite3
from pathlib import Path


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
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
            CREATE TABLE IF NOT EXISTS pages (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                slug       TEXT NOT NULL UNIQUE,
                sort_order INTEGER NOT NULL,
                is_system  INTEGER NOT NULL DEFAULT 0,
                is_hidden  INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pages_order ON pages(sort_order)")
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_segments_order ON segments(sort_order)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id             TEXT PRIMARY KEY,
                name           TEXT NOT NULL,
                student_number TEXT NOT NULL,
                sort_order     INTEGER NOT NULL,
                created_at     TEXT NOT NULL,
                updated_at     TEXT NOT NULL
            )
        """)

        # Migrate existing table schemas (add columns if missing)
        _migrate_columns(conn)

        # Remove legacy segment types
        conn.execute("DELETE FROM segments WHERE type IN ('link', 'team')")

        conn.commit()

        # Ensure default pages exist
        _migrate_default_page(conn)
        _ensure_team_page(conn)
    finally:
        conn.close()


def _migrate_columns(conn: sqlite3.Connection) -> None:
    """Add any missing columns to existing tables."""
    seg_cols = [row["name"] for row in conn.execute("PRAGMA table_info(segments)").fetchall()]
    if "page_id" not in seg_cols:
        conn.execute("ALTER TABLE segments ADD COLUMN page_id TEXT REFERENCES pages(id)")

    page_cols = [row["name"] for row in conn.execute("PRAGMA table_info(pages)").fetchall()]
    if "is_system" not in page_cols:
        conn.execute("ALTER TABLE pages ADD COLUMN is_system INTEGER NOT NULL DEFAULT 0")
    if "is_hidden" not in page_cols:
        conn.execute("ALTER TABLE pages ADD COLUMN is_hidden INTEGER NOT NULL DEFAULT 0")


def _migrate_default_page(conn: sqlite3.Connection) -> None:
    """Ensure a Home page exists and all segments have a page_id."""
    from datetime import UTC, datetime
    from uuid import uuid4

    home_id: str | None = None
    home = conn.execute("SELECT id FROM pages WHERE slug = 'home'").fetchone()
    if not home:
        # Only create Home if no pages exist at all
        page_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM pages WHERE is_system = 0"
        ).fetchone()["cnt"]
        if page_count == 0:
            now = datetime.now(UTC).isoformat()
            default_id = str(uuid4())
            conn.execute(
                "INSERT INTO pages"
                " (id, name, slug, sort_order, is_system, is_hidden, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, 1, 0, ?, ?)",
                (default_id, "Home", "home", 0, now, now),
            )
            conn.commit()
            home_id = default_id
        else:
            first = conn.execute(
                "SELECT id FROM pages WHERE is_system = 0 ORDER BY sort_order ASC LIMIT 1"
            ).fetchone()
            home_id = first["id"] if first else None
    else:
        home_id = home["id"]

    if home_id:
        conn.execute("UPDATE segments SET page_id = ? WHERE page_id IS NULL", (home_id,))
        conn.commit()

    conn.execute("UPDATE pages SET is_system = 1 WHERE slug = 'home'")
    conn.commit()


def _ensure_team_page(conn: sqlite3.Connection) -> None:
    """Ensure the system Team page exists (always pinned last)."""
    from datetime import UTC, datetime
    from uuid import uuid4

    existing = conn.execute("SELECT id FROM pages WHERE slug = 'team'").fetchone()
    if existing:
        # Make sure it's marked as system
        conn.execute("UPDATE pages SET is_system = 1 WHERE slug = 'team'")
        conn.commit()
        return

    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO pages"
        " (id, name, slug, sort_order, is_system, is_hidden, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, 1, 0, ?, ?)",
        (str(uuid4()), "Team", "team", 9999, now, now),
    )
    conn.commit()


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn
