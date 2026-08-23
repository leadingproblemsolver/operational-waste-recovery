from __future__ import annotations

from pathlib import Path

import pytest

from recovery_taskmaster import tools


def test_complete_bounded_recovery_and_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)

    prepared = tools.prepare_demo_run("judge-run")
    finding_id = str(prepared["strongest_finding_id"])
    evidence = tools.inspect_recovery_evidence("judge-run", finding_id)
    receipt = tools.materialize_recovery_capsule("judge-run", finding_id)
    verified = tools.verify_recovery_receipt("judge-run", finding_id, str(receipt["sha256"]))
    replay = tools.materialize_recovery_capsule("judge-run", finding_id)

    assert prepared["state"] == "OBSERVED"
    assert prepared["analysis"]["duplicate_pairs"] == 1
    assert evidence["audit_id"] == finding_id
    assert evidence["finding"]["state"] == "OBSERVED"
    assert evidence["inference"]["state"] == "INFERRED"
    assert receipt["status"] == "EXECUTED"
    assert receipt["target_path"].startswith(".recovery/")
    assert receipt["overwritten"] is False
    assert verified["status"] == "VERIFIED"
    assert verified["actual_sha256"] == receipt["sha256"]
    assert replay["status"] == "ALREADY_EXISTS"
    assert replay["sha256"] == receipt["sha256"]
    assert replay["overwritten"] is False


def test_missing_finding_blocks_without_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)
    tools.prepare_demo_run("blocked-run")

    evidence = tools.inspect_recovery_evidence("blocked-run", "missing")
    receipt = tools.materialize_recovery_capsule("blocked-run", "missing")

    assert evidence == {
        "state": "BLOCKED",
        "reason": "finding_not_found",
        "finding_id": "missing",
    }
    assert receipt == {"status": "BLOCKED", "reason": "finding_not_found"}
    assert not (tmp_path / "blocked-run" / "repo" / ".recovery").exists()


def test_run_id_cannot_escape_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)

    with pytest.raises(ValueError, match="run_id"):
        tools.prepare_demo_run("../escape")
