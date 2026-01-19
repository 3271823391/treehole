from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel
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


class CloneFromTextRequest(BaseModel):
    user_id: str
    texts: list[str]


@router.post("/clone_from_text")
async def clone_from_text(req: CloneFromTextRequest):
    # ① 文本清洗
    texts = [t.strip() for t in req.texts if t and t.strip()]

    if len(texts) < 5:
        return {
            "success": False,
            "message": "文本太少，无法克隆"
        }

    # ② 合并文本
    merged_text = "\n".join(texts)

    # ③ 下面这两行，直接复用你原来的逻辑
    personality = extract_personality_for_clone(merged_text)
    system_prompt = generate_system_prompt_clone(personality)

    # ④ 存用户数据（你原来怎么存，现在一模一样）
    user_info = load_user_data(req.user_id)
    user_info["system_prompt"] = system_prompt
    user_info.setdefault("history", [])
    save_user_data(req.user_id, user_info)

    return {
        "success": True,
        "message": "克隆成功",
        "preview_text": merged_text[:300]
    }
