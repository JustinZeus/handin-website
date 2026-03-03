import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.database import get_connection
from app.models import Page, PageCreateRequest, PageUpdateRequest


def _row_to_page(row: sqlite3.Row) -> Page:
    return Page(
        id=row["id"],
        name=row["name"],
        slug=row["slug"],
        sort_order=row["sort_order"],
        is_system=bool(row["is_system"]),
        is_hidden=bool(row["is_hidden"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def list_pages(db_path: Path) -> list[Page]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM pages ORDER BY is_system ASC, sort_order ASC"
        ).fetchall()
        return [_row_to_page(row) for row in rows]
    finally:
        conn.close()


def get_page(db_path: Path, page_id: str) -> Page | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        return _row_to_page(row) if row else None
    finally:
        conn.close()


def get_page_by_slug(db_path: Path, slug: str) -> Page | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM pages WHERE slug = ?", (slug,)).fetchone()
        return _row_to_page(row) if row else None
    finally:
        conn.close()


def create_page(db_path: Path, request: PageCreateRequest) -> Page:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order) + 1, 0) AS next_order FROM pages WHERE is_system = 0"
        ).fetchone()
        sort_order: int = row["next_order"] if row else 0

        page_id = str(uuid4())
        now = datetime.now(UTC).isoformat()

        conn.execute(
            "INSERT INTO pages"
            " (id, name, slug, sort_order, is_system, is_hidden, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, 0, 0, ?, ?)",
            (page_id, request.name, request.slug, sort_order, now, now),
        )
        conn.commit()

        return Page(
            id=page_id,
            name=request.name,
            slug=request.slug,
            sort_order=sort_order,
            is_system=False,
            is_hidden=False,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )
    finally:
        conn.close()


def update_page(db_path: Path, page_id: str, request: PageUpdateRequest) -> Page | None:
    conn = get_connection(db_path)
    try:
        existing = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        if existing is None:
            return None

        now = datetime.now(UTC).isoformat()
        name = request.name if request.name is not None else existing["name"]
        slug = request.slug if request.slug is not None else existing["slug"]
        is_hidden = (
            int(request.is_hidden) if request.is_hidden is not None else existing["is_hidden"]
        )

        conn.execute(
            "UPDATE pages SET name = ?, slug = ?, is_hidden = ?, updated_at = ? WHERE id = ?",
            (name, slug, is_hidden, now, page_id),
        )
        conn.commit()
        return get_page(db_path, page_id)
    finally:
        conn.close()


def delete_page(db_path: Path, page_id: str) -> tuple[bool, str | None]:
    """Cascade-deletes the page and all its segments."""
    conn = get_connection(db_path)
    try:
        existing = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
        if existing is None:
            return False, "not_found"
        if existing["is_system"]:
            return False, "system_page"

        conn.execute("DELETE FROM segments WHERE page_id = ?", (page_id,))
        conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))
        conn.commit()
        return True, None
    finally:
        conn.close()


def reorder_pages(db_path: Path, page_ids: list[str]) -> list[Page]:
    """Reorders only non-system pages."""
    conn = get_connection(db_path)
    try:
        existing_ids = {
            row["id"]
            for row in conn.execute("SELECT id FROM pages WHERE is_system = 0").fetchall()
        }
        requested_ids = set(page_ids)
        missing = requested_ids - existing_ids
        if missing:
            raise ValueError(f"Page IDs not found: {missing}")

        now = datetime.now(UTC).isoformat()
        for index, pid in enumerate(page_ids):
            conn.execute(
                "UPDATE pages SET sort_order = ?, updated_at = ? WHERE id = ?",
                (index, now, pid),
            )
        conn.commit()
        return list_pages(db_path)
    finally:
        conn.close()
