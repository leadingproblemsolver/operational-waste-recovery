#!/usr/bin/env sh
set -eu
ROOT=${1:-.}
owrp --root "$ROOT" ingest --input "$ROOT/data/sample_events.jsonl"
owrp --root "$ROOT" status
owrp --root "$ROOT" analyze
owrp --root "$ROOT" query "redis timeout" --json
owrp --root "$ROOT" report
owrp --root "$ROOT" export --format json --output "$ROOT/reports/interactions.json"
