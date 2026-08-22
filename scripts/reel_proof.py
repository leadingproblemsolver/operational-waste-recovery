from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from owrp.reel_proof import build_reel_proof  # noqa: E402


def main() -> int:
    sample = REPO_ROOT / "data" / "sample_events.jsonl"
    with tempfile.TemporaryDirectory(prefix="owrp-reel-proof-") as tmp:
        proof = build_reel_proof(sample, Path(tmp))
    print(json.dumps(proof, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
