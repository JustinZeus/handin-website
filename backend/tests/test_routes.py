from uuid import uuid4

from fastapi.testclient import TestClient

from tests.conftest import TEST_ADMIN_TOKEN

BEARER_HEADERS = {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}


def _create_segment(
    client: TestClient,
    title: str = "Test",
    seg_type: str = "markdown",
) -> dict[str, object]:
    resp = client.post(
        "/api/segments",
        json={"type": seg_type, "title": title},
        headers=BEARER_HEADERS,
    )
    assert resp.status_code == 201
    data: dict[str, object] = resp.json()
    return data


# --- Segment route tests ---


def test_list_segments_empty(client: TestClient) -> None:
    resp = client.get("/api/segments")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_segment(client: TestClient) -> None:
    data = _create_segment(client, title="Intro")
    assert "id" in data
    assert data["title"] == "Intro"
    assert data["type"] == "markdown"
    assert data["sort_order"] == 0


def test_create_segment_unauthorized(client: TestClient) -> None:
    resp = client.post("/api/segments", json={"type": "markdown", "title": "X"})
    assert resp.status_code == 401


def test_create_segment_wrong_token(client: TestClient) -> None:
    resp = client.post(
        "/api/segments",
        json={"type": "markdown", "title": "X"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401


def test_create_segment_via_query_param(client: TestClient) -> None:
    resp = client.post(
        f"/api/segments?token={TEST_ADMIN_TOKEN}",
        json={"type": "markdown", "title": "Query Auth"},
    )
    assert resp.status_code == 201


def test_get_segment(client: TestClient) -> None:
    created = _create_segment(client, title="Fetch Me")
    seg_id = created["id"]
    resp = client.get(f"/api/segments/{seg_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Fetch Me"


def test_get_segment_not_found(client: TestClient) -> None:
    resp = client.get(f"/api/segments/{uuid4()}")
    assert resp.status_code == 404


def test_update_segment(client: TestClient) -> None:
    created = _create_segment(client, title="Original")
    seg_id = created["id"]
    resp = client.patch(
        f"/api/segments/{seg_id}",
        json={"title": "Updated"},
        headers=BEARER_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_update_segment_not_found(client: TestClient) -> None:
    resp = client.patch(
        f"/api/segments/{uuid4()}",
        json={"title": "Nope"},
        headers=BEARER_HEADERS,
    )
    assert resp.status_code == 404


def test_update_segment_unauthorized(client: TestClient) -> None:
    created = _create_segment(client, title="NoAuth")
    seg_id = created["id"]
    resp = client.patch(
        f"/api/segments/{seg_id}",
        json={"title": "Hacked"},
    )
    assert resp.status_code == 401


def test_delete_segment(client: TestClient) -> None:
    created = _create_segment(client, title="Delete Me")
    seg_id = created["id"]
    resp = client.delete(f"/api/segments/{seg_id}", headers=BEARER_HEADERS)
    assert resp.status_code == 204
    resp2 = client.get(f"/api/segments/{seg_id}")
    assert resp2.status_code == 404


def test_delete_segment_not_found(client: TestClient) -> None:
    resp = client.delete(f"/api/segments/{uuid4()}", headers=BEARER_HEADERS)
    assert resp.status_code == 404


def test_delete_segment_unauthorized(client: TestClient) -> None:
    created = _create_segment(client, title="NoAuthDel")
    seg_id = created["id"]
    resp = client.delete(f"/api/segments/{seg_id}")
    assert resp.status_code == 401


def test_reorder_segments(client: TestClient) -> None:
    a = _create_segment(client, title="A")
    b = _create_segment(client, title="B")
    c = _create_segment(client, title="C")

    resp = client.put(
        "/api/segments/reorder",
        json={"segment_ids": [c["id"], a["id"], b["id"]]},
        headers=BEARER_HEADERS,
    )
    assert resp.status_code == 200

    listing = client.get("/api/segments").json()
    titles = [s["title"] for s in listing]
    assert titles == ["C", "A", "B"]


def test_reorder_segments_invalid_ids(client: TestClient) -> None:
    resp = client.put(
        "/api/segments/reorder",
        json={"segment_ids": [str(uuid4())]},
        headers=BEARER_HEADERS,
    )
    assert resp.status_code == 400


def test_reorder_segments_unauthorized(client: TestClient) -> None:
    resp = client.put(
        "/api/segments/reorder",
        json={"segment_ids": []},
    )
    assert resp.status_code == 401


# --- Site route tests ---


def test_get_site_title_default(client: TestClient) -> None:
    resp = client.get("/api/site")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Untitled Site"


def test_update_site_title(client: TestClient) -> None:
    resp = client.put(
        "/api/site",
        json={"title": "My Course"},
        headers=BEARER_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "My Course"

    resp2 = client.get("/api/site")
    assert resp2.json()["title"] == "My Course"


def test_update_site_title_unauthorized(client: TestClient) -> None:
    resp = client.put("/api/site", json={"title": "Hacked"})
    assert resp.status_code == 401


# --- Auth route tests ---


def test_auth_verify_valid_bearer(client: TestClient) -> None:
    resp = client.get("/api/auth/verify", headers=BEARER_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {"valid": True}


def test_auth_verify_valid_query_param(client: TestClient) -> None:
    resp = client.get(f"/api/auth/verify?token={TEST_ADMIN_TOKEN}")
    assert resp.status_code == 200
    assert resp.json() == {"valid": True}


def test_auth_verify_invalid(client: TestClient) -> None:
    resp = client.get(
        "/api/auth/verify",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401


def test_auth_verify_no_token(client: TestClient) -> None:
    resp = client.get("/api/auth/verify")
    assert resp.status_code == 401


# --- Health test ---


def test_health(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
