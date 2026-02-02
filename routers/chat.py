from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from data_store import load_user_data, save_user_data
from chat_core import stream_chat_with_deepseek
from core.auth_utils import verify_token_from_request

router = APIRouter()

@router.get("/greeting")
def greeting(user_id: str, request: Request):
    token_user_id, error = verify_token_from_request(request)
    if error:
        return error
    if token_user_id != user_id:
        return JSONResponse(status_code=401, content={"ok": False, "msg": "unauthorized"})

    user_info = load_user_data(user_id)

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


@router.post("/chat_stream")
async def chat_stream(req: ChatStreamRequest, request: Request):
    token_user_id, error = verify_token_from_request(request)
    if error:
        return error

    user_id = req.user_id.strip()
    if token_user_id != user_id:
        return JSONResponse(status_code=401, content={"ok": False, "msg": "unauthorized"})

    user_input = req.user_input.strip()

    user_info = load_user_data(user_id)
    if not user_info.get("system_prompt"):
        raise HTTPException(status_code=400, detail="请先完成AI性格定制")

    stream = stream_chat_with_deepseek(user_id, user_input)
    return StreamingResponse(stream, media_type="text/plain")


@router.get("/load_history")
def load_history(request: Request, user_id: str):
    token_user_id, error = verify_token_from_request(request)
    if error:
        return error
    if token_user_id != user_id:
        return JSONResponse(status_code=401, content={"ok": False, "msg": "unauthorized"})

    user_info = load_user_data(user_id)
    return {"ok": True, "history": user_info.get("history", [])}
