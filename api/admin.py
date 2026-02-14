from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from core.log_buffer import get_logs

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
USER_DATA_FILE = BASE_DIR / "user_data.json"


def _load_all_users() -> dict[str, Any]:
    if not USER_DATA_FILE.exists():
        return {}
    try:
        return json.loads(USER_DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _build_user_item(user_id: str, user: dict[str, Any]) -> dict[str, Any]:
    profile = user.get("profile") if isinstance(user, dict) else {}
    if not isinstance(profile, dict):
        profile = {}
    history = user.get("history") if isinstance(user, dict) else []
    if not isinstance(history, list):
        history = []

    return {
        "user_id": user_id,
        "display_name": profile.get("display_name") or profile.get("username") or "",
        "plan": user.get("plan", "plus") if isinstance(user, dict) else "plus",
        "chat_count": user.get("chat_count", len(history)) if isinstance(user, dict) else 0,
        "ip_name": user.get("ip_name", "") if isinstance(user, dict) else "",
        "last_active_at": user.get("last_active_at", "") if isinstance(user, dict) else "",
        "updated_at": user.get("updated_at", "") if isinstance(user, dict) else "",
    }


@router.get("/api/admin/users")
def list_users() -> dict[str, Any]:
    data = _load_all_users()
    items = [_build_user_item(user_id, user) for user_id, user in data.items()]
    return {"ok": True, "count": len(items), "items": items}


@router.get("/api/admin/user/{user_id}")
def get_user(user_id: str) -> dict[str, Any]:
    data = _load_all_users()
    user = data.get(user_id, {})
    profile = user.get("profile") if isinstance(user, dict) and isinstance(user.get("profile"), dict) else {}
    history = user.get("history") if isinstance(user, dict) and isinstance(user.get("history"), list) else []

    return {
        "ok": True,
        "user_id": user_id,
        "plan": user.get("plan", "plus") if isinstance(user, dict) else "plus",
        "chat_count": user.get("chat_count", len(history)) if isinstance(user, dict) else 0,
        "profile": profile,
        "memories": user.get("memories", []) if isinstance(user, dict) else [],
        "history": history,
    }


@router.get("/api/admin/logs")
def list_admin_logs(category: str | None = Query(default=None), limit: int = Query(default=200)) -> dict[str, Any]:
    items = get_logs(limit=limit)
    if category:
        needle = category.lower()
        items = [item for item in items if needle in str(item.get("source", "")).lower()]
    return {"ok": True, "count": len(items), "items": items}
