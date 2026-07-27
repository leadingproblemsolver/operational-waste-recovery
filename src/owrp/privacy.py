from __future__ import annotations

import json
import re
from dataclasses import replace
from typing import Any

from owrp.core.types import Interaction

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\beyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd)\b\s*[:=]\s*['\"]?([^\s,'\"]{8,})"),
    re.compile(r"\bsk-[a-zA-Z0-9_-]{12,}\b"),
]
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)")


def contains_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def redact_text(value: str) -> str:
    text = value
    for pattern in SECRET_PATTERNS:
        if "PRIVATE KEY" in pattern.pattern:
            text = pattern.sub("[REDACTED_PRIVATE_KEY]", text)
        else:
            text = pattern.sub("[REDACTED_SECRET]", text)
    text = EMAIL.sub("[REDACTED_EMAIL]", text)
    text = PHONE.sub("[REDACTED_PHONE]", text)
    return text


def _redact_object(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _redact_object(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_object(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_object(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


def secret_locations(event: Interaction) -> list[str]:
    fields = {
        "prompt": event.prompt,
        "response": event.response,
        "metadata": json.dumps(event.metadata, sort_keys=True, default=str),
        "files_read": "\n".join(event.files_read),
        "files_modified": "\n".join(event.files_modified),
    }
    return [name for name, value in fields.items() if contains_secret(value)]


def sanitize_interaction(
    event: Interaction,
    *,
    redact_sensitive: bool = False,
    reject_secrets: bool = True,
) -> Interaction:
    locations = secret_locations(event)
    if locations and reject_secrets and not redact_sensitive:
        raise ValueError(f"possible secret detected in: {', '.join(locations)}; use --redact-sensitive or explicitly --allow-secrets")
    if not redact_sensitive:
        return event
    return replace(
        event,
        prompt=redact_text(event.prompt),
        response=redact_text(event.response),
        files_read=tuple(redact_text(value) for value in event.files_read),
        files_modified=tuple(redact_text(value) for value in event.files_modified),
        metadata=_redact_object(event.metadata),
    )
