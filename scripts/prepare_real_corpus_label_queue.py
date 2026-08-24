from __future__ import annotations

import argparse
import json
from pathlib import Path

from owrp.evaluation import build_pair_label_queue
from owrp.storage.sqlite_store import SQLiteStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the complete same-repo human-label queue for a real OWR corpus."
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="isolated OWR root containing the ingested corpus SQLite state",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="write label-queue JSONL here",
    )
    parser.add_argument(
        "--session-metadata-key",
        default="session_id",
        help="metadata field carrying provider/session provenance",
    )
    parser.add_argument(
        "--prompt-excerpt-chars",
        type=int,
        default=320,
        help="prompt excerpt length included for human review",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store = SQLiteStore(args.root)
    try:
        queue = build_pair_label_queue(
            store,
            session_metadata_key=args.session_metadata_key,
            prompt_excerpt_chars=args.prompt_excerpt_chars,
        )
    finally:
        store.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for item in queue:
            handle.write(json.dumps(item, sort_keys=True) + "\n")

    summary = {
        "pair_count": len(queue),
        "cross_session_pairs": sum(
            item["left_session_id"] != item["right_session_id"] for item in queue
        ),
        "repositories": sorted({item["repo_id"] for item in queue}),
        "output": str(args.output),
        "claim_boundary": (
            "This file is an unlabeled review queue, not ground truth. "
            "Human labels/evidence must be completed and frozen before metrics are published."
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
