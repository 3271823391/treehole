from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api import admin_logs, client_log, debug_relationship
from config import HOST, PORT
from core.log_buffer import add_log
from core.log_handler import BufferLogHandler
from core.session_auth import get_current_user_id
from routers import admin_api, auth, chat, emotion, page, voice_clone

app = FastAPI(title="DeepSeek虚拟树洞（精致版）")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
AVATAR_DIR = os.path.join(STATIC_DIR, "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _ensure_buffer_logging() -> None:
    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, BufferLogHandler):
            return
    root.addHandler(BufferLogHandler())


_ensure_buffer_logging()

_PUBLIC_PATHS = {
    "/login",
    "/register",
    "/auth/login",
    "/auth/register",
    "/auth/status",
}


@app.middleware("http")
async def auth_guard_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/static") or path in _PUBLIC_PATHS:
        return await call_next(request)

    user_id = get_current_user_id(request)
    if not user_id:
        if request.method == "GET":
            return RedirectResponse(url="/login", status_code=302)
        return JSONResponse(status_code=401, content={"ok": False, "msg": "unauthorized"})

    return await call_next(request)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    path = request.url.path
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
app.include_router(page.router)
app.include_router(chat.router)
app.include_router(voice_clone.router)
app.include_router(admin_api.router)
app.include_router(debug_relationship.router)
app.include_router(client_log.router)
app.include_router(admin_logs.router)


def run_api():
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    run_api()
