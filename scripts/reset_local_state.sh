#!/usr/bin/env sh
set -eu
ROOT=${1:-.}
rm -f "$ROOT/data/owrp.sqlite" "$ROOT/data/owrp.sqlite-shm" "$ROOT/data/owrp.sqlite-wal"
rm -f "$ROOT/reports/recovery_report.json" "$ROOT/reports/recovery_report.md" "$ROOT/reports/interactions.json"
