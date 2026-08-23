from __future__ import annotations

import json
from pathlib import Path

import pytest

from owrp.real_corpus_eval import (
    HumanLabel,
    canonical_pair,
    load_labels,
    score_predictions,
)


def test_canonical_pair_is_order_independent() -> None:
    assert canonical_pair("evt-b", "evt-a") == ("evt-a", "evt-b")
    with pytest.raises(ValueError):
        canonical_pair("evt-a", "evt-a")


def test_score_predictions_keeps_ambiguous_and_unreviewed_out_of_accuracy() -> None:
    labels = [
        HumanLabel("a", "b", "duplicate"),
        HumanLabel("a", "c", "legitimate_revisit"),
        HumanLabel("a", "d", "duplicate"),
        HumanLabel("b", "c", "ambiguous"),
    ]
    predictions = [
        {"left_id": "b", "right_id": "a", "similarity": 0.91},
        {"left_id": "a", "right_id": "c", "similarity": 0.82},
        {"left_id": "b", "right_id": "d", "similarity": 0.75},
    ]

    result = score_predictions(labels, predictions, detector_threshold=0.72)

    assert result["reviewed_pairs"] == 3
    assert result["ambiguous_ignored"] == 1
    assert result["unreviewed_predictions"] == 1
    assert result["confusion"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 0}
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert result["f1"] == 0.5
    assert result["confidence_buckets"]["ge_0_90"]["precision"] == 1.0
    assert result["confidence_buckets"]["0_80_to_0_90"]["precision"] == 0.0


def test_load_labels_rejects_duplicate_pair_and_returns_digest(tmp_path: Path) -> None:
    path = tmp_path / "labels.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "left_id": "evt-1",
                        "right_id": "evt-2",
                        "label": "duplicate",
                        "rationale": "same investigation",
                    }
                ),
                json.dumps(
                    {
                        "left_id": "evt-2",
                        "right_id": "evt-1",
                        "label": "legitimate_revisit",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate human label"):
        load_labels(path)


def test_load_labels_rejects_unknown_label(tmp_path: Path) -> None:
    path = tmp_path / "labels.jsonl"
    path.write_text(
        json.dumps({"left_id": "a", "right_id": "b", "label": "probably"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="label must be one of"):
        load_labels(path)
