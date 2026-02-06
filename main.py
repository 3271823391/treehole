from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from api import client_log, debug_relationship
from config import HOST, PORT
from core.log_buffer import add_log
from core.log_handler import BufferLogHandler
from routers import admin_api, admin_console, auth, chat, emotion, page, profile, voice_clone

app = FastAPI(title="DeepSeek虚拟树洞（精致版）")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
AVATAR_DIR = os.path.join(STATIC_DIR, "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

print("STATIC DIR EXISTS:", os.path.exists(STATIC_DIR))
print("STATIC ABS PATH:", STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _ensure_buffer_logging() -> None:
    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, BufferLogHandler):
            return
    root.addHandler(BufferLogHandler())


_ensure_buffer_logging()

_IGNORED_ACCESS_PREFIXES = (
    "/favicon.ico",
    "/.well-known/",
    "/hybridaction/",
    "/static/",
    "/__pycache__/",
)
_ALWAYS_KEEP_PATHS = (
    "/",
    "/ip",
    "/chat_stream",
    "/load_history",
    "/profile",
)


def _should_skip_access(path: str) -> bool:
    if path in _ALWAYS_KEEP_PATHS:
        return False
    if path.startswith("/ip/"):
        return False
    return path.startswith(_IGNORED_ACCESS_PREFIXES)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    path = request.url.path

    if not _should_skip_access(path):
        add_log(
            {
                "ts": time.time(),
                "level": "INFO",
                "source": "access",
                "message": f"{request.method} {path} {response.status_code} {duration_ms}ms",
                "meta": {
                    "method": request.method,
                    "path": path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "query": str(request.url.query or ""),
                },
            }
        )

    return response


app.include_router(emotion.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(page.router)
app.include_router(chat.router)
app.include_router(voice_clone.router)
app.include_router(debug_relationship.router)
app.include_router(client_log.router)
app.include_router(admin_console.router)
if os.getenv("DEBUG_ADMIN", "0") == "1":
    app.include_router(admin_api.router)


def run_api():
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    run_api()
