from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def intro_page():
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, "ai树洞计划.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@router.get("/page", response_class=HTMLResponse)
async def chat_page(request: Request):
    plan = request.query_params.get("plan", "free")

    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, "treehole.html")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{DEFAULT_PLAN}}", plan)
    return html
