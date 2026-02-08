from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import Lock
from time import time
from typing import Any

_LOGS: deque[dict[str, Any]] = deque(maxlen=5000)
_LOCK = Lock()


def _normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    ts = float(entry.get("ts") or time())
    iso = entry.get("iso")
    if not isinstance(iso, str) or not iso:
        iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    level = str(entry.get("level") or "INFO").upper()
    source = str(entry.get("source") or "server")
    message = str(entry.get("message") or "")
    meta = entry.get("meta")
    if not isinstance(meta, dict):
        meta = {}

    return {
        "ts": ts,
        "iso": iso,
        "level": level,
        "source": source,
        "message": message,
        "meta": meta,
    }


def add_log(entry: dict[str, Any]) -> None:
    normalized = _normalize_entry(entry)
    with _LOCK:
        _LOGS.append(normalized)


def get_logs(since: float | None = None, limit: int = 500) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 500), 5000))
    with _LOCK:
        items = list(_LOGS)

    if since is not None:
        items = [item for item in items if float(item.get("ts", 0)) > since]

    return items[-safe_limit:]


def clear_logs() -> None:
    with _LOCK:
        _LOGS.clear()
