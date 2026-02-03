import argparse
import os
import sys

import requests


def classify_failure(payload: dict | None) -> str:
    if not payload:
        return "unknown"
    msg = payload.get("msg") or ""
    detail = payload.get("detail") or {}
    reason = detail.get("reason") if isinstance(detail, dict) else ""
    stage = detail.get("stage") if isinstance(detail, dict) else ""
    if msg == "lipvoice_sign_missing":
        return "sign_missing"
    if msg == "missing_audio_id":
        return "missing_audio_id"
    if reason == "poll_timeout":
        return "poll_timeout"
    if reason == "status_failed":
        return "upstream_status_failed"
    if stage == "create":
        return "create_failed"
    if stage == "poll":
        return "poll_failed"
    if stage == "fetch":
        return "fetch_failed"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="LipVoice TTS self-check script")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--user-id", default=os.getenv("USER_ID"))
    args = parser.parse_args()

    if not args.user_id:
        print("ERROR: --user-id or USER_ID env is required.")
        return 1

    base_url = args.base_url.rstrip("/")
    print(f"BASE_URL={base_url}")
    print(f"USER_ID={args.user_id}")

    debug_url = f"{base_url}/api/voice_clone/debug_get_audio_id"
    debug_resp = requests.get(debug_url, params={"user_id": args.user_id}, timeout=10)
    print(f"[debug_get_audio_id] status={debug_resp.status_code}")
    if debug_resp.headers.get("content-type", "").startswith("application/json"):
        debug_data = debug_resp.json()
        print(f"[debug_get_audio_id] ok={debug_data.get('ok')} audioId={debug_data.get('audioId')}")
    else:
        print(f"[debug_get_audio_id] body={debug_resp.text[:200]}")

    tts_url = f"{base_url}/api/voice_clone/tts"
    tts_resp = requests.post(
        tts_url,
        json={"user_id": args.user_id, "text": "你好"},
        timeout=60
    )
    body = tts_resp.content or b""
    content_type = tts_resp.headers.get("content-type", "")
    print(f"[tts] status={tts_resp.status_code}")
    print(f"[tts] content-type={content_type}")
    print(f"[tts] content-length={len(body)}")
    print(f"[tts] first-16-bytes-hex={body[:16].hex()}")

    if tts_resp.status_code != 200 or "audio/" not in content_type or len(body) <= 1000:
        payload = None
        if content_type.startswith("application/json"):
            try:
                payload = tts_resp.json()
            except ValueError:
                payload = None
        classification = classify_failure(payload)
        print(f"[tts] assertion_failed classification={classification}")
        if payload:
            print(f"[tts] payload={payload}")
        return 1

    print("tts_selfcheck_ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
