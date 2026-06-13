# MODE: VIBECODABLE
# BRAAT BLOCK: Duplicate work detector
# MISSION: Detect repeated prompts and context loads with inspectable local math.

from __future__ import annotations

import json
from collections import defaultdict

from owrp.core.hashing import jaccard, token_fingerprint
from owrp.core.resource_accounting import estimate_context_minutes
from owrp.core.types import RecoveryMetric
from owrp.storage.sqlite_store import SQLiteStore


def detect_duplicate_prompts(store: SQLiteStore, threshold: float = 0.55) -> int:
    rows = store.fetch_llm_rows()
    found = 0
    fingerprints = {row["interaction_id"]: token_fingerprint(row["prompt"]) for row in rows}
    for i, left in enumerate(rows):
        for right in rows[i + 1 :]:
            if left["repo_id"] != right["repo_id"]:
                continue
            sim = jaccard(fingerprints[left["interaction_id"]], fingerprints[right["interaction_id"]])
            same_context = left["context_hash"] == right["context_hash"]
            if sim >= threshold or same_context:
                avoidable_tokens = min(int(left["tokens_spent"]), int(right["tokens_spent"]))
                avoidable_cost = min(float(left["cost_usd"]), float(right["cost_usd"]))
                store.insert_duplicate_pair(
                    left["interaction_id"],
                    right["interaction_id"],
                    round(sim, 4),
                    avoidable_tokens,
                    round(avoidable_cost, 6),
                )
                store.insert_recovery_metric(
                    RecoveryMetric(
                        metric_name="recovered_token_cost",
                        resource_lost=float(left["cost_usd"]) + float(right["cost_usd"]),
                        resource_measured=avoidable_cost,
                        resource_recovered=avoidable_cost,
                        unit="usd",
                        source=f"duplicate_prompt_pair:{left['interaction_id']}:{right['interaction_id']}",
                    )
                )
                found += 1
    return found


def detect_context_reconstruction(store: SQLiteStore) -> int:
    rows = store.fetch_llm_rows()
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for row in rows:
        grouped[(row["repo_id"], row["context_hash"])].append(row)

    found = 0
    for (repo_id, ctx_hash), group in grouped.items():
        if len(group) <= 1:
            continue
        sorted_group = sorted(group, key=lambda row: row["timestamp"])
        base_files = set(json.loads(sorted_group[0]["files_read_json"]))
        repeated_tokens = 0
        repeated_cost = 0.0
        for row in sorted_group[1:]:
            files = set(json.loads(row["files_read_json"]))
            overlap = len(base_files & files)
            if overlap == 0:
                continue
            ratio = overlap / max(1, len(files))
            repeated_tokens += int(int(row["tokens_spent"]) * min(1.0, ratio))
            repeated_cost += float(row["cost_usd"]) * min(1.0, ratio)
        if repeated_tokens <= 0:
            continue
        store.insert_context_reconstruction(
            ctx_hash=ctx_hash,
            repo_id=repo_id,
            repeated_loads=len(group) - 1,
            avoidable_context_tokens=repeated_tokens,
            avoidable_context_cost_usd=round(repeated_cost, 6),
        )
        store.insert_recovery_metric(
            RecoveryMetric(
                metric_name="recovered_engineer_time",
                resource_lost=estimate_context_minutes(sum(int(row["tokens_spent"]) for row in group)),
                resource_measured=estimate_context_minutes(repeated_tokens),
                resource_recovered=estimate_context_minutes(repeated_tokens),
                unit="engineer_minutes",
                source=f"context_reconstruction:{repo_id}:{ctx_hash}",
            )
        )
        found += 1
    return found


def run_measurement_pipeline(store: SQLiteStore) -> dict[str, int]:
    store.clear_detected_metrics()
    duplicate_pairs = detect_duplicate_prompts(store)
    context_events = detect_context_reconstruction(store)
    return {"duplicate_prompt_pairs": duplicate_pairs, "context_reconstruction_events": context_events}
