from __future__ import annotations

from core.schemas import ReplyPlan


def render_history_text(summary: str, history: list[dict], limit_rounds: int = 12) -> str:
    lines: list[str] = []
    if summary:
        lines.append(f"summary: {summary}")
    recent = history[-(limit_rounds * 2) :]
    for item in recent:
        role = item.get("role", "user")
        content = item.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _plan_block(plan: ReplyPlan) -> str:
    banned = "不要机械复述,不要模板化安慰,不要空洞大道理"
    return (
        "[CONTROL_BLOCK]\n"
        f"warmth={plan.warmth:.2f}\n"
        f"calmness={plan.calmness:.2f}\n"
        f"firmness={plan.firmness:.2f}\n"
        f"verbosity={plan.verbosity:.2f}\n"
        f"safety_mode={str(plan.safety_mode).lower()}\n"
        f"style_flags={','.join(plan.style_flags)}\n"
        f"disable_phrases={banned}"
    )


def build_messages(system_prompt: str, plan: ReplyPlan, history_text: str, user_input: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": _plan_block(plan)},
        {"role": "user", "content": f"历史对话:\n{history_text}\n\n本轮用户输入:\n{user_input}"},
    ]
