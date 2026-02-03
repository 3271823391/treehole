import os
import pathlib
import wave

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]


def ensure_test_wav(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 1600)


def run():
    base_url = os.getenv("E2E_BASE_URL", "http://127.0.0.1:8000")
    wav_path = ROOT / "e2e_assets" / "voice.wav"
    ensure_test_wav(wav_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{base_url}/treehole_pro", wait_until="domcontentloaded")

        page.fill("#login-username", "e2e_user")
        page.press("#login-username", "Tab")

        page.click("#voice-output-toggle")

        page.click("[data-voice-clone-trigger]")
        page.set_input_files("#voice-clone-file", str(wav_path))
        page.fill("#voice-clone-name", "E2E Voice")
        page.click("#voice-clone-action")
        page.wait_for_selector("#voice-clone-status.success", timeout=10000)

        def is_tts_audio(res):
            if not res.url.startswith(f"{base_url}/api/voice_clone/tts/audio"):
                return False
            content_type = res.headers.get("content-type", "")
            return res.status == 200 and content_type.startswith("audio/")

        page.fill("#msg-input", "你好，来一段语音测试。")
        page.click("#send-btn")

        page.wait_for_event("response", predicate=is_tts_audio, timeout=15000)

        browser.close()


if __name__ == "__main__":
    run()
