from __future__ import annotations

import json
from pathlib import Path

from owrp.adapters import adapt
from owrp.storage.sqlite_store import SQLiteStore
from owrp.privacy import sanitize_interaction

MAX_INPUT_BYTES = 50 * 1024 * 1024
MAX_LINE_BYTES = 2 * 1024 * 1024


def ingest_jsonl(path: Path, store: SQLiteStore, fmt="canonical", mapping=None, strict=True, redact_sensitive=False, reject_secrets=True):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"input does not exist or is not a file: {path}")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("input exceeds 50 MB")

    counts = {"inserted": 0, "rejected": 0, "lines": 0}
    errors: list[dict[str, object]] = []
    accepted = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            counts["lines"] += 1
            try:
                if len(line.encode("utf-8")) > MAX_LINE_BYTES:
                    raise ValueError("line exceeds 2 MB")
                raw = json.loads(line)
                if not isinstance(raw, dict):
                    raise ValueError("each JSONL record must be an object")
                event = adapt(raw, fmt, mapping)
                event = sanitize_interaction(event, redact_sensitive=redact_sensitive, reject_secrets=reject_secrets)
                problems = event.validate()
                if problems:
                    raise ValueError("; ".join(problems))
                accepted.append(event)
            except Exception as error:
                counts["rejected"] += 1
                errors.append({"line": line_number, "error": str(error)})

    if strict and errors:
        raise ValueError(f"line {errors[0]['line']}: {errors[0]['error']}")
    if accepted:
        store.insert_many(accepted)
    counts["inserted"] = len(accepted)
    return counts, errors
