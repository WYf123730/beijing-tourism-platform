"""
北京市文旅景点服务平台 —— FastAPI 后端主入口
FastAPI + SQLAlchemy 2.0 异步模式 + MySQL
包含用户认证、景点管理、空间查询、路径规划、综合分析、天气服务

启动方式: uvicorn app:app --reload --port 8001
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from api import ai as ai_api
from api import analysis as analysis_api
from api import query as query_api
from api import route as route_api
from api import scenic as scenic_api
from api import seed as seed_api
from api import user as user_api
from api import weather as weather_api
from config import settings
from core.exceptions import global_exception_handler
from core.middleware import setup_middleware
from database import init_db
from services.weather_task import setup_weather_scheduler


# ==================== 日志配置 ====================
def setup_logging():
    """配置全局日志：控制台输出 + 文件轮转"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiomysql").setLevel(logging.WARNING)

    return logging.getLogger("travel_platform")


logger = setup_logging()


# ==================== 应用生命周期 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库表和天气定时任务"""
    logger.info("北京市文旅景点服务平台启动中...")
    # 初始化数据库表
    await init_db()
    # 启动天气定时任务
    scheduler = setup_weather_scheduler()
    yield
    # 关闭调度器
    if scheduler:
        scheduler.shutdown()
    logger.info("北京市文旅景点服务平台已停止")


# ==================== 创建应用实例 ====================
app = FastAPI(
    title="北京市文旅景点服务平台 - 后端 API",
    description="""
    基于 FastAPI + SQLAlchemy + MySQL 的北京市文旅景点服务平台

    ## 功能模块
    - 👤 **用户模块**: 注册、登录(JWT)、个人信息管理
    - 🏞️ **景点 GIS 模块**: 景点 CRUD、关键词搜索、附近景点查询
    - 📍 **空间查询模块**: POI点/矩形/圆形/多边形范围查询
    - 🗺️ **路径规划模块**: 驾车路径规划、旅行商分析、公交换乘
    - 🔍 **综合分析模块**: 缓冲区分析、叠置分析（救援信息）
    - 🌤️ **天气模块**: 城市天气查询、景区天气展示（定时更新）

    ## 技术栈
    - FastAPI (异步 Web 框架)
    - SQLAlchemy 2.0 (异步 ORM)
    - MySQL + aiomysql (数据库)
    - Shapely (空间几何计算)
    - 高德地图 Web API (地理编码/天气/路径规划)
    - JWT + bcrypt (认证安全)
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==================== 注册中间件 ====================
setup_middleware(app)


# ==================== 注册全局异常处理器 ====================
app.add_exception_handler(Exception, global_exception_handler)


# ==================== 注册路由 ====================
app.include_router(user_api.router)
app.include_router(scenic_api.router)
app.include_router(seed_api.router)
app.include_router(query_api.router)
app.include_router(route_api.router)
app.include_router(analysis_api.router)
app.include_router(weather_api.router)
app.include_router(ai_api.router)

# ==================== 挂载前端静态文件 ====================
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "前端")
if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"前端静态文件已挂载: {frontend_dir} → /app")


# ==================== 根路由 ====================
@app.get("/", summary="服务状态")
async def root():
    """直接跳转到前端页面"""
    return RedirectResponse(url="/app/")


# ==================== 启动入口 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.SERVER_PORT,
        reload=True,
        log_level="info",
    )
