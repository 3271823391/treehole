from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from fastapi.responses import JSONResponse

from services.ocr_service import extract_texts_from_uploadfiles
from data_store import load_user_data, save_user_data
from chat_core import extract_personality_for_clone, generate_system_prompt_clone

router = APIRouter()

@router.post("/clone_from_image")
async def clone_from_image(
    user_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    images = [await f.read() for f in files]
    texts = extract_texts_from_uploadfiles(images)

    if len(texts) < 5:
        return JSONResponse({
            "success": False,
            "message": "识别文字过少，请上传清晰的聊天截图"
        })

    clone_text = "\n".join(texts)
    personality = extract_personality_for_clone(clone_text)
    system_prompt = generate_system_prompt_clone(personality)

    user_info = load_user_data(user_id)
    user_info["system_prompt"] = system_prompt
    user_info.setdefault("history", [])
    save_user_data(user_id, user_info)

    return JSONResponse({
        "success": True,
        "message": "截图语气克隆成功",
        "preview_text": clone_text[:300]
    })