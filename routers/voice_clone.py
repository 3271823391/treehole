import logging
import os
import base64

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


def _preview_binary(content: bytes, limit: int = 64) -> str:
    """二进制内容预览，避免打印大段音频数据。"""
    if not content:
        return ""
    snippet = content[:limit]
    return base64.b64encode(snippet).decode("ascii")


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
    confirm_info = load_user_data(user_id)
    confirm_audio_id = (confirm_info.get("voice_clone") or {}).get("audioId")
    logger.info(
        "LipVoice upload saved user_id=%s audioId=%s confirmed_audioId=%s",
        user_id,
        audio_id,
        confirm_audio_id
    )

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
    if os.getenv("TTS_FORCE_SAMPLE") == "1":
        sample_path = os.path.join("tests", "assets", "sample.wav")
        if not os.path.exists(sample_path):
            return JSONResponse(
                status_code=500,
                content={"ok": False, "msg": "sample_audio_missing"}
            )
        with open(sample_path, "rb") as f:
            logger.info("TTS_FORCE_SAMPLE enabled, serving sample wav.")
            return Response(content=f.read(), media_type="audio/wav")

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
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_audio_id"})

    base_url = os.getenv("LIPVOICE_BASE_URL", "https://openapi.lipvoice.cn")
    tts_path = os.getenv("LIPVOICE_TTS_PATH", "/api/third/tts")
    audio_id_field = os.getenv("LIPVOICE_TTS_AUDIOID_FIELD", "audioId")
    text_field = os.getenv("LIPVOICE_TTS_TEXT_FIELD", "text")
    url = f"{base_url}{tts_path}"
    tts_payload = {text_field: text, audio_id_field: audio_id}
    # 记录第三方调用信息（不包含 sign），便于定位 502/默认音色问题。
    logger.info(
        "LipVoice TTS request user_id=%s text_len=%s audioId=%s url=%s method=POST sign_present=%s payload_keys=%s",
        user_id,
        len(text),
        audio_id,
        url,
        bool(sign),
        list(tts_payload.keys())
    )
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
    body_preview = ""
    if "text" in content_type or "json" in content_type:
        body_preview = _truncate_body(response.text)
    else:
        body_preview = _preview_binary(response.content)
    logger.info(
        "LipVoice TTS response status=%s content_type=%s body_preview=%s",
        response.status_code,
        content_type or "unknown",
        body_preview
    )

    if response.status_code != 200:
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

    logger.info(
        "LipVoice TTS proxy success status=%s content_type=%s bytes=%s",
        response.status_code,
        content_type or "audio/mpeg",
        len(response.content)
    )
    return Response(content=response.content, media_type=content_type or "audio/mpeg")


@router.get("/api/voice_clone/debug_get_audio_id")
async def debug_get_audio_id(user_id: str):
    if os.getenv("DEBUG") != "1":
        return JSONResponse(status_code=404, content={"ok": False, "msg": "debug_disabled"})
    user_info = load_user_data(user_id)
    voice_clone_info = user_info.get("voice_clone") or {}
    audio_id = voice_clone_info.get("audioId")
    return {
        "ok": True,
        "audioId": audio_id,
        "has_voice_clone": bool(voice_clone_info)
    }
