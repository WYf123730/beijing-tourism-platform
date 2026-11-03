"""
安全模块
提供 JWT 令牌生成/验证、密码加密/验证功能
使用 python-jose + bcrypt
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings

security = HTTPBearer()


# ==================== 密码加密 ====================

def hash_password(password: str) -> str:
    """使用 bcrypt 对明文密码进行加密"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与加密密码是否匹配"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ==================== JWT 令牌 ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    Args:
        data: 要编码的数据（通常包含用户ID）
        expires_delta: 过期时间（默认使用配置中的120分钟）
    Returns:
        JWT 令牌字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    解码 JWT 令牌
    Args:
        token: JWT 令牌字符串
    Returns:
        解码后的 payload 字典
    Raises:
        HTTPException: 令牌无效或过期
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """
    从请求头中提取当前用户 ID（依赖注入）
    用于需要登录认证的接口
    """
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="令牌中缺少用户信息")
    return int(user_id)
