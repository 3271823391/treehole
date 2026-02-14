from __future__ import annotations

from core.schemas import EmotionAnalysis, ReplyPlan


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def compute_plan(
    analysis: EmotionAnalysis,
    character_bias: dict[str, float],
    last_plan: ReplyPlan | None,
) -> ReplyPlan:
    warmth = 0.65 + (0.2 if analysis.sadness > 0.5 else 0.0) - (0.1 if analysis.anger > 0.6 else 0.0)
    calmness = 0.6 + analysis.anxiety * 0.3 + analysis.anger * 0.2
    firmness = 0.35 + analysis.anger * 0.2
    verbosity = 0.45 + (0.15 if analysis.intent in {"venting", "support"} else 0.0)

    safety_mode = analysis.risk_self_harm >= 0.35
    style_flags = ["reflective"]
    if safety_mode:
        style_flags.append("safety")
        firmness = min(firmness, 0.5)

    warmth = _clamp(warmth + character_bias.get("warmth", 0.0))
    calmness = _clamp(calmness + character_bias.get("calmness", 0.0))
    firmness = _clamp(firmness + character_bias.get("firmness", 0.0))
    verbosity = _clamp(verbosity + character_bias.get("verbosity", 0.0))

    plan = ReplyPlan(
        warmth=warmth,
        calmness=calmness,
        firmness=firmness,
        verbosity=verbosity,
        safety_mode=safety_mode,
        style_flags=style_flags,
    )

    if last_plan is None:
        return plan

    alpha = 0.6
    return ReplyPlan(
        warmth=_clamp(alpha * plan.warmth + (1 - alpha) * last_plan.warmth),
        calmness=_clamp(alpha * plan.calmness + (1 - alpha) * last_plan.calmness),
        firmness=_clamp(alpha * plan.firmness + (1 - alpha) * last_plan.firmness),
        verbosity=_clamp(alpha * plan.verbosity + (1 - alpha) * last_plan.verbosity),
        safety_mode=plan.safety_mode,
        style_flags=plan.style_flags,
    )
