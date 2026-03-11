"""FastAPI 应用入口"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings
from app.tasks.scheduler import start_scheduler, stop_scheduler

# 路由
from app.wechat.callback import router as wechat_router
from app.accounts.router import router as accounts_router
from app.content.router import router as content_router
from app.materials.router import router as materials_router
from app.analytics.router import router as analytics_router
from app.schedule.router import router as schedule_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name}")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Application shutdown")


app = FastAPI(
    title="公众号矩阵管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(wechat_router)
app.include_router(accounts_router)
app.include_router(content_router)
app.include_router(materials_router)
app.include_router(analytics_router)
app.include_router(schedule_router)


# 健康检查
@app.get("/api/system/health")
async def health_check():
    return {"status": "ok"}


# 前端静态文件（Vite build 产物）
import os

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback — 所有非 API/wechat 路由返回 index.html"""
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
