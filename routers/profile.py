import os
import time

from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from PIL import Image

from core.auth_utils import is_valid_user_id
from data_store import load_user_data, save_user_data
from routers.page import LOGIN_COOKIE_NAME

router = APIRouter()


def normalize_profile(user_info: dict) -> dict:
    profile = user_info.setdefault("profile", {})
    base_username = (profile.get("base_username") or profile.get("username") or "").strip()
    base_avatar = (profile.get("base_avatar") or profile.get("avatar_url") or "").strip()
    profile["base_username"] = base_username
    profile["base_avatar"] = base_avatar
    profile["username"] = base_username
    profile["avatar_url"] = base_avatar
    profile.setdefault("display_name", "")
    overrides = profile.get("virtual_ip_overrides")
    if not isinstance(overrides, dict):
        overrides = {}
    normalized = {}
    for key, value in overrides.items():
        if not isinstance(value, dict):
            continue
        normalized[key] = {
            "ip_display_username": (value.get("ip_display_username") or "").strip(),
            "ip_display_avatar": (value.get("ip_display_avatar") or "").strip(),
        }
    profile["virtual_ip_overrides"] = normalized
    return profile


def resolve_profile_payload(profile: dict, character_id: str = "") -> dict:
    base_username = profile.get("base_username", "")
    base_avatar = profile.get("base_avatar", "")
    override = {}
    if character_id:
        override = profile.get("virtual_ip_overrides", {}).get(character_id, {})
    ip_display_username = override.get("ip_display_username", "")
    ip_display_avatar = override.get("ip_display_avatar", "")
    return {
        "username": ip_display_username or base_username,
        "display_name": profile.get("display_name", ""),
        "avatar_url": ip_display_avatar or base_avatar,
        "base_username": base_username,
        "base_avatar": base_avatar,
        "ip_display_username": ip_display_username,
        "ip_display_avatar": ip_display_avatar,
    }


@router.get("/profile")
def get_profile(request: Request, user_id: str = "", character_id: str = ""):
    if not user_id:
        user_id = (request.cookies.get(LOGIN_COOKIE_NAME) or "").strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})
    user_info = load_user_data(user_id)
    character_id = (character_id or "").strip()
    profile = normalize_profile(user_info)
    save_user_data(user_id, user_info)
    payload = resolve_profile_payload(profile, character_id)
    return {
        "ok": True,
        "user_id": user_id,
        "profile": payload,
    }


@router.post("/profile")
def update_profile(payload: dict, request: Request):
    payload = payload or {}
    user_id = (request.cookies.get(LOGIN_COOKIE_NAME) or "").strip()
    if not user_id:
        return JSONResponse(status_code=401, content={"ok": False, "msg": "not_logged_in"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    username = (payload.get("username") or "").strip()
    display_name = payload.get("display_name")
    avatar_url = payload.get("avatar_url")
    if display_name is not None:
        display_name = (display_name or "").strip()
    if avatar_url is not None:
        avatar_url = (avatar_url or "").strip()

    if not username and display_name is None and avatar_url is None:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "profile_empty"})

    character_id = (payload.get("character_id") or "").strip()
    is_virtual_ip = bool(character_id)

    user_info = load_user_data(user_id)
    profile = normalize_profile(user_info)
    if username:
        profile["base_username"] = username
        profile["username"] = username
    if display_name is not None:
        profile["display_name"] = display_name
    if avatar_url is not None:
        profile["base_avatar"] = avatar_url
        profile["avatar_url"] = avatar_url

    if is_virtual_ip:
        overrides = profile.setdefault("virtual_ip_overrides", {})
        role_override = overrides.setdefault(character_id, {
            "ip_display_username": "",
            "ip_display_avatar": "",
        })
        if username:
            role_override["ip_display_username"] = username
        if avatar_url is not None:
            role_override["ip_display_avatar"] = avatar_url

    save_user_data(user_id, user_info)
    profile_data = resolve_profile_payload(profile, character_id)
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "user_id": user_id,
            "profile": profile_data,
        },
    )


@router.post("/avatar_upload")
def avatar_upload(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    character_id: str = Form(""),
):
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_image"})

    try:
        image = Image.open(file.file).convert("RGBA")
        image.thumbnail((512, 512))
    except Exception:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_image"})

    base_dir = os.path.dirname(os.path.dirname(__file__))
    avatar_dir = os.path.join(base_dir, "static", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    filename = f"{user_id}.png"
    path = os.path.join(avatar_dir, filename)
    image.save(path, format="PNG")

    avatar_url = f"/static/avatars/{filename}"
    user_info = load_user_data(user_id)
    profile = normalize_profile(user_info)
    profile["base_avatar"] = avatar_url
    profile["avatar_url"] = avatar_url
    character_id = (character_id or "").strip()
    if character_id:
        overrides = profile.setdefault("virtual_ip_overrides", {})
        role_override = overrides.setdefault(character_id, {
            "ip_display_username": "",
            "ip_display_avatar": "",
        })
        role_override["ip_display_avatar"] = avatar_url
    save_user_data(user_id, user_info)
    cache_bust = int(time.time())
    return JSONResponse(
        status_code=200,
        content={"ok": True, "avatar_url": f"{avatar_url}?t={cache_bust}"},
    )
