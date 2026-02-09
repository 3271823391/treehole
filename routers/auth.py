import json
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import base64
import hashlib
import hmac

from core.session_auth import clear_session_cookie, get_current_user_id, set_session_cookie
from data_store import load_user_data, save_user_data

router = APIRouter()
AUTH_FILE = Path(__file__).resolve().parent.parent / "auth_users.json"


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return base64.b64encode(salt + digest).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    try:
        raw = base64.b64decode(hashed.encode("utf-8"))
        salt, digest = raw[:16], raw[16:]
        expect = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
        return hmac.compare_digest(expect, digest)
    except Exception:
        return False



def _load_auth_users() -> dict:
    if not AUTH_FILE.exists():
        AUTH_FILE.write_text("{}", encoding="utf-8")
    return json.loads(AUTH_FILE.read_text(encoding="utf-8"))


def _save_auth_users(data: dict) -> None:
    AUTH_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _render_html(filename: str) -> HTMLResponse:
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, filename)
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if get_current_user_id(request):
        return RedirectResponse(url="/", status_code=302)
    return _render_html("login.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if get_current_user_id(request):
        return RedirectResponse(url="/", status_code=302)
    return _render_html("register.html")


@router.post("/auth/register")
async def register(request: Request):
    payload = await request.json()
    username = (payload.get("username") or "").strip().lower()
    password = (payload.get("password") or "").strip()
    confirm_password = (payload.get("confirm_password") or "").strip()

    if not username or not password or password != confirm_password:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "注册信息无效"})

    users = _load_auth_users()
    if username in users:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "注册失败"})

    user_id = f"u_{uuid.uuid4()}"
    users[username] = {
        "user_id": user_id,
        "password_hash": _hash_password(password),
    }
    _save_auth_users(users)

    user_info = load_user_data(user_id)
    user_info.setdefault("profile", {})
    save_user_data(user_id, user_info)

    return {"ok": True}


@router.post("/auth/login")
async def login(request: Request):
    payload = await request.json()
    username = (payload.get("username") or "").strip().lower()
    password = (payload.get("password") or "").strip()

    users = _load_auth_users()
    record = users.get(username)
    if not username or not password or not record:
        return JSONResponse(status_code=401, content={"ok": False, "msg": "账号或密码错误"})

    if not _verify_password(password, record.get("password_hash", "")):
        return JSONResponse(status_code=401, content={"ok": False, "msg": "账号或密码错误"})

    response = JSONResponse(status_code=200, content={"ok": True, "redirect": "/"})
    set_session_cookie(response, record["user_id"])
    return response


@router.post("/auth/logout")
def logout():
    response = JSONResponse(status_code=200, content={"ok": True})
    clear_session_cookie(response)
    return response


@router.get("/auth/status")
def auth_status(request: Request):
    return {"ok": True, "authenticated": bool(get_current_user_id(request))}
