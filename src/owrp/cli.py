from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from owrp.core.config import load_config
from owrp.pipeline.ingest import ingest_jsonl
from owrp.pipeline.reports import build_report
from owrp.server import serve
from owrp.storage.sqlite_store import SQLiteStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="owrp",
        description="Measure repeated AI/engineering work and generate reusable context evidence.",
    )
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest")
    ingest.add_argument("--input", required=True)
    ingest.add_argument("--format", choices=["canonical", "openai", "generic"], default="canonical")
    ingest.add_argument("--mapping")
    ingest.add_argument("--allow-rejected", action="store_true")
    ingest.add_argument("--redact-sensitive", action="store_true", help="redact likely secrets, email addresses, and phone numbers before storage")
    ingest.add_argument("--allow-secrets", action="store_true", help="permit possible credentials in stored content; use only in controlled local environments")

    sub.add_parser("status")
    sub.add_parser("repositories")
    purge = sub.add_parser("purge")
    purge.add_argument("--before", help="delete interactions older than this ISO-8601 timestamp")
    purge.add_argument("--repo")
    purge.add_argument("--yes", action="store_true")
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--threshold", type=float)

    query = sub.add_parser("query")
    query.add_argument("text")
    query.add_argument("--limit", type=int, default=8)
    query.add_argument("--json", action="store_true")

    sub.add_parser("report")
    export = sub.add_parser("export")
    export.add_argument("--format", choices=["json", "csv"], default="json")
    export.add_argument("--output", required=True)

    server = sub.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8787)

    sub.add_parser("validate")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "serve":
        serve(root, args.host, args.port)
        return 0

    store = SQLiteStore(root)
    try:
        if args.command == "ingest":
            mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8")) if args.mapping else None
            counts, errors = ingest_jsonl(
                Path(args.input),
                store,
                args.format,
                mapping,
                strict=not args.allow_rejected,
                redact_sensitive=args.redact_sensitive,
                reject_secrets=not args.allow_secrets,
            )
            analysis = store.analyze(load_config(root).duplicate_threshold)
            print(json.dumps({"counts": counts, "errors": errors, "analysis": analysis}, indent=2))
            return 0 if not errors else 2

        if args.command == "status":
            print(json.dumps(store.status(), indent=2, sort_keys=True))
            return 0

        if args.command == "repositories":
            print(json.dumps({"repositories": store.repositories()}, indent=2, sort_keys=True))
            return 0

        if args.command == "purge":
            if not args.yes:
                print(json.dumps({"status": "blocked", "reason": "pass --yes to confirm destructive deletion"}, indent=2))
                return 2
            print(json.dumps(store.purge(before=args.before, repo_id=args.repo), indent=2))
            return 0

        if args.command == "analyze":
            threshold = args.threshold or load_config(root).duplicate_threshold
            print(json.dumps(store.analyze(threshold), indent=2))
            return 0

        if args.command == "query":
            hits = [hit.to_dict() for hit in store.query(args.text, args.limit)]
            if args.json:
                print(json.dumps(hits, indent=2))
            elif hits:
                blocks = []
                for hit in hits:
                    blocks.append(
                        f"[{hit['score']:.2f}] {hit['repo_id']} / {hit['classification']} / {hit['event_id']}\n"
                        f"{hit['prompt']}\n{hit['response']}"
                    )
                print("\n\n".join(blocks))
            else:
                print("No matching events.")
            return 0

        if args.command == "report":
            print(json.dumps(build_report(store, root), indent=2))
            return 0

        if args.command == "export":
            rows = store.export_rows()
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            if args.format == "json":
                output.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
            else:
                fields = [
                    "event_id", "timestamp", "user_id", "repo_id", "source", "model_name",
                    "prompt", "response", "prompt_tokens", "completion_tokens", "total_tokens",
                    "cost_usd", "classification",
                ]
                with output.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows({key: row.get(key) for key in fields} for row in rows)
            print(output)
            return 0

        if args.command == "validate":
            errors = []
            for relative in ("README.md", "pyproject.toml", "src/owrp/cli.py", "data/sample_events.jsonl"):
                if not (root / relative).exists():
                    errors.append(f"missing {relative}")
            result = {"status": "ok" if not errors else "fail", "errors": errors, "db": str(store.path)}
            print(json.dumps(result, indent=2))
            return 0 if not errors else 1
    finally:
        store.close()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
