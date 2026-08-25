from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from main import INSPECTOR_HTML, _snapshot
from recovery_taskmaster import tools


def test_snapshot_tracks_real_persisted_run_to_verified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)

    prepared = tools.prepare_demo_run("inspector-run")
    finding_id = str(prepared["strongest_finding_id"])

    observed = _snapshot("inspector-run")
    assert observed["run"]["state"] == "OBSERVED"
    assert observed["run"]["action_count"] == 0
    assert observed["artifact"]["exists"] is False
    assert observed["verification"]["settled"] is False
    assert observed["timeline"][0] == {"phase": "OBSERVED", "status": "current"}

    evidence = tools.inspect_recovery_evidence("inspector-run", finding_id)
    assert evidence["runtime_state"] == "EVIDENCE_READY"

    execution = tools.materialize_recovery_capsule("inspector-run", finding_id)
    assert execution["status"] == "EXECUTED"

    verification = tools.verify_recovery_receipt(
        "inspector-run",
        finding_id,
        str(execution["sha256"]),
    )
    assert verification["status"] == "VERIFIED"

    settled = _snapshot("inspector-run")
    assert settled["run"]["state"] == "VERIFIED"
    assert settled["run"]["action_count"] == 1
    assert settled["artifact"]["exists"] is True
    assert settled["artifact"]["path"] == execution["target_path"]
    assert settled["verification"]["expected_sha256"] == execution["sha256"]
    assert settled["verification"]["observed_sha256"] == execution["sha256"]
    assert settled["verification"]["match"] is True
    assert settled["verification"]["settled"] is True
    assert all(item["status"] in {"complete", "current"} for item in settled["timeline"])
    assert settled["timeline"][-1] == {"phase": "VERIFIED", "status": "current"}


def test_snapshot_missing_run_is_explicit_not_mocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tools, "_BASE", tmp_path)

    with pytest.raises(HTTPException) as raised:
        _snapshot("missing-run")

    assert raised.value.status_code == 404
    assert raised.value.detail == "run not found"


def test_inspector_contract_is_read_only_and_comprehensible() -> None:
    assert "Read-only inspector" in INSPECTOR_HTML
    assert "Nothing on this page executes or retries work" in INSPECTOR_HTML
    assert "Execution timeline" in INSPECTOR_HTML
    assert "Independent verification" in INSPECTOR_HTML
    assert "Raw persisted runtime state" in INSPECTOR_HTML
    assert "/api/runs/${encodeURIComponent(runId)}" in INSPECTOR_HTML
    assert "mock" not in INSPECTOR_HTML.lower()
