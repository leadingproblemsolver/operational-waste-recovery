from __future__ import annotations

import json
from typing import Any

from strands import Agent, tool
from strands.vended_interventions.hitl import HumanInTheLoop

from .core import (
    execute_recovery_action,
    inspect_history,
    inspect_repo_state,
    load_recovery_evidence,
    propose_recovery_action,
)


@tool
def inspect_coding_history(root: str, threshold: float = 0.72, limit: int = 5) -> str:
    """Analyze persisted coding-agent history and return observed repeated-work findings."""
    return json.dumps(inspect_history(root, threshold=threshold, limit=limit), sort_keys=True)


@tool
def inspect_repository(repo_path: str) -> str:
    """Read current Git repository HEAD, branch, and uncommitted changed paths."""
    return json.dumps(inspect_repo_state(repo_path), sort_keys=True)


@tool
def get_recovery_evidence(root: str, finding_id: str) -> str:
    """Load exact OWR evidence and Recovery Capsule for one persisted finding."""
    return json.dumps(load_recovery_evidence(root, finding_id), sort_keys=True)


@tool
def propose_bounded_recovery_action(root: str, repo_path: str, finding_id: str) -> str:
    """Create one deterministic evidence-linked recovery action proposal. This does not mutate the repository."""
    return json.dumps(
        propose_recovery_action(root=root, repo_path=repo_path, finding_id=finding_id),
        sort_keys=True,
    )


@tool
def execute_approved_recovery_action(root: str, action_json: str) -> str:
    """Execute one previously proposed Recovery Action. This mutates repo state and requires human approval."""
    action: dict[str, Any] = json.loads(action_json)
    return json.dumps(execute_recovery_action(action, root=root), sort_keys=True)


SYSTEM_PROMPT = """
You are Recovery Agent, a professional coding-continuity agent.

Goal: prevent a coding agent or developer from reconstructing investigation that is already present in persisted evidence.

Required behavior:
1. Inspect coding history with inspect_coding_history.
2. Inspect current repository state with inspect_repository.
3. If there are no repeated-work findings, stop and report NO_ACTION.
4. For one strongest finding only, load exact evidence with get_recovery_evidence.
5. Keep OBSERVED evidence distinct from INFERRED interpretation. Similarity is not proof of wasted work or realized savings.
6. Propose exactly one bounded action with propose_bounded_recovery_action.
7. Never invent evidence IDs, token counts, costs, files, or completed investigations.
8. execute_approved_recovery_action is the only side-effecting tool. Human approval is authoritative; denial means stop with no substitute mutation.
9. After execution, report the returned action receipt. Never claim execution without that receipt.
10. If any tool fails or evidence is missing, fail closed and explain the missing evidence or dependency.

Do not create multiple actions, refactor the repository, edit source files, commit, push, or run arbitrary shell commands.
""".strip()


def build_agent(*, model: Any | None = None, ask: str | Any | None = "stdio") -> Agent:
    safe_tools = [
        "inspect_coding_history",
        "inspect_repository",
        "get_recovery_evidence",
        "propose_bounded_recovery_action",
    ]
    kwargs: dict[str, Any] = {
        "system_prompt": SYSTEM_PROMPT,
        "tools": [
            inspect_coding_history,
            inspect_repository,
            get_recovery_evidence,
            propose_bounded_recovery_action,
            execute_approved_recovery_action,
        ],
        "interventions": [
            HumanInTheLoop(
                ask=ask,
                allowed_tools=safe_tools,
                enable_trust=False,
            )
        ],
    }
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)
