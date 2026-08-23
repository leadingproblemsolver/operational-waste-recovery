from __future__ import annotations

import argparse
import json
from pathlib import Path

from owrp.real_corpus_eval import evaluate_store
from owrp.storage.sqlite_store import SQLiteStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Score the current OWR duplicate detector against a frozen human-labeled "
            "pair set without converting ambiguous/unreviewed pairs into accuracy claims."
        )
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--labels", required=True)
    parser.add_argument("--threshold", type=float, default=0.72)
    parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    labels = Path(args.labels).resolve()
    store = SQLiteStore(root)
    try:
        result = evaluate_store(store, labels, detector_threshold=args.threshold)
    finally:
        store.close()

    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        print(output)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
