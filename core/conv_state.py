from __future__ import annotations

from core.schemas import ConversationState
from data_store import load_user_data, save_user_data


CONV_STATE_KEY = "conv_states"


def _state_validate(raw: dict) -> ConversationState:
    if hasattr(ConversationState, "model_validate"):
        return ConversationState.model_validate(raw)
    return ConversationState.parse_obj(raw)


def _state_dump(state: ConversationState) -> dict:
    if hasattr(state, "model_dump"):
        return state.model_dump()
    return state.dict()


def make_conv_key(user_id: str, device_id: str, character_id: str | None) -> str:
    return f"{user_id}:{device_id}:{character_id or 'default'}"


def load_state(user_id: str, conv_key: str) -> ConversationState | None:
    user_info = load_user_data(user_id)
    raw = user_info.get(CONV_STATE_KEY, {}).get(conv_key)
    if not raw:
        return None
    return _state_validate(raw)


def save_state(user_id: str, state: ConversationState) -> None:
    user_info = load_user_data(user_id)
    conv_states = user_info.setdefault(CONV_STATE_KEY, {})
    conv_states[state.conv_key] = _state_dump(state)
    save_user_data(user_id, user_info)


def ensure_state(user_id: str, conv_key: str) -> ConversationState:
    state = load_state(user_id, conv_key)
    if state is not None:
        return state
    state = ConversationState(conv_key=conv_key)
    save_state(user_id, state)
    return state


def next_round_id(state: ConversationState) -> int:
    state.round_seq += 1
    return state.round_seq
