from __future__ import annotations

import subprocess
from pathlib import Path

from owrp.core.types import Interaction
from owrp.storage.sqlite_store import SQLiteStore

from recovery_agent.core import preflight_recovery


def interaction(event_id: str, prompt: str, timestamp: str) -> Interaction:
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


def setup_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "judge@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Judge Fixture"], check=True)
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-m", "fixture"], check=True, capture_output=True, text=True)


def seed(root: Path) -> str:
    store = SQLiteStore(root)
    try:
        store.insert_many([
            interaction("episode-a", "debug retry timeout", "2026-08-23T10:00:00Z"),
            interaction("episode-b", "debug retry timeout again", "2026-08-23T10:05:00Z"),
        ])
        store.analyze(0.5)
        row = store.conn.execute("SELECT pair_id FROM duplicate_pairs").fetchone()
        assert row is not None
        return str(row["pair_id"])
    finally:
        store.close()


def test_preflight_passes_only_with_persisted_finding_capsule_and_repo(tmp_path: Path) -> None:
    owr_root = tmp_path / "owr"
    repo = tmp_path / "repo"
    setup_repo(repo)
    finding_id = seed(owr_root)

    result = preflight_recovery(root=str(owr_root), repo_path=str(repo), finding_id=finding_id)

    assert result["state"] == "READY_FOR_PROPOSAL"
    assert [check["state"] for check in result["checks"]] == ["PASS", "PASS", "PASS", "PASS"]
    assert len(result["evidence_ids"]) == 3


def test_preflight_blocks_unknown_finding(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    setup_repo(repo)
    result = preflight_recovery(root=str(tmp_path / "owr"), repo_path=str(repo), finding_id="0" * 24)
    assert result["state"] == "BLOCKED"
    assert result["checks"][0]["gate"] == "finding_exists"
    assert result["checks"][0]["state"] == "BLOCK"
