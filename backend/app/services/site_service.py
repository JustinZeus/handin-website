from pathlib import Path

from app.database import get_connection

DEFAULT_SITE_TITLE = "Untitled Site"


def get_site_title(db_path: Path, *, default: str = DEFAULT_SITE_TITLE) -> str:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT value FROM site WHERE key = ?", ("title",)).fetchone()
        if row is None:
            return default
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
