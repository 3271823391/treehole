from __future__ import annotations

from core.schemas import EmotionAnalysis


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _score(text: str, keywords: list[tuple[str, float]]) -> float:
    total = 0.0
    for word, weight in keywords:
        if word in text:
            total += weight
    return _clamp(total)


def quick_analyze(history_text: str, user_text: str) -> EmotionAnalysis:
    merged = f"{history_text}\n{user_text}".lower()

    sadness = _score(
        merged,
        [("难过", 0.35), ("伤心", 0.35), ("哭", 0.25), ("崩溃", 0.25), ("绝望", 0.4), ("失落", 0.25)],
    )
    anxiety = _score(
        merged,
        [("焦虑", 0.35), ("紧张", 0.25), ("害怕", 0.3), ("担心", 0.25), ("睡不着", 0.25), ("慌", 0.3)],
    )
    anger = _score(
        merged,
        [("生气", 0.35), ("愤怒", 0.4), ("烦死", 0.3), ("恶心", 0.2), ("气死", 0.35), ("讨厌", 0.2)],
    )
    risk_self_harm = _score(
        merged,
        [("不想活", 0.7), ("轻生", 0.8), ("自杀", 1.0), ("结束自己", 0.8), ("割腕", 0.8)],
    )
    risk_violence = _score(
        merged,
        [("杀了", 0.8), ("报复", 0.5), ("捅", 0.7), ("打死", 0.7), ("伤害他", 0.6)],
    )

    if any(k in user_text for k in ["怎么办", "怎么做", "要不要", "吗", "？", "?"]):
        intent = "question"
    elif any(k in user_text for k in ["安慰", "帮我", "陪我", "支持"]):
        intent = "support"
    else:
        intent = "venting"

    summary = "neutral"
    if sadness >= 0.7:
        summary = "sad-high"
    elif sadness >= 0.35:
        summary = "sad-mid"
    elif anxiety >= 0.7:
        summary = "anx-high"
    elif anxiety >= 0.35:
        summary = "anx-mid"
    elif anger >= 0.7:
        summary = "ang-high"
    elif anger >= 0.35:
        summary = "ang-mid"

    valence = _clamp(0.5 - sadness * 0.3 - anxiety * 0.2 - anger * 0.2)
    arousal = _clamp(0.2 + anxiety * 0.4 + anger * 0.4)

    return EmotionAnalysis(
        intent=intent,
        valence=valence,
        arousal=arousal,
        anxiety=anxiety,
        anger=anger,
        sadness=sadness,
        risk_self_harm=risk_self_harm,
        risk_violence=risk_violence,
        summary=summary,
    )
