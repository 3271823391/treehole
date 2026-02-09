import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from core.auth_utils import (
    decode_token,
    get_auth_secret,
    is_valid_user_id,
    make_user_id,
    normalize_username,
    verify_pin,
    create_token,
)
from data_store import load_user_data, save_user_data
router = APIRouter()

LOGIN_COOKIE_NAME = "auth_token"
REMEMBER_SECONDS = 7 * 24 * 60 * 60


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user: str
    password: str = Field(alias="pass")
    remember: bool = False


def _get_current_user_id(request: Request) -> str | None:
    token = request.cookies.get(LOGIN_COOKIE_NAME, "").strip()
    if not token:
        return None

    secret = get_auth_secret()
    if not secret:
        return None

    payload, err = decode_token(token, secret)
    if err or not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id or not is_valid_user_id(user_id):
        return None
    return user_id


def _is_logged_in(request: Request) -> bool:
    return _get_current_user_id(request) is not None


def _require_login_redirect(request: Request):
    if not _is_logged_in(request):
        return RedirectResponse(url="/login", status_code=302)
    return None


def _render_html_file(filename: str) -> str:
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, filename)
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()



def _with_admin_logger(html: str) -> str:
    script_tag = '<script src="/static/admin_console_logger.js"></script>'
    if script_tag in html:
        return html
    return html.replace("</body>", f"    {script_tag}\n</body>")


def _with_admin_link(html: str) -> str:
    show_link = os.getenv("SHOW_ADMIN_LINK", "1") == "1"
    return html.replace("{{ADMIN_CONSOLE_LINK}}", '<a href="/admin/console" class="admin-console-link">🛠</a>' if show_link else "")

@router.get("/", response_class=HTMLResponse)
async def intro_page(request: Request):
    if _is_logged_in(request):
        return RedirectResponse(url="/ai树洞计划.html", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _is_logged_in(request):
        return RedirectResponse(url="/ai树洞计划.html", status_code=302)
    return HTMLResponse(_render_html_file("login.html"))




@router.get("/register")
async def register_page(request: Request):
    if _is_logged_in(request):
        return RedirectResponse(url="/ai树洞计划.html", status_code=302)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return FileResponse(os.path.join(base_dir, "static", "register.html"))
@router.post("/login")
async def login_action(payload: LoginRequest):
    user = (payload.user or "").strip()
    password = payload.password or ""

    norm = normalize_username(user)
    if not norm:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "username_required"})

    user_id = make_user_id(norm)
    user_info = load_user_data(user_id)
    profile = user_info.get("profile", {})
    pin_hash = profile.get("pin_hash", "")

    if not pin_hash or not verify_pin(password, pin_hash):
        return JSONResponse(status_code=401, content={"ok": False, "msg": "invalid_credentials"})

    secret = get_auth_secret()
    if not secret:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "auth_secret_missing"})

    token_expire_seconds = REMEMBER_SECONDS if payload.remember else 12 * 60 * 60
    token = create_token(user_id, secret, expire_seconds=token_expire_seconds)

    response = JSONResponse(status_code=200, content={"ok": True, "user_id": user_id})
    cookie_kwargs = {
        "key": LOGIN_COOKIE_NAME,
        "value": token,
        "httponly": True,
        "path": "/",
        "samesite": "lax",
    }

    if payload.remember:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=REMEMBER_SECONDS)
        cookie_kwargs["max_age"] = REMEMBER_SECONDS
        cookie_kwargs["expires"] = expires_at.strftime("%a, %d %b %Y %H:%M:%S GMT")

    response.set_cookie(**cookie_kwargs)
    return response


@router.get("/logout")
async def logout_action():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(LOGIN_COOKIE_NAME, path="/")
    return response


@router.get("/ai树洞计划.html", response_class=HTMLResponse)
async def ai_treehole_page(request: Request):
    if not _is_logged_in(request):
        return RedirectResponse(url="/login", status_code=302)
    html = _render_html_file("ai树洞计划.html")
    return HTMLResponse(_with_admin_logger(_with_admin_link(html)))

@router.get("/ip", response_class=HTMLResponse)
async def ip_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, "虚拟ip.html")

    with open(html_path, "r", encoding="utf-8") as f:
        return _with_admin_logger(f.read())

@router.get("/二级页面2第六版.html", response_class=HTMLResponse)
async def evolution_plus_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    return render_html("二级页面2第六版.html")

@router.get("/page", response_class=HTMLResponse)
async def chat_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    plan = request.query_params.get("plan", "plus")

    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, "treehole.html")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{DEFAULT_PLAN}}", plan)
    return _with_admin_logger(html)


@router.get("/treehole_plus", response_class=HTMLResponse)
async def treehole_plus_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    return render_html("treehole_plus.html")

@router.get("/treehole_pro", response_class=HTMLResponse)
async def treehole_pro_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    return render_html("treehole_pro.html")

def render_html(filename: str):
    return _with_admin_logger(_render_html_file(filename))

def resolve_ip_user_id(request: Request) -> str:
    user_id = request.query_params.get("user_id", "")
    if is_valid_user_id(user_id):
        return user_id
    return make_user_id("web_user")


@router.get("/ip/linyu", response_class=HTMLResponse)
async def linyu_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "linyu"   # ★ 必须

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/林屿哥哥.html", encoding="utf-8").read()))



@router.get("/ip/suwan", response_class=HTMLResponse)
async def suwan_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "suwan"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/苏晚姐姐.html", encoding="utf-8").read()))


@router.get("/ip/xiaxingmian", response_class=HTMLResponse)
async def xiaxingmian_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "xiaxingmian"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/病娇校花.html", encoding="utf-8").read()))

@router.get("/ip/jiangche", response_class=HTMLResponse)
async def jiangche_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "jiangche"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/白月光江澈.html", encoding="utf-8").read()))

@router.get("/ip/luchengyu", response_class=HTMLResponse)
async def luchengyu_page(request: Request):
    unauthorized = _require_login_redirect(request)
    if unauthorized:
        return unauthorized
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "luchengyu"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/学长.html", encoding="utf-8").read()))
