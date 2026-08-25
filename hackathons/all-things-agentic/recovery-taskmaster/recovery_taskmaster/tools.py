from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from owrp.core.types import Interaction
from owrp.review import build_review
from owrp.storage.sqlite_store import SQLiteStore


_RUN_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_BASE = Path(os.environ.get("RECOVERY_TASKMASTER_ROOT", "/tmp/recovery-taskmaster"))

_OBSERVED = "OBSERVED"
_EVIDENCE_READY = "EVIDENCE_READY"
_ACTION_PENDING = "ACTION_PENDING"
_EXECUTED = "EXECUTED"
_VERIFIED = "VERIFIED"
_BLOCKED = "BLOCKED"
_FAILED = "FAILED"


def _run_root(run_id: str) -> Path:
    if not _RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must contain only letters, numbers, _ or - and be <=64 chars")
    root = (_BASE / run_id).resolve()
    root.relative_to(_BASE.resolve())
    return root


def _paths(run_id: str) -> tuple[Path, Path]:
    root = _run_root(run_id)
    return root / "owr", root / "repo"


def _state_path(run_id: str) -> Path:
    return _run_root(run_id) / "run-state.json"


def _read_run_state(run_id: str) -> dict[str, object] | None:
    path = _state_path(run_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_run_state(run_id: str, state: dict[str, object]) -> None:
    path = _state_path(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _block(run_id: str, reason: str, **extra: object) -> dict[str, object]:
    current = _read_run_state(run_id) or {"run_id": run_id, "action_count": 0}
    blocked = {**current, "state": _BLOCKED, "reason": reason, **extra}
    _write_run_state(run_id, blocked)
    return {"status": _BLOCKED, "reason": reason, **extra}


def _interaction(event_id: str, prompt: str, timestamp: str, files: list[str]) -> Interaction:
    return Interaction(
        event_id=event_id,
        timestamp=timestamp,
        user_id="taskmaster-demo",
        repo_id="recovery-taskmaster-demo",
        source="google-adk-demo",
        model_name="coding-agent",
        prompt=prompt,
        response="Observed prior investigation and retry-path findings.",
        prompt_tokens=120,
        completion_tokens=30,
        total_tokens=150,
        cost_usd=0.01,
        classification="debugging",
        files_read=files,
        files_modified=[],
        metadata={"synthetic_demo": True},
    )


def prepare_demo_run(run_id: str) -> dict[str, object]:
    """Prepare a deterministic sanitized fixture and persist the host-owned OBSERVED state."""
    owr_root, repo = _paths(run_id)
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "src").mkdir(exist_ok=True)
    (repo / "README.md").write_text("# Recovery Taskmaster demo workspace\n", encoding="utf-8")
    (repo / "src" / "retry.py").write_text(
        "def retry_delay(attempt: int) -> int:\n    return min(2 ** attempt, 30)\n",
        encoding="utf-8",
    )

    store = SQLiteStore(owr_root)
    try:
        store.insert_many(
            [
                _interaction(
                    "taskmaster-episode-a",
                    "Investigate retry storm after deploy and trace backoff behavior",
                    "2026-08-23T18:00:00Z",
                    ["src/retry.py"],
                ),
                _interaction(
                    "taskmaster-episode-b",
                    "Investigate retry storm after deploy again and trace backoff behavior",
                    "2026-08-23T18:08:00Z",
                    ["src/retry.py"],
                ),
            ]
        )
        analysis = store.analyze(0.5)
        row = store.conn.execute(
            "SELECT pair_id, similarity FROM duplicate_pairs ORDER BY similarity DESC LIMIT 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("demo fixture did not produce a repeated-work finding")
        finding_id = str(row["pair_id"])
        files = []
        for path in sorted(p for p in repo.rglob("*") if p.is_file()):
            payload = path.read_bytes()
            files.append({"path": str(path.relative_to(repo)), "sha256": hashlib.sha256(payload).hexdigest()})
        _write_run_state(
            run_id,
            {
                "run_id": run_id,
                "state": _OBSERVED,
                "finding_id": finding_id,
                "action_count": 0,
            },
        )
        return {
            "state": _OBSERVED,
            "run_id": run_id,
            "analysis": analysis,
            "strongest_finding_id": finding_id,
            "similarity": float(row["similarity"]),
            "workspace_files": files,
            "fixture": "synthetic_sanitized",
        }
    finally:
        store.close()


def inspect_recovery_evidence(run_id: str, finding_id: str) -> dict[str, object]:
    """Load exact persisted evidence and advance OBSERVED -> EVIDENCE_READY in host code."""
    state = _read_run_state(run_id)
    if state is None:
        return _block(run_id, "run_not_prepared")
    if state.get("finding_id") != finding_id:
        _block(run_id, "finding_not_authorized", finding_id=finding_id)
        return {"state": _BLOCKED, "reason": "finding_not_authorized", "finding_id": finding_id}
    if state.get("state") not in {_OBSERVED, _EVIDENCE_READY}:
        return {
            "state": _BLOCKED,
            "reason": "invalid_transition",
            "from_state": state.get("state"),
            "required_state": _OBSERVED,
        }

    owr_root, _ = _paths(run_id)
    store = SQLiteStore(owr_root)
    try:
        review = build_review(store, finding_id)
        if review is None:
            _block(run_id, "finding_not_found", finding_id=finding_id)
            return {"state": _BLOCKED, "reason": "finding_not_found", "finding_id": finding_id}
        _write_run_state(run_id, {**state, "state": _EVIDENCE_READY})
        return {**review, "runtime_state": _EVIDENCE_READY}
    finally:
        store.close()


def _target_and_payload(run_id: str, finding_id: str) -> tuple[Path, Path, bytes, list[str]] | dict[str, object]:
    owr_root, repo = _paths(run_id)
    store = SQLiteStore(owr_root)
    try:
        review = build_review(store, finding_id)
        if review is None:
            return {"status": _BLOCKED, "reason": "finding_not_found"}
        capsule = review.get("recovery_capsule")
        if not isinstance(capsule, dict) or not capsule.get("text"):
            return {"status": _BLOCKED, "reason": "recovery_capsule_missing"}
        evidence_ids = sorted(
            [
                str(review["episode_a"]["event_id"]),
                str(review["episode_b"]["event_id"]),
                str(capsule["capsule_id"]),
            ]
        )
        target_rel = Path(".recovery") / f"recovery-{finding_id}.md"
        target = (repo / target_rel).resolve()
        target.relative_to(repo.resolve())
        body = (
            "# Recovery Capsule\n\n"
            f"Finding: `{finding_id}`\n"
            f"Evidence: {', '.join(evidence_ids)}\n\n"
            f"{capsule['text']}\n\n"
            "## Boundary\n"
            "Observed recurrence is preserved separately from inferred avoidable work. "
            "This artifact does not claim realized labor or cost savings.\n"
        )
        return target, target_rel, body.encode("utf-8"), evidence_ids
    finally:
        store.close()


def _materialize_recovery_capsule(
    run_id: str,
    finding_id: str,
    *,
    simulate_crash_after_write: bool = False,
) -> dict[str, object]:
    """Host-enforced mutation path with reconciliation for ambiguous post-action crashes."""
    state = _read_run_state(run_id)
    if state is None:
        return _block(run_id, "run_not_prepared")
    if state.get("finding_id") != finding_id:
        return _block(run_id, "finding_not_authorized", finding_id=finding_id)

    current = str(state.get("state"))
    if current not in {_EVIDENCE_READY, _ACTION_PENDING, _EXECUTED, _VERIFIED}:
        return _block(
            run_id,
            "invalid_transition",
            from_state=current,
            required_state=_EVIDENCE_READY,
        )

    prepared = _target_and_payload(run_id, finding_id)
    if isinstance(prepared, dict):
        return _block(run_id, str(prepared["reason"]))
    target, target_rel, payload, evidence_ids = prepared
    target.parent.mkdir(parents=True, exist_ok=True)

    # ACTION_PENDING is persisted before the side effect. On resume, presence of the
    # target is reconciled before any retry, so an ambiguous crash cannot duplicate it.
    if current == _ACTION_PENDING and target.exists():
        existing = target.read_bytes()
        digest = hashlib.sha256(existing).hexdigest()
        reconciled = {
            **state,
            "state": _EXECUTED,
            "sha256": digest,
            "target_path": str(target_rel),
        }
        _write_run_state(run_id, reconciled)
        return {
            "status": "ALREADY_EXISTS",
            "runtime_state": _EXECUTED,
            "target_path": str(target_rel),
            "sha256": digest,
            "evidence_ids": evidence_ids,
            "overwritten": False,
            "reconciled_after_ambiguous_execution": True,
            "action_count": int(state.get("action_count", 0)),
        }

    if target.exists():
        existing = target.read_bytes()
        digest = hashlib.sha256(existing).hexdigest()
        if current in {_EXECUTED, _VERIFIED}:
            return {
                "status": "ALREADY_EXISTS",
                "runtime_state": current,
                "target_path": str(target_rel),
                "sha256": digest,
                "evidence_ids": evidence_ids,
                "overwritten": False,
                "reconciled_after_ambiguous_execution": False,
                "action_count": int(state.get("action_count", 0)),
            }
        return _block(run_id, "unexpected_existing_target", target_path=str(target_rel))

    pending = {**state, "state": _ACTION_PENDING}
    _write_run_state(run_id, pending)
    target.write_bytes(payload)
    action_count = int(state.get("action_count", 0)) + 1

    if simulate_crash_after_write:
        # Test-only crash point: external effect exists while durable state remains ACTION_PENDING.
        _write_run_state(run_id, {**pending, "action_count": action_count})
        raise RuntimeError("simulated crash after side effect before EXECUTED settlement")

    digest = hashlib.sha256(payload).hexdigest()
    executed = {
        **pending,
        "state": _EXECUTED,
        "sha256": digest,
        "target_path": str(target_rel),
        "action_count": action_count,
    }
    _write_run_state(run_id, executed)
    return {
        "status": _EXECUTED,
        "runtime_state": _EXECUTED,
        "target_path": str(target_rel),
        "sha256": digest,
        "bytes": len(payload),
        "evidence_ids": evidence_ids,
        "overwritten": False,
        "reconciled_after_ambiguous_execution": False,
        "action_count": action_count,
    }


def materialize_recovery_capsule(run_id: str, finding_id: str) -> dict[str, object]:
    """Perform exactly one host-authorized action, reconciling ambiguous prior execution first."""
    return _materialize_recovery_capsule(run_id, finding_id)


def verify_recovery_receipt(run_id: str, finding_id: str, expected_sha256: str) -> dict[str, object]:
    """Independently reread the action artifact and advance EXECUTED -> VERIFIED in host code."""
    state = _read_run_state(run_id)
    if state is None:
        return _block(run_id, "run_not_prepared")
    if state.get("finding_id") != finding_id:
        return _block(run_id, "finding_not_authorized", finding_id=finding_id)
    current = str(state.get("state"))
    if current not in {_EXECUTED, _VERIFIED}:
        return _block(run_id, "invalid_transition", from_state=current, required_state=_EXECUTED)

    _, repo = _paths(run_id)
    target_rel = Path(".recovery") / f"recovery-{finding_id}.md"
    target = (repo / target_rel).resolve()
    target.relative_to(repo.resolve())
    if not target.is_file():
        _write_run_state(run_id, {**state, "state": _FAILED, "reason": "recovery_note_missing"})
        return {"status": _FAILED, "reason": "recovery_note_missing", "target_path": str(target_rel)}

    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    status = _VERIFIED if actual == expected_sha256 else _FAILED
    _write_run_state(
        run_id,
        {
            **state,
            "state": status,
            "expected_sha256": expected_sha256,
            "actual_sha256": actual,
        },
    )
    return {
        "status": status,
        "runtime_state": status,
        "target_path": str(target_rel),
        "expected_sha256": expected_sha256,
        "actual_sha256": actual,
        "action_count": int(state.get("action_count", 0)),
    }
