from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os
import uuid
from data_store import load_user_data, save_user_data
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
async def linyu_page():
    user_id = "web_user"
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "linyu"   # ★ 必须
    user_info["history"] = []
    user_info["has_greeted"] = False

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/林屿哥哥.html", encoding="utf-8").read())



@router.get("/ip/suwan", response_class=HTMLResponse)
async def suwan_page():
    user_id = "web_user"
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "suwan"
    user_info["history"] = []
    user_info["has_greeted"] = False

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/苏晚姐姐.html", encoding="utf-8").read())


@router.get("/ip/xiaxingmian", response_class=HTMLResponse)
async def xiaxingmian_page():
    user_id = "web_user"   # ★ 固定一个
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "xiaxingmian"
    user_info["history"] = []
    user_info["has_greeted"] = False

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/病娇校花.html", encoding="utf-8").read())

@router.get("/ip/jiangche", response_class=HTMLResponse)
async def jiangche_page():
    user_id = "web_user"   # ★ 固定一个
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "jiangche"
    user_info["history"] = []
    user_info["has_greeted"] = False

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/白月光江澈.html", encoding="utf-8").read())

@router.get("/ip/luchengyu", response_class=HTMLResponse)
async def luchengyu_page():
    user_id = "web_user"   # ★ 固定一个
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "luchengyu"
    user_info["history"] = []
    user_info["has_greeted"] = False

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/学长.html", encoding="utf-8").read())
