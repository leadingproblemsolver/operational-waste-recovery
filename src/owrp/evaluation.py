from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import combinations
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from owrp.core.hashing import similarity


VALID_PAIR_LABELS = frozenset(
    {"repeated_work", "legitimate_revisit", "non_duplicate", "ambiguous"}
)
NEGATIVE_PAIR_LABELS = frozenset({"legitimate_revisit", "non_duplicate"})


def pair_key(left_event_id: str, right_event_id: str) -> tuple[str, str]:
    left = str(left_event_id).strip()
    right = str(right_event_id).strip()
    if not left or not right:
        raise ValueError("pair labels require both event ids")
    if left == right:
        raise ValueError("pair labels must reference two distinct events")
    return tuple(sorted((left, right)))


@dataclass(frozen=True, slots=True)
class PairLabel:
    left_event_id: str
    right_event_id: str
    left_session_id: str
    right_session_id: str
    label: str
    evidence: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PairLabel":
        raw_left = str(raw.get("left_event_id") or "").strip()
        raw_right = str(raw.get("right_event_id") or "").strip()
        if not raw_left or not raw_right:
            raise ValueError("pair labels require both event ids")
        if raw_left == raw_right:
            raise ValueError("pair labels must reference two distinct events")

        shared_session = str(raw.get("session_id") or "").strip()
        left_session = str(raw.get("left_session_id") or shared_session).strip()
        right_session = str(raw.get("right_session_id") or shared_session).strip()
        if not left_session or not right_session:
            raise ValueError(
                "pair labels require left_session_id and right_session_id "
                "(or session_id when both events are in one session)"
            )

        label = str(raw.get("label") or "").strip().lower()
        evidence = str(raw.get("evidence") or raw.get("rationale") or "").strip()
        if label not in VALID_PAIR_LABELS:
            raise ValueError(
                f"unsupported pair label {label!r}; expected one of {sorted(VALID_PAIR_LABELS)}"
            )
        if not evidence:
            raise ValueError("pair labels require human-inspectable evidence/rationale")

        if raw_left <= raw_right:
            left, right = raw_left, raw_right
            left_session_id, right_session_id = left_session, right_session
        else:
            left, right = raw_right, raw_left
            left_session_id, right_session_id = right_session, left_session

        return cls(
            left,
            right,
            left_session_id,
            right_session_id,
            label,
            evidence,
        )

    @property
    def key(self) -> tuple[str, str]:
        return pair_key(self.left_event_id, self.right_event_id)

    @property
    def scored(self) -> bool:
        return self.label != "ambiguous"

    @property
    def is_positive(self) -> bool:
        return self.label == "repeated_work"

    @property
    def crosses_sessions(self) -> bool:
        return self.left_session_id != self.right_session_id

    def to_dict(self) -> dict[str, str]:
        return {
            "left_event_id": self.left_event_id,
            "right_event_id": self.right_event_id,
            "left_session_id": self.left_session_id,
            "right_session_id": self.right_session_id,
            "label": self.label,
            "evidence": self.evidence,
        }


def load_pair_labels(path: Path) -> list[PairLabel]:
    labels: list[PairLabel] = []
    seen: dict[tuple[str, str], PairLabel] = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                if not isinstance(raw, dict):
                    raise ValueError("label record must be an object")
                label = PairLabel.from_mapping(raw)
            except Exception as error:
                raise ValueError(f"label line {line_number}: {error}") from error
            if label.key in seen:
                raise ValueError(
                    f"duplicate pair label for {label.key[0]} / {label.key[1]}"
                )
            seen[label.key] = label
            labels.append(label)
    if not labels:
        raise ValueError("label file contains no pair labels")
    return labels


def _predictions(store: Any) -> dict[tuple[str, str], float]:
    rows = store.conn.execute(
        "SELECT left_id, right_id, similarity FROM duplicate_pairs"
    ).fetchall()
    result: dict[tuple[str, str], float] = {}
    for row in rows:
        result[pair_key(row["left_id"], row["right_id"])] = float(row["similarity"])
    return result


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall == 0:
        return None
    return round(2 * precision * recall / (precision + recall), 6)


def _sessions(labels: Iterable[PairLabel]) -> set[str]:
    result: set[str] = set()
    for label in labels:
        result.add(label.left_session_id)
        result.add(label.right_session_id)
    return result


def build_pair_label_queue(
    store: Any,
    *,
    session_metadata_key: str = "session_id",
    prompt_excerpt_chars: int = 320,
) -> list[dict[str, Any]]:
    """Build the complete human-label queue over the detector's same-repo scope.

    The detector compares every pair of interactions in the same repo, including
    cross-session pairs. The labeling queue therefore does the same rather than
    sampling convenient pairs. Every event must carry an explicit session id in
    metadata; missing session provenance is a hard error rather than an inferred
    session count.
    """

    key = session_metadata_key.strip()
    if not key:
        raise ValueError("session_metadata_key is required")
    if prompt_excerpt_chars < 40:
        raise ValueError("prompt_excerpt_chars must be at least 40")

    rows = store.conn.execute(
        """
        SELECT event_id, timestamp, repo_id, prompt, metadata_json
        FROM interactions
        ORDER BY timestamp, event_id
        """
    ).fetchall()
    events: list[dict[str, str]] = []
    for row in rows:
        metadata = json.loads(row["metadata_json"] or "{}")
        if not isinstance(metadata, dict):
            raise ValueError(f"event {row['event_id']} metadata must be an object")
        session_id = str(metadata.get(key) or "").strip()
        if not session_id:
            raise ValueError(
                f"event {row['event_id']} is missing metadata.{key}; "
                "session provenance must be supplied by the provider adapter"
            )
        events.append(
            {
                "event_id": str(row["event_id"]),
                "timestamp": str(row["timestamp"]),
                "repo_id": str(row["repo_id"]),
                "prompt": str(row["prompt"]),
                "session_id": session_id,
            }
        )

    grouped: dict[str, list[dict[str, str]]] = {}
    for event in events:
        grouped.setdefault(event["repo_id"], []).append(event)

    queue: list[dict[str, Any]] = []
    for repo_id in sorted(grouped):
        for first, second in combinations(grouped[repo_id], 2):
            if first["event_id"] <= second["event_id"]:
                left, right = first, second
            else:
                left, right = second, first
            queue.append(
                {
                    "left_event_id": left["event_id"],
                    "right_event_id": right["event_id"],
                    "left_session_id": left["session_id"],
                    "right_session_id": right["session_id"],
                    "repo_id": repo_id,
                    "detector_similarity": round(
                        similarity(left["prompt"], right["prompt"]), 6
                    ),
                    "left_prompt_excerpt": left["prompt"][:prompt_excerpt_chars],
                    "right_prompt_excerpt": right["prompt"][:prompt_excerpt_chars],
                    "label": "",
                    "evidence": "",
                }
            )
    return queue


def evaluate_duplicate_pairs(
    store: Any,
    labels: Iterable[PairLabel],
    *,
    require_all_predictions_labeled: bool = True,
) -> dict[str, Any]:
    """Score persisted duplicate predictions against frozen human pair labels.

    `ambiguous` labels are reported but excluded from precision/recall so uncertain
    human judgment is not coerced into fake binary ground truth.

    By default, every predicted pair must have a human label. This prevents a
    selectively labeled corpus from inflating precision by silently omitting
    inconvenient predictions.
    """

    label_list = list(labels)
    if not label_list:
        raise ValueError("evaluation requires at least one pair label")

    by_key: dict[tuple[str, str], PairLabel] = {}
    for label in label_list:
        if label.key in by_key:
            raise ValueError(f"duplicate label for pair {label.key}")
        by_key[label.key] = label

    predictions = _predictions(store)
    unlabeled_predictions = sorted(set(predictions) - set(by_key))
    if require_all_predictions_labeled and unlabeled_predictions:
        preview = ", ".join(f"{a}/{b}" for a, b in unlabeled_predictions[:5])
        raise ValueError(
            "predicted pairs are missing human labels; refusing selective precision "
            f"measurement ({preview})"
        )

    tp = fp = fn = tn = 0
    false_positives: list[dict[str, Any]] = []
    false_negatives: list[dict[str, Any]] = []
    ambiguous = 0

    for key, label in by_key.items():
        predicted = key in predictions
        if not label.scored:
            ambiguous += 1
            continue
        if label.is_positive and predicted:
            tp += 1
        elif label.is_positive and not predicted:
            fn += 1
            false_negatives.append({**label.to_dict(), "similarity": None})
        elif label.label in NEGATIVE_PAIR_LABELS and predicted:
            fp += 1
            false_positives.append(
                {**label.to_dict(), "similarity": round(predictions[key], 6)}
            )
        else:
            tn += 1

    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = _f1(precision, recall)

    confidence_precision: dict[str, dict[str, int | float | None]] = {}
    for minimum in (0.72, 0.80, 0.90):
        selected = [
            (key, score)
            for key, score in predictions.items()
            if score >= minimum and key in by_key and by_key[key].scored
        ]
        selected_tp = sum(1 for key, _ in selected if by_key[key].is_positive)
        selected_fp = sum(
            1 for key, _ in selected if by_key[key].label in NEGATIVE_PAIR_LABELS
        )
        confidence_precision[f">={minimum:.2f}"] = {
            "predictions": len(selected),
            "tp": selected_tp,
            "fp": selected_fp,
            "precision": _ratio(selected_tp, selected_tp + selected_fp),
        }

    event_ids = {
        event_id
        for label in label_list
        for event_id in (label.left_event_id, label.right_event_id)
    }
    sessions = _sessions(label_list)

    return {
        "schema_version": 1,
        "work_episodes": len(event_ids),
        "distinct_sessions": len(sessions),
        "pair_labels": len(label_list),
        "cross_session_pairs": sum(label.crosses_sessions for label in label_list),
        "scored_pairs": len(label_list) - ambiguous,
        "ambiguous_pairs": ambiguous,
        "predicted_pairs": len(predictions),
        "unlabeled_predictions": [
            {"left_event_id": left, "right_event_id": right}
            for left, right in unlabeled_predictions
        ],
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confidence_stratified_precision": confidence_precision,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def canonical_labels_sha256(labels: Iterable[PairLabel]) -> str:
    canonical = "\n".join(
        json.dumps(label.to_dict(), sort_keys=True, separators=(",", ":"))
        for label in sorted(labels, key=lambda item: item.key)
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_frozen_manifest(
    labels: Iterable[PairLabel],
    *,
    source: str,
    frozen_at: str,
) -> dict[str, Any]:
    label_list = list(labels)
    if not source.strip() or not frozen_at.strip():
        raise ValueError("frozen manifests require source and frozen_at")
    event_ids = {
        event_id
        for label in label_list
        for event_id in (label.left_event_id, label.right_event_id)
    }
    sessions = _sessions(label_list)
    return {
        "schema_version": 1,
        "frozen": True,
        "source": source.strip(),
        "frozen_at": frozen_at.strip(),
        "labels_sha256": canonical_labels_sha256(label_list),
        "work_episodes": len(event_ids),
        "distinct_sessions": len(sessions),
        "pair_labels": len(label_list),
        "cross_session_pairs": sum(label.crosses_sessions for label in label_list),
    }


def validate_release_floor(
    manifest: Mapping[str, Any],
    labels: Iterable[PairLabel],
    *,
    minimum_episodes: int = 30,
    minimum_sessions: int = 5,
) -> None:
    label_list = list(labels)
    if manifest.get("frozen") is not True:
        raise ValueError("real-corpus labels must be frozen before tuning")
    expected_hash = canonical_labels_sha256(label_list)
    if manifest.get("labels_sha256") != expected_hash:
        raise ValueError("label hash does not match frozen manifest")

    actual_episode_count = len(
        {
            event_id
            for label in label_list
            for event_id in (label.left_event_id, label.right_event_id)
        }
    )
    actual_session_count = len(_sessions(label_list))
    if int(manifest.get("work_episodes") or 0) != actual_episode_count:
        raise ValueError("manifest work_episodes does not match labels")
    if int(manifest.get("distinct_sessions") or 0) != actual_session_count:
        raise ValueError("manifest distinct_sessions does not match labels")
    if actual_episode_count < minimum_episodes:
        raise ValueError(f"real-corpus floor requires at least {minimum_episodes} episodes")
    if actual_session_count < minimum_sessions:
        raise ValueError(f"real-corpus floor requires at least {minimum_sessions} sessions")
