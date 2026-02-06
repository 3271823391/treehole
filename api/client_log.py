from __future__ import annotations

import time
from collections import deque
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core.log_buffer import add_log

router = APIRouter()

_CLIENT_RATE: dict[str, deque[float]] = {}
_MAX_PER_SECOND = 30
_NOISE_KEYWORDS = ["zybtrackerstatisticsaction", "chrome.devtools", "favicon"]


class ClientLogPayload(BaseModel):
    level: str = "log"
    message: str = ""
    page: str = ""
    user_id: str | None = None
    character_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


def _rate_ok(ip: str) -> bool:
    now = time.time()
    bucket = _CLIENT_RATE.setdefault(ip, deque())
    while bucket and now - bucket[0] > 1.0:
        bucket.popleft()
    if len(bucket) >= _MAX_PER_SECOND:
        return False
    bucket.append(now)
    return True


@router.post("/api/client_log")
async def client_log(payload: ClientLogPayload, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_ok(client_ip):
        return {"ok": True, "dropped": True, "reason": "rate_limit"}

    message = (payload.message or "").strip()
    if not message:
        return {"ok": True, "dropped": True, "reason": "empty"}

    lowered = message.lower()
    if any(item in lowered for item in _NOISE_KEYWORDS):
        return {"ok": True, "dropped": True, "reason": "noise"}

    level_map = {
        "log": "INFO",
        "info": "INFO",
        "warn": "WARN",
        "warning": "WARN",
        "error": "ERROR",
        "debug": "DEBUG",
    }

    meta = {
        "page": payload.page,
        "user_id": payload.user_id,
        "character_id": payload.character_id,
        "extra": payload.extra,
        "ip": client_ip,
    }

    add_log(
        {
            "ts": time.time(),
            "level": level_map.get(payload.level.lower(), "INFO"),
            "source": "client",
            "message": message,
            "meta": meta,
        }
    )

    return {"ok": True}
