import os

import requests
from fastapi import APIRouter, Body, File, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

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


@router.post("/api/voice_clone/tts")
async def voice_clone_tts(payload: dict = Body(...)):
    """代理 LipVoice TTS 接口，使用 audioId 输出克隆音色。"""
    sign = os.getenv("LIPVOICE_SIGN")
    if not sign:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "lipvoice_sign_missing"})

    user_id = (payload.get("user_id") or "").strip()
    text = (payload.get("text") or "").strip()
    if not user_id or not text:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_payload"})

    user_info = load_user_data(user_id)
    audio_id = (user_info.get("voice") or {}).get("audioId")
    if not audio_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "voice_not_initialized"})

    base_url = os.getenv("LIPVOICE_BASE_URL", "https://openapi.lipvoice.cn")
    try:
        # 根据 LipVoice TTS 文档，必须携带 audioId 才能使用克隆音色，否则会回落到默认音色。
        response = requests.post(
            f"{base_url}/api/third/tts",
            headers={"sign": sign},
            json={"text": text, "audioId": audio_id},
            stream=True,
            timeout=30
        )
    except requests.RequestException as exc:
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": str(exc)}
        )
    except Exception as exc:  # pragma: no cover - 兜底异常
        return JSONResponse(
            status_code=500,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": str(exc)}
        )

    if response.status_code != 200:
        detail = None
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": detail}
        )

    content_type = response.headers.get("content-type", "audio/mpeg")
    if "application/json" in content_type:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": detail}
        )

    def iter_audio():
        try:
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        finally:
            response.close()

    return StreamingResponse(iter_audio(), media_type=content_type)
