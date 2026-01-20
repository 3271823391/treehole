from fastapi import FastAPI
from config import HOST, PORT
from routers import page, customize, chat

app = FastAPI(title="DeepSeek虚拟树洞（精致版）")

app.include_router(page.router)
app.include_router(customize.router)
app.include_router(chat.router)

def run_api():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    run_api()
