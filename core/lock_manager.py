from __future__ import annotations

import asyncio

_LOCKS: dict[str, asyncio.Lock] = {}
_LOCKS_GUARD = asyncio.Lock()


async def get_conv_lock(conv_key: str) -> asyncio.Lock:
    async with _LOCKS_GUARD:
        lock = _LOCKS.get(conv_key)
        if lock is None:
            lock = asyncio.Lock()
            _LOCKS[conv_key] = lock
        return lock
