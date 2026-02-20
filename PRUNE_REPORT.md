# PRUNE REPORT

## 1) 运行时入口文件列表
- `main.py`（FastAPI 应用创建、静态挂载、路由注册）
- `run.py`（仅调用 `main.run_api` 启动）

基于命令：
- `rg -n "include_router|mount\(|StaticFiles\(|APIRouter\(" -S .`
- `sed -n '1,220p' main.py`
- `sed -n '1,220p' run.py`

## 2) 被注册的路由模块列表（事实清单）
`main.py` 中实际 `include_router(...)` 注册：
- `routers.emotion`
- `routers.auth`
- `routers.profile`
- `routers.page`
- `routers.chat`
- `routers.voice_clone`
- `api.debug_relationship`
- `api.client_log`
- `api.admin`

另外静态挂载：
- `/static -> static/`
- `/routers -> routers/`

## 3) 被 HTML 引用的静态资源列表
基于命令：
- `rg -n "<script|<link|fetch\(|/api/|/chat_stream|/load_history" -S routers static`

汇总（`routers/*.html` 中直接引用）：
- `/static/js/pro_api_logic.js`
- `/static/shared_shell.css`
- `/static/shared_shell.js`
- `/static/virtual_ip_chat.css`
- `/static/virtual_ip_chat.js`
- `/static/avatars/default.svg`
- `/static/avatars/xiaxingmian.jpg`

## 4) 删除列表与未引用证据

### A. 明确清理项（按任务要求）
1. `.idea/` 与 `routers/.idea/`
   - 证据：IDE 配置目录，非运行时依赖；`main.py`/`run.py` 无任何导入或读取。
2. `tests/` 与 `e2e/`
   - 证据：用户明确要求删除测试文件。
3. `requirements-e2e.txt`、`requirements-tts-selfcheck.txt`
   - 证据：仅在 `readme.md` 的测试/自检步骤中被提及；运行时代码无导入。
4. `scripts/mock_lipvoice.py`、`scripts/selftest_voice_clone.py`、`scripts/tts_selfcheck.py`
   - 证据：`rg -n "selftest_voice_clone|tts_selfcheck|mock_lipvoice" -S --glob '*.py'` 显示仅脚本内部与 e2e 场景出现，未被 `main.py` 或已注册路由导入。

### B. 重复/冗余模块（满足“未注册 + 未导入”）
5. `routers/admin_api.py`
   - 证据：`main.py` 无 `include_router(admin_api.router)`；
   - 证据：`rg -n "routers\.admin_api|from routers import admin_api|import admin_api|include_router\(admin_api" -S .` 无命中。
6. `routers/admin_console.py`
   - 证据：`main.py` 无 `include_router(admin_console.router)`；
   - 证据：`rg -n "routers\.admin_console|from routers import admin_console|import admin_console|include_router\(admin_console" -S .` 无命中。
7. `api/admin_logs.py`
   - 证据：`main.py` 仅 `from api import admin, client_log, debug_relationship`；
   - 证据：`rg -n "from api import admin_logs|import api\.admin_logs|api\.admin_logs|admin_logs\.router|include_router\(admin_logs" -S .` 无命中。

### C. 未被引用静态资源
8. `static/admin_console_btn.js`
   - 证据：`rg -n "admin_console_btn\.js" -S .` 全仓库无引用。

## 5) 文件数量对比
- 清理前（tracked files）：`141`
- 清理后（tracked files）：`123`
- 减少：`18`

统计命令：
- 清理前：`git ls-files | wc -l`
- 清理后：`git add -A && git ls-files | wc -l`

## 6) 验收命令（清理后）
- `python -c "import main; print('import main ok')"`
- `python -m py_compile $(git ls-files '*.py')`
