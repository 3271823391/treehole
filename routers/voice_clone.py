import os

import requests
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from data_store import load_user_data, save_user_data

router = APIRouter()


@router.post("/api/voice_clone/reference/upload")
async def upload_reference_audio(
    file: UploadFile = File(...),
    name: str = Form(...),
    describe: str = Form(""),
    voice_profile_id: str = Form(...),
    user_id: str = Form("")
):
    """代理 LipVoice 参考音频上传接口。"""
    sign = os.getenv("LIPVOICE_SIGN")
    if not sign:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "lipvoice_sign_missing"})

    base_url = os.getenv("LIPVOICE_BASE_URL", "https://openapi.lipvoice.cn")
    try:
        file_bytes = await file.read()
        if not file_bytes:
            return JSONResponse(status_code=400, content={"ok": False, "msg": "empty_file"})

        # TODO: 统一上传异常处理，避免将第三方错误泄漏给前端
        response = requests.post(
            f"{base_url}/api/third/reference/upload",
            headers={"sign": sign},
            files={
                "file": (
                    file.filename or "reference_audio",
                    file_bytes,
                    file.content_type or "application/octet-stream"
                )
            },
            data={"name": name, "describe": describe or ""},
            timeout=30
        )
    except requests.RequestException as exc:
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_upload_failed", "detail": str(exc)}
        )
    except Exception as exc:  # pragma: no cover - 兜底异常
        return JSONResponse(
            status_code=500,
            content={"ok": False, "msg": "lipvoice_upload_failed", "detail": str(exc)}
        )

    try:
        payload = response.json()
    except ValueError:
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_upload_failed", "detail": "invalid_json"}
        )

    if response.status_code != 200 or payload.get("code") != 0:
        detail = payload.get("msg") or payload.get("message") or payload
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_upload_failed", "detail": detail}
        )

    audio_id = payload.get("data", {}).get("audioId")
    if not audio_id:
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_upload_failed", "detail": "missing_audio_id"}
        )

    if user_id:
        user_info = load_user_data(user_id)
        user_info["voice"] = {
            "profile_id": voice_profile_id,
            "audioId": audio_id
        }
        save_user_data(user_id, user_info)

    return {
        "ok": True,
        "data": {
            "audioId": audio_id,
            "name": name,
            "describe": describe or "",
            "voice_profile_id": voice_profile_id
        }
    }
