from fastapi import HTTPException, Request

from app.config import get_settings


def require_admin(request: Request) -> None:
    token = request.query_params.get("token")
    if token is None:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")

    if token is None or token != get_settings().admin_token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
