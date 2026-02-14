import os
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from chat_core import IP_PROMPT_MAP, build_character_history_key, check_sensitive
from config import MAX_HISTORY
from core.auth_utils import is_valid_user_id
from core.characters import get_character_bias, get_character_system_prompt
from core.conv_state import ensure_state, make_conv_key, next_round_id, save_state
from core.emotion_analyzer import EmotionAnalyzerError, analyze_emotion
from core.guards import enforce_reply
from core.llm_client import llm_stream
from core.lock_manager import get_lock
from core.prompt_builder import build_messages as build_pipeline_messages, render_history_text
from core.response_planner import compute_plan
from core.schemas import EmotionAnalysis, TurnRecord
from data_store import load_user_data, save_user_data

router = APIRouter()


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


@router.post("/chat_stream")
async def chat_stream(req: ChatStreamRequest, request: Request):
    user_id = req.user_id.strip()
    if not user_id:
        return JSONResponse(status_code=400, content={"ok": False, "msg": "missing_user_id"})
    if not is_valid_user_id(user_id):
        return JSONResponse(status_code=400, content={"ok": False, "msg": "invalid_user_id"})

    user_input = req.user_input.strip()
    character_id = (req.character_id or "").strip() or None
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

    device_id = (req.device_id or "").strip() or "default"
    conv_key = make_conv_key(user_id, device_id, character_id)
    lock = get_lock(conv_key)

    async with lock:
        state = ensure_state(user_id, conv_key)
        history_map = user_info.get("character_histories", {})
        if character_id:
            history_key = build_character_history_key(user_id, character_id)
            history = history_map.get(history_key, history_map.get(character_id, []))
        else:
            history = user_info.get("history", [])

        history_text = render_history_text(state.summary, history, limit_rounds=12)

        analysis_error = None
        try:
            analysis = analyze_emotion(history_text, user_input)
        except EmotionAnalyzerError as exc:
            analysis_error = str(exc)
            analysis = EmotionAnalysis(intent="venting", summary="fallback-neutral", error=analysis_error)

        last_plan = state.turns[-1].plan if state.turns else None
        plan = compute_plan(analysis, get_character_bias(character_id), last_plan)

        round_id = next_round_id(state)
        state.turns.append(
            TurnRecord(
                round_id=round_id,
                user_text=user_input,
                assistant_text="",
                analysis=analysis,
                plan=plan,
                error=analysis_error,
            )
        )
        save_state(user_id, state)

    system_prompt = get_character_system_prompt(user_info, character_id)
    messages = build_pipeline_messages(system_prompt, plan, history_text, user_input)

    async def pipeline_stream():
        full_reply = ""
        try:
            for delta in llm_stream(messages):
                if delta:
                    full_reply += delta
                    yield delta
                    time.sleep(0.01)
        except Exception:
            full_reply = "（对话异常，请稍后再试）"
            for c in full_reply:
                yield c
                time.sleep(0.01)

        final_text = enforce_reply(full_reply, safety_mode=plan.safety_mode)

        async with lock:
            user_info_latest = load_user_data(user_id)
            history_map_latest = user_info_latest.get("character_histories", {})
            if character_id:
                history_key_latest = build_character_history_key(user_id, character_id)
                history_latest = history_map_latest.get(history_key_latest, history_map_latest.get(character_id, []))
                history_latest.append({"role": "user", "content": user_input})
                history_latest.append({"role": "assistant", "content": final_text})
                user_info_latest.setdefault("character_histories", {})[history_key_latest] = history_latest[-MAX_HISTORY * 2 :]
            else:
                history_latest = user_info_latest.get("history", [])
                history_latest.append({"role": "user", "content": user_input})
                history_latest.append({"role": "assistant", "content": final_text})
                user_info_latest["history"] = history_latest[-MAX_HISTORY * 2 :]
            save_user_data(user_id, user_info_latest)

            state_latest = ensure_state(user_id, conv_key)
            for idx, record in enumerate(state_latest.turns):
                if record.round_id == round_id:
                    state_latest.turns[idx].assistant_text = final_text
                    break
            save_state(user_id, state_latest)

    return StreamingResponse(pipeline_stream(), media_type="text/plain")


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
