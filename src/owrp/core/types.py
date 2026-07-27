from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Interaction:
    event_id: str
    timestamp: str
    user_id: str
    repo_id: str
    source: str
    model_name: str
    prompt: str
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    classification: str = "unclassified"
    files_read: tuple[str, ...] = field(default_factory=tuple)
    files_modified: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for key in ("event_id", "timestamp", "user_id", "repo_id", "source", "model_name"):
            value = str(getattr(self, key))
            if not value:
                errors.append(f"{key} is required")
            if len(value) > 500:
                errors.append(f"{key} exceeds 500 characters")
        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError:
            errors.append("timestamp must be ISO-8601")
        if len(self.prompt) > 250_000 or len(self.response) > 500_000:
            errors.append("prompt or response exceeds the ingestion size limit")
        if len(self.classification) > 200:
            errors.append("classification exceeds 200 characters")
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            if getattr(self, key) < 0:
                errors.append(f"{key} cannot be negative")
        if self.cost_usd < 0:
            errors.append("cost_usd cannot be negative")
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            errors.append("total_tokens must equal prompt_tokens + completion_tokens")
        if not isinstance(self.metadata, dict):
            errors.append("metadata must be an object")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["files_read"] = list(self.files_read)
        data["files_modified"] = list(self.files_modified)
        return data


@dataclass(frozen=True, slots=True)
class QueryHit:
    event_id: str
    score: float
    repo_id: str
    classification: str
    prompt: str
    response: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
