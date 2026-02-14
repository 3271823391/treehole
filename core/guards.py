from __future__ import annotations

import re

from core.schemas import ReplyPlan


FORBIDDEN = ["作为AI", "作为一个AI"]
SAFETY_SUPPRESS = ["你只能", "离不开我", "必须听我的"]


def _limit_sentences(text: str, min_count: int = 2, max_count: int = 6) -> str:
    parts = [p.strip() for p in re.split(r"(?<=[。！？!?])", text) if p.strip()]
    if not parts:
        return text.strip()
    if len(parts) > max_count:
        return "".join(parts[:max_count])
    if len(parts) < min_count:
        return text.strip() + " 我会一直在这里陪你。"
    return "".join(parts)


def enforce_reply(text: str, plan: ReplyPlan) -> str:
    clean = text
    for w in FORBIDDEN + plan.banned_phrases:
        clean = clean.replace(w, "")
    if plan.safety_mode:
        for w in SAFETY_SUPPRESS:
            clean = clean.replace(w, "")
    clean = _limit_sentences(clean)
    return clean.strip()
