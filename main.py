from config import HOST, PORT
from routers import page, customize, chat
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="DeepSeek虚拟树洞（精致版）")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

print("STATIC DIR EXISTS:", os.path.exists(STATIC_DIR))
print("STATIC ABS PATH:", STATIC_DIR)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)

from routers import page, customize, chat
app.include_router(page.router)
app.include_router(customize.router)
app.include_router(chat.router)

def run_api():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    run_api()
