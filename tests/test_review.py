from __future__ import annotations

from owrp.adapters import adapt
from owrp.review import build_review
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
            "response": "investigated the same timeout path",
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30,
            "cost_usd": 0.02,
            "classification": "debugging",
            "files_read": ["src/cache.py"],
        }
    )


def test_review_reads_persisted_pair_and_preserves_evidence_states(tmp_path) -> None:
    store = SQLiteStore(tmp_path)
    try:
        store.insert(event("a", "debug redis timeout in cache layer"))
        store.insert(event("b", "debug redis timeout in cache layer again"))
        analysis = store.analyze(0.4)
        assert analysis["duplicate_pairs"] == 1

        pair_id = store.conn.execute("SELECT pair_id FROM duplicate_pairs").fetchone()[0]
        review = build_review(store, pair_id)

        assert review is not None
        assert review["audit_id"] == pair_id
        assert review["measurement_state"] == "OBSERVED"
        assert review["finding"]["state"] == "OBSERVED"
        assert review["inference"]["state"] == "INFERRED"
        assert review["evidence"]["similarity"] >= 0.4
        assert review["evidence"]["avoidable_tokens"] == 30
        assert review["episode_a"]["event_id"] == "a"
        assert review["episode_b"]["event_id"] == "b"
        assert review["recovery_capsule"] is not None
        assert review["recovery_capsule"]["source_count"] == 2
        assert "Realized labor savings" in review["inference"]["summary"]
    finally:
        store.close()


def test_review_returns_none_for_unknown_or_malformed_pair(tmp_path) -> None:
    store = SQLiteStore(tmp_path)
    try:
        assert build_review(store, "f" * 24) is None
        assert build_review(store, "../../etc/passwd") is None
    finally:
        store.close()
