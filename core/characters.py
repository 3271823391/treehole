from __future__ import annotations

from chat_core import IP_PROMPT_MAP, load_system_prompt


CHARACTER_BIAS = {
    "linyu": {"warmth": 0.05, "calmness": 0.1, "firmness": -0.05, "verbosity": 0.05},
    "suwan": {"warmth": 0.08, "calmness": 0.05, "firmness": -0.03, "verbosity": 0.02},
    "xiaxingmian": {"warmth": -0.03, "calmness": 0.02, "firmness": 0.1, "verbosity": -0.05},
    "jiangche": {"warmth": 0.03, "calmness": 0.0, "firmness": 0.05, "verbosity": 0.03},
    "jiangan": {"warmth": 0.06, "calmness": 0.04, "firmness": -0.02, "verbosity": 0.02},
}


def get_character_bias(character_id: str | None) -> dict[str, float]:
    if not character_id:
        return {"warmth": 0.0, "calmness": 0.0, "firmness": 0.0, "verbosity": 0.0}
    return CHARACTER_BIAS.get(character_id, {"warmth": 0.0, "calmness": 0.0, "firmness": 0.0, "verbosity": 0.0})


def get_character_system_prompt(user_info: dict, character_id: str | None) -> str:
    return load_system_prompt(user_info, character_id)


def known_character(character_id: str | None) -> bool:
    return bool(character_id) and character_id in IP_PROMPT_MAP
