from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


DecisionState = Literal["READY", "NEEDS_HUMAN", "BLOCKED", "NO_ACTION"]
ActionType = Literal["write_recovery_note"]


@dataclass(frozen=True, slots=True)
class RepoState:
    repo_path: str
    head: str
    branch: str
    dirty: bool
    changed_paths: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["changed_paths"] = list(self.changed_paths)
        return data


@dataclass(frozen=True, slots=True)
class RecoveryAction:
    action_id: str
    action_type: ActionType
    state: DecisionState
    repo_path: str
    finding_id: str
    target_path: str
    evidence_ids: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data


@dataclass(frozen=True, slots=True)
class ActionReceipt:
    action_id: str
    status: Literal["EXECUTED", "BLOCKED", "ALREADY_EXISTS"]
    target_path: str
    evidence_ids: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data
