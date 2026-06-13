# MODE: VIBECODABLE
# BRAAT BLOCK: Smoke test
# MISSION: Prove ingest -> status -> validate -> query without style dependencies.

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def copy_repo_fixture(tmp_path: Path) -> Path:
    source = Path.cwd()
    target = tmp_path / "repo"
    ignore = shutil.ignore_patterns(".venv", "__pycache__", "*.pyc", "data/*.sqlite", "logs/*.log", "reports/*.json")
    shutil.copytree(source, target, ignore=ignore)
    return target


def run_cmd(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "owrp.cli", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_cli_proof_path(tmp_path: Path) -> None:
    repo = copy_repo_fixture(tmp_path)
    env = dict(**__import__('os').environ)
    env['PYTHONPATH'] = str(repo / 'src')
    for args in [("ingest",), ("status",), ("validate",), ("query", "redis timeout")]:
        result = subprocess.run(
            [sys.executable, "-m", "owrp.cli", *args],
            cwd=repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout
    assert (repo / "data" / "owrp.sqlite").exists()
    assert (repo / "logs" / "owrp.log").exists()
    assert (repo / "reports" / "weekly_recovery.json").exists()
