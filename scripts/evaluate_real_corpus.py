from __future__ import annotations

import argparse
import json
from pathlib import Path

from owrp.evaluation import (
    evaluate_duplicate_pairs,
    load_pair_labels,
    validate_release_floor,
)
from owrp.storage.sqlite_store import SQLiteStore


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Score OWR duplicate-pair predictions against frozen human labels."
    )
    p.add_argument("--root", type=Path, required=True, help="isolated OWR root containing the eval SQLite state")
    p.add_argument("--labels", type=Path, required=True, help="frozen pair-label JSONL")
    p.add_argument("--manifest", type=Path, required=True, help="frozen dataset manifest JSON")
    p.add_argument("--output", type=Path, required=True, help="write evaluation report JSON here")
    p.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="rerun deterministic duplicate analysis at this threshold before scoring; use only on an isolated eval root",
    )
    p.add_argument(
        "--release-floor",
        action="store_true",
        help="require >=30 work episodes and >=5 distinct sessions",
    )
    return p


def main() -> int:
    args = parser().parse_args()
    labels = load_pair_labels(args.labels)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")

    validate_release_floor(
        manifest,
        labels,
        minimum_episodes=30 if args.release_floor else 1,
        minimum_sessions=5 if args.release_floor else 1,
    )

    store = SQLiteStore(args.root)
    try:
        analysis = None
        if args.threshold is not None:
            analysis = store.analyze(args.threshold)
        report = evaluate_duplicate_pairs(store, labels)
    finally:
        store.close()

    result = {
        "measurement_state": "OBSERVED",
        "manifest": manifest,
        "analysis_run": analysis,
        "evaluation": report,
        "claim_boundary": (
            "Metrics describe this frozen labeled corpus only. They do not establish "
            "organization-wide labor savings, production ROI, or accuracy on unseen providers."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
