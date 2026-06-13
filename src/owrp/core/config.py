# MODE: HYBRID
# BRAAT BLOCK: Minimal runtime config
# MISSION: Load only values used by implemented commands.
# MANUAL LINE: OPENAI_API_KEY may be supplied in .env, but current local proof path does not require it.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    openai_api_key: str | None
    db_url: str


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config(root: Path | None = None) -> RuntimeConfig:
    base = root or Path.cwd()
    env_file = _read_dotenv(base / ".env")
    api_key = os.getenv("OPENAI_API_KEY") or env_file.get("OPENAI_API_KEY") or None
    return RuntimeConfig(openai_api_key=api_key, db_url=str(base / "data" / "owrp.sqlite"))
