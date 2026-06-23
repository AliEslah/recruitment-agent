from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecretRedaction:
    value: str | None
    replacement: str


def redact_secrets(text: str, secrets_to_redact: list[SecretRedaction] | None = None) -> str:
    redacted = text
    for secret in secrets_to_redact or []:
        if secret.value:
            redacted = redacted.replace(secret.value, secret.replacement)
    return redacted
