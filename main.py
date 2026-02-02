from config import HOST, PORT
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import auth, chat, emotion, page, profile, voice_clone
import os
app = FastAPI(title="DeepSeek虚拟树洞（精致版）")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
AVATAR_DIR = os.path.join(STATIC_DIR, "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)

print("STATIC DIR EXISTS:", os.path.exists(STATIC_DIR))
print("STATIC ABS PATH:", STATIC_DIR)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)
app.include_router(emotion.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(page.router)
app.include_router(chat.router)
app.include_router(voice_clone.router)

def run_api():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    run_api()
