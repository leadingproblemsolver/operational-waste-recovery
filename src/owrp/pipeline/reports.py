# MODE: VIBECODABLE
# BRAAT BLOCK: Resource recovery report
# MISSION: Report resources recovered, not AI vanity metrics.

from __future__ import annotations

import json
from pathlib import Path

from owrp.core.paths import ensure_runtime_dirs, weekly_report_path
from owrp.core.resource_accounting import percent_recovered
from owrp.storage.sqlite_store import SQLiteStore


def build_weekly_report(store: SQLiteStore, root: Path | None = None) -> dict[str, object]:
    status = store.status()
    duplicate_cost = float(status["duplicate_cost"])
    context_cost = float(status["avoidable_context_cost"])
    raw_avoidable_cost = duplicate_cost + context_cost
    llm_spend = float(status["llm_spend"])
    # Duplicate prompts and context reconstruction can overlap. Use the stronger single
    # signal for the headline number so the report stays conservative.
    avoidable_cost = min(llm_spend, max(duplicate_cost, context_cost))
    report = {
        "llm_spend_usd": round(llm_spend, 6),
        "avoidable_spend_usd": round(avoidable_cost, 6),
        "raw_detected_avoidable_spend_usd": round(raw_avoidable_cost, 6),
        "recovered_percent": percent_recovered(llm_spend, avoidable_cost),
        "tokens_spent": int(status["tokens_spent"]),
        "duplicate_token_spend": int(status["duplicate_tokens"]),
        "avoidable_context_tokens": int(status["avoidable_context_tokens"]),
        "repeated_investigations_detected": int(status["duplicate_pairs"]),
        "repeated_context_loads_detected": int(status["repeated_context_events"]),
        "incident_reasoning_nodes": int(status["incident_nodes"]),
        "context_capsules": int(status["context_capsules"]),
    }
    ensure_runtime_dirs(root)
    weekly_report_path(root).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report
