# MODE: VIBECODABLE
# BRAAT BLOCK: Inspectable local logs
# MISSION: Make every CLI run verifiable without external telemetry.

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from owrp.core.paths import ensure_runtime_dirs, log_path


def log_event(message: str, root: Path | None = None) -> None:
    ensure_runtime_dirs(root)
    line = f"{datetime.now(timezone.utc).isoformat()} {message}\n"
    log_path(root).open("a", encoding="utf-8").write(line)
