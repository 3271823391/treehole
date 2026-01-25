from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from data_store import load_user_data, save_user_data
from data_store import load_user_data
from chat_core import stream_chat_with_deepseek

router = APIRouter()

@router.get("/greeting")
def greeting(user_id: str):
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
async def chat_stream(req: ChatStreamRequest):
    user_id = req.user_id.strip()
    user_input = req.user_input.strip()

    user_info = load_user_data(user_id)
    if not user_info.get("system_prompt"):
        raise HTTPException(status_code=400, detail="请先完成AI性格定制")

    stream = stream_chat_with_deepseek(user_id, user_input)
    return StreamingResponse(stream, media_type="text/plain")