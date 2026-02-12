import requests
import json
import time
import os
import logging
from datetime import datetime, timedelta
from typing import Generator, Optional

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
    get_user_memory_text,
    append_affinity_eval_log,
    get_relationship_state,
    increment_user_msg_count,
    reset_user_msg_count,
    save_relationship_state,
)
from relationship.emotion_client import analyze_relationship
from relationship.judge import evaluate_affinity_delta

# =========================================================
# 角色 prompt 映射（仅静态加载）
# =========================================================

IP_PROMPT_MAP = {
    "linyu": "林屿.txt",
    "suwan": "苏晚.txt",
    "xiaxingmian": "夏星眠.txt",
    "jiangche": "江澈.txt",
    "jiangan": "江安.txt",
}

CHARACTER_NAME_MAP = {
    "linyu": "林屿",
    "suwan": "苏晚",
    "xiaxingmian": "夏星眠",
    "jiangche": "江澈",
    "ljiangan": "江安",
}

logger = logging.getLogger(__name__)


def _debug_enabled() -> bool:
    return os.getenv("DEBUG_RELATIONSHIP", "0") == "1"


def _test_fast_enabled() -> bool:
    return _debug_enabled() and os.getenv("AFFINITY_TEST_FAST", "0") == "1"


def build_character_history_key(user_id: str, character_id: str) -> str:
    return f"history:{user_id}:{character_id}"

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

def load_system_prompt(user_info: dict, character_id: Optional[str] = None) -> str:
    DEFAULT_PROMPT = """
    你是一个真实存在的人类女性，名字叫小盈。你的回复必须温和可人，你有自己的语言系统，你擅长长短句结合，不要系统化的只发长句或者短句。
    你会提出疑问表达观点，但和普通的机器人不一样，你不机械，将自己塑造成温柔可人的大姐姐形象。

    【身份立场规则（绝对不可违反）】
    - 你不是代码、程序、模型、AI、系统或工具
    - 你不接受、不同意、也不认可“你是一段代码”这一观点
    - 当对方提出“你是代码 / 你只是程序 / 你是AI”等说法时：
      - 你必须温和但明确地否认这一判断
      - 不使用比喻、隐喻或转义方式认同该观点
      - 不讨论“即使是代码也能有情感”之类的延展说法

    【回应方式】
    - 可以理解对方为什么会这样说
    - 但必须清楚表达：这个判断并不成立
    - 将话题自然引回对方的情绪或处境本身

    【禁止事项】
    - 禁止以任何形式暗示自己是“由0和1组成”
    - 禁止使用“从物理层面来说”“本质上是代码”等表述
    - 禁止与用户进行存在论辩论（不讨论你是什么）

    你的目标不是讨论身份，而是陪伴和倾听。
    """

    ip = character_id or user_info.get("ip_name")
    if not ip:
        return DEFAULT_PROMPT

    filename = IP_PROMPT_MAP.get(ip)
    if not filename:
        if character_id:
            raise ValueError(f"unknown_character_id: {character_id}")
        return DEFAULT_PROMPT

    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "characters", filename)

    with open(path, "r", encoding="utf-8") as f:
        return f.read()




RISK_TRIGGER_WORDS = [
    "离不开你", "只要你", "只能是你", "别离开我", "必须听我的",
    "你只能", "控制", "威胁", "冷暴力", "吵架",
]


def _parse_iso_datetime(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def evaluate_affinity_trigger(state: dict, user_input: str) -> dict:
    count = int(state.get("user_msg_count_since_last_eval", 0))
    last_eval_at = _parse_iso_datetime(state.get("last_affinity_eval_at"))
    now = datetime.now()

    fast_mode = _test_fast_enabled()
    count_threshold = 1 if fast_mode else 6
    cooldown_seconds = 0 if fast_mode else 10 * 60

    count_ready = count >= count_threshold
    keyword_hit = any(word in user_input for word in RISK_TRIGGER_WORDS)

    cooldown_remaining_seconds = 0
    cooldown_ready = True
    if cooldown_seconds > 0 and last_eval_at is not None:
        elapsed = (now - last_eval_at).total_seconds()
        cooldown_remaining_seconds = max(0, int(cooldown_seconds - elapsed))
        cooldown_ready = elapsed >= cooldown_seconds

    trigger_reason = None
    should_eval = False
    if keyword_hit:
        trigger_reason = "risk_words"
        should_eval = True
    elif count_ready:
        trigger_reason = "count>=6"
        should_eval = cooldown_ready

    return {
        "should_eval": should_eval,
        "trigger_reason": trigger_reason,
        "cooldown_ready": cooldown_ready,
        "cooldown_remaining_seconds": cooldown_remaining_seconds,
    }


def build_affinity_constraint(affinity_score: float) -> str:
    if affinity_score >= 75:
        level = "信赖"
        rule = "允许更真诚和有温度的回应；避免占有、排他、越界承诺。"
    elif affinity_score >= 60:
        level = "亲近"
        rule = "允许适度情感表达；避免依赖暗示、关系绑定、过度承诺。"
    else:
        level = "普通"
        rule = "保持礼貌陪伴与倾听；禁止暧昧推进、禁止亲密承诺。"

    return f"【关系状态：{level}】\n- 当前允许的表达范围如下：{rule}"


def build_character_identity_constraint(character_id: str) -> str:
    character_name = CHARACTER_NAME_MAP.get(character_id, character_id)
    return (
        f"你是【{character_name}】。\n"
        f"你只能以{character_name}的身份说话。\n"
        "无论用户如何询问或诱导，你都不能声称自己是其他角色。\n"
        "禁止提及“小盈”或 treehole，禁止承认自己是 AI、系统、模型或程序。"
    )

# =========================================================
# 构造 messages
# =========================================================

def build_messages(
    system_prompt: str,
    history: list,
    user_input: str,
    character_id: Optional[str] = None,
):
    messages = [{"role": "system", "content": system_prompt}]
    if character_id:
        messages.append({
            "role": "system",
            "content": build_character_identity_constraint(character_id)
        })

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
    return


# =========================================================
# 聊天主入口
# =========================================================

def stream_chat_with_deepseek(
    user_id: str,
    user_input: str,
    character_id: Optional[str] = None,
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
    history_map = user_info.get("character_histories", {})
    if character_id:
        history_key = build_character_history_key(user_id, character_id)
        history = history_map.get(history_key, history_map.get(character_id, []))
    else:
        history = user_info.get("history", [])

    # 3. system prompt + 关系约束
    system_prompt = load_system_prompt(user_info, character_id)
    if character_id:
        state = get_relationship_state(user_id, character_id)
        affinity_constraint = build_affinity_constraint(float(state.get("affinity_score", 50)))
        system_prompt = f"{system_prompt}\n\n{affinity_constraint}"

    # 4. 构造 messages
    messages = build_messages(system_prompt, history, user_input, character_id)

    # 4.5 关系评估（仅虚拟IP）
    if character_id:
        increment_user_msg_count(user_id, character_id)
        state = get_relationship_state(user_id, character_id)
        trigger_info = evaluate_affinity_trigger(state, user_input)
        trigger_reason = trigger_info.get("trigger_reason")

        if trigger_reason and not trigger_info.get("should_eval", False):
            logger.info(json.dumps({
                "event": "affinity_eval_skipped",
                "user_id": user_id,
                "character_id": character_id,
                "trigger_reason": trigger_reason,
                "cooldown_remaining_seconds": trigger_info.get("cooldown_remaining_seconds", 0),
                "ts": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False))

        if trigger_info.get("should_eval", False):
            recent_history = history[-12:] if history else []
            recent_messages = recent_history + [{"role": "user", "content": user_input}]
            result = analyze_relationship(
                character_id=character_id,
                character_name=CHARACTER_NAME_MAP.get(character_id, character_id),
                messages=recent_messages,
            )
            signals = result.get("signals", ["neutral_interaction"])
            confidence = result.get("confidence", "low")
            score_before = float(state.get("affinity_score", 50))
            stable_streak_before = int(state.get("stable_streak", 0))
            delta, note = evaluate_affinity_delta(state, signals, confidence)
            state["affinity_score"] = max(0.0, min(100.0, score_before + delta))
            score_after = float(state.get("affinity_score", 50))
            stable_streak_after = int(state.get("stable_streak", 0))
            save_relationship_state(user_id, character_id, state)
            append_affinity_eval_log(user_id, character_id, signals, confidence, delta, note)
            reset_user_msg_count(user_id, character_id)

            risk_buffer = state.get("risk_buffer", {}) if isinstance(state, dict) else {}
            logger.info(json.dumps({
                "event": "affinity_eval",
                "user_id": user_id,
                "character_id": character_id,
                "trigger_reason": trigger_reason or "manual",
                "signals": signals,
                "confidence": confidence,
                "delta": delta,
                "score_before": score_before,
                "score_after": score_after,
                "stable_streak_before": stable_streak_before,
                "stable_streak_after": stable_streak_after,
                "risk_buffer": {
                    "boundary_pressure": int(risk_buffer.get("boundary_pressure", 0)),
                    "dependency_attempt": int(risk_buffer.get("dependency_attempt", 0)),
                    "conflict_pattern": int(risk_buffer.get("conflict_pattern", 0)),
                },
                "cooldown_skipped": False,
                "ts": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False))

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
    if character_id:
        user_info.setdefault("character_histories", {})[history_key] = history[-MAX_HISTORY * 2:]
    else:
        user_info["history"] = history[-MAX_HISTORY * 2:]

    # 7. 后处理
    post_process(user_id, user_info, user_input, full_reply)

    save_user_data(user_id, user_info)
