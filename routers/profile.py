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
    profile["display_name"] = (profile.get("display_name") or "").strip()
    profile["avatar_url"] = (profile.get("avatar_url") or "").strip()
    # 清理与昵称耦合的历史字段
    for key in ["username", "base_username", "base_avatar", "virtual_ip_overrides"]:
        profile.pop(key, None)
    return profile


@router.get("/profile")
def get_profile(request: Request):
    user_id = (request.cookies.get(LOGIN_COOKIE_NAME) or "").strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_info = load_user_data(user_id)
    profile = normalize_profile(user_info)
    save_user_data(user_id, user_info)
    return {
        "ok": True,
        "profile": {
            "user_id": user_id,
            "display_name": profile.get("display_name", ""),
            "avatar_url": profile.get("avatar_url", ""),
        },
    }


@router.post("/profile")
def update_profile(payload: dict, request: Request):
    payload = payload or {}
    user_id = (request.cookies.get(LOGIN_COOKIE_NAME) or "").strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    display_name = payload.get("display_name")
    avatar_url = payload.get("avatar_url")
    if display_name is not None:
        display_name = (display_name or "").strip()
    if avatar_url is not None:
        avatar_url = (avatar_url or "").strip()

    if display_name is None and avatar_url is None:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "profile_empty"})

    user_info = load_user_data(user_id)
    profile = normalize_profile(user_info)
    if display_name is not None:
        profile["display_name"] = display_name
    if avatar_url is not None:
        profile["avatar_url"] = avatar_url

    save_user_data(user_id, user_info)
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "profile": {
                "display_name": profile.get("display_name", ""),
                "avatar_url": profile.get("avatar_url", ""),
            },
        },
    )


@router.post("/avatar_upload")
def avatar_upload(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(""),
    character_id: str = Form(""),
):
    user_id = (user_id or request.cookies.get(LOGIN_COOKIE_NAME) or "").strip()
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
    profile["avatar_url"] = avatar_url
    save_user_data(user_id, user_info)
    cache_bust = int(time.time())
    return JSONResponse(
        status_code=200,
        content={"ok": True, "avatar_url": f"{avatar_url}?t={cache_bust}"},
    )
