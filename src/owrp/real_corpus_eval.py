from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from owrp.storage.sqlite_store import SQLiteStore

_ALLOWED_LABELS = {"duplicate", "legitimate_revisit", "ambiguous"}


def canonical_pair(left_id: str, right_id: str) -> tuple[str, str]:
    left = str(left_id).strip()
    right = str(right_id).strip()
    if not left or not right:
        raise ValueError("pair ids must be non-empty")
    if left == right:
        raise ValueError("pair ids must refer to two different events")
    return tuple(sorted((left, right)))


@dataclass(frozen=True, slots=True)
class HumanLabel:
    left_id: str
    right_id: str
    label: str
    rationale: str = ""

    @property
    def pair(self) -> tuple[str, str]:
        return canonical_pair(self.left_id, self.right_id)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "HumanLabel":
        label = str(value.get("label") or "").strip().lower()
        if label not in _ALLOWED_LABELS:
            raise ValueError(
                "label must be one of duplicate, legitimate_revisit, ambiguous"
            )
        return cls(
            left_id=str(value.get("left_id") or "").strip(),
            right_id=str(value.get("right_id") or "").strip(),
            label=label,
            rationale=str(value.get("rationale") or "").strip(),
        )


def load_labels(path: Path) -> tuple[list[HumanLabel], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    labels: list[HumanLabel] = []
    seen: dict[tuple[str, str], str] = {}
    for line_no, raw_line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid label JSON on line {line_no}: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValueError(f"label line {line_no} must be an object")
        item = HumanLabel.from_mapping(value)
        pair = item.pair
        prior = seen.get(pair)
        if prior is not None:
            raise ValueError(
                f"duplicate human label for pair {pair[0]}:{pair[1]} (existing={prior})"
            )
        seen[pair] = item.label
        labels.append(item)
    if not labels:
        raise ValueError("label file contains no labeled pairs")
    return labels, digest


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall == 0:
        return None
    return round(2 * precision * recall / (precision + recall), 6)


def score_predictions(
    labels: Iterable[HumanLabel],
    predictions: Iterable[Mapping[str, object]],
    *,
    detector_threshold: float,
) -> dict[str, object]:
    if not 0 <= detector_threshold <= 1:
        raise ValueError("detector_threshold must be between 0 and 1")

    label_map = {item.pair: item for item in labels}
    prediction_map: dict[tuple[str, str], dict[str, object]] = {}
    for value in predictions:
        pair = canonical_pair(str(value["left_id"]), str(value["right_id"]))
        score = float(value["similarity"])
        if not 0 <= score <= 1:
            raise ValueError("prediction similarity must be between 0 and 1")
        prediction_map[pair] = {
            "left_id": pair[0],
            "right_id": pair[1],
            "similarity": score,
        }

    tp = fp = fn = tn = 0
    reviewed_predictions: list[dict[str, object]] = []
    ambiguous_ignored = 0
    for pair, label in label_map.items():
        predicted = pair in prediction_map
        if label.label == "ambiguous":
            ambiguous_ignored += 1
            continue
        if predicted:
            reviewed_predictions.append(prediction_map[pair])
        if label.label == "duplicate" and predicted:
            tp += 1
        elif label.label == "duplicate" and not predicted:
            fn += 1
        elif label.label == "legitimate_revisit" and predicted:
            fp += 1
        elif label.label == "legitimate_revisit" and not predicted:
            tn += 1

    precision = _safe_ratio(tp, tp + fp)
    recall = _safe_ratio(tp, tp + fn)
    f1 = _f1(precision, recall)

    unreviewed = [
        value for pair, value in prediction_map.items() if pair not in label_map
    ]

    def bucket(low: float, high: float | None) -> dict[str, object]:
        items = [
            value
            for value in reviewed_predictions
            if float(value["similarity"]) >= low
            and (high is None or float(value["similarity"]) < high)
        ]
        bucket_tp = 0
        bucket_fp = 0
        for value in items:
            pair = canonical_pair(str(value["left_id"]), str(value["right_id"]))
            label = label_map[pair].label
            if label == "duplicate":
                bucket_tp += 1
            elif label == "legitimate_revisit":
                bucket_fp += 1
        return {
            "reviewed_predictions": len(items),
            "tp": bucket_tp,
            "fp": bucket_fp,
            "precision": _safe_ratio(bucket_tp, bucket_tp + bucket_fp),
        }

    return {
        "reviewed_pairs": tp + fp + fn + tn,
        "human_duplicates": tp + fn,
        "human_legitimate_revisits": fp + tn,
        "ambiguous_ignored": ambiguous_ignored,
        "predictions_total": len(prediction_map),
        "unreviewed_predictions": len(unreviewed),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confidence_buckets": {
            "ge_0_90": bucket(0.90, None),
            "0_80_to_0_90": bucket(0.80, 0.90),
            "threshold_to_0_80": bucket(detector_threshold, 0.80),
        },
        "unreviewed_prediction_pairs": sorted(
            unreviewed,
            key=lambda value: (
                -float(value["similarity"]),
                str(value["left_id"]),
                str(value["right_id"]),
            ),
        ),
    }


def evaluate_store(
    store: SQLiteStore,
    labels_path: Path,
    *,
    detector_threshold: float,
) -> dict[str, object]:
    labels, labels_sha256 = load_labels(labels_path)
    analysis = store.analyze(detector_threshold)
    predictions = [
        dict(row)
        for row in store.conn.execute(
            "SELECT left_id, right_id, similarity FROM duplicate_pairs ORDER BY pair_id"
        )
    ]
    metrics = score_predictions(
        labels,
        predictions,
        detector_threshold=detector_threshold,
    )
    return {
        "schema_version": 1,
        "status": "scored",
        "labels_sha256": labels_sha256,
        "detector_threshold": detector_threshold,
        "analysis": analysis,
        "metrics": metrics,
        "claim_boundary": {
            "proves": "detector behavior against the supplied frozen human labels",
            "does_not_prove": [
                "general population accuracy",
                "realized labor savings",
                "customer ROI",
                "production-scale reliability",
            ],
        },
    }
