import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.session_auth import get_current_user_id

router = APIRouter()


def _render_html(filename: str) -> HTMLResponse:
    base_dir = os.path.dirname(__file__)
    with open(os.path.join(base_dir, filename), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@router.get("/", response_class=HTMLResponse)
def root_page(request: Request):
    if not get_current_user_id(request):
        return RedirectResponse(url="/login", status_code=302)
    return _render_html("treehole.html")


@router.get("/page", response_class=HTMLResponse)
def page_alias(request: Request):
    if not get_current_user_id(request):
        return RedirectResponse(url="/login", status_code=302)
    return _render_html("treehole.html")
