from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from tests.conftest import TEST_ADMIN_TOKEN

BEARER_HEADERS = {"Authorization": f"Bearer {TEST_ADMIN_TOKEN}"}


def test_concurrent_creates(client: TestClient) -> None:
    def create_segment(i: int) -> dict[str, object]:
        resp = client.post(
            "/api/segments",
            json={"type": "markdown", "title": f"Seg {i}"},
            headers=BEARER_HEADERS,
        )
        assert resp.status_code == 201
        data: dict[str, object] = resp.json()
        return data

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(create_segment, range(10)))

    assert len(results) == 10

    ids = {r["id"] for r in results}
    assert len(ids) == 10

    listing = client.get("/api/segments").json()
    assert len(listing) == 10

    sort_orders = sorted(s["sort_order"] for s in listing)
    assert sort_orders == list(range(10))


def test_concurrent_create_and_reorder(client: TestClient) -> None:
    segments = []
    for i in range(3):
        resp = client.post(
            "/api/segments",
            json={"type": "markdown", "title": f"Init {i}"},
            headers=BEARER_HEADERS,
        )
        assert resp.status_code == 201
        segments.append(resp.json())

    seg_ids = [s["id"] for s in segments]

    def create_extra(i: int) -> dict[str, object]:
        resp = client.post(
            "/api/segments",
            json={"type": "markdown", "title": f"Extra {i}"},
            headers=BEARER_HEADERS,
        )
        assert resp.status_code == 201
        data: dict[str, object] = resp.json()
        return data

    def reorder() -> int:
        resp = client.put(
            "/api/segments/reorder",
            json={"segment_ids": list(reversed(seg_ids))},
            headers=BEARER_HEADERS,
        )
        return resp.status_code

    with ThreadPoolExecutor(max_workers=10) as pool:
        create_futures = [pool.submit(create_extra, i) for i in range(2)]
        reorder_future = pool.submit(reorder)

        for f in create_futures:
            f.result()
        reorder_status = reorder_future.result()

    assert 200 <= reorder_status < 300

    listing = client.get("/api/segments").json()
    assert len(listing) == 5

    sort_orders = [s["sort_order"] for s in listing]
    assert len(set(sort_orders)) == 5
