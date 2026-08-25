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
    state = tools._read_run_state("judge-run")

    assert prepared["state"] == "OBSERVED"
    assert prepared["analysis"]["duplicate_pairs"] == 1
    assert evidence["audit_id"] == finding_id
    assert evidence["finding"]["state"] == "OBSERVED"
    assert evidence["inference"]["state"] == "INFERRED"
    assert evidence["runtime_state"] == "EVIDENCE_READY"
    assert receipt["status"] == "EXECUTED"
    assert receipt["runtime_state"] == "EXECUTED"
    assert receipt["target_path"].startswith(".recovery/")
    assert receipt["overwritten"] is False
    assert receipt["action_count"] == 1
    assert verified["status"] == "VERIFIED"
    assert verified["actual_sha256"] == receipt["sha256"]
    assert verified["action_count"] == 1
    assert replay["status"] == "ALREADY_EXISTS"
    assert replay["sha256"] == receipt["sha256"]
    assert replay["overwritten"] is False
    assert replay["action_count"] == 1
    assert state is not None
    assert state["state"] == "VERIFIED"
    assert state["action_count"] == 1


def test_host_rejects_materialize_before_evidence_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)

    prepared = tools.prepare_demo_run("ordering-run")
    finding_id = str(prepared["strongest_finding_id"])
    receipt = tools.materialize_recovery_capsule("ordering-run", finding_id)

    assert receipt["status"] == "BLOCKED"
    assert receipt["reason"] == "invalid_transition"
    assert receipt["from_state"] == "OBSERVED"
    assert not (tmp_path / "ordering-run" / "repo" / ".recovery").exists()


def test_ambiguous_post_action_crash_reconciles_without_duplicate_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)

    prepared = tools.prepare_demo_run("crash-run")
    finding_id = str(prepared["strongest_finding_id"])
    tools.inspect_recovery_evidence("crash-run", finding_id)

    with pytest.raises(RuntimeError, match="simulated crash"):
        tools._materialize_recovery_capsule(
            "crash-run",
            finding_id,
            simulate_crash_after_write=True,
        )

    state_after_crash = tools._read_run_state("crash-run")
    target = tmp_path / "crash-run" / "repo" / ".recovery" / f"recovery-{finding_id}.md"
    assert target.is_file()
    original = target.read_bytes()
    assert state_after_crash is not None
    assert state_after_crash["state"] == "ACTION_PENDING"
    assert state_after_crash["action_count"] == 1

    # Simulate a fresh worker/process by calling only the public recovery path.
    reconciled = tools.materialize_recovery_capsule("crash-run", finding_id)
    state_after_reconcile = tools._read_run_state("crash-run")

    assert reconciled["status"] == "ALREADY_EXISTS"
    assert reconciled["runtime_state"] == "EXECUTED"
    assert reconciled["reconciled_after_ambiguous_execution"] is True
    assert reconciled["action_count"] == 1
    assert target.read_bytes() == original
    assert state_after_reconcile is not None
    assert state_after_reconcile["state"] == "EXECUTED"
    assert state_after_reconcile["action_count"] == 1

    verified = tools.verify_recovery_receipt("crash-run", finding_id, str(reconciled["sha256"]))
    final_state = tools._read_run_state("crash-run")

    assert verified["status"] == "VERIFIED"
    assert verified["action_count"] == 1
    assert final_state is not None
    assert final_state["state"] == "VERIFIED"
    assert final_state["action_count"] == 1


def test_missing_finding_blocks_without_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)
    tools.prepare_demo_run("blocked-run")

    evidence = tools.inspect_recovery_evidence("blocked-run", "missing")
    receipt = tools.materialize_recovery_capsule("blocked-run", "missing")

    assert evidence == {
        "state": "BLOCKED",
        "reason": "finding_not_authorized",
        "finding_id": "missing",
    }
    assert receipt["status"] == "BLOCKED"
    assert receipt["reason"] in {"finding_not_authorized", "invalid_transition"}
    assert not (tmp_path / "blocked-run" / "repo" / ".recovery").exists()


def test_run_id_cannot_escape_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)

    with pytest.raises(ValueError, match="run_id"):
        tools.prepare_demo_run("../escape")
