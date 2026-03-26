from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, history
from app.database import engine, Base

# 创建FastAPI应用实例
app = FastAPI(title="AI对话助手API", version="1.0.0")

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api", tags=["聊天"])
app.include_router(history.router, prefix="/api", tags=["历史记录"])

# 启动时创建数据库表
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 根路径
@app.get("/")
async def root():
    return {"message": "AI对话助手API服务已启动"}
