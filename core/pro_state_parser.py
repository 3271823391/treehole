from __future__ import annotations

import json


def split_reply_and_state(text: str) -> tuple[str, dict | None]:
    reply_text = text
    state_dict = None

    reply_start = text.find("<REPLY>")
    reply_end = text.find("</REPLY>")
    if reply_start != -1 and reply_end != -1 and reply_end > reply_start:
        reply_text = text[reply_start + len("<REPLY>") : reply_end].strip()

    state_start = text.find("<STATE>")
    state_end = text.find("</STATE>")
    if state_start != -1 and state_end != -1 and state_end > state_start:
        state_text = text[state_start + len("<STATE>") : state_end].strip()
        try:
            parsed = json.loads(state_text)
            if isinstance(parsed, dict):
                state_dict = parsed
        except Exception:
            state_dict = None

    return reply_text, state_dict


def apply_treehole_state(user_info: dict, state: dict) -> None:
    profile = user_info.setdefault("treehole_profile", {})
    bond_points = int(profile.get("bond_points", 0))
    memory_nuggets = profile.get("memory_nuggets", [])
    if not isinstance(memory_nuggets, list):
        memory_nuggets = []

    bond_delta = state.get("bond_delta", 0)
    if isinstance(bond_delta, (int, float)):
        bond_points += int(bond_delta)
    if bond_points < 0:
        bond_points = 0

    for item in state.get("memory_add", []):
        if isinstance(item, str):
            stripped = item.strip()
            if stripped and stripped not in memory_nuggets:
                memory_nuggets.append(stripped)

    profile["bond_points"] = bond_points
    if bond_points < 10:
        profile["bond_level"] = 0
    elif bond_points < 40:
        profile["bond_level"] = 1
    else:
        profile["bond_level"] = 2
    profile["memory_nuggets"] = memory_nuggets[-20:]
