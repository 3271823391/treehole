from __future__ import annotations

from core.schemas import EmotionAnalysis, ReplyPlan


EMA_ALPHA = 0.65


def _clamp(v: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, v))


def _ema(current: float, prev: float | None) -> float:
    if prev is None:
        return current
    return prev * (1 - EMA_ALPHA) + current * EMA_ALPHA


def compute_plan(
    analysis: EmotionAnalysis,
    character_bias: dict[str, float] | None = None,
    last_plan: ReplyPlan | None = None,
) -> ReplyPlan:
    calmness = 0.55 + analysis.anxiety * 0.35 + analysis.anger * 0.20
    warmth = 0.55 + max(0.0, -analysis.valence) * 0.25 + analysis.sadness * 0.2
    verbosity = 0.45 + analysis.sadness * 0.15 - analysis.anger * 0.15
    firmness = 0.30 + analysis.anger * 0.25
    empathy = 0.65 + analysis.sadness * 0.2 + analysis.anxiety * 0.1
    directness = 0.50 + analysis.anger * 0.1

    safety_mode = analysis.risk_self_harm >= 0.35
    if safety_mode:
        firmness = max(firmness, 0.55)
        warmth = max(warmth, 0.7)

    bias = character_bias or {}
    calmness += bias.get("calmness", 0.0)
    warmth += bias.get("warmth", 0.0)
    verbosity += bias.get("verbosity", 0.0)
    firmness += bias.get("firmness", 0.0)
    empathy += bias.get("empathy", 0.0)
    directness += bias.get("directness", 0.0)

    plan = ReplyPlan(
        calmness=_clamp(_ema(calmness, last_plan.calmness if last_plan else None)),
        warmth=_clamp(_ema(warmth, last_plan.warmth if last_plan else None)),
        verbosity=_clamp(_ema(verbosity, last_plan.verbosity if last_plan else None)),
        firmness=_clamp(_ema(firmness, last_plan.firmness if last_plan else None)),
        empathy=_clamp(_ema(empathy, last_plan.empathy if last_plan else None)),
        directness=_clamp(_ema(directness, last_plan.directness if last_plan else None)),
        safety_mode=safety_mode,
        style_flags=["short_paragraphs", "concrete_support"],
        banned_phrases=["作为AI", "作为一个AI", "不能保证"],
    )
    if safety_mode:
        plan.style_flags.append("safety_first")
        plan.banned_phrases.extend(["你只能", "离不开我"])
    return plan
