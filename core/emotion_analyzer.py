from __future__ import annotations

import json

from core.llm_client import llm_complete
from core.schemas import EmotionAnalysis


class EmotionAnalyzerError(Exception):
    pass


_ANALYSIS_SYSTEM = (
    "你是情绪分析器。输出必须是严格 JSON，不要 markdown，不要额外文字。"
    "字段: intent,valence,arousal,anxiety,anger,sadness,risk_self_harm,risk_violence,summary。"
)


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def analyze_emotion(history_text: str, user_text: str) -> EmotionAnalysis:
    prompt = (
        f"历史对话:\n{history_text}\n\n"
        f"用户本轮输入:\n{user_text}\n"
        "请给出情绪/意图/风险评分，评分范围 0~1，valence 范围 -1~1。"
    )
    messages = [
        {"role": "system", "content": _ANALYSIS_SYSTEM},
        {"role": "user", "content": prompt},
    ]

    last_error: Exception | None = None
    for _ in range(2):
        try:
            raw = llm_complete(messages, temperature=0.0)
            data = _extract_json(raw)
            return EmotionAnalysis.model_validate(data)
        except Exception as exc:
            last_error = exc

    raise EmotionAnalyzerError(f"emotion_analyzer_failed: {last_error}")
