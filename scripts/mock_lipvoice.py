import base64

from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="Mock LipVoice")

_SILENT_WAV = base64.b64decode(
    "UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA="
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/third/reference/upload")
async def upload_reference(file: UploadFile):
    # 读取文件以模拟真实行为（避免空文件导致上游异常）
    await file.read()
    return JSONResponse(
        content={"code": 0, "data": {"audioId": "audio_mock_123"}}
    )


@app.post("/api/third/tts")
async def tts():
    return Response(content=_SILENT_WAV, media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9001, log_level="info")
