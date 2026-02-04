import logging
import os
import time
import base64
import binascii
import json
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

import httpx
from fastapi import APIRouter, Body, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from data_store import load_user_data, save_user_data

router = APIRouter()
logger = logging.getLogger(__name__)
SAMPLE_WAV_BASE64 = (
    "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"
    "/PRF9tj3qfmr+839"
)


class LipVoiceTtsError(Exception):
    def __init__(self, detail: dict):
        self.detail = detail
        super().__init__(detail.get("reason") or "lipvoice_tts_failed")


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


def _decode_base64_audio(encoded: str) -> bytes:
    padded = encoded + ("=" * (-len(encoded) % 4))
    return base64.b64decode(padded)


def _build_upstream_detail(response: httpx.Response) -> dict:
    content_type = response.headers.get("content-type", "") or "unknown"
    if "text" in content_type or "json" in content_type:
        body_preview = _truncate_body(response.text)
    else:
        body_preview = _preview_binary(response.content)
    return {
        "status_code": response.status_code,
        "content_type": content_type,
        "body_preview": body_preview
    }


def _normalize_base64_text(value: str) -> str:
    cleaned = value.strip()
    if "base64," in cleaned:
        cleaned = cleaned.split("base64,", 1)[-1]
    return "".join(cleaned.split())


def _looks_like_base64(value: str) -> bool:
    cleaned = _normalize_base64_text(value)
    if len(cleaned) < 16:
        return False
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    return all(char in allowed for char in cleaned)


def _find_base64_candidate(payload: object) -> str | None:
    candidate_keys = {"audio", "audiobase64", "base64", "content", "voice", "file", "body", "data"}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(key, str) and key.lower() in candidate_keys and isinstance(value, str):
                if _looks_like_base64(value):
                    return value
            nested = _find_base64_candidate(value)
            if nested:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = _find_base64_candidate(item)
            if nested:
                return nested
    elif isinstance(payload, str):
        if _looks_like_base64(payload):
            return payload
    return None


def _extract_media_type(payload: object) -> str | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(key, str) and key.lower() in {
                "contenttype",
                "content_type",
                "mediatype",
                "media_type",
                "mimetype",
                "mime"
            }:
                if isinstance(value, str) and value:
                    return value
            nested = _extract_media_type(value)
            if nested:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = _extract_media_type(item)
            if nested:
                return nested
    return None


def _extract_audio_bytes_from_response(response: httpx.Response) -> tuple[bytes, str, str]:
    content_type = (response.headers.get("content-type", "") or "").lower()
    if content_type.startswith("audio/"):
        return response.content, content_type, "audio/raw"

    if "application/octet-stream" in content_type:
        media_type = _sniff_audio_mime(response.content)
        if media_type:
            return response.content, media_type, "audio/octet-sniffed"
        return response.content, "application/octet-stream", "audio/octet"

    if "json" in content_type:
        try:
            payload = response.json()
        except ValueError as exc:
            detail = {"stage": "fetch", "reason": "invalid_audio_payload", **_build_upstream_detail(response)}
            raise LipVoiceTtsError(detail) from exc

        base64_text = _find_base64_candidate(payload)
        if not base64_text:
            detail = {"stage": "fetch", "reason": "json_missing_base64", **_build_upstream_detail(response)}
            raise LipVoiceTtsError(detail)

        normalized = _normalize_base64_text(base64_text)
        try:
            audio_bytes = _decode_base64_audio(normalized)
        except (binascii.Error, ValueError) as exc:
            detail = {
                "stage": "fetch",
                "reason": "decode_error",
                **_build_upstream_detail(response),
                "error": str(exc)
            }
            raise LipVoiceTtsError(detail) from exc

        media_type = _extract_media_type(payload) or "audio/wav"
        return audio_bytes, media_type, "base64/json"

    if content_type.startswith("text/"):
        text_payload = response.content.decode("utf-8", errors="ignore")
        normalized = "".join(text_payload.split())
        try:
            audio_bytes = _decode_base64_audio(normalized)
        except (binascii.Error, ValueError) as exc:
            detail = {"stage": "fetch", "reason": "invalid_audio_payload", **_build_upstream_detail(response)}
            raise LipVoiceTtsError(detail) from exc
        return audio_bytes, "audio/wav", "base64/text"

    detail = {"stage": "fetch", "reason": "invalid_audio_payload", **_build_upstream_detail(response)}
    raise LipVoiceTtsError(detail)


def _sniff_audio_mime(content: bytes) -> str | None:
    if len(content) < 12:
        return None
    if content[:4] == b"RIFF" and content[8:12] == b"WAVE":
        return "audio/wav"
    if content[:3] == b"ID3":
        return "audio/mpeg"
    if content[:4] == b"OggS":
        return "audio/ogg"
    return None


def _append_sign_param(url: str, sign: str | None) -> str:
    if not sign:
        return url
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if query.get("sign"):
        return url
    query["sign"] = sign
    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))


_EMOTION_KEY_ALIASES = {
    "happy": "happy",
    "开心": "happy",
    "angry": "angry",
    "anger": "angry",
    "愤怒": "angry",
    "sad": "sad",
    "sadness": "sad",
    "悲伤": "sad",
    "fear": "fear",
    "恐惧": "fear",
    "disgust": "disgust",
    "厌恶": "disgust",
    "depressed": "depressed",
    "depression": "depressed",
    "忧郁": "depressed",
    "surprise": "surprise",
    "惊讶": "surprise",
    "calm": "calm",
    "平静": "calm",
    "quiet": "calm"
}


def normalize_emotion_ext(ext: dict | None) -> dict:
    if not isinstance(ext, dict):
        return {}
    normalized: dict[str, float] = {}
    for raw_key, raw_value in ext.items():
        if raw_value is None:
            continue
        key = _EMOTION_KEY_ALIASES.get(str(raw_key).strip().lower())
        if not key:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if value > 1 and value <= 100:
            value = value / 100
        value = max(0.0, min(1.0, value))
        if value <= 0:
            continue
        normalized[key] = value
    return normalized


async def lipvoice_create_task(
    text: str,
    audio_id: str,
    style: str | None = None,
    ext: dict | None = None,
    genre: str | None = None,
    speed: str | None = None
) -> tuple[str, int]:
    sign = os.getenv("LIPVOICE_SIGN")
    base_url = os.getenv("LIPVOICE_BASE_URL", "https://openapi.lipvoice.cn")
    url = f"{base_url}/api/third/tts/create"
    payload = {
        "content": text,
        "audioId": audio_id
    }
    payload["style"] = style or "2"
    if ext and isinstance(ext, dict) and len(ext) > 0:
        payload["ext"] = ext
    if genre:
        payload["genre"] = genre
    if speed:
        payload["speed"] = speed
    logger.info(
        "LipVoice TTS create request audioId=%s text_len=%s url=%s payload_keys=%s sign_present=%s",
        audio_id,
        len(text),
        url,
        list(payload.keys()),
        bool(sign)
    )
    logger.info(
        "LipVoice create ext=%s",
        json.dumps(payload.get("ext"), ensure_ascii=False)[:300]
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers={"sign": sign}, json=payload)
    except httpx.RequestError as exc:
        raise LipVoiceTtsError({"stage": "create", "reason": "request_error", "error": str(exc)}) from exc

    if response.status_code != 200:
        detail = {"stage": "create", **_build_upstream_detail(response)}
        logger.warning("LipVoice TTS create failed detail=%s", detail)
        raise LipVoiceTtsError(detail)

    try:
        payload_json = response.json()
    except ValueError as exc:
        detail = {"stage": "create", "reason": "invalid_json", **_build_upstream_detail(response)}
        logger.warning("LipVoice TTS create invalid json detail=%s", detail)
        raise LipVoiceTtsError(detail) from exc

    if payload_json.get("code") != 0:
        detail = {"stage": "create", "reason": "upstream_error", "payload": payload_json}
        logger.warning("LipVoice TTS create error detail=%s", detail)
        raise LipVoiceTtsError(detail)

    data = payload_json.get("data") or {}
    task_id = data.get("taskId")
    if not task_id:
        detail = {"stage": "create", "reason": "missing_task_id", "payload": payload_json}
        logger.warning("LipVoice TTS create missing task id detail=%s", detail)
        raise LipVoiceTtsError(detail)
    status = data.get("status", 1)
    return task_id, status


async def lipvoice_get_result(task_id: str) -> tuple[int | None, str | None]:
    sign = os.getenv("LIPVOICE_SIGN")
    base_url = os.getenv("LIPVOICE_BASE_URL", "https://openapi.lipvoice.cn")
    url = f"{base_url}/api/third/tts/result"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers={"sign": sign}, params={"taskId": task_id})
    except httpx.RequestError as exc:
        raise LipVoiceTtsError({"stage": "result", "reason": "request_error", "error": str(exc)}) from exc

    if response.status_code != 200:
        detail = {"stage": "result", **_build_upstream_detail(response)}
        logger.warning("LipVoice TTS result failed detail=%s", detail)
        raise LipVoiceTtsError(detail)

    try:
        payload_json = response.json()
    except ValueError as exc:
        detail = {"stage": "result", "reason": "invalid_json", **_build_upstream_detail(response)}
        logger.warning("LipVoice TTS result invalid json detail=%s", detail)
        raise LipVoiceTtsError(detail) from exc

    if payload_json.get("code") != 0:
        detail = {"stage": "result", "reason": "upstream_error", "payload": payload_json}
        logger.warning("LipVoice TTS result upstream error detail=%s", detail)
        raise LipVoiceTtsError(detail)

    data = payload_json.get("data") or {}
    status = data.get("status")
    voice_url = data.get("voiceUrl")
    logger.info("LipVoice TTS result status=%s voice_url_present=%s", status, bool(voice_url))
    return status, voice_url


async def lipvoice_fetch_audio(voice_url: str) -> tuple[bytes, str]:
    sign = os.getenv("LIPVOICE_SIGN")
    signed_url = _append_sign_param(voice_url, sign)
    logger.info(
        "LipVoice TTS fetch audio url=%s signed_url=%s sign_present=%s",
        voice_url,
        signed_url,
        bool(sign)
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(signed_url, headers={"sign": sign})
    except httpx.RequestError as exc:
        raise LipVoiceTtsError({"stage": "fetch", "reason": "request_error", "error": str(exc)}) from exc

    if response.status_code != 200:
        detail = {"stage": "fetch", **_build_upstream_detail(response)}
        logger.warning("LipVoice TTS fetch invalid audio detail=%s", detail)
        raise LipVoiceTtsError(detail)

    try:
        audio_bytes, media_type, mode = _extract_audio_bytes_from_response(response)
    except LipVoiceTtsError as exc:
        detail = exc.detail
        logger.warning("LipVoice TTS fetch invalid audio detail=%s", detail)
        raise
    except Exception as exc:  # pragma: no cover - 兜底异常
        detail = {
            "stage": "fetch",
            "reason": "invalid_audio_payload",
            **_build_upstream_detail(response),
            "error": str(exc)
        }
        logger.warning("LipVoice TTS fetch invalid audio detail=%s", detail)
        raise LipVoiceTtsError(detail) from exc

    logger.info(
        "LipVoice TTS fetch success mode=%s media_type=%s len=%s upstream_content_type=%s",
        mode,
        media_type,
        len(audio_bytes),
        response.headers.get("content-type", "") or "unknown"
    )
    return audio_bytes, media_type


_MOCK_TTS_TASKS: dict[str, float] = {}


@router.post("/api/third/tts/create")
async def mock_lipvoice_tts_create(payload: dict = Body(...), request: Request = None):
    if os.getenv("LIPVOICE_MOCK") != "1":
        return JSONResponse(status_code=404, content={"ok": False, "msg": "mock_disabled"})

    content = (payload.get("content") or "").strip()
    audio_id = (payload.get("audioId") or "").strip()
    style = payload.get("style")
    if not content or not audio_id:
        return JSONResponse(status_code=400, content={"code": 1, "msg": "invalid_payload"})

    task_id = f"mock-{int(time.time() * 1000)}"
    _MOCK_TTS_TASKS[task_id] = time.monotonic()
    logger.info(
        "Mock LipVoice create audioId=%s style=%s taskId=%s",
        audio_id,
        style,
        task_id
    )
    return {"code": 0, "data": {"taskId": task_id}}


@router.get("/api/third/tts/result")
async def mock_lipvoice_tts_result(taskId: str, request: Request = None):
    if os.getenv("LIPVOICE_MOCK") != "1":
        return JSONResponse(status_code=404, content={"ok": False, "msg": "mock_disabled"})

    start_time = _MOCK_TTS_TASKS.get(taskId)
    if not start_time:
        return {"code": 0, "data": {"status": 3}}

    elapsed = time.monotonic() - start_time
    if elapsed < 2:
        return {"code": 0, "data": {"status": 1}}

    base_url = os.getenv("LIPVOICE_BASE_URL") or str(request.base_url).rstrip("/")
    voice_url = f"{base_url}/api/third/tts/voice/{taskId}"
    return {"code": 0, "data": {"status": 2, "voiceUrl": voice_url}}


@router.get("/api/third/tts/voice/{task_id}")
async def mock_lipvoice_tts_voice(task_id: str, request: Request):
    if os.getenv("LIPVOICE_MOCK") != "1":
        return JSONResponse(status_code=404, content={"ok": False, "msg": "mock_disabled"})

    sign = request.headers.get("sign") or request.query_params.get("sign")
    if not sign:
        return JSONResponse(status_code=401, content={"ok": False, "msg": "missing_sign"})

    audio_bytes = _decode_base64_audio(SAMPLE_WAV_BASE64) * 4
    return Response(content=audio_bytes, media_type="audio/wav")


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
    """兼容旧版同步接口，返回任务信息以避免阻塞。"""
    user_id = (payload.get("user_id") or "").strip()
    text = (payload.get("text") or "").strip()
    raw_ext = payload.get("ext") or {}
    if not isinstance(raw_ext, dict):
        raw_ext = {}
    ext = normalize_emotion_ext(raw_ext)
    if not user_id or not text:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_payload"})

    user_info = load_user_data(user_id)
    voice_clone_info = user_info.get("voice_clone") or {}
    audio_id = voice_clone_info.get("audioId")
    if not audio_id:
        logger.warning("LipVoice TTS missing audioId user_id=%s", user_id)
        return JSONResponse(status_code=400, content={"ok": False, "msg": "voice_not_initialized"})

    sign = os.getenv("LIPVOICE_SIGN")
    if not sign:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "lipvoice_sign_missing"})

    try:
        logger.info("LipVoice TTS legacy create user_id=%s audioId=%s", user_id, audio_id)
        task_id, status = await lipvoice_create_task(text=text, audio_id=audio_id, style="2", ext=ext or None)
        logger.info("LipVoice TTS legacy created taskId=%s user_id=%s audioId=%s", task_id, user_id, audio_id)
    except LipVoiceTtsError as exc:
        detail = exc.detail
        logger.warning("LipVoice TTS failed detail=%s", detail)
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": detail}
        )
    except Exception as exc:  # pragma: no cover - 兜底异常
        logger.exception("LipVoice TTS unexpected error")
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_failed", "detail": {"reason": str(exc)}}
        )

    return {"ok": True, "taskId": task_id, "status": status}


@router.post("/api/voice_clone/tts/create")
async def voice_clone_tts_create(payload: dict = Body(...)):
    user_id = (payload.get("user_id") or "").strip()
    text = (payload.get("text") or "").strip()
    style = payload.get("style")
    raw_ext = payload.get("ext") or {}
    if not isinstance(raw_ext, dict):
        raw_ext = {}
    ext = normalize_emotion_ext(raw_ext)
    genre = payload.get("genre")
    speed = payload.get("speed")
    if not user_id or not text:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_payload"})

    user_info = load_user_data(user_id)
    voice_clone_info = user_info.get("voice_clone") or {}
    audio_id = voice_clone_info.get("audioId")
    if not audio_id:
        logger.warning("LipVoice TTS create missing audioId user_id=%s", user_id)
        return JSONResponse(status_code=400, content={"ok": False, "msg": "voice_not_initialized"})

    sign = os.getenv("LIPVOICE_SIGN")
    if not sign:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "lipvoice_sign_missing"})

    try:
        task_id, status = await lipvoice_create_task(
            text=text,
            audio_id=audio_id,
            style=style,
            ext=ext or None,
            genre=genre,
            speed=speed
        )
    except LipVoiceTtsError as exc:
        detail = exc.detail
        logger.warning("LipVoice TTS create failed detail=%s", detail)
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_create_failed", "detail": detail}
        )

    user_info.setdefault("tts_tasks", {})[task_id] = {
        "created_at": time.time(),
        "text_len": len(text)
    }
    save_user_data(user_id, user_info)

    return {"ok": True, "taskId": task_id, "status": status}


@router.get("/api/voice_clone/tts/result")
async def voice_clone_tts_result(user_id: str, taskId: str):
    if not user_id or not taskId:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_payload"})

    sign = os.getenv("LIPVOICE_SIGN")
    if not sign:
        return JSONResponse(status_code=500, content={"ok": False, "msg": "lipvoice_sign_missing"})

    try:
        status, voice_url = await lipvoice_get_result(task_id=taskId)
    except LipVoiceTtsError as exc:
        detail = exc.detail
        logger.warning("LipVoice TTS result failed detail=%s", detail)
        return {"ok": False, "msg": "lipvoice_tts_result_failed", "detail": detail}
    return {"ok": True, "status": status, "voiceUrl": voice_url or ""}


@router.get("/api/voice_clone/tts/audio")
async def voice_clone_tts_audio(voiceUrl: str):
    if not voiceUrl:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_payload"})

    try:
        audio_bytes, media_type = await lipvoice_fetch_audio(voice_url=voiceUrl)
    except LipVoiceTtsError as exc:
        detail = exc.detail
        logger.warning("LipVoice TTS audio failed detail=%s", detail)
        return JSONResponse(
            status_code=502,
            content={"ok": False, "msg": "lipvoice_tts_audio_failed", "detail": detail}
        )

    return Response(content=audio_bytes, media_type=media_type)


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
