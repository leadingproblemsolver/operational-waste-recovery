from __future__ import annotations

import json
import sqlite3

import pytest

from owrp.evaluation import build_pair_label_queue


class InteractionStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE interactions (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                repo_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )

    def add(self, event_id: str, timestamp: str, repo: str, prompt: str, session: str | None) -> None:
        metadata = {} if session is None else {"session_id": session}
        self.conn.execute(
            "INSERT INTO interactions VALUES (?, ?, ?, ?, ?)",
            (event_id, timestamp, repo, prompt, json.dumps(metadata)),
        )
        self.conn.commit()


def test_queue_matches_complete_same_repo_pair_universe() -> None:
    store = InteractionStore()
    store.add("e1", "2026-08-23T10:00:00Z", "repo-a", "debug redis timeout", "s1")
    store.add("e2", "2026-08-23T10:01:00Z", "repo-a", "debug redis timeout again", "s1")
    store.add("e3", "2026-08-23T11:00:00Z", "repo-a", "redis timeout investigation", "s2")
    store.add("e4", "2026-08-23T12:00:00Z", "repo-b", "debug redis timeout", "s9")

    queue = build_pair_label_queue(store)

    assert len(queue) == 3
    assert {(row["left_event_id"], row["right_event_id"]) for row in queue} == {
        ("e1", "e2"),
        ("e1", "e3"),
        ("e2", "e3"),
    }
    assert sum(row["left_session_id"] != row["right_session_id"] for row in queue) == 2
    assert all(row["repo_id"] == "repo-a" for row in queue)
    assert all(row["label"] == "" and row["evidence"] == "" for row in queue)


def test_queue_uses_detector_similarity_and_is_deterministic() -> None:
    store = InteractionStore()
    store.add("e1", "2026-08-23T10:00:00Z", "repo-a", "redis timeout retry", "s1")
    store.add("e2", "2026-08-23T10:01:00Z", "repo-a", "redis timeout", "s2")

    first = build_pair_label_queue(store)
    second = build_pair_label_queue(store)

    assert first == second
    assert first[0]["detector_similarity"] == pytest.approx(2 / 3, abs=1e-6)


def test_missing_session_provenance_is_a_hard_error() -> None:
    store = InteractionStore()
    store.add("e1", "2026-08-23T10:00:00Z", "repo-a", "first", "s1")
    store.add("e2", "2026-08-23T10:01:00Z", "repo-a", "second", None)

    with pytest.raises(ValueError, match="missing metadata.session_id"):
        build_pair_label_queue(store)


def test_custom_session_metadata_key_is_supported_without_inference() -> None:
    store = InteractionStore()
    store.conn.execute("DELETE FROM interactions")
    store.conn.execute(
        "INSERT INTO interactions VALUES (?, ?, ?, ?, ?)",
        ("e1", "2026-08-23T10:00:00Z", "repo-a", "first", json.dumps({"thread_id": "t1"})),
    )
    store.conn.execute(
        "INSERT INTO interactions VALUES (?, ?, ?, ?, ?)",
        ("e2", "2026-08-23T10:01:00Z", "repo-a", "second", json.dumps({"thread_id": "t2"})),
    )
    store.conn.commit()

    queue = build_pair_label_queue(store, session_metadata_key="thread_id")

    assert len(queue) == 1
    assert queue[0]["left_session_id"] == "t1"
    assert queue[0]["right_session_id"] == "t2"
