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


@router.get("/")
def list_segments(db_path: DbPath) -> list[SegmentResponse]:
    segments = segment_service.list_segments(db_path)
    return [SegmentResponse.model_validate(s.model_dump()) for s in segments]


@router.post("/", status_code=201)
def create_segment(
    request: SegmentCreateRequest,
    _: Admin,
    db_path: DbPath,
) -> SegmentResponse:
    with _write_lock:
        segment = segment_service.create_segment(db_path, request)
    return SegmentResponse.model_validate(segment.model_dump())


@router.put("/reorder")
def reorder_segments(
    request: ReorderRequest,
    _: Admin,
    db_path: DbPath,
) -> list[SegmentResponse]:
    with _write_lock:
        try:
            segments = segment_service.reorder_segments(db_path, request.segment_ids)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    return [SegmentResponse.model_validate(s.model_dump()) for s in segments]


@router.get("/{segment_id}")
def get_segment(segment_id: UUID, db_path: DbPath) -> SegmentResponse:
    segment = segment_service.get_segment(db_path, segment_id)
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return SegmentResponse.model_validate(segment.model_dump())


@router.patch("/{segment_id}")
def update_segment(
    segment_id: UUID,
    request: SegmentUpdateRequest,
    _: Admin,
    db_path: DbPath,
) -> SegmentResponse:
    segment = segment_service.update_segment(db_path, segment_id, request)
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return SegmentResponse.model_validate(segment.model_dump())


@router.delete("/{segment_id}", status_code=204)
def delete_segment(segment_id: UUID, _: Admin, db_path: DbPath) -> Response:
    deleted = segment_service.delete_segment(db_path, segment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Segment not found")
    return Response(status_code=204)
