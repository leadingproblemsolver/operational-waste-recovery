from __future__ import annotations

import json
from http.server import ThreadingHTTPServer
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from owrp.adapters import adapt
from owrp.server import Handler
from owrp.storage.sqlite_store import SQLiteStore


def event(event_id: str, prompt: str):
    return adapt(
        {
            "event_id": event_id,
            "timestamp": "2026-08-22T12:00:00Z",
            "user_id": "u",
            "repo_id": "reworktrace",
            "source": "test",
            "model_name": "m",
            "prompt": prompt,
            "response": "inspected the same timeout path",
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30,
            "cost_usd": 0.02,
            "classification": "debugging",
        }
    )


def test_review_http_path_is_authenticated_and_reads_persisted_pair(tmp_path) -> None:
    store = SQLiteStore(tmp_path)
    try:
        store.insert(event("a", "debug redis timeout in cache layer"))
        store.insert(event("b", "debug redis timeout in cache layer again"))
        store.analyze(0.4)
        pair_id = store.conn.execute("SELECT pair_id FROM duplicate_pairs").fetchone()[0]
    finally:
        store.close()

    Handler.root = tmp_path
    Handler.token = "review-test-token"
    Handler.cors_origin = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    try:
        with pytest.raises(HTTPError) as unauthorized:
            urlopen(f"{base_url}/api/review/{pair_id}")
        assert unauthorized.value.code == 401
        assert json.loads(unauthorized.value.read())["error"] == "unauthorized"

        request = Request(
            f"{base_url}/api/review/{pair_id}",
            headers={"Authorization": "Bearer review-test-token"},
        )
        with urlopen(request) as response:
            assert response.status == 200
            assert response.headers["Cache-Control"] == "no-store"
            review = json.loads(response.read())
        assert review["audit_id"] == pair_id
        assert review["measurement_state"] == "OBSERVED"
        assert review["episode_a"]["event_id"] == "a"
        assert review["episode_b"]["event_id"] == "b"

        missing = Request(
            f"{base_url}/api/review/{'f' * 24}",
            headers={"Authorization": "Bearer review-test-token"},
        )
        with pytest.raises(HTTPError) as not_found:
            urlopen(missing)
        assert not_found.value.code == 404
        assert json.loads(not_found.value.read())["error"] == "review_not_found"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        Handler.token = None
