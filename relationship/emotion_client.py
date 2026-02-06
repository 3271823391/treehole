import json
import os
from typing import Any

import requests

DEEPSEEK_EMOTION_URL = "https://api.deepseek.com/chat/completions"
ALLOWED_SIGNALS = {
    "boundary_pressure",
    "dependency_attempt",
    "emotional_support",
    "conflict_pattern",
    "stable_interaction",
    "neutral_interaction",
}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}

SYSTEM_PROMPT = """你是关系信号标注器，只负责从多轮对话中识别关系信号。
只输出 JSON，不要解释，不要安慰。


允许的 signals：
- boundary_pressure
- dependency_attempt
- emotional_support
- conflict_pattern
- stable_interaction
- neutral_interaction


confidence 只能是 low / medium / high


输出示例：
{
  \"signals\": [\"stable_interaction\"],
  \"confidence\": \"medium\"
}"""


def _fallback() -> dict:
    return {
        "signals": ["neutral_interaction"],
        "confidence": "low",
    }


def _normalize_result(raw: Any) -> dict:
    if not isinstance(raw, dict):
        return _fallback()

    signals = raw.get("signals")
    confidence = raw.get("confidence")

    if not isinstance(signals, list) or not signals:
        return _fallback()

    normalized_signals = []
    for s in signals:
        if not isinstance(s, str) or s not in ALLOWED_SIGNALS:
            return _fallback()
        normalized_signals.append(s)

    if not isinstance(confidence, str) or confidence not in ALLOWED_CONFIDENCE:
        return _fallback()

    return {
        "signals": normalized_signals,
        "confidence": confidence,
    }


def analyze_relationship(character_id: str, character_name: str, messages: list[dict]) -> dict:
    api_key = os.getenv("DEEPSEEK_EMOTION_API_KEY", "").strip()
    if not api_key:
        return _fallback()

    user_prompt = {
        "character_id": character_id,
        "character_name": character_name,
        "messages": messages,
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ],
        "stream": False,
        "temperature": 0,
        "max_tokens": 120,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            DEEPSEEK_EMOTION_URL,
            headers=headers,
            json=payload,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        content = (((data.get("choices") or [{}])[0]).get("message") or {}).get("content", "")
        if not content:
            return _fallback()
        parsed = json.loads(content)
        return _normalize_result(parsed)
    except Exception:
        return _fallback()
