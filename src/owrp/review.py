from __future__ import annotations

import re
from typing import Any

from owrp.storage.sqlite_store import SQLiteStore


_PAIR_ID = re.compile(r"^[0-9a-f]{24}$")


def build_review(store: SQLiteStore, pair_id: str) -> dict[str, Any] | None:
    """Return one persisted duplicate finding as an evidence-first review model."""
    normalized = pair_id.strip().lower()
    if not _PAIR_ID.fullmatch(normalized):
        return None

    row = store.conn.execute(
        """
        SELECT
            pair.pair_id,
            pair.similarity,
            pair.avoidable_tokens,
            pair.avoidable_cost_usd,
            left_event.event_id AS left_event_id,
            left_event.timestamp AS left_timestamp,
            left_event.repo_id AS left_repo_id,
            left_event.classification AS left_classification,
            left_event.prompt AS left_prompt,
            left_event.response AS left_response,
            right_event.event_id AS right_event_id,
            right_event.timestamp AS right_timestamp,
            right_event.repo_id AS right_repo_id,
            right_event.classification AS right_classification,
            right_event.prompt AS right_prompt,
            right_event.response AS right_response
        FROM duplicate_pairs AS pair
        JOIN interactions AS left_event ON left_event.event_id = pair.left_id
        JOIN interactions AS right_event ON right_event.event_id = pair.right_id
        WHERE pair.pair_id = ?
        """,
        (normalized,),
    ).fetchone()
    if row is None:
        return None

    capsule = store.conn.execute(
        """
        SELECT capsule_id, capsule_text, source_count, estimated_tokens_saved
        FROM context_capsules
        WHERE repo_id = ?
        ORDER BY created_at DESC, capsule_id ASC
        LIMIT 1
        """,
        (row["left_repo_id"],),
    ).fetchone()

    def episode(prefix: str) -> dict[str, str]:
        return {
            "event_id": str(row[f"{prefix}_event_id"]),
            "timestamp": str(row[f"{prefix}_timestamp"]),
            "repo_id": str(row[f"{prefix}_repo_id"]),
            "classification": str(row[f"{prefix}_classification"]),
            "prompt_excerpt": str(row[f"{prefix}_prompt"])[:240],
            "response_excerpt": str(row[f"{prefix}_response"])[:320],
        }

    return {
        "audit_id": str(row["pair_id"]),
        "measurement_state": "OBSERVED",
        "finding": {
            "state": "OBSERVED",
            "summary": "Repeated-work pair detected by deterministic prompt similarity.",
        },
        "evidence": {
            "similarity": round(float(row["similarity"]), 6),
            "avoidable_tokens": int(row["avoidable_tokens"]),
            "avoidable_cost_usd": round(float(row["avoidable_cost_usd"]), 6),
        },
        "episode_a": episode("left"),
        "episode_b": episode("right"),
        "inference": {
            "state": "INFERRED",
            "summary": (
                "This pair may represent avoidable context reconstruction. "
                "Realized labor savings and production ROI are not measured."
            ),
        },
        "recovery_capsule": (
            {
                "capsule_id": str(capsule["capsule_id"]),
                "text": str(capsule["capsule_text"]),
                "source_count": int(capsule["source_count"]),
                "estimated_tokens_saved": int(capsule["estimated_tokens_saved"]),
            }
            if capsule is not None
            else None
        ),
    }
