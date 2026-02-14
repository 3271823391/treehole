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
    raw = data.get(user_id, {})
    if not isinstance(raw, dict):
        raw = {}
    default_user = {
        "plan": "plus",
        "system_prompt": "你是一个温柔的倾听者，善于共情，不批判、不说教，回复简洁温暖",
        "memories": [],
        "history": [],
        "has_greeted": False,
        "chat_count": 0,
        "character_histories": {},
        "conversation_states": {},
        "ip_name": "",
        "last_active_at": "",
        "updated_at": "",
        "profile": {
            "display_name": "",
            "avatar_url": "",
            "password_hash": ""
        }
    }
    user_info = {**default_user}
    for key in default_user:
        if key in raw:
            user_info[key] = raw[key]
    if not isinstance(user_info.get("profile"), dict):
        user_info["profile"] = default_user["profile"].copy()
    else:
        profile = default_user["profile"].copy()
        profile.update(user_info["profile"])
        user_info["profile"] = profile
    return user_info


def save_user_data(user_id: str, user_info: dict):
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(user_info, dict):
        legacy_map_key = "relation" + "ships"
        user_info.pop(legacy_map_key, None)
        for key in list(user_info.keys()):
            if key.endswith("_score") or key.endswith("Score"):
                user_info.pop(key, None)
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
