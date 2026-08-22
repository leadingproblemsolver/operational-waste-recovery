from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRADER = ROOT / "evals" / "atomic_ingest" / "grader.py"


def load_grader():
    spec = importlib.util.spec_from_file_location("atomic_ingest_grader", GRADER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_atomic_ingest_grader_rejects_only_the_known_atomicity_mutant() -> None:
    grader = load_grader()
    result = grader.self_check()

    assert result["passed"] is True
    assert result["reference"]["score"] == {"passed": 3, "total": 3}
    assert result["known_bad_mutant"]["score"] == {"passed": 2, "total": 3}
    assert result["discrimination"]["actual_mutant_failures"] == ["mixed_strict_atomic"]
