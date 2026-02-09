import base64
import hashlib
import hmac
import os
import time
from fastapi import Request, Response

SESSION_COOKIE_NAME = "treehole_session"
SESSION_MAX_AGE = 7 * 24 * 3600


def get_session_secret() -> str:
    return os.getenv("SESSION_SECRET", "treehole-dev-session-secret")


def _sign(payload: str) -> str:
    return hmac.new(get_session_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_cookie(user_id: str) -> str:
    ts = str(int(time.time()))
    raw = f"{user_id}|{ts}"
    return base64.urlsafe_b64encode(f"{raw}|{_sign(raw)}".encode()).decode()


def get_current_user_id(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    if not token:
        return ""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, ts, sig = raw.split("|", 2)
        payload = f"{user_id}|{ts}"
        if not hmac.compare_digest(_sign(payload), sig):
            return ""
        if int(time.time()) - int(ts) > SESSION_MAX_AGE:
            return ""
        return user_id.strip()
    except Exception:
        return ""


def set_session_cookie(response: Response, user_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_cookie(user_id),
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
