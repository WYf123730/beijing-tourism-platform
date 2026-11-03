"""
数据库会话模块
使用 SQLAlchemy 2.0 异步模式管理 MySQL 数据库连接和会话
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger("travel_platform")


# ==================== 引擎 ====================
# 注意：aiomysql 0.3.2 + SQLAlchemy 2.0.43 在某些Python版本上
# 可能存在 ping() 兼容性问题，如果遇到相关错误，将 pool_pre_ping 改为 False
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=False,  # 设为 False 避免 aiomysql ping 兼容性问题
)


# ==================== 会话工厂 ====================
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ==================== 声明式基类 ====================
class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类，所有模型继承此类"""
    pass


# ==================== 获取会话（依赖注入） ====================
async def get_db() -> AsyncSession:
    """FastAPI 依赖注入 —— 获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库表，在应用启动时调用"""
    async with engine.begin() as conn:
        import models  # noqa: F401 — 确保所有模型类被加载到 Base.metadata
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表初始化完成 ✓")
