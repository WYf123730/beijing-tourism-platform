"""
项目核心配置模块
从 .env 文件读取配置，提供全局配置对象
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类，自动从 .env 文件读取环境变量"""

    # ==================== MySQL 数据库配置 ====================
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "Mysql@2026"
    DB_NAME: str = "travel_platform"

    # ==================== JWT 令牌配置 ====================
    SECRET_KEY: str = "default-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # ==================== 高德地图配置 ====================
    AMAP_WEB_KEY: str = ""

    # ==================== 服务端口 ====================
    SERVER_PORT: int = 8001

    # ==================== 数据库连接 URL（自动拼装） ====================
    @property
    def DATABASE_URL(self) -> str:
        """异步 MySQL 连接 URL（aiomysql 驱动）"""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局单例配置对象
settings = Settings()
