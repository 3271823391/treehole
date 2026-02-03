import logging
import os

import httpx
from fastapi import APIRouter, Body, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response

from data_store import load_user_data, save_user_data

router = APIRouter()
logger = logging.getLogger(__name__)


def _truncate_body(content: str, limit: int = 500) -> str:
    """截断第三方响应体，避免日志过长。"""
    if not content:
        return ""
    if len(content) <= limit:
        return content
    return f"{content[:limit]}...<truncated>"


@router.post("/api/voice_clone/reference/upload")
async def upload_reference_audio(
    file: UploadFile = File(...),
    name: str = Form(...),
    describe: str = Form(""),
    user_id: str = Form(...)
):
    """代理 LipVoice 参考音频上传接口。"""
    sign = os.getenv("LIPVOICE_SIGN")
    if not sign:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "lipvoice_sign_missing"})

    base_url = os.getenv("LIPVOICE_BASE_URL", "https://openapi.lipvoice.cn")
    url = f"{base_url}/api/third/reference/upload"
    try:
        file_bytes = await file.read()
        if not file_bytes:
            return JSONResponse(status_code=400, content={"ok": False, "msg": "empty_file"})

        # 使用 httpx.AsyncClient，避免在 async 路由里阻塞事件循环。
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={"sign": sign},
                files={
                    "file": (
                        file.filename or "reference_audio",
                        file_bytes,
                        file.content_type or "application/octet-stream"
                    )
                },
                data={"name": name, "describe": describe or ""}
            )
    except httpx.RequestError as exc:
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

    user_info = load_user_data(user_id)
    user_info["voice_clone"] = {
        "audioId": audio_id
    }
    save_user_data(user_id, user_info)

    return {
        "ok": True,
        "data": {
            "audioId": audio_id,
            "name": name,
            "describe": describe or ""
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
    voice_clone_info = user_info.get("voice_clone") or {}
    audio_id = voice_clone_info.get("audioId")
    if not audio_id:
        logger.warning("LipVoice TTS missing audioId user_id=%s", user_id)
        return JSONResponse(status_code=400, content={"ok": False, "msg": "voice_not_initialized"})

    base_url = os.getenv("LIPVOICE_BASE_URL", "https://openapi.lipvoice.cn")
    tts_path = os.getenv("LIPVOICE_TTS_PATH", "/api/third/tts")
    audio_id_field = os.getenv("LIPVOICE_TTS_AUDIOID_FIELD", "audioId")
    text_field = os.getenv("LIPVOICE_TTS_TEXT_FIELD", "text")
    url = f"{base_url}{tts_path}"
    tts_payload = {text_field: text, audio_id_field: audio_id}
    # 记录第三方调用信息（不包含 sign），便于定位 502/默认音色问题。
    logger.info("LipVoice TTS request url=%s payload=%s", url, tts_payload)
    try:
        # 根据 LipVoice TTS 文档，必须携带 audioId 才能使用克隆音色，否则会回落到默认音色。
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={"sign": sign},
                json=tts_payload
            )
    except httpx.RequestError as exc:
        logger.warning(
            "LipVoice TTS request error url=%s payload=%s error=%s",
            url,
            tts_payload,
            exc
        )
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": str(exc)}
        )
    except Exception as exc:  # pragma: no cover - 兜底异常
        logger.exception(
            "LipVoice TTS unexpected error url=%s payload=%s",
            url,
            tts_payload
        )
        return JSONResponse(
            status_code=500,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": str(exc)}
        )

    content_type = response.headers.get("content-type", "")
    logger.info(
        "LipVoice TTS response status=%s content_type=%s",
        response.status_code,
        content_type or "unknown"
    )

    if response.status_code != 200:
        body_preview = _truncate_body(
            response.text
            if "text" in content_type or "json" in content_type
            else response.content[:500].decode(errors="replace")
        )
        logger.warning(
            "LipVoice TTS failed url=%s status=%s content_type=%s body_preview=%s",
            url,
            response.status_code,
            content_type or "unknown",
            body_preview
        )
        detail = {
            "status_code": response.status_code,
            "content_type": content_type or "unknown",
            "body_preview": body_preview
        }
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": detail}
        )

    if not content_type.startswith("audio/"):
        body_preview = _truncate_body(
            response.text
            if "text" in content_type or "json" in content_type
            else response.content[:500].decode(errors="replace")
        )
        logger.warning(
            "LipVoice TTS invalid content url=%s status=%s content_type=%s body_preview=%s",
            url,
            response.status_code,
            content_type or "unknown",
            body_preview
        )
        detail = {
            "status_code": response.status_code,
            "content_type": content_type or "unknown",
            "body_preview": body_preview
        }
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": detail}
        )

    return Response(
        content=response.content,
        media_type=content_type or "audio/mpeg"
    )
