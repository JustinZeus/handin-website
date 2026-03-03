import threading
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.auth import require_admin
from app.config import get_settings
from app.database import init_db
from app.models import (
    Page,
    PageCreateRequest,
    PageReorderRequest,
    PageUpdateRequest,
    SegmentResponse,
)
from app.services import page_service, segment_service

router = APIRouter(prefix="/api/pages", tags=["pages"])

_write_lock = threading.Lock()


def get_db_path() -> Path:
    data_dir = get_settings().data_dir
    db_path = Path(data_dir) / "handin.db"
    init_db(db_path)
    return db_path


DbPath = Annotated[Path, Depends(get_db_path)]
Admin = Annotated[None, Depends(require_admin)]


@router.get("/")
def list_pages(db_path: DbPath) -> list[Page]:
    return page_service.list_pages(db_path)


@router.post("/", status_code=201)
def create_page(request: PageCreateRequest, _: Admin, db_path: DbPath) -> Page:
    with _write_lock:
        # Check slug uniqueness
        existing = page_service.get_page_by_slug(db_path, request.slug)
        if existing:
            raise HTTPException(status_code=409, detail="A page with this slug already exists")
        return page_service.create_page(db_path, request)


@router.put("/reorder")
def reorder_pages(request: PageReorderRequest, _: Admin, db_path: DbPath) -> list[Page]:
    with _write_lock:
        try:
            return page_service.reorder_pages(db_path, request.page_ids)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{page_id}")
def get_page(page_id: str, db_path: DbPath) -> Page:
    page = page_service.get_page(db_path, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.get("/by-slug/{slug}")
def get_page_by_slug(slug: str, db_path: DbPath) -> Page:
    page = page_service.get_page_by_slug(db_path, slug)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.patch("/{page_id}")
def update_page(page_id: str, request: PageUpdateRequest, _: Admin, db_path: DbPath) -> Page:
    if request.slug is not None:
        existing = page_service.get_page_by_slug(db_path, request.slug)
        if existing and existing.id != page_id:
            raise HTTPException(status_code=409, detail="A page with this slug already exists")
    page = page_service.update_page(db_path, page_id, request)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.delete("/{page_id}", status_code=204)
def delete_page(page_id: str, _: Admin, db_path: DbPath) -> Response:
    deleted, error = page_service.delete_page(db_path, page_id)
    if not deleted:
        if error == "not_found":
            raise HTTPException(status_code=404, detail="Page not found")
        if error == "system_page":
            raise HTTPException(status_code=403, detail="System pages cannot be deleted")
    return Response(status_code=204)


@router.get("/{page_id}/segments")
def list_page_segments(page_id: str, db_path: DbPath) -> list[SegmentResponse]:
    page = page_service.get_page(db_path, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    segments = segment_service.list_segments(db_path, page_id=page_id)
    return [SegmentResponse.model_validate(s.model_dump()) for s in segments]
