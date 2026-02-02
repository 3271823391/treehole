import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Optional, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse

PIN_MIN_LEN = 4
PIN_MAX_LEN = 6
TOKEN_EXPIRE_SECONDS = 12 * 60 * 60
PBKDF2_ITERATIONS = 120_000
USER_ID_SHA1_PATTERN = re.compile(r"^u_[0-9a-f]{40}$", re.IGNORECASE)
USER_ID_UUID_PATTERN = re.compile(
    r"^u_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def make_user_id(username: str) -> str:
    norm = normalize_username(username)
    digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()
    return f"u_{digest}"


def is_valid_user_id(user_id: str) -> bool:
    if not isinstance(user_id, str):
        return False
    if not user_id:
        return False
    return bool(USER_ID_SHA1_PATTERN.match(user_id) or USER_ID_UUID_PATTERN.match(user_id))


def validate_pin(pin: str) -> Tuple[bool, str]:
    if not isinstance(pin, str):
        return False, "pin_invalid"
    if not pin.isdigit():
        return False, "pin_digits_only"
    if not (PIN_MIN_LEN <= len(pin) <= PIN_MAX_LEN):
        return False, "pin_length"
    return True, ""


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return "pbkdf2_sha256$%s$%s$%s" % (
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("utf-8").rstrip("="),
        base64.urlsafe_b64encode(dk).decode("utf-8").rstrip("="),
    )


def verify_pin(pin: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        algo, iter_str, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = _b64url_decode(salt_b64)
        expected = _b64url_decode(hash_b64)
    except Exception:
        return False

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(dk, expected)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(user_id: str, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"user_id": user_id, "iat": now, "exp": now + TOKEN_EXPIRE_SECONDS}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_token(token: str, secret: str) -> Tuple[Optional[dict], str]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        return None, "token_format"

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(_b64url_encode(expected_signature), signature_b64):
        return None, "token_signature"

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None, "token_payload"

    if payload.get("exp") and int(payload["exp"]) < int(time.time()):
        return None, "token_expired"

    return payload, ""


def get_auth_secret() -> Optional[str]:
    return os.getenv("AUTH_SECRET")


def unauthorized_response(msg: str = "unauthorized", status_code: int = 401) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"ok": False, "msg": msg})


def verify_token_from_request(request: Request) -> Tuple[Optional[str], Optional[JSONResponse]]:
    secret = get_auth_secret()
    if not secret:
        return None, unauthorized_response("auth_secret_missing", status_code=500)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, unauthorized_response()

    token = auth_header.replace("Bearer ", "", 1).strip()
    if not token:
        return None, unauthorized_response()

    payload, err = decode_token(token, secret)
    if not payload or err:
        return None, unauthorized_response()

    user_id = payload.get("user_id")
    if not user_id:
        return None, unauthorized_response()

    return user_id, None
