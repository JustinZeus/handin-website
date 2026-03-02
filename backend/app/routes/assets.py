from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse

from app.auth import require_admin
from app.config import Settings, get_settings
from app.services import asset_service

router = APIRouter(prefix="/api/assets", tags=["assets"])


def get_assets_dir() -> Path:
    return Path(get_settings().data_dir) / "assets"


AssetsDir = Annotated[Path, Depends(get_assets_dir)]
Admin = Annotated[None, Depends(require_admin)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@router.post("/", status_code=201)
async def upload_asset(
    file: UploadFile,
    _admin: Admin,
    assets_dir: AssetsDir,
    settings: AppSettings,
) -> dict[str, str]:
    content = await file.read()
    try:
        saved = asset_service.save_asset(
            assets_dir,
            file.filename or "upload",
            content,
            settings.allowed_upload_types,
            settings.max_upload_bytes,
        )
    except ValueError as exc:
        msg = str(exc)
        if "File too large" in msg:
            raise HTTPException(status_code=413, detail=msg) from None
        raise HTTPException(status_code=415, detail=msg) from None
    return {"filename": saved}


@router.get("/{filename}")
def serve_asset(
    filename: str,
    assets_dir: AssetsDir,
) -> FileResponse:
    file_path = (assets_dir / filename).resolve()
    if not str(file_path).startswith(str(assets_dir.resolve())):
        raise HTTPException(status_code=404, detail="Asset not found")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(file_path)


@router.delete("/{filename}")
def delete_asset(
    filename: str,
    _admin: Admin,
    assets_dir: AssetsDir,
) -> Response:
    deleted = asset_service.delete_asset(assets_dir, filename)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    return Response(status_code=204)
