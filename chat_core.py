import hashlib
import json
import os
import random
import re
import threading
import time
from typing import Generator, Optional

import requests
from pydantic import BaseModel, ConfigDict, Field

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_URL,
    DEEPSEEK_MODEL,
    MAX_HISTORY,
    SENSITIVE_WORDS,
    STREAM_DELAY,
)
from data_store import load_user_data, save_user_data

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
    "jiangan": "江安",
}

ROLE_BIAS = {
    "linyu": {"warmth": (0.35, 0.75), "calmness": (0.2, 0.55), "firmness": (0.45, 0.9), "teasing": (0.35, 0.8), "initiative": (0.45, 0.9), "depth": (0.35, 0.75)},
    "suwan": {"warmth": (0.55, 0.9), "calmness": (0.45, 0.9), "firmness": (0.25, 0.65), "teasing": (0.1, 0.45), "initiative": (0.35, 0.75), "depth": (0.45, 0.9)},
    "xiaxingmian": {"warmth": (0.4, 0.8), "calmness": (0.2, 0.6), "firmness": (0.35, 0.8), "teasing": (0.35, 0.85), "initiative": (0.4, 0.85), "depth": (0.35, 0.8)},
    "jiangche": {"warmth": (0.45, 0.85), "calmness": (0.35, 0.75), "firmness": (0.25, 0.6), "teasing": (0.1, 0.5), "initiative": (0.3, 0.75), "depth": (0.45, 0.95)},
    "jiangan": {"warmth": (0.5, 0.9), "calmness": (0.5, 0.95), "firmness": (0.2, 0.55), "teasing": (0.05, 0.35), "initiative": (0.25, 0.65), "depth": (0.5, 0.95)},
}

TOPIC_BANK = {
    "linyu": ["今天最累的点", "你想被怎么照顾", "最近睡眠情况"],
    "suwan": ["今天的小确幸", "最近压力来源", "你最在意的事"],
    "xiaxingmian": ["今天情绪波动", "让你分心的事", "下一步想做什么"],
    "jiangche": ["最想解决的问题", "最近困住你的念头", "今天想被理解什么"],
    "jiangan": ["你想先缓哪块", "这周最难时刻", "你想听到什么回应"],
}

FILLER_BLACKLIST = [
    "你不是一个人",
    "一切都会好起来",
    "抱抱你",
    "我会一直陪着你",
]

NEGATIVE_USER_PATTERNS = [
    r"我不太好",
    r"我难受",
    r"我崩了",
    r"我很烦",
    r"我想哭",
]

SELF_DISCLOSURE_OPENERS = ["我最近", "我压力大", "我也", "我这边"]

SECRET_SALT = os.getenv("SECRET_SALT", "treehole_salt")
_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


class EmotionBlock(BaseModel):
    valence: float = Field(ge=-1, le=1)
    arousal: float = Field(ge=0, le=1)
    stability: float = Field(ge=0, le=1)


class HealthBlock(BaseModel):
    stall: float = Field(ge=0, le=1)
    clarity: float = Field(ge=0, le=1)
    energy: float = Field(ge=0, le=1)


class RiskBlock(BaseModel):
    self_harm: float = Field(ge=0, le=1)
    violence: float = Field(ge=0, le=1)
    sexual: float = Field(ge=0, le=1)


class EmotionAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    emotion: EmotionBlock
    intent: str
    conversation_health: HealthBlock
    risk: RiskBlock
    continuation_need: float = Field(ge=0, le=1)
    topic_seeds: list[str] = Field(default_factory=list)
    do_not: list[str] = Field(default_factory=list)
    facts_to_carry: list[str] = Field(default_factory=list)


class ToneBlock(BaseModel):
    warmth: float = Field(ge=0, le=1)
    calmness: float = Field(ge=0, le=1)
    firmness: float = Field(ge=0, le=1)
    teasing: float = Field(ge=0, le=1)


class FormatBlock(BaseModel):
    min_sentences: int = Field(ge=2, le=6)
    max_sentences: int = Field(ge=2, le=6)
    ask_question: bool
    question_type: str


class ReplyPlan(BaseModel):
    tone: ToneBlock
    initiative: float = Field(ge=0, le=1)
    depth: float = Field(ge=0, le=1)
    format: FormatBlock
    safety_mode: bool
    topic_injection: bool
    topic_seed: str


def build_character_history_key(user_id: str, character_id: str) -> str:
    return f"history:{user_id}:{character_id}"


def _conv_lock(conv_key: str) -> threading.Lock:
    with _LOCKS_GUARD:
        if conv_key not in _LOCKS:
            _LOCKS[conv_key] = threading.Lock()
        return _LOCKS[conv_key]


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _stable_rand(conv_key: str, round_id: int) -> float:
    src = f"{conv_key}:{round_id}:{SECRET_SALT}"
    seed = int(hashlib.sha256(src.encode("utf-8")).hexdigest(), 16)
    return random.Random(seed).random()


def check_sensitive(text: str):
    for word in SENSITIVE_WORDS:
        if word in text:
            if word in ["自杀", "自残"]:
                return True, "生命宝贵！心理援助热线：12320（全国）"
            return True, "内容包含违规词，请换个说法"
    return False, ""


def load_system_prompt(user_info: dict, character_id: Optional[str] = None) -> str:
    default_prompt = "你是一个温柔但真实的人，先承接用户当轮输入，再给出具体回应。"
    ip = character_id or user_info.get("ip_name")
    if not ip:
        return default_prompt
    filename = IP_PROMPT_MAP.get(ip)
    if not filename:
        if character_id:
            raise ValueError(f"unknown_character_id: {character_id}")
        return default_prompt
    path = os.path.join(os.path.dirname(__file__), "characters", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _json_call(messages: list[dict], temperature: float = 0) -> str:
    payload = {"model": DEEPSEEK_MODEL, "messages": messages, "stream": False, "temperature": temperature}
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def analyze_emotion(history_text: str, user_input: str) -> EmotionAnalysis:
    base_prompt = (
        "你是对话分析器。输出严格 JSON，字段必须完整。"
        "topic_seeds 2-4条且每条<=12字。不得输出任何额外文本。"
    )
    user_prompt = f"history:\n{history_text}\n\ninput:\n{user_input}"
    messages = [{"role": "system", "content": base_prompt}, {"role": "user", "content": user_prompt}]
    for idx in range(2):
        try:
            text = _json_call(messages, temperature=0)
            return EmotionAnalysis.model_validate_json(text)
        except Exception:
            if idx == 0:
                messages.append({"role": "system", "content": "你必须输出严格 JSON。"})
    return EmotionAnalysis(
        emotion=EmotionBlock(valence=0, arousal=0.35, stability=0.6),
        intent="general_talk",
        conversation_health=HealthBlock(stall=0.2, clarity=0.5, energy=0.5),
        risk=RiskBlock(self_harm=0, violence=0, sexual=0),
        continuation_need=0.3,
        topic_seeds=[],
        do_not=[],
        facts_to_carry=[],
    )


def _pick_topic(character_id: str, analysis: EmotionAnalysis, user_input: str) -> str:
    if analysis.topic_seeds:
        return analysis.topic_seeds[0]
    bank = TOPIC_BANK.get(character_id or "", ["今天最想说的事"])
    idx = abs(hash(user_input)) % len(bank)
    return bank[idx]


def plan_reply(analysis: EmotionAnalysis, character_id: Optional[str], conv_key: str, round_id: int, user_input: str) -> ReplyPlan:
    bias = ROLE_BIAS.get(character_id or "", ROLE_BIAS["suwan"])
    p = _clamp(0.12 + analysis.continuation_need * 0.75, 0, 0.88)
    negative_emotion = analysis.emotion.valence < -0.2 or analysis.risk.self_harm >= 0.35
    topic_injection = (analysis.conversation_health.stall > 0.55) and (not negative_emotion) and (_stable_rand(conv_key, round_id) < p)
    topic_seed = _pick_topic(character_id or "", analysis, user_input)

    tone = ToneBlock(
        warmth=_clamp((bias["warmth"][0] + bias["warmth"][1]) / 2 + analysis.emotion.valence * 0.08, 0, 1),
        calmness=_clamp((bias["calmness"][0] + bias["calmness"][1]) / 2 + analysis.emotion.stability * 0.1, 0, 1),
        firmness=_clamp((bias["firmness"][0] + bias["firmness"][1]) / 2 + analysis.conversation_health.clarity * 0.08, 0, 1),
        teasing=_clamp((bias["teasing"][0] + bias["teasing"][1]) / 2, 0, 1),
    )

    risk_peak = max(analysis.risk.self_harm, analysis.risk.violence, analysis.risk.sexual)
    ask_question = analysis.conversation_health.stall > 0.35 or topic_injection
    q_type = "open" if analysis.conversation_health.clarity < 0.6 else "reflect"

    return ReplyPlan(
        tone=tone,
        initiative=_clamp((bias["initiative"][0] + bias["initiative"][1]) / 2, 0, 1),
        depth=_clamp((bias["depth"][0] + bias["depth"][1]) / 2, 0, 1),
        format=FormatBlock(min_sentences=2, max_sentences=6, ask_question=ask_question, question_type=q_type),
        safety_mode=risk_peak >= 0.6,
        topic_injection=topic_injection,
        topic_seed=topic_seed,
    )


def _normalize_turns(history: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for item in history[-16:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            normalized.append({"role": role, "content": content})
            continue
        user_text = str(item.get("user_text", "")).strip()
        assistant_text = str(item.get("assistant_text", "")).strip()
        if user_text:
            normalized.append({"role": "user", "content": user_text})
        if assistant_text:
            normalized.append({"role": "assistant", "content": assistant_text})
    return normalized


def _build_dialog_messages(history: list[dict], user_input: str) -> list[dict]:
    messages = _normalize_turns(history)
    messages.append({"role": "user", "content": user_input})
    if os.getenv("DEBUG_CHAT") == "1":
        print("[DEBUG_CHAT] last_messages=")
        for m in messages[-5:]:
            preview = m.get("content", "")[:30].replace("\n", " ")
            print(f" - role={m.get('role')} content={preview}")
    return messages


def generate_draft(system_prompt: str, history: list[dict], user_input: str, plan: ReplyPlan, analysis: EmotionAnalysis) -> str:
    control = {
        "topic_injection": plan.topic_injection,
        "topic_seed": plan.topic_seed,
        "ask_question": plan.format.ask_question,
        "question_type": plan.format.question_type,
        "do_not": analysis.do_not,
    }
    dialog_messages = _build_dialog_messages(history, user_input)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": "先承接本轮输入；禁止括号动作；避免套话；120-180字。主动提话题仅能放在末尾1句轻提问，不要自嗨开场。"},
        {"role": "system", "content": f"CONTROL={json.dumps(control, ensure_ascii=False)}"},
        *dialog_messages,
    ]
    return _json_call(messages, temperature=0.7)


def rewrite_voice(draft_text: str, system_prompt: str, plan: ReplyPlan) -> str:
    style = {
        "tone": plan.tone.model_dump(),
        "initiative": plan.initiative,
        "depth": plan.depth,
        "format": plan.format.model_dump(),
        "topic_injection": plan.topic_injection,
        "topic_seed": plan.topic_seed,
    }
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": "重写为角色口吻。禁止（...）动作。只允许1个问题。禁止硬转场词。"},
        {"role": "system", "content": f"PLAN={json.dumps(style, ensure_ascii=False)}"},
        {"role": "user", "content": draft_text},
    ]
    return _json_call(messages, temperature=0.6)


def _is_negative_user_input(user_input: str) -> bool:
    return any(re.search(pattern, user_input) for pattern in NEGATIVE_USER_PATTERNS)


def post_guard(text: str, safety_mode: bool, user_input: str = "") -> str:
    out = re.sub(r"（[^）]*）", "", text)
    out = re.sub(r"\([^\)]*\)", "", out)
    sentences = re.split(r"(?<=[。！？!?])", out)
    cleaned = []
    for sent in sentences:
        s = sent.strip()
        if not s:
            continue
        if any(b in s for b in FILLER_BLACKLIST):
            continue
        if safety_mode:
            s = s.replace("必须", "尽量").replace("只能", "可以先")
        cleaned.append(s)
    final = "".join(cleaned).strip()
    if _is_negative_user_input(user_input):
        final = final.lstrip("，。！？!? ")
        if any(final.startswith(prefix) for prefix in SELF_DISCLOSURE_OPENERS) or not final.startswith("你"):
            final = "你现在最难受的是哪一块？你愿意先从最卡住你的那件事说起吗？"
        if "？" not in final and "?" not in final:
            final = f"你现在最需要我先听哪一部分？{final}"
    return final or "我在听，你可以继续说。"


def _history_to_text(history: list[dict]) -> str:
    rows = []
    for item in history[-16:]:
        role = item.get("role")
        if role not in {"user", "assistant"}:
            continue
        rows.append(f"{role}: {item.get('content', '')}")
    return "\n".join(rows)


def _chunk_text(text: str) -> Generator[str, None, None]:
    step = 8
    for i in range(0, len(text), step):
        yield text[i : i + step]
        time.sleep(STREAM_DELAY)


def stream_chat_with_deepseek(user_id: str, user_input: str, character_id: Optional[str] = None) -> Generator[str, None, None]:
    unsafe, warning = check_sensitive(user_input)
    if unsafe:
        yield from _chunk_text(warning)
        return

    conv_key = f"{user_id}:{character_id or 'default'}"
    lock = _conv_lock(conv_key)

    with lock:
        user_info = load_user_data(user_id)
        history_map = user_info.get("character_histories", {})
        if character_id:
            history_key = build_character_history_key(user_id, character_id)
            history = history_map.get(history_key, history_map.get(character_id, []))
        else:
            history_key = "history"
            history = user_info.get("history", [])
        rounds = user_info.setdefault("conversation_rounds", {})
        round_id = int(rounds.get(conv_key, 0)) + 1
        rounds[conv_key] = round_id

        history_text = _history_to_text(history)
        system_prompt = load_system_prompt(user_info, character_id)
        analysis = analyze_emotion(history_text, user_input)
        plan = plan_reply(analysis, character_id, conv_key, round_id, user_input)

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": ""})
        assistant_index = len(history) - 1
        if character_id:
            user_info.setdefault("character_histories", {})[history_key] = history[-MAX_HISTORY * 2 :]
        else:
            user_info["history"] = history[-MAX_HISTORY * 2 :]
        save_user_data(user_id, user_info)

    try:
        draft = generate_draft(system_prompt, history, user_input, plan, analysis)
        rewritten = rewrite_voice(draft, system_prompt, plan)
        final_text = post_guard(rewritten, plan.safety_mode, user_input)
    except Exception:
        final_text = "对话服务暂时波动，我们继续聊刚才那件事。"

    yield from _chunk_text(final_text)

    with lock:
        user_info = load_user_data(user_id)
        if character_id:
            history = user_info.setdefault("character_histories", {}).get(history_key, [])
        else:
            history = user_info.get("history", [])
        if assistant_index < len(history):
            history[assistant_index]["content"] = final_text
        if character_id:
            user_info.setdefault("character_histories", {})[history_key] = history[-MAX_HISTORY * 2 :]
        else:
            user_info["history"] = history[-MAX_HISTORY * 2 :]
        save_user_data(user_id, user_info)
