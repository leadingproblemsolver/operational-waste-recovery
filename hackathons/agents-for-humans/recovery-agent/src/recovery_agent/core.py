from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

from owrp.review import build_review
from owrp.storage.sqlite_store import SQLiteStore

from .contracts import ActionReceipt, RecoveryAction, RepoState


class RecoveryAgentError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        timeout=5,
    )
    if result.returncode:
        raise RecoveryAgentError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def inspect_repo_state(repo_path: str) -> dict[str, object]:
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise RecoveryAgentError("repo_path must be an existing directory")
    _git(repo, "rev-parse", "--git-dir")
    changed = tuple(
        line[2:].strip()
        for line in _git(repo, "status", "--porcelain=v1").splitlines()
        if len(line) >= 3 and line[2:].strip()
    )
    return RepoState(
        str(repo),
        _git(repo, "rev-parse", "HEAD"),
        _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        bool(changed),
        changed,
    ).to_dict()


def inspect_history(root: str, threshold: float = 0.72, limit: int = 5) -> dict[str, object]:
    if not 0 <= threshold <= 1 or not 1 <= limit <= 20:
        raise RecoveryAgentError("invalid threshold or limit")
    store = SQLiteStore(Path(root).resolve())
    try:
        analysis = store.analyze(threshold)
        rows = store.conn.execute(
            """
            SELECT pair_id,left_id,right_id,similarity,avoidable_tokens,avoidable_cost_usd
            FROM duplicate_pairs
            ORDER BY similarity DESC,pair_id ASC
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
            raise RecoveryAgentError("finding_id was not found")
        return review
    finally:
        store.close()


def preflight_recovery(*, root: str, repo_path: str, finding_id: str) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    try:
        review = load_recovery_evidence(root, finding_id)
        checks.append({"gate": "finding_exists", "state": "PASS"})
    except RecoveryAgentError as error:
        return {
            "state": "BLOCKED",
            "checks": [{"gate": "finding_exists", "state": "BLOCK", "reason": str(error)}],
            "reason": "Persisted finding evidence is required before any recovery action.",
        }

    capsule = review.get("recovery_capsule")
    if not isinstance(capsule, dict) or not capsule.get("text"):
        checks.append({"gate": "capsule_exists", "state": "BLOCK"})
        return {
            "state": "BLOCKED",
            "checks": checks,
            "reason": "Recovery Capsule is missing; no side effect is authorized.",
        }
    checks.append({"gate": "capsule_exists", "state": "PASS"})

    try:
        repo = inspect_repo_state(repo_path)
        checks.append({"gate": "repo_state_readable", "state": "PASS"})
    except RecoveryAgentError as error:
        checks.append({"gate": "repo_state_readable", "state": "BLOCK", "reason": str(error)})
        return {
            "state": "BLOCKED",
            "checks": checks,
            "reason": "Current repository state must be observable before action planning.",
        }

    checks.append({"gate": "single_bounded_action", "state": "PASS"})
    return {
        "state": "READY_FOR_PROPOSAL",
        "checks": checks,
        "repo": repo,
        "finding_id": finding_id,
        "evidence_ids": [
            str(review["episode_a"]["event_id"]),
            str(review["episode_b"]["event_id"]),
            str(capsule["capsule_id"]),
        ],
    }


def propose_recovery_action(*, root: str, repo_path: str, finding_id: str) -> dict[str, object]:
    preflight = preflight_recovery(root=root, repo_path=repo_path, finding_id=finding_id)
    if preflight["state"] != "READY_FOR_PROPOSAL":
        return preflight

    repo = preflight["repo"]
    evidence_ids = [str(item) for item in preflight["evidence_ids"]]
    digest = hashlib.sha256(
        f"{finding_id}:{repo['head']}:{':'.join(evidence_ids)}".encode()
    ).hexdigest()[:16]
    return RecoveryAction(
        action_id=f"recovery-{digest}",
        action_type="write_recovery_note",
        state="NEEDS_HUMAN",
        repo_path=str(repo["repo_path"]),
        finding_id=finding_id,
        target_path=f".recovery/recovery-{finding_id}.md",
        evidence_ids=tuple(evidence_ids),
        reason=(
            "Persist one evidence-linked Recovery Capsule so the next coding-agent session "
            "resumes from completed investigation. Human approval is required before mutation."
        ),
    ).to_dict()


def execute_recovery_action(action: dict[str, Any], *, root: str) -> dict[str, object]:
    if action.get("state") != "NEEDS_HUMAN" or action.get("action_type") != "write_recovery_note":
        raise RecoveryAgentError("action is not executable")

    repo = Path(str(action.get("repo_path", ""))).resolve()
    rel = Path(str(action.get("target_path", "")))
    if not repo.is_dir():
        raise RecoveryAgentError("repo_path must still exist at execution time")
    if rel.is_absolute() or ".." in rel.parts:
        raise RecoveryAgentError("target_path escapes repository")
    target = (repo / rel).resolve()
    try:
        target.relative_to(repo)
    except ValueError as error:
        raise RecoveryAgentError("target_path escapes repository") from error

    review = load_recovery_evidence(root, str(action["finding_id"]))
    capsule = review.get("recovery_capsule")
    if not isinstance(capsule, dict):
        raise RecoveryAgentError("Recovery Capsule disappeared before execution")

    expected = {
        str(review["episode_a"]["event_id"]),
        str(review["episode_b"]["event_id"]),
        str(capsule["capsule_id"]),
    }
    if {str(x) for x in action.get("evidence_ids", [])} != expected:
        raise RecoveryAgentError("action evidence does not match persisted evidence")

    target.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "# Recovery Capsule\n\n"
        f"Finding: `{action['finding_id']}`\n"
        f"Evidence: {', '.join(sorted(expected))}\n\n"
        f"{capsule['text']}\n\n"
        "This is evidence-linked recovery context, not a claim of realized savings.\n"
    )
    try:
        with target.open("x", encoding="utf-8") as handle:
            handle.write(body)
    except FileExistsError:
        return ActionReceipt(
            str(action["action_id"]),
            "ALREADY_EXISTS",
            str(rel),
            tuple(sorted(expected)),
            "Existing note preserved; no overwrite.",
        ).to_dict()

    return ActionReceipt(
        str(action["action_id"]),
        "EXECUTED",
        str(rel),
        tuple(sorted(expected)),
        "One approved evidence-linked Recovery Capsule was written.",
    ).to_dict()
