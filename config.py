from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    POSTGRES_URL: str
    POSTGRES_PRISMA_URL: str
    POSTGRES_URL_NON_POOLING: str
    POSTGRES_URL_NO_SSL: str
    POSTGRES_USER: str
    POSTGRES_HOST: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_RATE_LIMIT: str = "5/minute"
    CODE_EXPIRY_DAYS: int = 180
    # 添加 API Key 配置
    API_KEY: str = secrets.token_urlsafe(32)  # 如果环境变量中没有，则生成随机值
    API_KEY_NAME: str = "X-API-Key"
    
    # 计算 DATABASE_URL
    @property
    def DATABASE_URL(self) -> str:
        return self.POSTGRES_URL.replace('postgres://', 'postgresql://', 1)

    # 添加Vercel Postgres配置
    POSTGRES_URL: str
    POSTGRES_PRISMA_URL: str
    POSTGRES_URL_NON_POOLING: str
    POSTGRES_USER: str
    POSTGRES_HOST: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str

    # 添加数据库连接池配置
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    # 添加 DEBUG 配置
    DEBUG: bool = False  # 默认为 False，可以通过环境变量覆盖

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
