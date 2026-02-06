from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os
from data_store import load_user_data, save_user_data
from core.auth_utils import is_valid_user_id, make_user_id
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

@router.get("/二级页面2第六版.html", response_class=HTMLResponse)
async def evolution_plus_page():
    return render_html("二级页面2第六版.html")

@router.get("/page", response_class=HTMLResponse)
async def chat_page(request: Request):
    plan = request.query_params.get("plan", "plus")

    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, "treehole.html")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{DEFAULT_PLAN}}", plan)
    return html


@router.get("/treehole_plus", response_class=HTMLResponse)
async def treehole_plus_page():
    return render_html("treehole_plus.html")

@router.get("/treehole_pro", response_class=HTMLResponse)
async def treehole_pro_page():
    return render_html("treehole_pro.html")

def render_html(filename: str):
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, filename)
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

def resolve_ip_user_id(request: Request) -> str:
    user_id = request.query_params.get("user_id", "")
    if is_valid_user_id(user_id):
        return user_id
    return make_user_id("web_user")


@router.get("/ip/linyu", response_class=HTMLResponse)
async def linyu_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "linyu"   # ★ 必须

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/林屿哥哥.html", encoding="utf-8").read())



@router.get("/ip/suwan", response_class=HTMLResponse)
async def suwan_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "suwan"

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/苏晚姐姐.html", encoding="utf-8").read())


@router.get("/ip/xiaxingmian", response_class=HTMLResponse)
async def xiaxingmian_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "xiaxingmian"

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/病娇校花.html", encoding="utf-8").read())

@router.get("/ip/jiangche", response_class=HTMLResponse)
async def jiangche_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "jiangche"

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/白月光江澈.html", encoding="utf-8").read())

@router.get("/ip/luchengyu", response_class=HTMLResponse)
async def luchengyu_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "luchengyu"

    save_user_data(user_id, user_info)

    return HTMLResponse(open("routers/学长.html", encoding="utf-8").read())
