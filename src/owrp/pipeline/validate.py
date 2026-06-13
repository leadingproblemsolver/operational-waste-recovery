# MODE: VIBECODABLE
# BRAAT BLOCK: Executability validator
# MISSION: Verify only real files, real tables, and real commands used by this repo.

from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path

from owrp.core.paths import db_path, log_path, weekly_report_path

REQUIRED_PACKAGES = [
    "owrp.core.paths",
    "owrp.core.hashing",
    "owrp.pipeline.ingest",
    "owrp.pipeline.deduplicate",
    "owrp.pipeline.reports",
    "owrp.storage.sqlite_store",
    "owrp.retrieval.query",
    "owrp.execution_context.capsules",
]

REQUIRED_TABLES = [
    "llm_interactions",
    "duplicate_prompt_pairs",
    "context_reconstruction_events",
    "recovery_ledger",
    "incident_events",
    "incident_edges",
    "context_capsules",
]

REQUIRED_PATHS = [
    "src/owrp/core",
    "src/owrp/pipeline",
    "src/owrp/storage",
    "src/owrp/retrieval",
    "src/owrp/execution_context",
    "docs/tools",
    "configs/waste-taxonomy.yaml",
    "configs/incident_ontology.yaml",
]


def validate_imports() -> list[str]:
    errors: list[str] = []
    for module_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            errors.append(f"import failed: {module_name}: {exc}")
    return errors


def validate_paths(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            errors.append(f"missing required path: {rel}")
    return errors


def validate_db(root: Path) -> list[str]:
    errors: list[str] = []
    path = db_path(root)
    if not path.exists():
        errors.append("missing database: run `python -m owrp.cli ingest` first")
        return errors
    conn = sqlite3.connect(path)
    try:
        present = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        for table in REQUIRED_TABLES:
            if table not in present:
                errors.append(f"missing table: {table}")
    finally:
        conn.close()
    return errors


def validate_runtime_outputs(root: Path) -> list[str]:
    warnings: list[str] = []
    if not log_path(root).exists():
        warnings.append("log not found yet: logs/owrp.log")
    if not weekly_report_path(root).exists():
        warnings.append("report not found yet: reports/weekly_recovery.json")
    return warnings


def run_validation(root: Path) -> tuple[list[str], list[str]]:
    errors = []
    errors.extend(validate_paths(root))
    errors.extend(validate_imports())
    errors.extend(validate_db(root))
    warnings = validate_runtime_outputs(root)
    return errors, warnings
