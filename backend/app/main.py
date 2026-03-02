from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routes.assets import router as assets_router
from app.routes.auth import router as auth_router
from app.routes.segments import router as segments_router
from app.routes.site import router as site_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    data_dir = Path(get_settings().data_dir)
    init_db(data_dir / "handin.db")
    assets_path = data_dir / "assets"
    assets_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Handin Website", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(segments_router)
app.include_router(site_router)
app.include_router(assets_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Serve built frontend SPA (must be registered last — catch-all)
_static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
