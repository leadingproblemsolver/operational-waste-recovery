# MODE: VIBECODABLE
# BRAAT BLOCK: Observation ingestion layer
# MISSION: Convert JSONL into measured interaction and incident records.
# PROOF REQUIRED: Rows visible in data/owrp.sqlite.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from owrp.core.hashing import context_hash
from owrp.core.types import IncidentEvent, LLMInteraction
from owrp.storage.sqlite_store import SQLiteStore


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return (str(value),)


def parse_event(raw: dict[str, Any]) -> LLMInteraction | IncidentEvent:
    kind = raw.get("event_type") or "llm_interaction"
    if kind == "llm_interaction":
        files_read = _as_tuple(raw.get("files_read"))
        prompt = str(raw.get("prompt", ""))
        return LLMInteraction(
            interaction_id=str(raw["interaction_id"]),
            timestamp=str(raw["timestamp"]),
            user_id=str(raw.get("user_id", "unknown")),
            repo_id=str(raw.get("repo_id", "unknown")),
            branch=str(raw.get("branch", "unknown")),
            prompt=prompt,
            response=str(raw.get("response", "")),
            tokens_spent=int(raw.get("tokens_spent", raw.get("token_count", 0))),
            cost_usd=float(raw.get("cost_usd", raw.get("cost", 0.0))),
            files_read=files_read,
            files_modified=_as_tuple(raw.get("files_modified")),
            conversation_hash=str(raw.get("conversation_hash", "")),
            context_hash=str(raw.get("context_hash") or context_hash(files_read, prompt)),
        )
    if kind == "incident_event":
        return IncidentEvent(
            incident_id=str(raw["incident_id"]),
            timestamp=str(raw["timestamp"]),
            service=str(raw.get("service", "unknown")),
            actor=str(raw.get("actor", "unknown")),
            node_type=str(raw.get("node_type", "observation")),
            text=str(raw.get("text", "")),
            confidence=float(raw.get("confidence", 0.0)),
            related_to=raw.get("related_to"),
            metadata=dict(raw.get("metadata", {})),
        )
    raise ValueError(f"Unsupported event_type: {kind!r}")


def ingest_jsonl(path: Path, store: SQLiteStore) -> dict[str, int]:
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    counts = {"llm_interaction": 0, "incident_event": 0, "skipped_blank": 0}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            counts["skipped_blank"] += 1
            continue
        try:
            event = parse_event(json.loads(line))
        except Exception as exc:
            raise ValueError(f"Failed to parse {path}:{line_number}: {exc}") from exc
        if isinstance(event, LLMInteraction):
            store.insert_llm_interaction(event)
            counts["llm_interaction"] += 1
        else:
            store.insert_incident_event(event)
            counts["incident_event"] += 1
    return counts












