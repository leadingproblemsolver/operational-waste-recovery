# MODE: VIBECODABLE
# BRAAT BLOCK: Shared data contracts
# MISSION: Keep event shapes explicit and import-safe.
# ANTI-PATTERN: Do not add abstract base classes until multiple real implementations exist.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

EventKind = Literal["llm_interaction", "incident_event"]


@dataclass(frozen=True)
class LLMInteraction:
    interaction_id: str
    timestamp: str
    user_id: str
    repo_id: str
    branch: str
    prompt: str
    response: str
    tokens_spent: int
    cost_usd: float
    files_read: tuple[str, ...] = field(default_factory=tuple)
    files_modified: tuple[str, ...] = field(default_factory=tuple)
    conversation_hash: str = ""
    context_hash: str = ""


@dataclass(frozen=True)
class IncidentEvent:
    incident_id: str
    timestamp: str
    service: str
    actor: str
    node_type: str
    text: str
    confidence: float = 0.0
    related_to: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecoveryMetric:
    metric_name: str
    resource_lost: float
    resource_measured: float
    resource_recovered: float
    unit: str
    source: str


@dataclass(frozen=True)
class QueryHit:
    source_type: str
    source_id: str
    score: float
    title: str
    summary: str
