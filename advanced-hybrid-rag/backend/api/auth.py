"""Authentication helpers for API and websocket endpoints."""

from __future__ import annotations

from fastapi import Header, HTTPException, status


def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
	"""Simple API-key check, designed for local/dev bootstrapping."""
	expected = "dev-key"
	if x_api_key is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
	if x_api_key != expected:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
	return x_api_key


__all__ = ["verify_api_key"]
