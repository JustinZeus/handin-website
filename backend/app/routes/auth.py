from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import require_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])

Admin = Annotated[None, Depends(require_admin)]


@router.get("/verify")
def verify_token(_: Admin) -> dict[str, bool]:
    return {"valid": True}
