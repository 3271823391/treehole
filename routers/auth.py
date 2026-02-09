import time
from threading import Lock

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.auth_utils import (
    create_token,
    get_auth_secret,
    hash_password,
    make_user_id,
    normalize_username,
    validate_password,
    verify_password,
)
from data_store import load_user_data, save_user_data

router = APIRouter()

_failed_attempts = {}
_failed_lock = Lock()
_MAX_FAILED = 5
_LOCK_SECONDS = 5 * 60


class AuthRequest(BaseModel):
    username: str
    pin: str


def _get_failed_state(user_id: str):
    with _failed_lock:
        return _failed_attempts.get(user_id, {"count": 0, "locked_until": 0})


def _set_failed_state(user_id: str, state: dict):
    with _failed_lock:
        _failed_attempts[user_id] = state


def _reset_failed_state(user_id: str):
    with _failed_lock:
        _failed_attempts.pop(user_id, None)


@router.post("/auth/init")
def auth_init(req: AuthRequest):
    secret = get_auth_secret()
    if not secret:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "auth_secret_missing"})

    norm = normalize_username(req.username)
    if not norm:
        return JSONResponse(status_code=200, content={"ok": False, "msg": "username_required"})

    valid_password, password_msg = validate_password(req.pin)
    if not valid_password:
        return JSONResponse(status_code=200, content={"ok": False, "msg": password_msg})

    user_id = make_user_id(norm)
    user_info = load_user_data(user_id)
    profile = user_info.setdefault("profile", {})

    if profile.get("password_hash"):
        return JSONResponse(status_code=200, content={"ok": False, "msg": "pin_already_set"})

    profile["password_hash"] = hash_password(req.pin)
    profile.pop("pin_hash", None)
    profile["username"] = req.username.strip()
    profile.setdefault("avatar_url", "")
    profile.setdefault("display_name", "")

    save_user_data(user_id, user_info)
    return {"ok": True}


@router.post("/auth/verify")
def auth_verify(req: AuthRequest):
    secret = get_auth_secret()
    if not secret:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "auth_secret_missing"})

    norm = normalize_username(req.username)
    if not norm:
        return JSONResponse(status_code=200, content={"ok": False, "msg": "username_required"})

    user_id = make_user_id(norm)
    user_info = load_user_data(user_id)
    profile = user_info.setdefault("profile", {})
    password_hash = profile.get("password_hash")

    if not password_hash:
        return JSONResponse(status_code=200, content={"ok": False, "need_init": True})

    state = _get_failed_state(user_id)
    now = int(time.time())
    locked_until = state.get("locked_until", 0)
    if locked_until and locked_until > now:
        return JSONResponse(
            status_code=200,
            content={
                "ok": False,
                "locked": True,
                "seconds_left": locked_until - now,
            },
        )

    valid_password, password_msg = validate_password(req.pin)
    if not valid_password:
        return JSONResponse(status_code=200, content={"ok": False, "msg": password_msg})

    if not verify_password(req.pin, password_hash):
        new_count = state.get("count", 0) + 1
        new_state = {"count": new_count, "locked_until": 0}
        if new_count >= _MAX_FAILED:
            new_state["locked_until"] = now + _LOCK_SECONDS
        _set_failed_state(user_id, new_state)
        response = {"ok": False, "msg": "pin_incorrect"}
        if new_state["locked_until"]:
            response.update({"locked": True, "seconds_left": _LOCK_SECONDS})
        return JSONResponse(status_code=200, content=response)

    _reset_failed_state(user_id)
    token = create_token(user_id, secret)
    profile_data = {
        "username": profile.get("username", req.username.strip()),
        "display_name": profile.get("display_name", ""),
        "avatar_url": profile.get("avatar_url", ""),
    }
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "user_id": user_id,
            "token": token,
            "profile": profile_data,
        },
    )
