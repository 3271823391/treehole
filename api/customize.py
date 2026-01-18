from fastapi import APIRouter
from fastapi.responses import JSONResponse
import time

from pydantic import BaseModel
from config import customize_progress
from data_store import load_user_data, save_user_data
from chat_core import (
    extract_personality_for_create,
    extract_personality_for_clone,
    generate_system_prompt_create,
    generate_system_prompt_clone
)

router = APIRouter()

class CustomizeRequest(BaseModel):
    user_id: str
    mode: str
    data: str

@router.post("/customize")
async def customize_character(req: CustomizeRequest):
    user_id = req.user_id.strip()
    mode = req.mode.strip()
    data = req.data.strip()

    user_info = load_user_data(user_id)

    try:
        customize_progress[user_id] = 10
        time.sleep(0.2)
        customize_progress[user_id] = 30

        if mode == "clone":
            personality = extract_personality_for_clone(data)
            system_prompt = generate_system_prompt_clone(personality)
        else:
            personality = extract_personality_for_create(data)
            system_prompt = generate_system_prompt_create(personality)

        customize_progress[user_id] = 100

        user_info["system_prompt"] = system_prompt
        user_info.setdefault("history", [])
        save_user_data(user_id, user_info)

        return JSONResponse({"success": True, "message": "定制成功"})

    except Exception as e:
        customize_progress[user_id] = -1
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)