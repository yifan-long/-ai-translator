from fastapi import FastAPI
from app.api.routes import history, translate

app = FastAPI(
    title="Translation API",
    version="1.0",
    description="A simple translation API",
)


@app.on_event("startup")
async def startup_event():
    print("ai翻译已经启动")

app.include_router(translate.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "AI 在线翻译 API 已启动", "status": "ok"}





