from datetime import datetime
from core.modes import MODES


def get_active_mode(user_info: dict) -> str:
    expire = user_info.get("plan_expire_at")
    if not expire:
        return "plus"

    try:
        if datetime.fromisoformat(expire) < datetime.utcnow():
            return "plus"
    except Exception:
        return "plus"

    active_plan = user_info.get("active_plan", "plus")
    return active_plan if active_plan in MODES else "plus"


def get_features(user_info: dict) -> dict:
    mode = get_active_mode(user_info)
    return MODES.get(mode, MODES["plus"])["features"]
