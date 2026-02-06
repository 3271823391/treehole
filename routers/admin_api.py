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
        relationships = info.get("relationships") if isinstance(info.get("relationships"), dict) else {}
        profile = info.get("profile") if isinstance(info.get("profile"), dict) else {}
        items.append(
            {
                "user_id": user_id,
                "plan": info.get("plan", "plus"),
                "chat_count": int(info.get("chat_count", 0) or 0),
                "memory_count": len(info.get("memories", []) or []),
                "history_count": len(info.get("history", []) or []),
                "relationship_count": len(relationships),
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
    relationships = user.get("relationships") if isinstance(user.get("relationships"), dict) else {}
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
        "relationship_count": len(relationships),
    }


@router.get("/user/{user_id}/characters")
def get_user_characters(user_id: str):
    user = load_user_data(user_id)
    relationships = user.get("relationships") if isinstance(user.get("relationships"), dict) else {}
    items = []
    for character_id, state in relationships.items():
        if not isinstance(state, dict):
            continue
        risk = state.get("risk_buffer") if isinstance(state.get("risk_buffer"), dict) else {}
        items.append(
            {
                "character_id": character_id,
                "affinity_score": float(state.get("affinity_score", 50)),
                "stable_streak": int(state.get("stable_streak", 0) or 0),
                "last_affinity_eval_at": state.get("last_affinity_eval_at"),
                "user_msg_count_since_last_eval": int(state.get("user_msg_count_since_last_eval", 0) or 0),
                "risk_buffer": {
                    "boundary_pressure": int(risk.get("boundary_pressure", 0) or 0),
                    "dependency_attempt": int(risk.get("dependency_attempt", 0) or 0),
                    "conflict_pattern": int(risk.get("conflict_pattern", 0) or 0),
                    "updated_at": risk.get("updated_at"),
                },
                "affinity_eval_log": state.get("affinity_eval_log", [])[-10:],
            }
        )
    return {"user_id": user_id, "count": len(items), "items": items}


@router.get("/relationship")
def get_relationship_overview():
    users = _read_all_users()
    rows = []
    for user_id, info in users.items():
        if not isinstance(info, dict):
            continue
        relationships = info.get("relationships") if isinstance(info.get("relationships"), dict) else {}
        for character_id, state in relationships.items():
            if not isinstance(state, dict):
                continue
            rows.append(
                {
                    "user_id": user_id,
                    "character_id": character_id,
                    "affinity_score": float(state.get("affinity_score", 50)),
                    "stable_streak": int(state.get("stable_streak", 0) or 0),
                    "last_affinity_eval_at": state.get("last_affinity_eval_at"),
                }
            )
    rows.sort(key=lambda x: x["affinity_score"], reverse=True)
    return {"count": len(rows), "items": rows}


@router.get("/logs")
def get_admin_logs(
    since: float | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    category: str | None = Query(default=None),
):
    return query_admin_logs(since=since, limit=limit, category=category)
