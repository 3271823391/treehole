from datetime import datetime
from core.modes import MODES

def get_active_mode(user_info: dict) -> str:
    expire = user_info.get("plan_expire_at")
    if not expire:
        return "free"

    try:
        if datetime.fromisoformat(expire) < datetime.utcnow():
            return "free"
    except Exception:
        return "free"

    return user_info.get("active_plan", "free")

def get_features(user_info: dict) -> dict:
    mode = get_active_mode(user_info)
    return MODES.get(mode, MODES["free"])["features"]