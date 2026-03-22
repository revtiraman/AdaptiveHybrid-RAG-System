from __future__ import annotations

import logging
from contextvars import ContextVar, Token

_REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _REQUEST_ID.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            handler.addFilter(_RequestIdFilter())
        root.setLevel(level.upper())
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
        )
    )
    handler.addFilter(_RequestIdFilter())
    root.addHandler(handler)
    root.setLevel(level.upper())


def bind_request_id(request_id: str) -> Token[str]:
    return _REQUEST_ID.set(request_id)


def reset_request_id(token: Token[str]) -> None:
    _REQUEST_ID.reset(token)
