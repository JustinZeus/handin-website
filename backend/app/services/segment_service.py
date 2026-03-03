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
        page_id=dict(row).get("page_id"),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def create_segment(db_path: Path, request: SegmentCreateRequest) -> Segment:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order) + 1, 0) AS next_order"
            " FROM segments WHERE page_id = ?",
            (request.page_id,),
        ).fetchone()
        sort_order: int = row["next_order"] if row else 0

        segment_id = uuid4()
        now = datetime.now(UTC).isoformat()
        metadata_json = json.dumps(request.metadata)

        cols = "id, type, sort_order, title, content, metadata, page_id, created_at, updated_at"
        conn.execute(
            f"INSERT INTO segments ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(segment_id),
                request.type.value,
                sort_order,
                request.title,
                request.content,
                metadata_json,
                request.page_id,
                now,
                now,
            ),
        )
        conn.commit()

        return Segment(
            id=segment_id,
            type=request.type,
            sort_order=sort_order,
            title=request.title,
            content=request.content,
            metadata=request.metadata,
            page_id=request.page_id,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )
    finally:
        conn.close()


def list_segments(db_path: Path, page_id: str | None = None) -> list[Segment]:
    conn = get_connection(db_path)
    try:
        if page_id is not None:
            rows = conn.execute(
                "SELECT * FROM segments WHERE page_id = ? ORDER BY sort_order ASC",
                (page_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM segments ORDER BY sort_order ASC").fetchall()
        return [_row_to_segment(row) for row in rows]
    finally:
        conn.close()


def get_segment(db_path: Path, segment_id: UUID) -> Segment | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM segments WHERE id = ?", (str(segment_id),)).fetchone()
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
            json.dumps(request.metadata) if request.metadata is not None else existing["metadata"]
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
        cursor = conn.execute("DELETE FROM segments WHERE id = ?", (str(segment_id),))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def reorder_segments(db_path: Path, segment_ids: list[UUID]) -> list[Segment]:
    conn = get_connection(db_path)
    try:
        existing_ids = {row["id"] for row in conn.execute("SELECT id FROM segments").fetchall()}
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

        # Return segments scoped to the same page as the first segment in the list
        if segment_ids:
            row = conn.execute(
                "SELECT page_id FROM segments WHERE id = ?", (str(segment_ids[0]),)
            ).fetchone()
            page_id = row["page_id"] if row else None
            return list_segments(db_path, page_id=page_id)
        return []
    finally:
        conn.close()
