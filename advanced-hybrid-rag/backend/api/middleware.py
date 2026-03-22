"""Middleware utilities used by the API app."""

from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestLoggingMiddleware(BaseHTTPMiddleware):
	"""Emit lightweight structured timing logs."""

	async def dispatch(self, request: Request, call_next):
		start = time.perf_counter()
		response = await call_next(request)
		elapsed_ms = (time.perf_counter() - start) * 1000
		response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
		return response


class AuthMiddleware(BaseHTTPMiddleware):
	"""Optional API-key enforcement for /api routes."""

	def __init__(self, app, enabled: bool = False, header_name: str = "x-api-key", expected_key: str = "dev-key"):
		super().__init__(app)
		self.enabled = enabled
		self.header_name = header_name
		self.expected_key = expected_key

	async def dispatch(self, request: Request, call_next):
		if not self.enabled or not request.url.path.startswith("/api"):
			return await call_next(request)
		incoming = request.headers.get(self.header_name)
		if incoming != self.expected_key:
			return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
		return await call_next(request)


__all__ = ["RequestLoggingMiddleware", "AuthMiddleware"]
