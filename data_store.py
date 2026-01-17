import json
import os
from datetime import datetime

# 存储路径
USER_DATA_FILE = "user_data.json"

# 初始化存储文件
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_user_data(user_id: str) -> dict:
    """加载用户数据（性格、记忆、历史）"""
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(user_id, {
        "system_prompt": "你是一个温柔的倾听者，善于共情，不批判、不说教，回复简洁温暖",
        "memories": [],  # 存储用户关键记忆
        "history": []    # 聊天历史
    })

def save_user_data(user_id: str, user_info: dict):
    """保存用户数据"""
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data[user_id] = user_info
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_user_memory(user_id: str, memory_text: str):
    """添加用户记忆（简化版：只保留关键信息）"""
    user_info = load_user_data(user_id)
    # 拼接记忆，控制长度
    new_memory = f"[{datetime.now().strftime('%m-%d')}] {memory_text[:100]}"
    user_info["memories"] = (user_info["memories"] + [new_memory])[-5:]  # 最多保留5条核心记忆
    save_user_data(user_id, user_info)

def get_user_memory_text(user_id: str) -> str:
    """获取用户记忆文本（用于拼接Prompt）"""
    user_info = load_user_data(user_id)
    if not user_info["memories"]:
        return "无特殊记忆"
    return "用户核心记忆：" + "；".join(user_info["memories"])