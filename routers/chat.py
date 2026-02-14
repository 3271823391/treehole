import logging
import os
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from chat_core import IP_PROMPT_MAP, build_character_history_key, check_sensitive
from core.auth_utils import is_valid_user_id
from core.characters import get_character_bias, get_character_system_prompt
from core.conv_state import build_conv_key, ensure_state, load_state, next_round_id, save_state
from core.emotion_analyzer import EmotionAnalyzeError, analyze_emotion, default_analysis
from core.guards import enforce_reply
from core.llm_client import llm_stream
from core.lock_manager import get_conv_lock
from core.prompt_builder import build_messages
from core.response_planner import compute_plan, should_inject_topic
from core.schemas import ConversationState, TurnRecord
from core.topic_seeds import pick_topic_seed
from data_store import load_user_data, save_user_data

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/greeting")
def greeting(user_id: str, request: Request):
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_info = load_user_data(user_id)
    save_user_data(user_id, user_info)

    if user_info.get("has_greeted"):
        return {"text": ""}

    text = "我在这里，你可以慢慢说。"

    user_info["has_greeted"] = True
    user_info.setdefault("history", []).append({"role": "assistant", "content": text})
    save_user_data(user_id, user_info)

    return {"text": text}


class ChatStreamRequest(BaseModel):
    user_id: str
    user_input: str
    character_id: str | None = None
    device_id: str | None = None


def _render_history_text(state: ConversationState, max_turns: int = 12) -> str:
    lines = []
    if state.summary:
        lines.append(f"summary: {state.summary}")
    for turn in state.turns[-max_turns:]:
        lines.append(f"user: {turn.user_text}")
        if turn.assistant_text:
            lines.append(f"assistant: {turn.assistant_text}")
    return "\n".join(lines)


@router.post("/chat_stream")
async def chat_stream(req: ChatStreamRequest, request: Request):
    user_id = req.user_id.strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_input = req.user_input.strip()
    character_id = (req.character_id or "").strip() or None
    device_id = (req.device_id or "").strip() or "default"
    if character_id and character_id not in IP_PROMPT_MAP:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_character_id"})

    user_info = load_user_data(user_id)
    save_user_data(user_id, user_info)
    if os.getenv("E2E_TEST_MODE") == "1":

        def e2e_stream():
            message = "你好。测试回复。"
            for ch in message:
                yield ch
                time.sleep(0.01)

        return StreamingResponse(e2e_stream(), media_type="text/plain")

    if not user_info.get("system_prompt"):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_system_prompt"})

    unsafe, warning = check_sensitive(user_input)
    if unsafe:

        def warning_stream():
            for c in warning:
                yield c
                time.sleep(0.01)

        return StreamingResponse(warning_stream(), media_type="text/plain")

    conv_character_id = character_id or "default"
    conv_key = build_conv_key(user_id, device_id, conv_character_id)

    lock = await get_conv_lock(conv_key)
    async with lock:
        state = ensure_state(user_id, device_id, conv_character_id)
        history_text = _render_history_text(state)
        error_msg = ""
        try:
            analysis = analyze_emotion(history_text, user_input)
        except EmotionAnalyzeError as exc:
            analysis = default_analysis()
            error_msg = f"analyze_failed:{exc}"
            logger.warning(error_msg)

        plan = compute_plan(
            analysis=analysis,
            character_bias=get_character_bias(character_id),
            last_plan=state.last_plan,
        )
        round_id = next_round_id(state)
        state.last_plan = plan
        state.turns.append(
            TurnRecord(
                round_id=round_id,
                user_text=user_input,
                assistant_text="",
                analysis=analysis,
                plan=plan,
                error=error_msg,
                created_at=time.time(),
            )
        )
        save_state(user_id, state)
        system_prompt = get_character_system_prompt(user_info, character_id)
        topic_injection = should_inject_topic(conv_key, round_id, analysis.continuation_need)
        topic_seed = pick_topic_seed(character_id, analysis.topic_seeds)
        messages = build_messages(
            system_prompt,
            plan,
            history_text,
            user_input,
            topic_injection=topic_injection,
            topic_seed=topic_seed,
        )

    async def pipeline_stream():
        raw_reply = ""
        try:
            for delta in llm_stream(messages):
                if delta:
                    raw_reply += delta
        except Exception:
            raw_reply = "（对话异常，请稍后再试）"

        final_text = enforce_reply(raw_reply, plan)
        for ch in final_text:
            yield ch
            time.sleep(0.01)

        await _save_final_text(user_id, device_id, conv_character_id, round_id, final_text)

    return StreamingResponse(pipeline_stream(), media_type="text/plain")


async def _save_final_text(user_id: str, device_id: str, character_id: str, round_id: int, final_text: str) -> None:
    conv_key = build_conv_key(user_id, device_id, character_id)
    lock = await get_conv_lock(conv_key)
    async with lock:
        state = ensure_state(user_id, device_id, character_id)
        for turn in state.turns:
            if turn.round_id == round_id:
                turn.assistant_text = final_text
                break
        save_state(user_id, state)


@router.get("/load_history")
def load_history(request: Request, user_id: str, character_id: str = ""):
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_info = load_user_data(user_id)
    save_user_data(user_id, user_info)
    character_id = (character_id or "").strip()
    if character_id:
        if character_id not in IP_PROMPT_MAP:
            return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_character_id"})
        history_key = build_character_history_key(user_id, character_id)
        history_map = user_info.get("character_histories", {})
        history = history_map.get(history_key, history_map.get(character_id, []))
    else:
        history = user_info.get("history", [])
    return {"ok": True, "history": history}


@router.get("/api/chat/history")
def chat_history(user_id: str, character_id: str, device_id: str = "default", limit: int = 50):
    user_id = user_id.strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    character_id = (character_id or "").strip() or "default"
    if character_id != "default" and character_id not in IP_PROMPT_MAP:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_character_id"})

    device_id = (device_id or "").strip() or "default"
    max_turns = max(1, min(limit or 50, 200))

    conv_key = build_conv_key(user_id, device_id, character_id)
    state = load_state(user_id, conv_key)
    turns = state.turns[-max_turns:] if state else []
    messages = []
    for turn in turns:
        if turn.user_text:
            messages.append({"role": "user", "content": turn.user_text})
        if turn.assistant_text:
            messages.append({"role": "assistant", "content": turn.assistant_text})
    return {"ok": True, "messages": messages}
