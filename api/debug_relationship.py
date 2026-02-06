import os
from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from data_store import get_relationship_state

router = APIRouter()


def _debug_enabled() -> bool:
    return os.getenv("DEBUG_RELATIONSHIP", "0") == "1"


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


@router.get("/api/debug/relationship")
def debug_relationship(
    user_id: str = Query(...),
    character_id: str = Query(...),
):
    if not _debug_enabled():
        raise HTTPException(status_code=404, detail="Not Found")

    state = get_relationship_state(user_id, character_id)
    logs = state.get("affinity_eval_log", []) if isinstance(state, dict) else []

    recent_eval_log = logs[-10:]
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_7d = []
    for item in logs:
        ts = _parse_iso(item.get("at") if isinstance(item, dict) else None)
        if ts and ts >= seven_days_ago:
            recent_7d.append(item)

    signal_counter = Counter()
    confidence_counter = Counter()
    net_delta = 0.0
    for item in recent_7d:
        if not isinstance(item, dict):
            continue
        for signal in item.get("signals", []) or []:
            if isinstance(signal, str):
                signal_counter[signal] += 1
        confidence = item.get("confidence")
        if isinstance(confidence, str):
            confidence_counter[confidence] += 1
        try:
            net_delta += float(item.get("delta", 0))
        except Exception:
            continue

    return {
        "user_id": user_id,
        "character_id": character_id,
        "state": state,
        "recent_eval_log": recent_eval_log,
        "stats_7d": {
            "eval_count": len(recent_7d),
            "net_delta": round(net_delta, 2),
            "signals_count": dict(signal_counter),
            "confidence_count": {
                "low": confidence_counter.get("low", 0),
                "medium": confidence_counter.get("medium", 0),
                "high": confidence_counter.get("high", 0),
            },
        },
    }
