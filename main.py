from core.env import init_env
init_env()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import HOST, PORT
app = FastAPI(title="DeepSeek虚拟树洞（精致版）")

from api.chat import router as chat_router
from api.customize import router as customize_router
from api.clone import router as clone_router
from api.progress import router as progress_router

app.include_router(chat_router)
app.include_router(customize_router)
app.include_router(clone_router)
app.include_router(progress_router)

# ✅ 关键：挂载前端
app.mount("/", StaticFiles(directory="static", html=True), name="static")

def run_api():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    run_api()
