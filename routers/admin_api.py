from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query

from admin_log import query_admin_logs
from data_store import USER_DATA_FILE, load_user_data

router = APIRouter(prefix="/api/admin", tags=["admin-api"])


def _read_all_users() -> dict:
    path = Path(USER_DATA_FILE)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
    return data if isinstance(data, dict) else {}


@router.get("/users")
def get_users():
    users = _read_all_users()
    items = []
    for user_id, info in users.items():
        if not isinstance(info, dict):
            continue
        profile = info.get("profile") if isinstance(info.get("profile"), dict) else {}
        items.append(
            {
                "user_id": user_id,
                "plan": info.get("plan", "plus"),
                "chat_count": int(info.get("chat_count", 0) or 0),
                "memory_count": len(info.get("memories", []) or []),
                "history_count": len(info.get("history", []) or []),
                "display_name": profile.get("display_name") or profile.get("username") or "",
                "ip_name": info.get("ip_name", ""),
            }
        )
    items.sort(key=lambda x: x["chat_count"], reverse=True)
    return {"count": len(items), "items": items}


@router.get("/user/{user_id}")
def get_user(user_id: str):
    user = load_user_data(user_id)
    profile = user.get("profile") if isinstance(user.get("profile"), dict) else {}
    return {
        "user_id": user_id,
        "plan": user.get("plan", "plus"),
        "chat_count": int(user.get("chat_count", 0) or 0),
        "has_greeted": bool(user.get("has_greeted", False)),
        "ip_name": user.get("ip_name", ""),
        "memories": user.get("memories", []),
        "history": user.get("history", []),
        "profile": {
            "username": profile.get("username", ""),
            "display_name": profile.get("display_name", ""),
            "avatar_url": profile.get("avatar_url", ""),
        },
    }


@router.get("/logs")
def get_admin_logs(
    since: float | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    category: str | None = Query(default=None),
):
    return query_admin_logs(since=since, limit=limit, category=category)
