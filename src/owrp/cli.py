# MODE: VIBECODABLE
# BRAAT BLOCK: CLI proof path
# MISSION: Make ingest -> status -> validate -> query executable and boring.

from __future__ import annotations

import argparse
import json
from pathlib import Path

from owrp.core.config import load_config
from owrp.core.logging import log_event
from owrp.core.paths import db_path, ensure_runtime_dirs
from owrp.execution_context.capsules import build_context_capsules
from owrp.pipeline.deduplicate import run_measurement_pipeline
from owrp.pipeline.ingest import ingest_jsonl
from owrp.pipeline.reports import build_weekly_report
from owrp.pipeline.validate import run_validation
from owrp.retrieval.query import format_hits, query_local_memory
from owrp.retrieval.similar_incidents import retrieve_similar_incidents
from owrp.storage.sqlite_store import SQLiteStore


def _store(root: Path) -> SQLiteStore:
    ensure_runtime_dirs(root)
    return SQLiteStore(root=root)


def cmd_ingest(args: argparse.Namespace) -> int:
    root = Path.cwd()
    input_path = Path(args.input)
    store = _store(root)
    try:
        counts = ingest_jsonl(input_path, store)
        measurement = run_measurement_pipeline(store)
        capsules = build_context_capsules(store)
        report = build_weekly_report(store, root)
        log_event(f"ingest input={input_path} counts={counts} measurement={measurement} capsules={capsules}", root)
        print("INGEST OK")
        print(json.dumps({"counts": counts, "measurement": measurement, "capsules_created": capsules, "report": report}, indent=2))
        return 0
    finally:
        store.close()


def cmd_status(args: argparse.Namespace) -> int:
    root = Path.cwd()
    store = _store(root)
    try:
        status = store.status()
        log_event(f"status {status}", root)
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0
    finally:
        store.close()


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path.cwd()
    errors, warnings = run_validation(root)
    if errors:
        print("VALIDATE FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1
    print("VALIDATE OK")
    for warning in warnings:
        print(f"WARN: {warning}")
    log_event("validate ok", root)
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    root = Path.cwd()
    store = _store(root)
    try:
        hits = query_local_memory(store, args.text, limit=args.limit)
        incidents = retrieve_similar_incidents(store, args.text, limit=3)
        print(format_hits(hits))
        if incidents:
            print("\nSimilar incident recovery candidates:")
            print(json.dumps(incidents, indent=2))
        log_event(f"query text={args.text!r} hits={len(hits)} incidents={len(incidents)}", root)
        return 0
    finally:
        store.close()


def cmd_report(args: argparse.Namespace) -> int:
    root = Path.cwd()
    store = _store(root)
    try:
        report = build_weekly_report(store, root)
        log_event("report generated", root)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    finally:
        store.close()


def cmd_inspect_db(args: argparse.Namespace) -> int:
    root = Path.cwd()
    print(db_path(root))
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    config = load_config(Path.cwd())
    print(json.dumps({"db_url": config.db_url, "openai_api_key_present": bool(config.openai_api_key)}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="owrp", description="Operational Waste Recovery Platform CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest JSONL telemetry and run recovery measurement")
    ingest.add_argument("--input", default="examples/example_events.jsonl", help="Path to JSONL event stream")
    ingest.set_defaults(func=cmd_ingest)

    status = sub.add_parser("status", help="Print inspectable resource ledger status")
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser("validate", help="Validate real paths, imports, database, and outputs")
    validate.set_defaults(func=cmd_validate)

    query = sub.add_parser("query", help="Query local interaction and incident memory")
    query.add_argument("text")
    query.add_argument("--limit", type=int, default=8)
    query.set_defaults(func=cmd_query)

    report = sub.add_parser("report", help="Generate weekly resource recovery report")
    report.set_defaults(func=cmd_report)

    inspect_db = sub.add_parser("inspect-db", help="Print actual SQLite DB path")
    inspect_db.set_defaults(func=cmd_inspect_db)

    config = sub.add_parser("config", help="Show config values used by implemented commands")
    config.set_defaults(func=cmd_config)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())






