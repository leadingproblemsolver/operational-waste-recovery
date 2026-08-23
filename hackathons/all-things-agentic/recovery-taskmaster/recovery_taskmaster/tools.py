from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from owrp.core.types import Interaction
from owrp.review import build_review
from owrp.storage.sqlite_store import SQLiteStore


_RUN_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_BASE = Path(os.environ.get("RECOVERY_TASKMASTER_ROOT", "/tmp/recovery-taskmaster"))


def _paths(run_id: str) -> tuple[Path, Path]:
    if not _RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must contain only letters, numbers, _ or - and be <=64 chars")
    root = (_BASE / run_id).resolve()
    base = _BASE.resolve()
    root.relative_to(base)
    return root / "owr", root / "repo"


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
    """Prepare a deterministic sanitized coding-history + workspace fixture for one run."""
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
        files = []
        for path in sorted(p for p in repo.rglob("*") if p.is_file()):
            payload = path.read_bytes()
            files.append(
                {
                    "path": str(path.relative_to(repo)),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        return {
            "state": "OBSERVED",
            "run_id": run_id,
            "analysis": analysis,
            "strongest_finding_id": str(row["pair_id"]),
            "similarity": float(row["similarity"]),
            "workspace_files": files,
            "fixture": "synthetic_sanitized",
        }
    finally:
        store.close()


def inspect_recovery_evidence(run_id: str, finding_id: str) -> dict[str, object]:
    """Load exact persisted OWR evidence and Recovery Capsule for one finding."""
    owr_root, _ = _paths(run_id)
    store = SQLiteStore(owr_root)
    try:
        review = build_review(store, finding_id)
        if review is None:
            return {"state": "BLOCKED", "reason": "finding_not_found", "finding_id": finding_id}
        return review
    finally:
        store.close()


def materialize_recovery_capsule(run_id: str, finding_id: str) -> dict[str, object]:
    """Write exactly one evidence-linked recovery note inside the bounded demo workspace."""
    owr_root, repo = _paths(run_id)
    store = SQLiteStore(owr_root)
    try:
        review = build_review(store, finding_id)
        if review is None:
            return {"status": "BLOCKED", "reason": "finding_not_found"}
        capsule = review.get("recovery_capsule")
        if not isinstance(capsule, dict) or not capsule.get("text"):
            return {"status": "BLOCKED", "reason": "recovery_capsule_missing"}

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
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = body.encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        if target.exists():
            existing = target.read_bytes()
            return {
                "status": "ALREADY_EXISTS",
                "target_path": str(target_rel),
                "sha256": hashlib.sha256(existing).hexdigest(),
                "evidence_ids": evidence_ids,
                "overwritten": False,
            }
        target.write_bytes(payload)
        return {
            "status": "EXECUTED",
            "target_path": str(target_rel),
            "sha256": digest,
            "bytes": len(payload),
            "evidence_ids": evidence_ids,
            "overwritten": False,
        }
    finally:
        store.close()


def verify_recovery_receipt(run_id: str, finding_id: str, expected_sha256: str) -> dict[str, object]:
    """Independently reread the bounded action artifact and verify its immutable receipt hash."""
    _, repo = _paths(run_id)
    target_rel = Path(".recovery") / f"recovery-{finding_id}.md"
    target = (repo / target_rel).resolve()
    target.relative_to(repo.resolve())
    if not target.is_file():
        return {"status": "FAILED", "reason": "recovery_note_missing", "target_path": str(target_rel)}
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    return {
        "status": "VERIFIED" if actual == expected_sha256 else "FAILED",
        "target_path": str(target_rel),
        "expected_sha256": expected_sha256,
        "actual_sha256": actual,
    }
