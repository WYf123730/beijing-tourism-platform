"""
用户模块接口路由
注册、登录、用户信息管理
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user_id, hash_password, verify_password, create_access_token
from database import get_db
from models import User
from schemas import UserLogin, UserRegister, UserUpdate, ResponseModel

logger = logging.getLogger("travel_platform.api.user")
router = APIRouter(prefix="/api/user", tags=["用户模块"])


@router.post("/register", summary="用户注册")
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    注册新用户
    - username: 用户名（3-50字符，必填）
    - password: 密码（6-100字符，必填）
    - nickname: 昵称（选填）
    - email: 邮箱（选填）
    """
    try:
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_in.username, User.is_deleted == False)
        )
        if result.scalar_one_or_none():
            return ResponseModel(code=400, msg="用户名已被注册").model_dump()

        user = User(
            username=user_in.username,
            password=hash_password(user_in.password),
            nickname=user_in.nickname or user_in.username,
            email=user_in.email or "",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"新用户注册成功: {user.username}(ID={user.id})")
        return ResponseModel(data=user.to_dict(), msg="注册成功").model_dump()
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return ResponseModel(code=400, msg=str(e)).model_dump()


@router.post("/login", summary="用户登录")
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    用户登录，返回 JWT Token
    - username: 用户名
    - password: 密码
    """
    try:
        result = await db.execute(
            select(User).where(User.username == user_in.username, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(user_in.password, user.password):
            return ResponseModel(code=400, msg="用户名或密码错误").model_dump()

        access_token = create_access_token(data={"user_id": user.id, "role": user.role})
        logger.info(f"用户登录成功: {user.username}")
        return ResponseModel(data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict(),
        }, msg="登录成功").model_dump()
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return ResponseModel(code=400, msg=str(e)).model_dump()


@router.get("/info", summary="获取当前用户信息")
async def get_user_info(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户的个人信息（需登录认证）"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            return ResponseModel(code=404, msg="用户不存在").model_dump()
        return ResponseModel(data=user.to_dict()).model_dump()
    except Exception as e:
        return ResponseModel(code=401, msg=str(e)).model_dump()


@router.put("/info", summary="修改个人信息")
async def update_user_info(
    user_in: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """修改当前登录用户的个人信息（需登录认证）"""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            return ResponseModel(code=404, msg="用户不存在").model_dump()

        update_data = user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
        return ResponseModel(data=user.to_dict(), msg="修改成功").model_dump()
    except Exception as e:
        return ResponseModel(code=400, msg=str(e)).model_dump()
