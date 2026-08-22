from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path

from owrp.adapters import adapt
from owrp.server import Handler, ThreadingHTTPServer
from owrp.storage.sqlite_store import SQLiteStore


def event(event_id: str, prompt: str, *, total_tokens: int, cost_usd: float) -> dict:
    return {
        "event_id": event_id,
        "timestamp": "2026-08-22T18:00:00+00:00",
        "user_id": "test-user",
        "repo_id": "test-repo",
        "source": "test",
        "model_name": "test-model",
        "prompt": prompt,
        "response": f"response for {event_id}",
        "prompt_tokens": total_tokens,
        "completion_tokens": 0,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
        "classification": "unclassified",
        "files_read": [],
        "files_modified": [],
        "metadata": {},
    }


def seed_finding(root: Path, *, measurable: bool = True) -> str:
    store = SQLiteStore(root)
    try:
        total_tokens = 12 if measurable else 0
        cost_usd = 0.04 if measurable else 0.0
        store.insert(adapt(event("left", "debug retry loop", total_tokens=total_tokens, cost_usd=cost_usd)))
        store.insert(adapt(event("right", "debug retry loop again", total_tokens=total_tokens, cost_usd=cost_usd)))
        pair_id = "pair-measured" if measurable else "pair-unmeasurable"
        store.conn.execute(
            """
            INSERT INTO duplicate_pairs (
                pair_id, left_id, right_id, similarity,
                avoidable_tokens, avoidable_cost_usd
            ) VALUES (?, 'left', 'right', 0.91, ?, ?)
            """,
            (pair_id, total_tokens, cost_usd),
        )
        store.conn.execute(
            """
            INSERT INTO context_capsules (
                capsule_id, repo_id, capsule_text, source_count, estimated_tokens_saved
            ) VALUES ('capsule-1', 'test-repo', 'Review retry context before debugging again.', 2, 8)
            """
        )
        store.conn.commit()
        return pair_id
    finally:
        store.close()


@contextmanager
def running_server(root: Path, token: str = "test-token"):
    Handler.root = root
    Handler.token = token
    Handler.cors_origin = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        Handler.token = None


def request_json(port: int, path: str, token: str | None = None) -> tuple[int, dict]:
    connection = HTTPConnection("127.0.0.1", port, timeout=2)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        payload = json.loads(response.read())
        return response.status, payload
    finally:
        connection.close()


def test_finding_endpoint_requires_auth_and_separates_observed_from_inferred(tmp_path: Path) -> None:
    pair_id = seed_finding(tmp_path)

    with running_server(tmp_path) as port:
        unauthorized_status, unauthorized = request_json(port, f"/api/findings/{pair_id}")
        status, payload = request_json(port, f"/api/findings/{pair_id}", "test-token")
        missing_status, missing = request_json(port, "/api/findings/missing", "test-token")

    assert unauthorized_status == 401
    assert unauthorized == {"error": "unauthorized"}
    assert missing_status == 404
    assert missing == {"error": "finding_not_found"}

    assert status == 200
    assert payload["finding_id"] == pair_id
    assert payload["measurement_state"] == "ESTIMATED"
    assert payload["observed"]["similarity"] == 0.91
    assert payload["observed"]["left"]["prompt"] == "debug retry loop"
    assert payload["observed"]["right"]["prompt"] == "debug retry loop again"
    assert payload["inferred"]["label"] == "potential_rework"
    assert payload["inferred"]["avoidable_tokens"] == 12
    assert payload["inferred"]["token_measurement_state"] == "ESTIMATED"
    assert payload["capsule"]["capsule_id"] == "capsule-1"


def test_finding_endpoint_marks_missing_telemetry_not_measurable(tmp_path: Path) -> None:
    pair_id = seed_finding(tmp_path, measurable=False)

    with running_server(tmp_path) as port:
        status, payload = request_json(port, f"/api/findings/{pair_id}", "test-token")

    assert status == 200
    assert payload["measurement_state"] == "NOT_MEASURABLE"
    assert payload["inferred"]["avoidable_tokens"] is None
    assert payload["inferred"]["avoidable_cost_usd"] is None
    assert payload["inferred"]["token_measurement_state"] == "NOT_MEASURABLE"
    assert payload["inferred"]["cost_measurement_state"] == "NOT_MEASURABLE"
