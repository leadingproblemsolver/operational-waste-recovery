# ============================================================
# MODE: HYBRID
# BRAAT BLOCK: Canonical Event Schema
# FILE: core/models.py
# ============================================================
#
# MISSION:
#   Define the one standard event shape that every later sprint
#   must use.
#
# WHY THIS FILE EXISTS:
#   External tools will all produce messy/different formats.
#   This file creates the internal truth format.
#
# RULE:
#   All ingestion adapters must eventually produce InteractionEvent.
#
# NON-NEGOTIABLE:
#   Do not add database logic here.
#   Do not add duplicate detection here.
#   Do not add recovery calculations here.
#   Do not import pipeline/storage/retrieval here.
#
# THIS FILE ONLY DEFINES DATA SHAPES.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ============================================================
# CORE UNIT
# ============================================================
#
# InteractionEvent is the smallest useful unit in the system.
#
# One row in JSONL = one InteractionEvent.
#
# Later sprints will:
#   - store it
#   - fingerprint it
#   - compare it
#   - classify waste
#   - calculate recovery
#
# But this file does none of that.
# ============================================================


@dataclass(slots=True)
class InteractionEvent:
    """
    Canonical local event.

    This represents one LLM-related work event.

    Keep this boring.
    Keep this explicit.
    Keep this inspectable.
    """

    # --------------------------------------------------------
    # Identity fields
    # --------------------------------------------------------
    # These answer:
    #   What event is this?
    #   Who caused it?
    #   Where did it happen?
    # --------------------------------------------------------

    event_id: str
    timestamp: str
    user_id: str
    repo_id: str
    source: str

    # --------------------------------------------------------
    # LLM accounting fields
    # --------------------------------------------------------
    # These answer:
    #   How many tokens were spent?
    #   How much money did this cost?
    # --------------------------------------------------------

    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float

    # --------------------------------------------------------
    # Classification field
    # --------------------------------------------------------
    # This is intentionally simple at first.
    #
    # Example values:
    #   debugging
    #   incident_investigation
    #   code_generation
    #   context_reconstruction
    #   documentation
    # --------------------------------------------------------

    classification: str

    # --------------------------------------------------------
    # Comparison fields
    # --------------------------------------------------------
    # These fields allow later sprints to detect repeated work.
    #
    # They may be empty during initial ingest.
    # Fingerprint sprint can populate them later.
    # --------------------------------------------------------

    prompt_hash: str = ""
    context_hash: str = ""
    conversation_hash: str = ""

    # --------------------------------------------------------
    # Repo context fields
    # --------------------------------------------------------
    # These help detect repeated context loading.
    # --------------------------------------------------------

    files_read: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)

    # --------------------------------------------------------
    # Raw metadata escape hatch
    # --------------------------------------------------------
    # This prevents overengineering.
    #
    # If a source has extra fields, store them here.
    # Do not create new top-level fields too early.
    # --------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------
    # Minimal validation only.
    # Do not create a full validation framework yet.
    # --------------------------------------------------------

    def validate(self) -> list[str]:
        """
        Return a list of human-readable validation errors.

        Empty list means the event is valid enough for local proof.
        """

        errors: list[str] = []

        if not self.event_id:
            errors.append("event_id is required")

        if not self.timestamp:
            errors.append("timestamp is required")

        if not self.user_id:
            errors.append("user_id is required")

        if not self.repo_id:
            errors.append("repo_id is required")

        if not self.source:
            errors.append("source is required")

        if not self.model_name:
            errors.append("model_name is required")

        if self.prompt_tokens < 0:
            errors.append("prompt_tokens cannot be negative")

        if self.completion_tokens < 0:
            errors.append("completion_tokens cannot be negative")

        if self.total_tokens < 0:
            errors.append("total_tokens cannot be negative")

        if self.cost_usd < 0:
            errors.append("cost_usd cannot be negative")

        expected_total = self.prompt_tokens + self.completion_tokens
        if self.total_tokens != expected_total:
            errors.append(
                "total_tokens must equal prompt_tokens + completion_tokens"
            )

        return errors

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------
    # Required so storage/reporting can inspect the event.
    # --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Convert event into a plain dictionary.

        SQLite, JSON reports, and logs can safely consume this.
        """

        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "repo_id": self.repo_id,
            "source": self.source,
            "model_name": self.model_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "classification": self.classification,
            "prompt_hash": self.prompt_hash,
            "context_hash": self.context_hash,
            "conversation_hash": self.conversation_hash,
            "files_read": list(self.files_read),
            "files_modified": list(self.files_modified),
            "metadata": dict(self.metadata),
        }


# ============================================================
# FACTORY FUNCTION
# ============================================================
#
# This is the safe entry point from raw JSON.
#
# Later:
#   pipeline/ingest_jsonl.py
#
# should call:
#   interaction_event_from_dict(row)
#
# Do not let every file manually construct InteractionEvent.
# ============================================================


def interaction_event_from_dict(row: dict[str, Any]) -> InteractionEvent:
    """
    Build InteractionEvent from one JSONL dictionary.

    This keeps parsing consistent across the repo.
    """

    prompt_tokens = int(row.get("prompt_tokens", 0))
    completion_tokens = int(row.get("completion_tokens", 0))

    total_tokens = int(
        row.get("total_tokens", prompt_tokens + completion_tokens)
    )

    return InteractionEvent(
        event_id=str(row.get("event_id", "")),
        timestamp=str(row.get("timestamp", current_utc_timestamp())),
        user_id=str(row.get("user_id", "")),
        repo_id=str(row.get("repo_id", "")),
        source=str(row.get("source", "manual_jsonl")),
        model_name=str(row.get("model_name", "")),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=float(row.get("cost_usd", 0.0)),
        classification=str(row.get("classification", "unclassified")),
        prompt_hash=str(row.get("prompt_hash", "")),
        context_hash=str(row.get("context_hash", "")),
        conversation_hash=str(row.get("conversation_hash", "")),
        files_read=list(row.get("files_read", [])),
        files_modified=list(row.get("files_modified", [])),
        metadata=dict(row.get("metadata", {})),
    )


def current_utc_timestamp() -> str:
    """
    Return an ISO timestamp.

    Used only as a fallback when raw local proof data does not
    include a timestamp.
    """

    return datetime.now(timezone.utc).isoformat()