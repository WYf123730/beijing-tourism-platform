"""
中间件模块
配置 CORS、请求日志等中间件
"""
import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

logger = logging.getLogger("travel_platform")


def setup_middleware(app: FastAPI):
    """配置所有中间件"""

    # ==================== CORS 跨域配置 ====================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源（开发环境）
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有 HTTP 方法
        allow_headers=["*"],  # 允许所有请求头
    )

    # ==================== 请求耗时日志中间件 ====================
    @app.middleware("http")
    async def log_request_time(request: Request, call_next):
        """记录每个请求的处理耗时"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"- 状态码: {response.status_code} "
            f"- 耗时: {process_time:.3f}s"
        )
        return response
