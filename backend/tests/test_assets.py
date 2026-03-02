import os
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import TEST_ADMIN_TOKEN

BEARER_HEADERS = {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}


def test_upload_asset(client: TestClient) -> None:
    resp = client.post(
        "/api/assets",
        headers=BEARER_HEADERS,
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "filename" in data
    assert data["filename"] != "test.pdf"
    assert data["filename"].endswith(".pdf")


def test_upload_asset_file_exists_on_disk(client: TestClient) -> None:
    resp = client.post(
        "/api/assets",
        headers=BEARER_HEADERS,
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert resp.status_code == 201
    filename = resp.json()["filename"]

    from app.config import get_settings

    assets_dir = Path(get_settings().data_dir) / "assets"
    file_path = assets_dir / filename
    assert file_path.exists()
    assert file_path.read_bytes() == b"fake pdf content"


def test_upload_asset_disallowed_type(client: TestClient) -> None:
    resp = client.post(
        "/api/assets",
        headers=BEARER_HEADERS,
        files={"file": ("malware.exe", b"evil bytes", "application/octet-stream")},
    )
    assert resp.status_code == 415


def test_upload_asset_too_large(client: TestClient) -> None:
    from app.config import get_settings

    original = os.environ.get("HANDIN_MAX_UPLOAD_BYTES")
    os.environ["HANDIN_MAX_UPLOAD_BYTES"] = "100"
    get_settings.cache_clear()
    try:
        resp = client.post(
            "/api/assets",
            headers=BEARER_HEADERS,
            files={"file": ("big.pdf", b"x" * 200, "application/pdf")},
        )
        assert resp.status_code == 413
    finally:
        if original is None:
            os.environ.pop("HANDIN_MAX_UPLOAD_BYTES", None)
        else:
            os.environ["HANDIN_MAX_UPLOAD_BYTES"] = original
        get_settings.cache_clear()


def test_upload_asset_unauthorized(client: TestClient) -> None:
    resp = client.post(
        "/api/assets",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert resp.status_code == 401


def test_delete_asset(client: TestClient) -> None:
    resp = client.post(
        "/api/assets",
        headers=BEARER_HEADERS,
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
    )
    assert resp.status_code == 201
    filename = resp.json()["filename"]

    from app.config import get_settings

    assets_dir = Path(get_settings().data_dir) / "assets"

    del_resp = client.delete(f"/api/assets/{filename}", headers=BEARER_HEADERS)
    assert del_resp.status_code == 204
    assert not (assets_dir / filename).exists()


def test_delete_asset_not_found(client: TestClient) -> None:
    resp = client.delete("/api/assets/nonexistent.pdf", headers=BEARER_HEADERS)
    assert resp.status_code == 404


def test_delete_asset_unauthorized(client: TestClient) -> None:
    resp = client.delete("/api/assets/somefile.pdf")
    assert resp.status_code == 401


def test_serve_asset(client: TestClient) -> None:
    content = b"fake pdf content for serving"
    resp = client.post(
        "/api/assets",
        headers=BEARER_HEADERS,
        files={"file": ("test.pdf", content, "application/pdf")},
    )
    assert resp.status_code == 201
    filename = resp.json()["filename"]

    get_resp = client.get(f"/api/assets/{filename}")
    assert get_resp.status_code == 200
    assert get_resp.content == content
