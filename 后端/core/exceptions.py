"""
全局异常处理模块
定义自定义异常类和全局异常处理器
"""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("travel_platform")


class AppException(Exception):
    """应用级自定义异常"""
    def __init__(self, code: int = 400, msg: str = "请求失败", data=None):
        self.code = code
        self.msg = msg
        self.data = data
        super().__init__(self.msg)


class NotFoundException(AppException):
    """资源不存在异常"""
    def __init__(self, msg: str = "资源不存在"):
        super().__init__(code=404, msg=msg)


class ValidationException(AppException):
    """参数校验异常"""
    def __init__(self, msg: str = "参数校验失败"):
        super().__init__(code=422, msg=msg)


class UnauthorizedException(AppException):
    """未授权异常"""
    def __init__(self, msg: str = "未授权访问"):
        super().__init__(code=401, msg=msg)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    捕获所有未被处理的异常，返回统一格式的错误响应
    """
    if isinstance(exc, AppException):
        return JSONResponse(
            status_code=exc.code,
            content={"code": exc.code, "msg": exc.msg, "data": exc.data},
        )

    logger.exception(f"未捕获的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "msg": "服务器内部错误", "data": None},
    )
