from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-console"])


def _enabled() -> bool:
    return os.getenv("DEBUG_ADMIN", "0") == "1"


def _assert_enabled() -> None:
    if not _enabled():
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/admin/console", response_class=HTMLResponse)
def admin_console_page():
    _assert_enabled()
    html_path = Path(__file__).resolve().parent.parent / "static" / "admin_console.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
