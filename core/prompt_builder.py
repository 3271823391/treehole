from __future__ import annotations

from core.schemas import ReplyPlan


def build_plan_block(plan: ReplyPlan, topic_injection: bool = False, topic_seed: str = "") -> str:
    return (
        "[REPLY_CONTROL]\n"
        f"warmth={plan.warmth:.2f}\n"
        f"calmness={plan.calmness:.2f}\n"
        f"firmness={plan.firmness:.2f}\n"
        f"verbosity={plan.verbosity:.2f}\n"
        f"empathy={plan.empathy:.2f}\n"
        f"directness={plan.directness:.2f}\n"
        f"safety_mode={str(plan.safety_mode).lower()}\n"
        f"style_flags={','.join(plan.style_flags)}\n"
        f"ban_phrases={','.join(plan.banned_phrases)}\n"
        f"topic_injection={str(topic_injection).lower()}\n"
        f"topic_seed={topic_seed}\n"
        "rule_if_topic_injection=true: 在回复末尾追加1句自然延展提问，必须与topic_seed或当前话题相关，"
        "禁止使用硬转场词（如“对了”“另外”）。"
    )


def build_messages(
    system_prompt: str,
    plan: ReplyPlan,
    history_text: str,
    current_input: str,
    topic_injection: bool = False,
    topic_seed: str = "",
) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": build_plan_block(plan, topic_injection, topic_seed)},
        {
            "role": "user",
            "content": f"对话历史:\n{history_text}\n\n用户本轮输入:\n{current_input}",
        },
    ]
