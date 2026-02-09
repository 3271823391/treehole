import json
import os
from datetime import datetime

USER_DATA_FILE = "user_data.json"

if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)


def load_user_data(user_id: str) -> dict:
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(user_id, {
        "plan": "plus",
        "system_prompt": "你是一个温柔的倾听者，善于共情，不批判、不说教，回复简洁温暖",
        "memories": [],
        "history": [],
        "has_greeted": False,
        "chat_count": 0,
        "relationships": {},
        "profile": {
            "username": "",
            "display_name": "",
            "avatar_url": "",
            "password_hash": ""
        }
    })


def save_user_data(user_id: str, user_info: dict):
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data[user_id] = user_info
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_user_memory(user_id: str, memory_text: str):
    user_info = load_user_data(user_id)

    new_memory = f"[{datetime.now().strftime('%m-%d')}] {memory_text[:100]}"
    user_info["memories"] = (user_info["memories"] + [new_memory])[-5:]
    save_user_data(user_id, user_info)


def get_user_memory_text(user_id: str) -> str:
    user_info = load_user_data(user_id)
    if not user_info["memories"]:
        return "无特殊记忆"
    return "用户核心记忆：" + "；".join(user_info["memories"])


def _default_relationship_state():
    return {
        "affinity_score": 50,
        "stable_streak": 0,
        "last_affinity_eval_at": None,
        "user_msg_count_since_last_eval": 0,
        "last_streak_reward_at": None,
        "risk_buffer": {
            "boundary_pressure": 0,
            "dependency_attempt": 0,
            "conflict_pattern": 0,
            "updated_at": None
        },
        "affinity_eval_log": []
    }


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def get_relationship_state(user_id: str, character_id: str) -> dict:
    user_info = load_user_data(user_id)
    relationships = user_info.setdefault("relationships", {})
    state = relationships.get(character_id)
    if not isinstance(state, dict):
        state = _default_relationship_state()
        relationships[character_id] = state
        save_user_data(user_id, user_info)
    return state


def save_relationship_state(user_id: str, character_id: str, state: dict) -> None:
    user_info = load_user_data(user_id)
    relationships = user_info.setdefault("relationships", {})
    relationships[character_id] = state
    save_user_data(user_id, user_info)


def increment_user_msg_count(user_id: str, character_id: str, inc: int = 1) -> int:
    state = get_relationship_state(user_id, character_id)
    state["user_msg_count_since_last_eval"] = int(state.get("user_msg_count_since_last_eval", 0)) + inc
    save_relationship_state(user_id, character_id, state)
    return state["user_msg_count_since_last_eval"]


def reset_user_msg_count(user_id: str, character_id: str) -> None:
    state = get_relationship_state(user_id, character_id)
    state["user_msg_count_since_last_eval"] = 0
    save_relationship_state(user_id, character_id, state)


def update_risk_buffer(user_id: str, character_id: str, signal: str, inc: int = 1) -> None:
    state = get_relationship_state(user_id, character_id)
    risk_buffer = state.setdefault("risk_buffer", _default_relationship_state()["risk_buffer"])
    risk_buffer[signal] = int(risk_buffer.get(signal, 0)) + inc
    risk_buffer["updated_at"] = _now_iso()
    save_relationship_state(user_id, character_id, state)


def clear_risk_buffer(user_id: str, character_id: str, signal: str | None = None) -> None:
    state = get_relationship_state(user_id, character_id)
    risk_buffer = state.setdefault("risk_buffer", _default_relationship_state()["risk_buffer"])
    if signal:
        risk_buffer[signal] = 0
    else:
        for key in ["boundary_pressure", "dependency_attempt", "conflict_pattern"]:
            risk_buffer[key] = 0
    risk_buffer["updated_at"] = _now_iso()
    save_relationship_state(user_id, character_id, state)


def append_affinity_eval_log(
    user_id: str,
    character_id: str,
    signals: list,
    confidence: str,
    delta: float,
    note: str = ""
) -> None:
    state = get_relationship_state(user_id, character_id)
    log_item = {
        "at": _now_iso(),
        "signals": signals,
        "confidence": confidence,
        "delta": delta,
        "note": note,
    }
    logs = state.setdefault("affinity_eval_log", [])
    logs.append(log_item)
    state["affinity_eval_log"] = logs[-20:]
    state["last_affinity_eval_at"] = log_item["at"]
    save_relationship_state(user_id, character_id, state)
