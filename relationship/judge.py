from datetime import datetime, timedelta

POSITIVE_SCORES = {
    "stable_interaction": {"high": 0.9, "medium": 0.6, "low": 0.2},
    "emotional_support": {"high": 0.5, "medium": 0.3, "low": 0.1},
}

NEGATIVE_SCORES = {
    "boundary_pressure": {"high": -1.8, "medium": -1.1, "low": -0.5},
    "dependency_attempt": {"high": -1.4, "medium": -0.9, "low": -0.4},
    "conflict_pattern": {"high": -1.2, "medium": -0.7, "low": -0.3},
}

NEGATIVE_PRIORITY = ["boundary_pressure", "dependency_attempt", "conflict_pattern"]
POSITIVE_PRIORITY = ["stable_interaction", "emotional_support"]


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _now() -> datetime:
    return datetime.now()


def evaluate_affinity_delta(
    state: dict,
    signals: list[str],
    confidence: str
) -> tuple[float, str]:
    delta = 0.0
    notes: list[str] = []

    risk_buffer = state.setdefault("risk_buffer", {
        "boundary_pressure": 0,
        "dependency_attempt": 0,
        "conflict_pattern": 0,
        "updated_at": None,
    })

    now = _now()
    updated_at = _parse_iso(risk_buffer.get("updated_at"))
    if updated_at and (now - updated_at) > timedelta(days=7):
        for signal in NEGATIVE_SCORES:
            risk_buffer[signal] = 0

    negative_signal = next((s for s in NEGATIVE_PRIORITY if s in signals), None)
    positive_signal = next((s for s in POSITIVE_PRIORITY if s in signals), None)

    if negative_signal:
        state["stable_streak"] = 0
        if confidence == "high":
            delta += NEGATIVE_SCORES[negative_signal]["high"]
            notes.append(f"high_negative:{negative_signal}")
        else:
            risk_buffer[negative_signal] = int(risk_buffer.get(negative_signal, 0)) + 1
            risk_buffer["updated_at"] = now.isoformat(timespec="seconds")
            count = risk_buffer[negative_signal]
            if count >= 2:
                delta += NEGATIVE_SCORES[negative_signal]["medium"]
                risk_buffer[negative_signal] = 0
                notes.append(f"buffer_trigger:{negative_signal}")
            else:
                notes.append(f"buffer_accumulate:{negative_signal}:{count}")
    else:
        if positive_signal:
            delta += POSITIVE_SCORES[positive_signal][confidence]
            notes.append(f"positive:{positive_signal}")

        if "stable_interaction" in signals:
            state["stable_streak"] = int(state.get("stable_streak", 0)) + 1
            streak = state["stable_streak"]
            reward_map = {4: 1.0, 9: 2.0, 15: 3.0}
            reward = reward_map.get(streak, 0)
            if reward > 0:
                last_reward_at = _parse_iso(state.get("last_streak_reward_at"))
                if (not last_reward_at) or (now - last_reward_at) >= timedelta(hours=72):
                    delta += reward
                    state["last_streak_reward_at"] = now.isoformat(timespec="seconds")
                    notes.append(f"streak_reward:{streak}")
                else:
                    notes.append("streak_reward_cooldown")
        else:
            state["stable_streak"] = 0

    current_score = float(state.get("affinity_score", 50))
    bounded = max(0.0, min(100.0, current_score + delta))
    delta = round(bounded - current_score, 2)

    return delta, ";".join(notes) or "no_change"
