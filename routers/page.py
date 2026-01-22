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

@router.get("/ip", response_class=HTMLResponse)
async def ip_page():
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, "虚拟ip.html")

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

def render_html(filename: str):
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, filename)
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@router.get("/ip/linyu", response_class=HTMLResponse)
async def ip_linyu():
    return render_html("林屿哥哥.html")

@router.get("/ip/suwan", response_class=HTMLResponse)
async def ip_suwan():
    return render_html("苏晚姐姐.html")

@router.get("/ip/xiaxingmian", response_class=HTMLResponse)
async def ip_xiaxingmian():
    return render_html("病娇校花.html")

@router.get("/ip/jiangche", response_class=HTMLResponse)
async def ip_jiangche():
    return render_html("白月光江澈.html")

@router.get("/ip/luchengyu", response_class=HTMLResponse)
async def ip_luchengyu():
    return render_html("学长.html")
