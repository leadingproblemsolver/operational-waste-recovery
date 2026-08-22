from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
REFERENCE = ROOT / "src" / "owrp" / "pipeline" / "ingest.py"
MUTANT = Path(__file__).resolve().parent / "mutants" / "early_insert.py"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from owrp.adapters import adapt  # noqa: E402
from owrp.storage.sqlite_store import SQLiteStore  # noqa: E402


def load_candidate(path: Path) -> ModuleType:
    path = path.resolve()
    spec = importlib.util.spec_from_file_location(f"atomic_ingest_candidate_{abs(hash(path))}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load candidate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "ingest_jsonl", None)):
        raise RuntimeError(f"candidate does not define ingest_jsonl(): {path}")
    return module


def read_one_jsonl(path: Path) -> dict[str, object]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise RuntimeError(f"expected exactly one JSONL record in {path}")
    value = json.loads(lines[0])
    if not isinstance(value, dict):
        raise RuntimeError(f"fixture record must be an object: {path}")
    return value


def seed_existing(store: SQLiteStore) -> None:
    raw = read_one_jsonl(FIXTURES / "seed_existing.jsonl")
    event = adapt(raw, "canonical")
    problems = event.validate()
    if problems:
        raise RuntimeError(f"invalid seed fixture: {'; '.join(problems)}")
    store.insert(event)


def row_snapshot(store: SQLiteStore) -> list[dict[str, object]]:
    return [dict(row) for row in store.rows()]


def case_all_valid(candidate: ModuleType) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="owrp-eval-valid-") as tmp:
        store = SQLiteStore(Path(tmp) / "state")
        try:
            counts, errors = candidate.ingest_jsonl(
                FIXTURES / "all_valid.jsonl",
                store,
                strict=True,
            )
            rows = row_snapshot(store)
            passed = (
                counts == {"inserted": 2, "rejected": 0, "lines": 2}
                and errors == []
                and [row["event_id"] for row in rows] == ["eval-valid-a", "eval-valid-b"]
            )
            return {
                "case": "all_valid_strict",
                "passed": passed,
                "counts": counts,
                "errors": errors,
                "event_ids": [row["event_id"] for row in rows],
            }
        except Exception as error:
            return {
                "case": "all_valid_strict",
                "passed": False,
                "unexpected_exception": f"{type(error).__name__}: {error}",
            }
        finally:
            store.close()


def case_mixed_non_strict(candidate: ModuleType) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="owrp-eval-nonstrict-") as tmp:
        store = SQLiteStore(Path(tmp) / "state")
        try:
            seed_existing(store)
            counts, errors = candidate.ingest_jsonl(
                FIXTURES / "mixed.jsonl",
                store,
                strict=False,
            )
            rows = row_snapshot(store)
            by_id = {row["event_id"]: row for row in rows}
            passed = (
                counts == {"inserted": 2, "rejected": 1, "lines": 3}
                and len(errors) == 1
                and errors[0].get("line") == 2
                and set(by_id) == {"eval-existing", "eval-new"}
                and by_id["eval-existing"]["prompt"] == "after"
            )
            return {
                "case": "mixed_non_strict",
                "passed": passed,
                "counts": counts,
                "errors": errors,
                "event_ids": sorted(by_id),
                "existing_prompt": by_id.get("eval-existing", {}).get("prompt"),
            }
        except Exception as error:
            return {
                "case": "mixed_non_strict",
                "passed": False,
                "unexpected_exception": f"{type(error).__name__}: {error}",
            }
        finally:
            store.close()


def case_mixed_strict_atomic(candidate: ModuleType) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="owrp-eval-strict-") as tmp:
        store = SQLiteStore(Path(tmp) / "state")
        try:
            seed_existing(store)
            before = row_snapshot(store)
            raised_value_error = False
            exception_text = None
            try:
                candidate.ingest_jsonl(
                    FIXTURES / "mixed.jsonl",
                    store,
                    strict=True,
                )
            except ValueError as error:
                raised_value_error = True
                exception_text = str(error)
            except Exception as error:
                exception_text = f"{type(error).__name__}: {error}"

            after = row_snapshot(store)
            passed = raised_value_error and after == before
            return {
                "case": "mixed_strict_atomic",
                "passed": passed,
                "raised_value_error": raised_value_error,
                "exception": exception_text,
                "before_event_ids": [row["event_id"] for row in before],
                "after_event_ids": [row["event_id"] for row in after],
                "before_existing_prompt": before[0]["prompt"] if before else None,
                "after_existing_prompt": after[0]["prompt"] if after else None,
            }
        finally:
            store.close()


def evaluate(candidate_path: Path) -> dict[str, object]:
    candidate = load_candidate(candidate_path)
    cases = [
        case_all_valid(candidate),
        case_mixed_non_strict(candidate),
        case_mixed_strict_atomic(candidate),
    ]
    passed_count = sum(1 for case in cases if case["passed"])
    return {
        "candidate": str(candidate_path.resolve()),
        "passed": passed_count == len(cases),
        "score": {"passed": passed_count, "total": len(cases)},
        "cases": cases,
    }


def self_check() -> dict[str, object]:
    reference = evaluate(REFERENCE)
    mutant = evaluate(MUTANT)
    mutant_failures = [case["case"] for case in mutant["cases"] if not case["passed"]]
    passed = (
        reference["passed"] is True
        and mutant["passed"] is False
        and mutant_failures == ["mixed_strict_atomic"]
    )
    return {
        "passed": passed,
        "reference": reference,
        "known_bad_mutant": mutant,
        "discrimination": {
            "expected_mutant_failure": "mixed_strict_atomic",
            "actual_mutant_failures": mutant_failures,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grade the OWR strict-ingest atomicity contract")
    parser.add_argument(
        "--candidate",
        type=Path,
        default=REFERENCE,
        help="Python file defining ingest_jsonl()",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Verify the reference passes and the known-bad early-write mutant is rejected",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = self_check() if args.self_check else evaluate(args.candidate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
