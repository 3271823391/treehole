from __future__ import annotations

from core.schemas import ReplyPlan

PLUS_DISABLE_PHRASES = [
    "根据你的描述",
    "作为AI",
    "建议你",
    "你需要做的是",
    "首先",
    "其次",
]

PRO_DISABLE_PHRASES = [
    "根据你的描述",
    "作为AI",
    "建议你",
    "你需要做的是",
    "首先",
    "其次",
    "请保持冷静",
    "可以尝试",
    "从专业角度",
]

TREEHOLE_PLUS_HINT = "语气温和、口语化，像真实朋友陪聊；避免条目式输出，避免说教。"
TREEHOLE_PRO_HINT = "强口语波动、更像真人，不要客服腔；先共情再轻推一小步，结尾自然追问。"
PRO_OUTPUT_FORMAT_RULE = "输出必须严格为：<REPLY>可见回复</REPLY><STATE>{\"bond_delta\":int,\"memory_add\":[string]}</STATE>"


def _plan_block(plan: ReplyPlan, tier: str) -> str:
    disable_phrases = PRO_DISABLE_PHRASES if tier == "pro" else PLUS_DISABLE_PHRASES
    tone = "treehole-pro" if tier == "pro" else "treehole-plus"
    return (
        "[CONTROL_BLOCK]\n"
        f"warmth={plan.warmth:.2f}\n"
        f"calmness={plan.calmness:.2f}\n"
        f"firmness={plan.firmness:.2f}\n"
        f"verbosity={plan.verbosity:.2f}\n"
        f"safety_mode={str(plan.safety_mode).lower()}\n"
        f"style_flags={','.join(plan.style_flags)}\n"
        f"tone={tone}\n"
        f"disable_phrases={','.join(disable_phrases)}"
    )


def build_treehole_messages(
    system_prompt: str,
    plan: ReplyPlan,
    history_text: str,
    user_input: str,
    tier: str,
    memory_nuggets: list[str],
    bond_level: int,
) -> list[dict]:
    hint = TREEHOLE_PRO_HINT if tier == "pro" else TREEHOLE_PLUS_HINT
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": _plan_block(plan, tier)},
    ]

    if tier == "pro":
        hints = [hint, PRO_OUTPUT_FORMAT_RULE]
        if memory_nuggets:
            hints.append("可自然吸收这些长期记忆，不要列表复述：" + "；".join(memory_nuggets[-8:]))
        hints.append(f"关系亲密度 bond_level={bond_level}，亲近但不过界。")
        messages.append({"role": "system", "content": "\n".join(hints)})
    else:
        messages.append({"role": "system", "content": hint})

    messages.append({"role": "user", "content": f"历史对话:\n{history_text}\n\n本轮用户输入:\n{user_input}"})
    return messages
