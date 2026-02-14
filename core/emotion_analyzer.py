from __future__ import annotations

import json

from core.llm_client import llm_complete
from core.schemas import EmotionAnalysis


class EmotionAnalyzeError(RuntimeError):
    pass


def _extract_json_block(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise EmotionAnalyzeError("json_block_not_found")
    return raw[start : end + 1]


def _build_messages(history_text: str, user_input: str) -> list[dict]:
    instruction = (
        "你是对话分析器。只输出严格 JSON，不要 markdown，不要解释。"
        "字段: sentiment, intent, arousal, valence, anxiety, anger, sadness, "
        "risk_self_harm, risk_violence, risk_abuse, notes。"
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": f"history:\n{history_text}\n\ninput:\n{user_input}"},
    ]


def analyze_emotion(history_text: str, user_input: str) -> EmotionAnalysis:
    last_err = None
    for _ in range(2):
        try:
            raw = llm_complete(_build_messages(history_text, user_input), temperature=0.0)
            payload = json.loads(_extract_json_block(raw))
            return EmotionAnalysis.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise EmotionAnalyzeError(str(last_err) if last_err else "analyze_failed")


def default_analysis() -> EmotionAnalysis:
    return EmotionAnalysis(sentiment="neutral", intent="venting")
