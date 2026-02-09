from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
import os
from data_store import load_user_data, save_user_data
from core.auth_utils import is_valid_user_id, make_user_id
router = APIRouter()

LOGIN_COOKIE_NAME = "auth_token"


def _is_logged_in(request: Request) -> bool:
    return request.cookies.get(LOGIN_COOKIE_NAME) == "true"


def _render_html_file(filename: str) -> str:
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, filename)
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()



def _with_admin_logger(html: str) -> str:
    script_tag = '<script src="/static/admin_console_logger.js"></script>'
    if script_tag in html:
        return html
    return html.replace("</body>", f"    {script_tag}\n</body>")


def _with_admin_link(html: str) -> str:
    show_link = os.getenv("SHOW_ADMIN_LINK", "1") == "1"
    return html.replace("{{ADMIN_CONSOLE_LINK}}", '<a href="/admin/console" class="admin-console-link">🛠</a>' if show_link else "")

@router.get("/", response_class=HTMLResponse)
async def intro_page(request: Request):
    if _is_logged_in(request):
        return RedirectResponse(url="/ai树洞计划.html", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _is_logged_in(request):
        return RedirectResponse(url="/ai树洞计划.html", status_code=302)
    return HTMLResponse(_render_html_file("login.html"))




@router.get("/register")
async def register_page(request: Request):
    if _is_logged_in(request):
        return RedirectResponse(url="/ai树洞计划.html", status_code=302)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    return FileResponse(os.path.join(base_dir, "static", "register.html"))
@router.post("/login")
async def login_action(request: Request):
    payload = await request.json()
    user = str(payload.get("user", "")).strip()
    password = str(payload.get("pass", ""))
    remember = bool(payload.get("remember", False))

    if not user:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "请输入登录账号"})
    if len(password) < 6:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "密码长度至少为6个字符"})

    response = JSONResponse(status_code=200, content={"ok": True})
    max_age = 7 * 24 * 60 * 60 if remember else None
    response.set_cookie(
        key=LOGIN_COOKIE_NAME,
        value="true",
        httponly=True,
        path="/",
        max_age=max_age,
        samesite="lax",
    )
    return response


@router.get("/logout")
async def logout_action():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(LOGIN_COOKIE_NAME, path="/")
    return response


@router.get("/ai树洞计划.html", response_class=HTMLResponse)
async def ai_treehole_page(request: Request):
    if not _is_logged_in(request):
        return RedirectResponse(url="/login", status_code=302)
    html = _render_html_file("ai树洞计划.html")
    return HTMLResponse(_with_admin_logger(_with_admin_link(html)))

@router.get("/ip", response_class=HTMLResponse)
async def ip_page():
    base_dir = os.path.dirname(__file__)
    html_path = os.path.join(base_dir, "虚拟ip.html")

    with open(html_path, "r", encoding="utf-8") as f:
        return _with_admin_logger(f.read())

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
    return _with_admin_logger(html)


@router.get("/treehole_plus", response_class=HTMLResponse)
async def treehole_plus_page():
    return render_html("treehole_plus.html")

@router.get("/treehole_pro", response_class=HTMLResponse)
async def treehole_pro_page():
    return render_html("treehole_pro.html")

def render_html(filename: str):
    return _with_admin_logger(_render_html_file(filename))

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

    return HTMLResponse(_with_admin_logger(open("routers/林屿哥哥.html", encoding="utf-8").read()))



@router.get("/ip/suwan", response_class=HTMLResponse)
async def suwan_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "suwan"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/苏晚姐姐.html", encoding="utf-8").read()))


@router.get("/ip/xiaxingmian", response_class=HTMLResponse)
async def xiaxingmian_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "xiaxingmian"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/病娇校花.html", encoding="utf-8").read()))

@router.get("/ip/jiangche", response_class=HTMLResponse)
async def jiangche_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "jiangche"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/白月光江澈.html", encoding="utf-8").read()))

@router.get("/ip/luchengyu", response_class=HTMLResponse)
async def luchengyu_page(request: Request):
    user_id = resolve_ip_user_id(request)
    user_info = load_user_data(user_id)

    user_info["ip_name"] = "luchengyu"

    save_user_data(user_id, user_info)

    return HTMLResponse(_with_admin_logger(open("routers/学长.html", encoding="utf-8").read()))
