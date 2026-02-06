from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import time

from core.log_buffer import add_log


class BufferLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self._should_ignore(record):
                return

            message = record.getMessage()
            if not isinstance(message, str):
                message = str(message)

            meta = {
                "logger": record.name,
                "module": record.module,
                "func": record.funcName,
                "line": record.lineno,
            }
            if record.exc_info:
                meta["exc"] = logging.Formatter().formatException(record.exc_info)

            ts = float(record.created or time())
            add_log(
                {
                    "ts": ts,
                    "iso": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                    "level": record.levelname.upper(),
                    "source": "server",
                    "message": message,
                    "meta": meta,
                }
            )
        except Exception:
            # must never break normal logging
            return

    @staticmethod
    def _should_ignore(record: logging.LogRecord) -> bool:
        if record.name == "uvicorn.access":
            return True

        if record.name == "uvicorn.error":
            msg = (record.getMessage() or "").lower()
            noisy_keywords = ["socket", "address already in use", "connection reset", "broken pipe"]
            return any(word in msg for word in noisy_keywords)

        return False
