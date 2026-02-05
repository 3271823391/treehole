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
        "profile": {
            "username": "",
            "display_name": "",
            "avatar_url": "",
            "pin_hash": ""
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
