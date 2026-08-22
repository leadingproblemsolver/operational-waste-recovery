from __future__ import annotations

from owrp.storage.sqlite_store import SQLiteStore


def _estimate_state(left_value: float, right_value: float) -> str:
    return "ESTIMATED" if left_value > 0 and right_value > 0 else "NOT_MEASURABLE"


def get_finding(store: SQLiteStore, pair_id: str) -> dict[str, object] | None:
    row = store.conn.execute(
        """
        SELECT
            pair.pair_id,
            pair.similarity,
            pair.avoidable_tokens,
            pair.avoidable_cost_usd,
            left_event.event_id AS left_event_id,
            left_event.timestamp AS left_timestamp,
            left_event.repo_id AS repo_id,
            left_event.source AS left_source,
            left_event.model_name AS left_model_name,
            left_event.prompt AS left_prompt,
            left_event.response AS left_response,
            left_event.total_tokens AS left_total_tokens,
            left_event.cost_usd AS left_cost_usd,
            left_event.classification AS left_classification,
            right_event.event_id AS right_event_id,
            right_event.timestamp AS right_timestamp,
            right_event.source AS right_source,
            right_event.model_name AS right_model_name,
            right_event.prompt AS right_prompt,
            right_event.response AS right_response,
            right_event.total_tokens AS right_total_tokens,
            right_event.cost_usd AS right_cost_usd,
            right_event.classification AS right_classification
        FROM duplicate_pairs AS pair
        JOIN interactions AS left_event ON left_event.event_id = pair.left_id
        JOIN interactions AS right_event ON right_event.event_id = pair.right_id
        WHERE pair.pair_id = ?
        """,
        (pair_id,),
    ).fetchone()
    if row is None:
        return None

    capsule = store.conn.execute(
        """
        SELECT capsule_id, capsule_text, source_count, estimated_tokens_saved
        FROM context_capsules
        WHERE repo_id = ?
        ORDER BY created_at DESC, capsule_id
        LIMIT 1
        """,
        (row["repo_id"],),
    ).fetchone()

    token_state = _estimate_state(row["left_total_tokens"], row["right_total_tokens"])
    cost_state = _estimate_state(row["left_cost_usd"], row["right_cost_usd"])
    measurement_state = (
        "ESTIMATED" if "ESTIMATED" in {token_state, cost_state} else "NOT_MEASURABLE"
    )

    return {
        "finding_id": row["pair_id"],
        "repo_id": row["repo_id"],
        "measurement_state": measurement_state,
        "observed": {
            "similarity": row["similarity"],
            "left": {
                "event_id": row["left_event_id"],
                "timestamp": row["left_timestamp"],
                "source": row["left_source"],
                "model_name": row["left_model_name"],
                "prompt": row["left_prompt"],
                "response": row["left_response"],
                "total_tokens": row["left_total_tokens"],
                "cost_usd": row["left_cost_usd"],
                "classification": row["left_classification"],
            },
            "right": {
                "event_id": row["right_event_id"],
                "timestamp": row["right_timestamp"],
                "source": row["right_source"],
                "model_name": row["right_model_name"],
                "prompt": row["right_prompt"],
                "response": row["right_response"],
                "total_tokens": row["right_total_tokens"],
                "cost_usd": row["right_cost_usd"],
                "classification": row["right_classification"],
            },
        },
        "inferred": {
            "label": "potential_rework",
            "avoidable_tokens": row["avoidable_tokens"] if token_state == "ESTIMATED" else None,
            "avoidable_cost_usd": (
                row["avoidable_cost_usd"] if cost_state == "ESTIMATED" else None
            ),
            "token_measurement_state": token_state,
            "cost_measurement_state": cost_state,
            "basis": (
                "Derived from prompt similarity and the minimum observed token/cost totals across "
                "the pair. This is an estimate, not realized savings."
            ),
        },
        "capsule": (
            {
                "capsule_id": capsule["capsule_id"],
                "text": capsule["capsule_text"],
                "source_count": capsule["source_count"],
                "estimated_tokens_saved": capsule["estimated_tokens_saved"],
                "measurement_state": "ESTIMATED",
            }
            if capsule is not None
            else None
        ),
    }
