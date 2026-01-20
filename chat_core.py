import requests
import json
import time
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
# 捏人模式（Create）
# =========================================================

def extract_personality_for_create(user_description: str) -> dict:
    prompt = f"""
请根据用户描述，提取人格特征，输出严格 JSON：

用户描述：
{user_description}

字段：
- 情绪特点
- 共情方式
- 回复风格
- 口头禅（数组）
- 语气强度
"""

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 600
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json=payload,
            timeout=60
        )
        return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception:
        return {}


def generate_system_prompt_create(p: dict) -> str:
    return f"""
你是一个具有以下人格特征的陪伴型 AI：

情绪特点：{p.get("情绪特点", "")}
共情方式：{p.get("共情方式", "")}
回复风格：{p.get("回复风格", "")}
口头禅：{",".join(p.get("口头禅", []))}
语气强度：{p.get("语气强度", "")}

要求：
- 共情优先，不批判、不说教
- 回答自然、有温度
- 用户情绪低落时，先安慰再回应
- 不暴露你是模型
"""


# =========================================================
# 克隆模式（Clone）
# =========================================================

def extract_personality_for_clone(reference_text: str) -> dict:
    prompt = f"""
请分析以下文本的说话风格，并输出严格 JSON：

文本：
{reference_text}

字段：
- 语气特点
- 常用词汇（数组）
- 句式特点
- 高频口头禅（数组）
"""

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json=payload,
            timeout=60
        )
        return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception:
        return {}


def generate_system_prompt_clone(p: dict) -> str:
    return f"""
你将完全模仿以下说话风格进行回复：

语气特点：{p.get("语气特点", "")}
句式特点：{p.get("句式特点", "")}
常用词汇：{",".join(p.get("常用词汇", []))}
高频口头禅：{",".join(p.get("高频口头禅", []))}

规则：
- 用词、语气、句式必须一致
- 优先使用给定口头禅
- 不解释风格来源
- 不自我暴露
"""


# =========================================================
# 聊天主逻辑（含记忆）
# =========================================================

def stream_chat_with_deepseek(
    user_id: str,
    user_input: str
) -> Generator[str, None, None]:

    # ---------- 1. 安全检测 ----------
    unsafe, warning = check_sensitive(user_input)
    if unsafe:
        for c in warning:
            yield c
            time.sleep(STREAM_DELAY)
        return

    # ---------- 2. 读取用户数据 ----------
    user_info = load_user_data(user_id)
    system_prompt = user_info["system_prompt"]
    history = user_info.get("history", [])

    # ---------- 2.x 主动问候（只触发一次） ----------

    if not user_info.get("has_greeted", False):
        greet_text = "我在呢。想从哪里开始说起都可以。"

        history.append({
            "role": "assistant",
            "content": greet_text
        })

        user_info["has_greeted"] = True
        user_info["history"] = history
        save_user_data(user_id, user_info)

    # ---------- 3. 构造 Prompt ----------
    messages = []

    messages.append({
        "role": "system",
        "content": system_prompt
    })

    messages.append({
        "role": "system",
        "content": get_user_memory_text(user_id)
    })

    for h in history[-MAX_HISTORY * 2:]:
        messages.append(h)

    messages.append({
        "role": "user",
        "content": user_input
    })

    # ---------- 4. 调用 DeepSeek ----------
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    full_reply = ""

    try:
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
                delta = chunk["choices"][0]["delta"].get("content", "")
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

    # ---------- 5. 写回历史 ----------
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": full_reply})
    user_info["history"] = history[-MAX_HISTORY * 2:]

    # ---------- 6. 长期记忆抽取 ----------
    if any(k in user_input for k in ["我叫", "我是", "我一直", "我总是", "我已经"]):
        add_user_memory(user_id, user_input)

    save_user_data(user_id, user_info)
