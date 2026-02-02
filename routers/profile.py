import os
import time

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image

from core.auth_utils import is_valid_user_id
from data_store import load_user_data, save_user_data

router = APIRouter()


@router.get("/profile")
def get_profile(user_id: str = ""):
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})
    user_info = load_user_data(user_id)
    save_user_data(user_id, user_info)
    profile = user_info.setdefault("profile", {})
    return {
        "ok": True,
        "user_id": user_id,
        "profile": {
            "username": profile.get("username", ""),
            "display_name": profile.get("display_name", ""),
            "avatar_url": profile.get("avatar_url", ""),
        },
    }


@router.post("/profile")
def update_profile(payload: dict):
    payload = payload or {}
    user_id = (payload.get("user_id") or "").strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
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

    user_info = load_user_data(user_id)
    profile = user_info.setdefault("profile", {})
    if username:
        profile["username"] = username
    if display_name is not None:
        profile["display_name"] = display_name
    if avatar_url is not None:
        profile["avatar_url"] = avatar_url
    save_user_data(user_id, user_info)
    return {
        "ok": True,
        "profile": {
            "username": profile.get("username", ""),
            "display_name": profile.get("display_name", ""),
            "avatar_url": profile.get("avatar_url", ""),
        },
    }


@router.post("/avatar_upload")
def avatar_upload(
    file: UploadFile = File(...),
    user_id: str = Form(...),
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
    profile = user_info.setdefault("profile", {})
    profile["avatar_url"] = avatar_url
    save_user_data(user_id, user_info)
    cache_bust = int(time.time())
    return JSONResponse(
        status_code=200,
        content={"ok": True, "avatar_url": f"{avatar_url}?t={cache_bust}"},
    )
