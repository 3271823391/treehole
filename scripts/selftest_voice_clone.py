import os
import subprocess
import sys
import time

import requests
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from data_store import load_user_data
from main import app


def wait_for_mock(url: str, timeout: float = 5.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            res = requests.get(url, timeout=1)
            if res.ok:
                return
        except requests.RequestException:
            time.sleep(0.1)
    raise RuntimeError("mock_lipvoice_start_failed")


def main() -> int:
    env = os.environ.copy()
    env.update(
        {
            "LIPVOICE_BASE_URL": "http://127.0.0.1:9001",
            "LIPVOICE_SIGN": "mock",
            "LIPVOICE_TTS_PATH": "/api/third/tts",
            "E2E_TEST_MODE": "1",
        }
    )
    os.environ.update(env)

    mock_proc = subprocess.Popen(
        [sys.executable, "scripts/mock_lipvoice.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_mock("http://127.0.0.1:9001/health")
        client = TestClient(app)
        user_id = "u_e2e_voice_clone"

        upload_resp = client.post(
            "/api/voice_clone/reference/upload",
            data={
                "name": "e2e",
                "describe": "mock",
                "user_id": user_id,
            },
            files={"file": ("ref.wav", b"fake-audio", "audio/wav")},
        )
        if upload_resp.status_code != 200:
            print("upload_failed", upload_resp.status_code, upload_resp.text)
            return 1
        upload_data = upload_resp.json()
        if not upload_data.get("ok") or upload_data.get("data", {}).get("audioId") != "audio_mock_123":
            print("upload_invalid_response", upload_data)
            return 1

        user_info = load_user_data(user_id)
        audio_id = user_info.get("voice_clone", {}).get("audioId")
        if audio_id != "audio_mock_123":
            print("user_data_not_updated", user_info)
            return 1

        tts_resp = client.post(
            "/api/voice_clone/tts",
            json={"user_id": user_id, "text": "测试语音"},
        )
        content_type = tts_resp.headers.get("content-type", "")
        if tts_resp.status_code != 200 or "audio/" not in content_type:
            print("tts_failed", tts_resp.status_code, content_type, tts_resp.text)
            return 1

        print("selftest_voice_clone_ok")
        return 0
    except Exception as exc:
        print("selftest_exception", exc)
        return 1
    finally:
        mock_proc.terminate()
        try:
            mock_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            mock_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
