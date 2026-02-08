from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from core.log_buffer import clear_logs, get_logs

router = APIRouter()


def _enabled() -> bool:
    return os.getenv("DEBUG_RELATIONSHIP", "0") == "1" or os.getenv("ADMIN_CONSOLE", "0") == "1"


def _assert_enabled() -> None:
    if not _enabled():
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/api/admin/logs")
def admin_logs(
    since: float | None = Query(default=None),
    level: str | None = Query(default=None),
    source: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=500),
):
    _assert_enabled()
    items = get_logs(since=since, limit=limit)

    if level:
        level_upper = level.upper()
        items = [item for item in items if str(item.get("level", "")).upper() == level_upper]

    if source:
        source_lower = source.lower()
        items = [item for item in items if str(item.get("source", "")).lower() == source_lower]

    if q:
        needle = q.lower()
        filtered = []
        for item in items:
            haystack = f"{item.get('message', '')} {json.dumps(item.get('meta', {}), ensure_ascii=False)}".lower()
            if needle in haystack:
                filtered.append(item)
        items = filtered

    next_since = items[-1]["ts"] if items else (since or 0)
    return {"next_since": next_since, "items": items}


@router.post("/api/admin/clear_logs")
def admin_clear_logs():
    _assert_enabled()
    clear_logs()
    return {"ok": True}


@router.get("/admin/console", response_class=HTMLResponse)
def admin_console_page():
    _assert_enabled()
    debug_mode = os.getenv("DEBUG_RELATIONSHIP", "0") == "1"
    clear_button = "<button id='clearBtn'>清空日志</button>" if debug_mode else ""
    html = f"""
<!doctype html>
<html lang='zh-CN'>
<head>
<meta charset='utf-8'>
<title>Admin Console</title>
<style>
body {{ font-family: sans-serif; margin: 0; background: #111; color: #eee; }}
.toolbar {{ position: sticky; top: 0; background: #1e1e1e; padding: 10px; display: flex; gap: 8px; align-items: center; }}
#logs {{ padding: 12px; }}
.row {{ border-bottom: 1px solid #2a2a2a; padding: 8px 4px; }}
.row.error {{ background: rgba(255, 0, 0, 0.12); }}
.meta {{ margin-top: 4px; color: #bdbdbd; font-size: 12px; white-space: pre-wrap; display: none; }}
.meta.open {{ display: block; }}
.badge {{ display: inline-block; min-width: 46px; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 8px; background: #333; }}
.pause {{ margin-left: auto; }}
</style>
</head>
<body>
<div class='toolbar'>
  <label>level <select id='level'><option value=''>ALL</option><option>INFO</option><option>WARN</option><option>ERROR</option><option>DEBUG</option></select></label>
  <label>source <select id='source'><option value=''>ALL</option><option>server</option><option>client</option><option>access</option></select></label>
  <input id='q' placeholder='keyword 搜索' />
  <button id='pauseBtn' class='pause'>暂停</button>
  {clear_button}
</div>
<div id='logs'></div>
<script>
const logsEl = document.getElementById('logs');
const levelEl = document.getElementById('level');
const sourceEl = document.getElementById('source');
const qEl = document.getElementById('q');
const pauseBtn = document.getElementById('pauseBtn');
const clearBtn = document.getElementById('clearBtn');
let paused = false;
let since = 0;

pauseBtn.addEventListener('click', () => {{
  paused = !paused;
  pauseBtn.textContent = paused ? '继续' : '暂停';
}});

if (clearBtn) {{
  clearBtn.addEventListener('click', async () => {{
    await fetch('/api/admin/clear_logs', {{ method: 'POST' }});
    logsEl.innerHTML = '';
    since = 0;
  }});
}}

function esc(s) {{
  const div = document.createElement('div');
  div.textContent = String(s ?? '');
  return div.innerHTML;
}}

function renderItem(item) {{
  const row = document.createElement('div');
  row.className = 'row ' + (item.level === 'ERROR' ? 'error' : '');
  const header = document.createElement('div');
  header.innerHTML = `<span class="badge">${{esc(item.source)}}</span><span class="badge">${{esc(item.level)}}</span>${{esc(item.iso)}} - ${{esc(item.message)}}`;
  row.appendChild(header);
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = JSON.stringify(item.meta || {{}}, null, 2);
  header.addEventListener('click', () => meta.classList.toggle('open'));
  row.appendChild(meta);
  logsEl.prepend(row);
}}

async function tick() {{
  if (paused) return;
  const params = new URLSearchParams();
  params.set('since', String(since));
  params.set('limit', '500');
  if (levelEl.value) params.set('level', levelEl.value);
  if (sourceEl.value) params.set('source', sourceEl.value);
  if (qEl.value) params.set('q', qEl.value);

  const res = await fetch('/api/admin/logs?' + params.toString());
  if (!res.ok) return;
  const data = await res.json();
  (data.items || []).forEach(renderItem);
  since = data.next_since || since;
}}

[levelEl, sourceEl, qEl].forEach(el => el.addEventListener('change', () => {{
  logsEl.innerHTML = '';
  since = 0;
}}));
setInterval(tick, 1000);
tick();
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)
