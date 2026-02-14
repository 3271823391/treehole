from __future__ import annotations

from data_store import load_user_data, save_user_data
from core.schemas import ConversationState


def build_conv_key(user_id: str, device_id: str, character_id: str) -> str:
    return f"{user_id}:{device_id}:{character_id}"


def load_state(user_id: str, conv_key: str) -> ConversationState | None:
    user_info = load_user_data(user_id)
    states = user_info.get("conversation_states", {})
    raw = states.get(conv_key)
    if not raw:
        return None
    return ConversationState.model_validate(raw)


def save_state(user_id: str, state: ConversationState) -> None:
    user_info = load_user_data(user_id)
    states = user_info.setdefault("conversation_states", {})
    states[state.conv_key] = state.model_dump()
    save_user_data(user_id, user_info)


def ensure_state(user_id: str, device_id: str, character_id: str) -> ConversationState:
    conv_key = build_conv_key(user_id, device_id, character_id)
    state = load_state(user_id, conv_key)
    if state is not None:
        return state
    state = ConversationState(
        conv_key=conv_key,
        user_id=user_id,
        device_id=device_id,
        character_id=character_id,
    )
    save_state(user_id, state)
    return state


def next_round_id(state: ConversationState) -> int:
    state.round_seq += 1
    return state.round_seq
