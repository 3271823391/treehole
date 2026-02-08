from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-console"])


@router.get("/admin/console", response_class=HTMLResponse)
def admin_console_page():
    html_path = Path(__file__).resolve().parent.parent / "static" / "admin_console.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
