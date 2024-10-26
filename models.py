from sqlalchemy import Column, String, DateTime, Boolean, func, Float, Enum, Integer
from database import Base, engine
from datetime import datetime
import enum
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any
from datetime import timedelta

# 定义泛型类型变量
T = TypeVar('T')

class ProductType(str, enum.Enum):
    TYPE_A = "type_a"  # 可以根据实际产品类型修改
    TYPE_B = "type_b"
    TYPE_C = "type_c"

# SQLAlchemy Model
class ActivationCode(Base):
    __tablename__ = "activation_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    product_type = Column(String)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    price = Column(Float, default=0.0)
    expiry = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=180))

# API 通用响应模型 - 现在支持泛型
class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None
    request_id: Optional[str] = None

# Pydantic Models for API
class ActivationCodeBase(BaseModel):
    code: str
    product_type: str
    used: bool = False

class ActivationCodeCreate(ActivationCodeBase):
    pass

class ActivationCodeResponse(ActivationCodeBase):
    id: int
    created_at: datetime
    used_at: Optional[datetime] = None
    status: str = "active"  # 添加 status 字段
    price: float
    expiry: datetime

    class Config:
        from_attributes = True

# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine)

# 确保表被创建
create_tables()
