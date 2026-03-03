import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.database import get_connection
from app.models import TeamMember, TeamMemberCreateRequest


def _row_to_member(row: sqlite3.Row) -> TeamMember:
    return TeamMember(
        id=row["id"],
        name=row["name"],
        student_number=row["student_number"],
        sort_order=row["sort_order"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def list_members(db_path: Path) -> list[TeamMember]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM team_members ORDER BY sort_order ASC").fetchall()
        return [_row_to_member(row) for row in rows]
    finally:
        conn.close()


def add_member(db_path: Path, request: TeamMemberCreateRequest) -> TeamMember:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order) + 1, 0) AS next_order FROM team_members"
        ).fetchone()
        sort_order: int = row["next_order"] if row else 0
        member_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        conn.execute(
            "INSERT INTO team_members"
            " (id, name, student_number, sort_order, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (member_id, request.name, request.student_number, sort_order, now, now),
        )
        conn.commit()
        return TeamMember(
            id=member_id,
            name=request.name,
            student_number=request.student_number,
            sort_order=sort_order,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )
    finally:
        conn.close()


def delete_member(db_path: Path, member_id: str) -> bool:
    conn = get_connection(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM team_members WHERE id = ?", (member_id,)
        ).fetchone()
        if existing is None:
            return False
        conn.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def reorder_members(db_path: Path, member_ids: list[str]) -> list[TeamMember]:
    conn = get_connection(db_path)
    try:
        existing_ids = {
            row["id"] for row in conn.execute("SELECT id FROM team_members").fetchall()
        }
        missing = set(member_ids) - existing_ids
        if missing:
            raise ValueError(f"Member IDs not found: {missing}")
        now = datetime.now(UTC).isoformat()
        for index, mid in enumerate(member_ids):
            conn.execute(
                "UPDATE team_members SET sort_order = ?, updated_at = ? WHERE id = ?",
                (index, now, mid),
            )
        conn.commit()
        return list_members(db_path)
    finally:
        conn.close()
