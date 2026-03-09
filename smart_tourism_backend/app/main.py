from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect

from app.api import routes_public, routes_admin, routes_auth, routes_realtime
from app.api.routes_ai import router as routes_ai
from app.config import settings
from app.db.session import engine
from app.models.common import Base
from app.models import user, poi, itinerary  # noqa: F401  注册模型
from app.services.websocket_service import manager, websocket_endpoint


app = FastAPI(
    title="Smart Cultural Tourism Platform",
    version="0.1.0",
    description="Multi-Agent based cultural tourism management backend",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """应用启动时自动创建数据库表（基于 SQLite）。"""
    Base.metadata.create_all(bind=engine)


@app.get("/")
def healthcheck() -> dict:
    return {"status": "ok", "docs": "/docs", "openapi": "/openapi.json"}


# WebSocket端点
@app.websocket("/ws/{user_id}")
async def websocket_connect(websocket: WebSocket, user_id: int):
    """WebSocket连接端点"""
    await websocket_endpoint(websocket, user_id)


# 获取连接状态
@app.get("/api/v1/ws/status")
async def ws_status():
    """获取WebSocket连接状态"""
    return {
        "connected_users": len(manager.get_connected_users()),
        "users": list(manager.get_connected_users()),
    }


app.include_router(routes_auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(routes_public.router, prefix="/api/v1/public", tags=["public"])
app.include_router(routes_admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(
    routes_realtime.router, prefix="/api/v1/realtime", tags=["realtime"]
)
app.include_router(routes_ai, prefix="/api/v1/ai", tags=["AI & LLM"])

