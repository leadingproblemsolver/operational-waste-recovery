#!/usr/bin/env bash
set -euo pipefail
python -m owrp.cli ingest
python -m owrp.cli status
python -m owrp.cli validate
python -m owrp.cli query "redis timeout"
