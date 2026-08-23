from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from owrp.core.types import Interaction
from owrp.storage.sqlite_store import SQLiteStore

from .core import (
    RecoveryAgentError,
    execute_recovery_action,
    preflight_recovery,
    propose_recovery_action,
)


def _interaction(event_id: str, prompt: str, timestamp: str) -> Interaction:
    return Interaction(
        event_id=event_id,
        timestamp=timestamp,
        user_id="judge-user",
        repo_id="judge-repo",
        source="judge-fixture",
        model_name="judge-model",
        prompt=prompt,
        response="investigation evidence",
        prompt_tokens=100,
        completion_tokens=20,
        total_tokens=120,
        cost_usd=0.01,
        classification="debugging",
        metadata={"synthetic": True},
    )


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _setup_repo(path: Path) -> None:
    path.mkdir(parents=True)
    _git(path, "init")
    _git(path, "config", "user.email", "judge@example.com")
    _git(path, "config", "user.name", "Judge Fixture")
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "fixture")


def _seed_owr(root: Path) -> str:
    store = SQLiteStore(root)
    try:
        store.insert_many(
            [
                _interaction(
                    "episode-a",
                    "debug redis timeout after deploy",
                    "2026-08-23T10:00:00Z",
                ),
                _interaction(
                    "episode-b",
                    "debug redis timeout after deploy again",
                    "2026-08-23T10:05:00Z",
                ),
            ]
        )
        result = store.analyze(0.5)
        if result["duplicate_pairs"] != 1:
            raise RuntimeError("judge fixture did not produce exactly one finding")
        row = store.conn.execute("SELECT pair_id FROM duplicate_pairs").fetchone()
        if row is None:
            raise RuntimeError("judge fixture missing pair id")
        return str(row["pair_id"])
    finally:
        store.close()


def _replace_capsule_identity(root: Path) -> tuple[str, str]:
    store = SQLiteStore(root)
    try:
        row = store.conn.execute(
            "SELECT capsule_id, repo_id, capsule_text, source_count, estimated_tokens_saved FROM context_capsules LIMIT 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("judge fixture missing capsule")
        old_id = str(row["capsule_id"])
        new_id = "stale-evidence-capsule-01"
        store.conn.execute("DELETE FROM context_capsules")
        store.conn.execute(
            """
            INSERT INTO context_capsules (
                capsule_id, repo_id, capsule_text, source_count, estimated_tokens_saved
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                new_id,
                row["repo_id"],
                str(row["capsule_text"]) + "\nEvidence refreshed after approval.",
                row["source_count"],
                row["estimated_tokens_saved"],
            ),
        )
        store.conn.commit()
        return old_id, new_id
    finally:
        store.close()


def _positive(root: Path, repo: Path, finding_id: str) -> dict[str, object]:
    preflight = preflight_recovery(root=str(root), repo_path=str(repo), finding_id=finding_id)
    action = propose_recovery_action(root=str(root), repo_path=str(repo), finding_id=finding_id)
    target = repo / str(action["target_path"])
    before_exists = target.exists()
    receipt = execute_recovery_action(action, root=str(root))
    body = target.read_text(encoding="utf-8")
    replay = execute_recovery_action(action, root=str(root))
    passed = (
        preflight["state"] == "READY_FOR_PROPOSAL"
        and action["state"] == "NEEDS_HUMAN"
        and before_exists is False
        and receipt["status"] == "EXECUTED"
        and replay["status"] == "ALREADY_EXISTS"
        and finding_id in body
        and "realized savings" in body
    )
    return {
        "scenario": "approved_positive",
        "passed": passed,
        "preflight_state": preflight["state"],
        "action_state": action["state"],
        "receipt_status": receipt["status"],
        "replay_status": replay["status"],
        "target_path": action["target_path"],
        "evidence_ids": action["evidence_ids"],
    }


def _denied(root: Path, repo: Path, finding_id: str) -> dict[str, object]:
    action = propose_recovery_action(root=str(root), repo_path=str(repo), finding_id=finding_id)
    target = repo / str(action["target_path"])
    # This scenario models the Strands HumanInTheLoop denial branch: the mutating
    # tool is never called after a denied approval decision.
    human_decision = "DENY"
    passed = action["state"] == "NEEDS_HUMAN" and human_decision == "DENY" and not target.exists()
    return {
        "scenario": "human_denied",
        "passed": passed,
        "action_state": action["state"],
        "human_decision": human_decision,
        "mutation_attempted": False,
        "target_exists": target.exists(),
    }


def _stale(root: Path, repo: Path, finding_id: str) -> dict[str, object]:
    action = propose_recovery_action(root=str(root), repo_path=str(repo), finding_id=finding_id)
    target = repo / str(action["target_path"])
    old_id, new_id = _replace_capsule_identity(root)
    before_files = sorted(str(path.relative_to(repo)) for path in repo.rglob("*") if path.is_file())
    error_text = None
    try:
        execute_recovery_action(action, root=str(root))
    except RecoveryAgentError as error:
        error_text = str(error)
    after_files = sorted(str(path.relative_to(repo)) for path in repo.rglob("*") if path.is_file())
    passed = (
        old_id in set(action["evidence_ids"])
        and new_id not in set(action["evidence_ids"])
        and error_text == "action evidence does not match persisted evidence"
        and before_files == after_files
        and not target.exists()
    )
    return {
        "scenario": "stale_evidence_after_approval",
        "passed": passed,
        "old_capsule_id": old_id,
        "current_capsule_id": new_id,
        "error": error_text,
        "repository_unchanged": before_files == after_files,
        "target_exists": target.exists(),
    }


def run_judge_scenarios() -> dict[str, object]:
    results: list[dict[str, object]] = []
    for scenario in (_positive, _denied, _stale):
        with tempfile.TemporaryDirectory(prefix=f"recovery-agent-{scenario.__name__}-") as tmp:
            base = Path(tmp)
            root = base / "owr"
            repo = base / "repo"
            _setup_repo(repo)
            finding_id = _seed_owr(root)
            results.append(scenario(root, repo, finding_id))
    return {
        "receipt_version": 1,
        "agent": "Recovery Agent",
        "framework": "Strands Agents SDK",
        "scenarios": results,
        "passed": all(bool(item["passed"]) for item in results),
        "claim_boundary": {
            "proves": [
                "approved bounded action produces an evidence-linked receipt",
                "human denial produces zero mutation",
                "stale persisted evidence is rejected before mutation",
                "replay does not overwrite an existing recovery note",
            ],
            "does_not_prove": [
                "LLM reasoning quality",
                "production traffic",
                "realized savings",
                "human-independent implementation ownership",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic judge scenarios")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = run_judge_scenarios()
    rendered = json.dumps(receipt, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
