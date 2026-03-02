from pathlib import Path
from uuid import uuid4


def save_asset(
    assets_dir: Path,
    filename: str,
    content: bytes,
    allowed_types: str,
    max_bytes: int,
) -> str:
    ext = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
    allowed = {t.strip() for t in allowed_types.split(",")}
    if ext not in allowed:
        raise ValueError("Unsupported file type")

    if len(content) > max_bytes:
        raise ValueError("File too large")

    new_filename = f"{uuid4()}.{ext}"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / new_filename).write_bytes(content)
    return new_filename


def delete_asset(assets_dir: Path, filename: str) -> bool:
    file_path = (assets_dir / filename).resolve()
    if not str(file_path).startswith(str(assets_dir.resolve())):
        return False

    if not file_path.exists():
        return False

    file_path.unlink()
    return True
