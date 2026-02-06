import os
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from data_store import load_user_data, save_user_data
from chat_core import IP_PROMPT_MAP, build_character_history_key, stream_chat_with_deepseek
from core.auth_utils import is_valid_user_id

router = APIRouter()

@router.get("/greeting")
def greeting(user_id: str, request: Request):
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_info = load_user_data(user_id)
    save_user_data(user_id, user_info)

    if user_info.get("has_greeted"):
        return {"text": ""}

    text = "我在这里，你可以慢慢说。"

    user_info["has_greeted"] = True
    user_info.setdefault("history", []).append({
        "role": "assistant",
        "content": text
    })
    save_user_data(user_id, user_info)

    return {"text": text}

class ChatStreamRequest(BaseModel):
    user_id: str
    user_input: str
    character_id: str | None = None


@router.post("/chat_stream")
async def chat_stream(req: ChatStreamRequest, request: Request):
    user_id = req.user_id.strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_input = req.user_input.strip()
    character_id = (req.character_id or "").strip() or None
    if character_id and character_id not in IP_PROMPT_MAP:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_character_id"})

    user_info = load_user_data(user_id)
    save_user_data(user_id, user_info)
    if os.getenv("E2E_TEST_MODE") == "1":
        def e2e_stream():
            message = "你好。测试回复。"
            for ch in message:
                yield ch
                time.sleep(0.01)
        return StreamingResponse(e2e_stream(), media_type="text/plain")

    if not user_info.get("system_prompt"):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_system_prompt"})

    stream = stream_chat_with_deepseek(user_id, user_input, character_id=character_id)
    return StreamingResponse(stream, media_type="text/plain")


@router.get("/load_history")
def load_history(request: Request, user_id: str, character_id: str = ""):
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_info = load_user_data(user_id)
    save_user_data(user_id, user_info)
    character_id = (character_id or "").strip()
    if character_id:
        if character_id not in IP_PROMPT_MAP:
            return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_character_id"})
        history_key = build_character_history_key(user_id, character_id)
        history_map = user_info.get("character_histories", {})
        history = history_map.get(history_key, history_map.get(character_id, []))
    else:
        history = user_info.get("history", [])
    return {"ok": True, "history": history}
