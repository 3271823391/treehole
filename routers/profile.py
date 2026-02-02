import os
import time

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image

from core.auth_utils import verify_token_from_request
from data_store import load_user_data, save_user_data

router = APIRouter()


@router.get("/profile")
def get_profile(request: Request):
    user_id, error = verify_token_from_request(request)
    if error:
        return error

    user_info = load_user_data(user_id)
    profile = user_info.setdefault("profile", {})
    return {
        "ok": True,
        "user_id": user_id,
        "profile": {
            "username": profile.get("username", ""),
            "avatar_url": profile.get("avatar_url", ""),
        },
    }


@router.post("/profile")
def update_profile(request: Request, payload: dict):
    user_id, error = verify_token_from_request(request)
    if error:
        return error

    username = (payload or {}).get("username", "").strip()
    if not username:
        return JSONResponse(status_code=200, content={"ok": False, "msg": "username_required"})

    user_info = load_user_data(user_id)
    profile = user_info.setdefault("profile", {})
    profile["username"] = username
    save_user_data(user_id, user_info)
    return {"ok": True, "profile": {"username": username, "avatar_url": profile.get("avatar_url", "")}}


@router.post("/avatar_upload")
def avatar_upload(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    token_user_id, error = verify_token_from_request(request)
    if error:
        return error

    if token_user_id != user_id:
        return JSONResponse(status_code=401, content={"ok": False, "msg": "unauthorized"})

    if not file.content_type or not file.content_type.startswith("image/"):
        return JSONResponse(status_code=200, content={"ok": False, "msg": "invalid_image"})

    try:
        image = Image.open(file.file).convert("RGBA")
        image.thumbnail((512, 512))
    except Exception:
        return JSONResponse(status_code=200, content={"ok": False, "msg": "invalid_image"})

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
