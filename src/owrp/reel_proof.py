from __future__ import annotations

import os
from pathlib import Path

from owrp.pipeline.ingest import ingest_jsonl
from owrp.storage.sqlite_store import SQLiteStore


def build_reel_proof(sample_path: Path, work_root: Path) -> dict:
    """Build a compact, deterministic proof object for cold-distribution demos.

    This intentionally runs against isolated local state and reports only what
    the repository can prove from the supplied telemetry. It does not claim
    realized time savings, ROI, or production adoption.
    """
    sample_path = Path(sample_path)
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    db_path = work_root / "data" / "reel-proof.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    previous_db_path = os.environ.get("OWRP_DB_PATH")
    os.environ["OWRP_DB_PATH"] = str(db_path)
    try:
        store = SQLiteStore(work_root)
        try:
            counts, errors = ingest_jsonl(sample_path, store, strict=True)
            analysis = store.analyze(0.72)
            capsules = store.capsules()
            top_capsule = max(
                capsules,
                key=lambda item: (int(item["source_count"]), int(item["estimated_tokens_saved"])),
                default=None,
            )
            return {
                "status": "proof_generated",
                "source": "synthetic_sample_data",
                "input_events": counts["inserted"],
                "rejected_events": counts["rejected"],
                "duplicate_pairs": analysis["duplicate_pairs"],
                "avoidable_tokens": analysis["avoidable_tokens"],
                "avoidable_cost_usd": analysis["avoidable_cost_usd"],
                "context_capsules": analysis["capsules"],
                "top_capsule": None
                if top_capsule is None
                else {
                    "repo_id": top_capsule["repo_id"],
                    "source_count": top_capsule["source_count"],
                    "estimated_tokens_saved": top_capsule["estimated_tokens_saved"],
                    "capsule_text": top_capsule["capsule_text"],
                },
                "errors": errors,
                "claim_boundary": (
                    "Deterministic measurement over synthetic sample telemetry only; "
                    "not proof of realized labor/time savings, ROI, or production adoption."
                ),
            }
        finally:
            store.close()
    finally:
        if previous_db_path is None:
            os.environ.pop("OWRP_DB_PATH", None)
        else:
            os.environ["OWRP_DB_PATH"] = previous_db_path
