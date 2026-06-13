# MODE: VIBECODABLE
# BRAAT BLOCK: Stable fingerprints
# MISSION: Provide reproducible local hashes without relying on external embeddings.

from __future__ import annotations

import hashlib
import re
from collections import Counter

_WORD_RE = re.compile(r"[a-z0-9_./:-]+", re.IGNORECASE)


def normalize_text(text: str) -> str:
    return " ".join(_WORD_RE.findall(text.lower()))


def stable_hash(text: str, length: int = 16) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()[:length]


def token_fingerprint(text: str) -> set[str]:
    return set(normalize_text(text).split())


def weighted_fingerprint(text: str) -> Counter[str]:
    return Counter(normalize_text(text).split())


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def estimate_tokens(text: str) -> int:
    # Conservative local estimator: roughly 4 chars/token for English-like text.
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // 4)


def context_hash(files_read: tuple[str, ...], prompt: str) -> str:
    # Context reconstruction is about repeated loaded material, not prompt wording.
    # The prompt parameter stays in the signature because ingestion already passes it.
    material = "\n".join(sorted(files_read))
    return stable_hash(material, length=20)
