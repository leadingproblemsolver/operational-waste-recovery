from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from owrp.evaluation import build_frozen_manifest, load_pair_labels, validate_release_floor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze completed human labels into a hash-bound real-corpus manifest."
    )
    parser.add_argument("--labels", type=Path, required=True, help="completed pair-label JSONL")
    parser.add_argument("--source", required=True, help="literal provider/corpus source description")
    parser.add_argument("--output", type=Path, required=True, help="write frozen manifest JSON here")
    parser.add_argument("--minimum-episodes", type=int, default=30)
    parser.add_argument("--minimum-sessions", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    labels = load_pair_labels(args.labels)
    manifest = build_frozen_manifest(
        labels,
        source=args.source,
        frozen_at=datetime.now(timezone.utc).isoformat(),
    )
    validate_release_floor(
        manifest,
        labels,
        minimum_episodes=args.minimum_episodes,
        minimum_sessions=args.minimum_sessions,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
