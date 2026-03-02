from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import require_admin
from app.config import get_settings
from app.models import SiteResponse, SiteUpdateRequest
from app.routes.segments import get_db_path
from app.services import site_service

router = APIRouter(prefix="/api/site", tags=["site"])

Admin = Annotated[None, Depends(require_admin)]
DbPath = Annotated[Path, Depends(get_db_path)]


@router.get("/")
def get_site(db_path: DbPath) -> SiteResponse:
    title = site_service.get_site_title(db_path, default=get_settings().site_title)
    return SiteResponse(title=title)


@router.put("/")
def update_site(
    request: SiteUpdateRequest,
    _: Admin,
    db_path: DbPath,
) -> SiteResponse:
    title = site_service.update_site_title(db_path, request.title)
    return SiteResponse(title=title)
