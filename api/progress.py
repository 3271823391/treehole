from fastapi import APIRouter
from fastapi.responses import JSONResponse
from config import customize_progress

router = APIRouter()

@router.get("/set_progress")
async def set_progress(user_id: str, progress: int):
    customize_progress[user_id] = progress
    return JSONResponse({"success": True})

@router.get("/get_customize_progress")
async def get_customize_progress(user_id: str):
    return JSONResponse({
        "progress": customize_progress.get(user_id, 0)
    })