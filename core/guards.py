from __future__ import annotations

import re

_BANNED_WORDS = ["自杀", "自残"]


def _limit_sentences(text: str, minimum: int = 2, maximum: int = 6) -> str:
    parts = [p.strip() for p in re.split(r"(?<=[。！？!?])", text) if p.strip()]
    if len(parts) > maximum:
        return "".join(parts[:maximum])
    if len(parts) < minimum and text.strip():
        return text.strip() + " 我在认真听你说。"
    return text


def enforce_reply(text: str, safety_mode: bool = False) -> str:
    cleaned = text
    for word in _BANNED_WORDS:
        cleaned = cleaned.replace(word, "***")
    if safety_mode:
        cleaned = cleaned.replace("控制", "尊重")
    return _limit_sentences(cleaned)
