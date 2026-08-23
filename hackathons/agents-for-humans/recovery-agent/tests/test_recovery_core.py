from __future__ import annotations

import subprocess
from pathlib import Path

from owrp.core.types import Interaction
from owrp.storage.sqlite_store import SQLiteStore

from recovery_agent.core import execute_recovery_action, inspect_repo_state, propose_recovery_action


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


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def setup_repo(path: Path) -> None:
    path.mkdir()
    git(path, "init")
    git(path, "config", "user.email", "judge@example.com")
    git(path, "config", "user.name", "Judge Fixture")
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "fixture")


def seed_owr(root: Path) -> str:
    store = SQLiteStore(root)
    try:
        store.insert_many([
            interaction("episode-a", "debug redis timeout after deploy", "2026-08-23T10:00:00Z"),
            interaction("episode-b", "debug redis timeout after deploy again", "2026-08-23T10:05:00Z"),
        ])
        result = store.analyze(0.5)
        assert result["duplicate_pairs"] == 1
        row = store.conn.execute("SELECT pair_id FROM duplicate_pairs").fetchone()
        assert row is not None
        return str(row["pair_id"])
    finally:
        store.close()


def test_propose_then_execute_one_evidence_linked_action(tmp_path: Path) -> None:
    owr_root = tmp_path / "owr"
    repo = tmp_path / "repo"
    setup_repo(repo)
    finding_id = seed_owr(owr_root)

    action = propose_recovery_action(root=str(owr_root), repo_path=str(repo), finding_id=finding_id)
    assert action["state"] == "NEEDS_HUMAN"
    assert action["action_type"] == "write_recovery_note"
    assert len(action["evidence_ids"]) == 3
    assert not (repo / action["target_path"]).exists()

    receipt = execute_recovery_action(action, root=str(owr_root))
    assert receipt["status"] == "EXECUTED"
    note = repo / action["target_path"]
    assert note.exists()
    body = note.read_text(encoding="utf-8")
    assert finding_id in body
    assert "realized savings" in body

    replay = execute_recovery_action(action, root=str(owr_root))
    assert replay["status"] == "ALREADY_EXISTS"
    assert note.read_text(encoding="utf-8") == body


def test_repo_state_reports_dirty_work_without_mutating(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    setup_repo(repo)
    (repo / "README.md").write_text("changed\n", encoding="utf-8")

    state = inspect_repo_state(str(repo))

    assert state["dirty"] is True
    assert "README.md" in state["changed_paths"]
