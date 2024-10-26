from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from config import settings

load_dotenv()

# 修改 POSTGRES_URL 的格式
POSTGRES_URL = os.getenv('POSTGRES_URL')
if POSTGRES_URL and POSTGRES_URL.startswith('postgres://'):
    # 将 postgres:// 替换为 postgresql://
    POSTGRES_URL = POSTGRES_URL.replace('postgres://', 'postgresql://', 1)

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,  # 连接池大小
    max_overflow=10,  # 超出池大小后的最大连接数
    pool_timeout=30,  # 连接超时时间
    pool_recycle=1800,  # 连接回收时间(30分钟)
    echo=False  # 或者直接设置为 False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 获取数据库会话的依赖函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
