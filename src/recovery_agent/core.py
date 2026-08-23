from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from owrp.review import build_review
from owrp.storage.sqlite_store import SQLiteStore

from recovery_agent.contracts import ActionReceipt, RecoveryAction, RepoState


class RecoveryAgentError(RuntimeError):
    pass


def _run_git(repo_path: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=False,
        text=True,
        capture_output=True,
        timeout=5,
    )
    if completed.returncode != 0:
        raise RecoveryAgentError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def inspect_repo_state(repo_path: str) -> dict[str, object]:
    root = Path(repo_path).resolve()
    if not root.is_dir():
        raise RecoveryAgentError("repo_path must be an existing directory")
    git_dir = _run_git(root, "rev-parse", "--git-dir")
    if not git_dir:
        raise RecoveryAgentError("repo_path is not a git repository")

    head = _run_git(root, "rev-parse", "HEAD")
    branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    porcelain = _run_git(root, "status", "--porcelain=v1")
    changed = tuple(
        line[3:].strip()
        for line in porcelain.splitlines()
        if len(line) >= 4 and line[3:].strip()
    )
    return RepoState(
        repo_path=str(root),
        head=head,
        branch=branch,
        dirty=bool(changed),
        changed_paths=changed,
    ).to_dict()


def inspect_history(root: str, threshold: float = 0.72, limit: int = 5) -> dict[str, object]:
    if not 0 <= threshold <= 1:
        raise RecoveryAgentError("threshold must be between 0 and 1")
    if not 1 <= limit <= 20:
        raise RecoveryAgentError("limit must be between 1 and 20")

    store = SQLiteStore(Path(root).resolve())
    try:
        analysis = store.analyze(threshold)
        rows = store.conn.execute(
            """
            SELECT pair_id, left_id, right_id, similarity, avoidable_tokens,
                   avoidable_cost_usd
            FROM duplicate_pairs
            ORDER BY similarity DESC, pair_id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {
            "state": "OBSERVED",
            "analysis": analysis,
            "findings": [dict(row) for row in rows],
        }
    finally:
        store.close()


def load_recovery_evidence(root: str, finding_id: str) -> dict[str, object]:
    store = SQLiteStore(Path(root).resolve())
    try:
        review = build_review(store, finding_id)
        if review is None:
            raise RecoveryAgentError("finding_id was not found in persisted OWR analysis")
        return review
    finally:
        store.close()


def propose_recovery_action(
    *,
    root: str,
    repo_path: str,
    finding_id: str,
) -> dict[str, object]:
    review = load_recovery_evidence(root, finding_id)
    repo = inspect_repo_state(repo_path)
    capsule = review.get("recovery_capsule")
    if not isinstance(capsule, dict) or not capsule.get("text"):
        return {
            "state": "BLOCKED",
            "reason": "No Recovery Capsule exists for this finding; no side effect is authorized.",
            "finding_id": finding_id,
            "evidence_ids": [
                review["episode_a"]["event_id"],
                review["episode_b"]["event_id"],
            ],
        }

    evidence_ids = (
        str(review["episode_a"]["event_id"]),
        str(review["episode_b"]["event_id"]),
        str(capsule["capsule_id"]),
    )
    digest = hashlib.sha256(
        f"{finding_id}:{repo['head']}:{':'.join(evidence_ids)}".encode()
    ).hexdigest()[:16]
    target = f".recovery/recovery-{finding_id}.md"
    reason = (
        "Persist one evidence-linked Recovery Capsule inside the repository so the next coding-agent "
        "session can resume from already-completed investigation instead of reconstructing it."
    )
    if repo["dirty"]:
        reason += " The repository currently has uncommitted changes, so human approval is mandatory."

    return RecoveryAction(
        action_id=f"recovery-{digest}",
        action_type="write_recovery_note",
        state="NEEDS_HUMAN",
        repo_path=str(repo["repo_path"]),
        finding_id=finding_id,
        target_path=target,
        evidence_ids=evidence_ids,
        reason=reason,
    ).to_dict()


def execute_recovery_action(action: dict[str, Any], *, root: str) -> dict[str, object]:
    if action.get("state") != "NEEDS_HUMAN":
        raise RecoveryAgentError("only a human-approved NEEDS_HUMAN action may execute")
    if action.get("action_type") != "write_recovery_note":
        raise RecoveryAgentError("unsupported action_type")

    repo_path = Path(str(action.get("repo_path", ""))).resolve()
    if not repo_path.is_dir():
        raise RecoveryAgentError("repo_path must be an existing directory")
    target_rel = Path(str(action.get("target_path", "")))
    if target_rel.is_absolute() or ".." in target_rel.parts:
        raise RecoveryAgentError("target_path must stay inside the repository")
    target = (repo_path / target_rel).resolve()
    try:
        target.relative_to(repo_path)
    except ValueError as error:
        raise RecoveryAgentError("target_path escapes repository") from error

    finding_id = str(action.get("finding_id", ""))
    review = load_recovery_evidence(root, finding_id)
    capsule = review.get("recovery_capsule")
    if not isinstance(capsule, dict) or not capsule.get("text"):
        raise RecoveryAgentError("Recovery Capsule disappeared before execution")

    expected_ids = {
        str(review["episode_a"]["event_id"]),
        str(review["episode_b"]["event_id"]),
        str(capsule["capsule_id"]),
    }
    supplied_ids = {str(item) for item in action.get("evidence_ids", [])}
    if supplied_ids != expected_ids:
        raise RecoveryAgentError("action evidence does not match current persisted evidence")

    body = "\n".join(
        [
            "# Recovery Capsule",
            "",
            f"Finding: `{finding_id}`",
            f"Evidence: {', '.join(sorted(expected_ids))}",
            "",
            str(capsule["text"]),
            "",
            "## Evidence boundary",
            "This note preserves observed OWR evidence and an estimated recovery aid. It does not prove realized savings.",
            "",
        ]
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8") as handle:
            handle.write(body)
    except FileExistsError:
        return ActionReceipt(
            action_id=str(action["action_id"]),
            status="ALREADY_EXISTS",
            target_path=str(target_rel),
            evidence_ids=tuple(sorted(expected_ids)),
            detail="Existing recovery note was preserved; no overwrite occurred.",
        ).to_dict()

    return ActionReceipt(
        action_id=str(action["action_id"]),
        status="EXECUTED",
        target_path=str(target_rel),
        evidence_ids=tuple(sorted(expected_ids)),
        detail="One evidence-linked Recovery Capsule was written after approval.",
    ).to_dict()


def render_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True)
