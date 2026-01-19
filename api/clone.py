from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from data_store import load_user_data, save_user_data
from chat_core import extract_personality_for_clone, generate_system_prompt_clone

router = APIRouter()

# =========================
# ❌ 图片克隆：Render 禁用
# =========================
@router.post("/clone_from_image")
async def clone_from_image(
    user_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": "当前服务器不支持图片OCR，请使用文本克隆接口 /clone_from_text"
        }
    )


# =========================
# ✅ 文本克隆：主力接口
# =========================
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

    # ③ 提取人格 & 生成 system prompt
    personality = extract_personality_for_clone(merged_text)
    system_prompt = generate_system_prompt_clone(personality)

    # ④ 存用户数据
    user_info = load_user_data(req.user_id)
    user_info["system_prompt"] = system_prompt
    user_info.setdefault("history", [])
    save_user_data(req.user_id, user_info)

    return {
        "success": True,
        "message": "克隆成功",
        "preview_text": merged_text[:300]
    }
