import threading
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth import require_admin
from app.config import get_settings
from app.database import init_db
from app.models import TeamMember, TeamMemberCreateRequest, TeamMemberReorderRequest
from app.services import team_service

router = APIRouter(prefix="/api/team", tags=["team"])

_write_lock = threading.Lock()


def get_db_path() -> Path:
    data_dir = get_settings().data_dir
    db_path = Path(data_dir) / "handin.db"
    init_db(db_path)
    return db_path


DbPath = Annotated[Path, Depends(get_db_path)]
Admin = Annotated[None, Depends(require_admin)]


@router.get("/")
def list_members(db_path: DbPath) -> list[TeamMember]:
    return team_service.list_members(db_path)


@router.post("/", status_code=201)
def add_member(request: TeamMemberCreateRequest, _: Admin, db_path: DbPath) -> TeamMember:
    with _write_lock:
        return team_service.add_member(db_path, request)


@router.put("/reorder")
def reorder_members(
    request: TeamMemberReorderRequest, _: Admin, db_path: DbPath
) -> list[TeamMember]:
    with _write_lock:
        try:
            return team_service.reorder_members(db_path, request.member_ids)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: str, _: Admin, db_path: DbPath) -> Response:
    deleted = team_service.delete_member(db_path, member_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Team member not found")
    return Response(status_code=204)
