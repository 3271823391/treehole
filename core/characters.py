from __future__ import annotations

from chat_core import IP_PROMPT_MAP, load_system_prompt


CHARACTER_BIAS: dict[str, dict[str, float]] = {
    "linyu": {"warmth": 0.05, "verbosity": 0.05},
    "suwan": {"calmness": 0.08, "firmness": -0.03},
    "xiaxingmian": {"warmth": 0.08, "verbosity": 0.08},
    "jiangche": {"directness": 0.08, "firmness": 0.06},
    "jiangan": {"calmness": 0.05, "empathy": 0.05},
}


def get_character_system_prompt(user_info: dict, character_id: str | None) -> str:
    return load_system_prompt(user_info, character_id)


def get_character_bias(character_id: str | None) -> dict[str, float]:
    if not character_id:
        return {}
    if character_id not in IP_PROMPT_MAP:
        return {}
    return CHARACTER_BIAS.get(character_id, {})
