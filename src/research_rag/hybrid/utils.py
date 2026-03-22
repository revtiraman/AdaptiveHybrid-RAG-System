from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def stable_id(prefix: str, raw: str) -> str:
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    cleaned = re.sub(r"[^a-zA-Z0-9-]+", "-", raw.lower()).strip("-")[:48] or "item"
    return f"{prefix}-{cleaned}-{digest}"


def sha256_bytes(content: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(content)
    return digest.hexdigest()


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()
