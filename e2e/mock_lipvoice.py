import io
import os
import wave

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response

app = FastAPI()


def build_silent_wav(duration_s: float = 0.4, sample_rate: int = 16000) -> bytes:
    frames = int(duration_s * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()


@app.post("/api/third/reference/upload")
async def upload_reference_audio(
    file: UploadFile = File(...),
    name: str = Form(...),
    describe: str = Form(""),
):
    content = await file.read()
    if not content:
        return JSONResponse(status_code=400, content={"code": 1, "msg": "empty_file"})
    return {
        "code": 0,
        "data": {
            "audioId": "mock-audio-id",
            "name": name,
            "describe": describe,
        },
    }


@app.post("/api/third/tts")
async def tts(payload: dict):
    payload = payload or {}
    text = (payload.get("text") or "").strip()
    audio_id = (payload.get("audioId") or "").strip()
    if not text or not audio_id:
        return JSONResponse(status_code=400, content={"code": 1, "msg": "invalid_payload"})

    wav_bytes = build_silent_wav()
    return Response(content=wav_bytes, media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MOCK_LIPVOICE_PORT", "9001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
