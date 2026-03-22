"""Privacy processing for sensitive documents."""

from __future__ import annotations

import re


class PrivacyProcessor:
    """Detect and redact basic PII patterns before indexing."""

    def redact(self, text: str) -> str:
        text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
        text = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]", text)
        text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)
        return text

    def add_embedding_noise(self, embedding: list[float], sigma: float = 0.01) -> list[float]:
        import random

        return [v + random.gauss(0, sigma) for v in embedding]


__all__ = ["PrivacyProcessor"]
