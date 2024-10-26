from fastapi import FastAPI, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random
import string
from datetime import datetime, timedelta
from models import ActivationCode, APIResponse  # 添加 APIResponse 的导入
from database import get_db, engine
from typing import Optional
import logging
from fastapi.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import settings
import logging.handlers
from auth import verify_api_key
import sqlalchemy
from uuid import uuid4

import models

# 日志配置
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

# 创建限流器
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Activation Code API",
    description="API for generating and validating activation codes",
    version="1.0.0"
)

# 加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActivationCodeCreate(BaseModel):
    product_type: str
    price: float

class ActivationCodeResponse(BaseModel):
    id: str
    activation_code: str
    product_type: str
    created_at: datetime
    price: float
    expiry: datetime
    used: bool
    used_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True

    @property
    def remaining_days(self) -> int:
        return (self.expiry - datetime.now()).days

class ActivationRequest(BaseModel):
    code: str
    product_type: str

# 添加新的路由组
from fastapi import APIRouter

# 创建两个路由组
admin_router = APIRouter(prefix="/admin", tags=["admin"])
client_router = APIRouter(tags=["client"])

# 管理端 API（需要 API Key）
@admin_router.post("/generate", response_model=APIResponse)
async def generate_activation_code(
    request: ActivationCodeCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    code = generate_code()
    logger.info(f"Generated activation code: {code} for product type: {request.product_type}")
    
    db_code = ActivationCode(
        code=code,
        product_type=request.product_type,
        price=request.price,
        used=False
    )
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    
    data = ActivationCodeResponse(
        id=str(db_code.id),
        activation_code=db_code.code,
        product_type=db_code.product_type,
        price=db_code.price,
        expiry=db_code.expiry,
        created_at=db_code.created_at,
        used=db_code.used,
        used_at=db_code.used_at,
        status="active"
    )
    
    return APIResponse(
        success=True,
        message="Activation code generated successfully",
        data=data
    )

class CodeStatusResponse(BaseModel):
    code: str
    product_type: str
    status: str  # 'valid', 'used', 'expired'
    used: bool
    used_at: Optional[datetime]
    expiry: datetime
    remaining_days: Optional[int]
    price: float

@admin_router.get("/status/{code}", response_model=APIResponse[CodeStatusResponse])
async def check_code_status(
    code: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_code = db.query(models.ActivationCode).filter(
        models.ActivationCode.code == code
    ).first()
    
    if not db_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Code not found"
        )
    
    status_value = 'expired' if datetime.now() > db_code.expiry else (
        'used' if db_code.used else 'valid'
    )
    
    return APIResponse(
        success=True,
        message="Code status retrieved successfully",
        data=CodeStatusResponse(
            code=db_code.code,
            product_type=db_code.product_type,
            status=status_value,
            used=db_code.used,
            used_at=db_code.used_at,
            expiry=db_code.expiry,
            remaining_days=(db_code.expiry - datetime.now()).days if not db_code.used else 0,
            price=db_code.price
        )
    )

class ValidationResponse(BaseModel):
    code: str
    status: str
    product_type: str
    price: float
    validated_at: datetime
    message: str

@client_router.post("/validate", response_model=APIResponse[ValidationResponse])
async def validate_activation_code(
    request: ActivationRequest,
    db: Session = Depends(get_db)
):
    try:
        db_code = db.query(models.ActivationCode).filter(
            models.ActivationCode.code == request.code,
            models.ActivationCode.product_type == request.product_type
        ).first()
        
        if not db_code:
            raise create_error_response(
                status.HTTP_404_NOT_FOUND,
                "Invalid activation code for this product"
            )
        
        if datetime.now() > db_code.expiry:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "Activation code has expired"
            )
        
        if db_code.used:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "Activation code has already been used"
            )
        
        # 标记为已使用
        db_code.used = True
        db_code.used_at = datetime.now()
        db.commit()
        
        logger.info(f"Validated and used code: {request.code}")
        return APIResponse(
            success=True,
            message="Activation code validated successfully",
            data=ValidationResponse(
                code=db_code.code,
                status="activated",
                product_type=db_code.product_type,
                price=db_code.price,
                validated_at=datetime.now(),
                message="Code successfully activated"
            ),
            request_id=str(uuid4())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error"
        )

# 注册路由组
app.include_router(admin_router)
app.include_router(client_router)

@app.get("/health")
async def health_check():
    try:
        # 验证数据库连接
        with engine.connect() as connection:
            connection.execute(sqlalchemy.text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )

# 在路由定义之前添加这个函数
def create_error_response(status_code: int, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=APIResponse(
            success=False,
            message=message,
            request_id=str(uuid4())
        ).dict()
    )

# 在文件开头的导入部分下面添加这个函数
def generate_code(length: int = 15) -> str:
    """
    生成指定长度的随机激活码
    :param length: 激活码长度，默认15位
    :return: 生成的激活码字符串
    """
    # 使用大写字母和数字
    characters = string.ascii_uppercase + string.digits
    # 生成随机字符串
    code = ''.join(random.choices(characters, k=length))
    return code
