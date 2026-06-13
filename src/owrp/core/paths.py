# MODE: VIBECODABLE
# BRAAT BLOCK: Real path registry
# MISSION: Prevent imagined paths by centralising only implemented paths.
# ALLOWED SCOPE: Repository-local files that are actually written/read by CLI commands.

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path.cwd()


def data_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "data"


def logs_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "logs"


def reports_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "reports"


def db_path(root: Path | None = None) -> Path:
    return data_dir(root) / "owrp.sqlite"


def log_path(root: Path | None = None) -> Path:
    return logs_dir(root) / "owrp.log"


def weekly_report_path(root: Path | None = None) -> Path:
    return reports_dir(root) / "weekly_recovery.json"


def ensure_runtime_dirs(root: Path | None = None) -> None:
    for folder in (data_dir(root), logs_dir(root), reports_dir(root)):
        folder.mkdir(parents=True, exist_ok=True)
