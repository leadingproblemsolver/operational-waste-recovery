from __future__ import annotations

import sqlite3

import pytest

from owrp.evaluation import (
    PairLabel,
    build_frozen_manifest,
    evaluate_duplicate_pairs,
    validate_release_floor,
)


class PredictionStore:
    def __init__(self, predictions: list[tuple[str, str, float]]):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE duplicate_pairs (left_id TEXT, right_id TEXT, similarity REAL)"
        )
        self.conn.executemany(
            "INSERT INTO duplicate_pairs (left_id, right_id, similarity) VALUES (?, ?, ?)",
            predictions,
        )


def label(
    left: str,
    right: str,
    left_session: str,
    value: str,
    right_session: str | None = None,
) -> PairLabel:
    return PairLabel.from_mapping(
        {
            "left_event_id": left,
            "right_event_id": right,
            "left_session_id": left_session,
            "right_session_id": right_session or left_session,
            "label": value,
            "evidence": f"human comparison of {left} and {right}",
        }
    )


def test_real_corpus_metrics_preserve_ambiguity_and_failure_examples() -> None:
    store = PredictionStore(
        [
            ("e1", "e2", 0.95),
            ("e3", "e4", 0.84),
            ("e7", "e8", 0.75),
        ]
    )
    labels = [
        label("e1", "e2", "s1", "repeated_work"),
        label("e3", "e4", "s1", "legitimate_revisit"),
        label("e5", "e6", "s2", "repeated_work"),
        label("e7", "e8", "s2", "ambiguous"),
        label("e9", "e10", "s2", "non_duplicate"),
    ]

    report = evaluate_duplicate_pairs(store, labels)

    assert report["confusion_matrix"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert report["precision"] == 0.5
    assert report["recall"] == 0.5
    assert report["f1"] == 0.5
    assert report["ambiguous_pairs"] == 1
    assert report["scored_pairs"] == 4
    assert report["false_positives"][0]["label"] == "legitimate_revisit"
    assert report["false_negatives"][0]["label"] == "repeated_work"
    assert report["confidence_stratified_precision"][">=0.90"]["precision"] == 1.0
    assert report["confidence_stratified_precision"][">=0.80"]["precision"] == 0.5


def test_cross_session_pair_keeps_event_to_session_provenance_when_ids_reorder() -> None:
    item = PairLabel.from_mapping(
        {
            "left_event_id": "z-event",
            "right_event_id": "a-event",
            "left_session_id": "later-session",
            "right_session_id": "earlier-session",
            "label": "repeated_work",
            "evidence": "same unresolved task reconstructed after context loss",
        }
    )

    assert item.left_event_id == "a-event"
    assert item.left_session_id == "earlier-session"
    assert item.right_event_id == "z-event"
    assert item.right_session_id == "later-session"
    assert item.crosses_sessions is True


def test_evaluator_refuses_selective_precision_when_prediction_is_unlabeled() -> None:
    store = PredictionStore([("e1", "e2", 0.92), ("e3", "e4", 0.81)])
    labels = [label("e1", "e2", "s1", "repeated_work")]

    with pytest.raises(ValueError, match="missing human labels"):
        evaluate_duplicate_pairs(store, labels)


def test_pair_label_requires_human_inspectable_evidence() -> None:
    with pytest.raises(ValueError, match="evidence"):
        PairLabel.from_mapping(
            {
                "left_event_id": "e1",
                "right_event_id": "e2",
                "session_id": "s1",
                "label": "repeated_work",
            }
        )


def test_release_floor_requires_frozen_hash_and_minimum_real_corpus_shape() -> None:
    labels: list[PairLabel] = []
    for session_number in range(5):
        session = f"session-{session_number}"
        ids = [f"{session}-event-{index}" for index in range(6)]
        for index in range(5):
            labels.append(
                label(ids[index], ids[index + 1], session, "non_duplicate")
            )

    manifest = build_frozen_manifest(
        labels,
        source="sanitized-coding-agent-history",
        frozen_at="2026-08-23T17:00:00Z",
    )

    validate_release_floor(manifest, labels)
    assert manifest["work_episodes"] == 30
    assert manifest["distinct_sessions"] == 5
    assert len(manifest["labels_sha256"]) == 64

    tampered = dict(manifest)
    tampered["labels_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        validate_release_floor(tampered, labels)


def test_release_floor_cannot_be_claimed_from_tiny_synthetic_fixture() -> None:
    labels = [label("e1", "e2", "s1", "repeated_work")]
    manifest = build_frozen_manifest(
        labels,
        source="synthetic-test",
        frozen_at="2026-08-23T17:00:00Z",
    )

    with pytest.raises(ValueError, match="at least 30 episodes"):
        validate_release_floor(manifest, labels)
