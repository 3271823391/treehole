import requests
import json
import time
import os
from typing import Generator

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    DEEPSEEK_API_URL,
    MAX_HISTORY,
    SENSITIVE_WORDS,
    STREAM_DELAY
)

from data_store import (
    load_user_data,
    save_user_data,
    add_user_memory,
    get_user_memory_text
)

# =========================================================
# 角色 prompt 映射（仅静态加载）
# =========================================================

IP_PROMPT_MAP = {
    "linyu": "林屿.txt",
    "suwan": "苏晚.txt",
    "xiaxingmian": "夏星眠.txt",
    "jiangche": "江澈.txt",
    "luchengyu": "陆承宇.txt",
}

# =========================================================
# 安全检测
# =========================================================

def check_sensitive(text: str):
    for word in SENSITIVE_WORDS:
        if word in text:
            if word in ["自杀", "自残"]:
                return True, "生命宝贵！心理援助热线：12320（全国）"
            return True, "内容包含违规词，请换个说法"
    return False, ""

# =========================================================
# system prompt 加载（不生成、不拼装）
# =========================================================

def load_system_prompt(user_info: dict) -> str:
    DEFAULT_PROMPT = "你是一个女孩子叫小盈，只负责倾听与回应,回复要尽可能地长"

    ip = user_info.get("ip_name")
    if not ip:
        return DEFAULT_PROMPT

    filename = IP_PROMPT_MAP.get(ip)
    if not filename:
        return DEFAULT_PROMPT

    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "characters", filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return DEFAULT_PROMPT

# =========================================================
# 构造 messages
# =========================================================

def build_messages(system_prompt: str, history: list, user_input: str):
    messages = [{"role": "system", "content": system_prompt}]

    for h in history:
        if h.get("role") in ("user", "assistant"):
            messages.append(h)

    messages.append({"role": "user", "content": user_input})
    return messages

# =========================================================
# DeepSeek 流式调用
# =========================================================

def call_deepseek_stream(messages):
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": 0.75
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    with requests.post(
        DEEPSEEK_API_URL,
        headers=headers,
        json=payload,
        stream=True,
        timeout=60
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if not line.startswith("data:"):
                continue

            data = line.replace("data:", "").strip()
            if data == "[DONE]":
                break

            chunk = json.loads(data)
            yield chunk["choices"][0]["delta"].get("content", "")

# =========================================================
# 后处理（记忆 / 情绪等扩展口）
# =========================================================

def post_process(user_id, user_info, user_input, reply):
    history = user_info.get("history", [])
    recent = history[-6:]

    try:
        r = requests.post(
            "http://127.0.0.1:8000/emotion",
            json={
                "history": recent,
                "current_input": user_input
            },
            timeout=10
        )
        emotion = r.json()
        user_info["last_emotion"] = emotion
    except Exception:
        pass


# =========================================================
# 聊天主入口
# =========================================================

def stream_chat_with_deepseek(
    user_id: str,
    user_input: str,
) -> Generator[str, None, None]:

    # 1. 安全检测
    unsafe, warning = check_sensitive(user_input)
    if unsafe:
        for c in warning:
            yield c
            time.sleep(STREAM_DELAY)
        return

    # 2. 读取用户数据
    user_info = load_user_data(user_id)
    history = user_info.get("history", [])

    # 3. system prompt
    system_prompt = load_system_prompt(user_info)

    # 4. 构造 messages
    messages = build_messages(system_prompt, history, user_input)

    # 5. 调模型
    full_reply = ""
    try:
        for delta in call_deepseek_stream(messages):
            if delta:
                full_reply += delta
                yield delta
                time.sleep(STREAM_DELAY)
    except Exception:
        err = "（对话异常，请稍后再试）"
        for c in err:
            yield c
            time.sleep(STREAM_DELAY)
        return

    # 6. 写回历史
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": full_reply})
    user_info["history"] = history[-MAX_HISTORY * 2:]

    # 7. 后处理
    post_process(user_id, user_info, user_input, full_reply)

    save_user_data(user_id, user_info)
