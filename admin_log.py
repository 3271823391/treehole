from __future__ import annotations

from typing import Any

from core.log_buffer import get_logs

_ALLOWED_CATEGORIES = {"chat", "user", "system", "error"}
_IGNORE_KEYWORDS = (
    "favicon",
    "/static/",
    "chrome.devtools",
    "zybtrackerstatisticsaction",
    "browser",
    "playwright",
)


def _looks_like_noise(message: str, meta: dict[str, Any]) -> bool:
    text = f"{message} {meta}".lower()
    return any(keyword in text for keyword in _IGNORE_KEYWORDS)


def _categorize(item: dict[str, Any]) -> str | None:
    level = str(item.get("level", "")).upper()
    message = str(item.get("message", ""))
    source = str(item.get("source", ""))
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}

    if _looks_like_noise(message, meta):
        return None

    if level == "ERROR" or source == "error":
        return "error"

    lower_text = f"{message} {source} {meta}".lower()
    if any(k in lower_text for k in ("/chat", "chat_stream", "character_id", "messages")):
        return "chat"
    if any(k in lower_text for k in ("/profile", "/auth", "user_id", "display_name", "pin")):
        return "user"
    return "system"


def query_admin_logs(since: float | None = None, limit: int = 500, category: str | None = None) -> dict[str, Any]:
    logs = get_logs(since=since, limit=limit)
    items: list[dict[str, Any]] = []

    for item in logs:
        cat = _categorize(item)
        if not cat:
            continue
        if category and category not in _ALLOWED_CATEGORIES:
            continue
        if category and cat != category:
            continue
        entry = {
            "ts": item.get("ts"),
            "iso": item.get("iso"),
            "level": item.get("level"),
            "source": item.get("source"),
            "category": cat,
            "message": item.get("message"),
            "meta": item.get("meta", {}),
        }
        items.append(entry)

    next_since = items[-1]["ts"] if items else (since or 0)
    return {
        "next_since": next_since,
        "count": len(items),
        "items": items,
    }
