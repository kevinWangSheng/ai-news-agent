"""API smoke — wire-up only; full integration tests need testcontainer."""
from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    with TestClient(app) as c:
        r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_openapi_lists_expected_routes():
    with TestClient(app) as c:
        r = c.get("/openapi.json")
    paths = r.json()["paths"]
    for p in (
        "/api/ingest",
        "/api/items",
        "/api/items/{item_id}",
        "/api/search",
        "/api/topics",
        "/api/entities",
        "/api/digests",
        "/api/sources",
        "/health/processing",
        "/health/scoring",
        "/health/db",
    ):
        assert p in paths, f"missing {p}"


def test_cursor_roundtrip():
    from datetime import datetime, timezone
    from app.api.cursor import decode, encode

    ts = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    c = encode(ts, 42)
    out = decode(c)
    assert out == (ts, 42)
    assert decode(None) is None
    assert decode("not-base64") is None


def test_rrf_merge_orders_by_combined_rank():
    from app.api.routes.search import _rrf_merge

    class It:
        def __init__(self, i):
            self.id = i
            self.final_score = None  # neutralize final_score so RRF alone orders

    a, b, c = It(1), It(2), It(3)
    out = _rrf_merge([(a, 0), (b, 0)], [(b, 0), (c, 0)])
    assert {x.id for x in out} == {1, 2, 3}
    assert out[0].id == 2  # appears in both lists → highest RRF
