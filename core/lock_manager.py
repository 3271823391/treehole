from __future__ import annotations

import asyncio

_LOCKS: dict[str, asyncio.Lock] = {}


def get_lock(conv_key: str) -> asyncio.Lock:
    lock = _LOCKS.get(conv_key)
    if lock is None:
        lock = asyncio.Lock()
        _LOCKS[conv_key] = lock
    return lock
