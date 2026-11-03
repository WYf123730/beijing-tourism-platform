"""
景点 GIS 模块接口路由
景点 CRUD、关键词搜索、附近景点查询
"""
import json
import logging
import math
from math import asin, cos, radians, sin, sqrt
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user_id
from database import get_db
from models import Scenic
from schemas import ResponseModel, ScenicSpotCreate, ScenicSpotUpdate

logger = logging.getLogger("travel_platform.api.scenic")
router = APIRouter(prefix="/api/scenic", tags=["景点GIS模块"])


def haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Haversine 公式计算两点间距离（米）"""
    R = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return R * 2 * asin(sqrt(a))


# ==================== 景点 CRUD ====================

@router.post("/", summary="新增景点")
async def create_scenic(
    scenic_in: ScenicSpotCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """新增景点（需要登录认证）"""
    try:
        scenic = Scenic(
            name=scenic_in.name,
            description=scenic_in.description or "",
            address=scenic_in.address or "",
            longitude=scenic_in.longitude,
            latitude=scenic_in.latitude,
            category=scenic_in.category or "",
            images=json.dumps(scenic_in.images or [], ensure_ascii=False),
            phone=scenic_in.phone or "",
            open_time=scenic_in.open_time or "",
            ticket_price=scenic_in.ticket_price or "",
            rating=scenic_in.rating or 0.0,
        )
        db.add(scenic)
        await db.commit()
        await db.refresh(scenic)
        logger.info(f"新增景点: {scenic.name}(ID={scenic.id})")
        return ResponseModel(data=scenic.to_dict(), msg="新增景点成功").model_dump()
    except Exception as e:
        logger.error(f"新增景点失败: {e}")
        return ResponseModel(code=400, msg=str(e)).model_dump()


@router.get("/", summary="景点列表")
async def list_scenic(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    category: Optional[str] = Query(None, description="景点主分类过滤"),
    subcategory: Optional[str] = Query(None, description="景点子分类过滤"),
    db: AsyncSession = Depends(get_db),
):
    """获取景点列表（分页、支持关键字搜索和分类过滤）"""
    conditions = [Scenic.is_deleted == False]
    if keyword:
        conditions.append(Scenic.name.like(f"%{keyword}%"))
    if category:
        conditions.append(Scenic.category == category)
    if subcategory:
        conditions.append(Scenic.subcategory == subcategory)

    # 查询总数
    count_query = select(func.count(Scenic.id)).where(*conditions)
    result_count = await db.execute(count_query)
    total = result_count.scalar() or 0

    # 分页查询
    query = (
        select(Scenic)
        .where(*conditions)
        .offset((page - 1) * size)
        .limit(size)
        .order_by(Scenic.created_at.desc())
    )
    result = await db.execute(query)
    spots = result.scalars().all()

    return {
        "code": 200,
        "msg": "获取成功",
        "data": [s.to_dict() for s in spots],
        "total": total,
        "page": page,
        "page_size": size,
    }


@router.get("/{scenic_id}", summary="景点详情")
async def get_scenic(scenic_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个景点详细信息"""
    result = await db.execute(
        select(Scenic).where(Scenic.id == scenic_id, Scenic.is_deleted == False)
    )
    scenic = result.scalar_one_or_none()
    if not scenic:
        return ResponseModel(code=404, msg="景点不存在").model_dump()
    return ResponseModel(data=scenic.to_dict()).model_dump()


@router.put("/{scenic_id}", summary="修改景点")
async def update_scenic(
    scenic_id: int,
    scenic_in: ScenicSpotUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """修改景点信息（需要登录认证）"""
    try:
        result = await db.execute(
            select(Scenic).where(Scenic.id == scenic_id, Scenic.is_deleted == False)
        )
        scenic = result.scalar_one_or_none()
        if not scenic:
            return ResponseModel(code=404, msg="景点不存在").model_dump()

        update_data = scenic_in.model_dump(exclude_unset=True)
        if "images" in update_data and update_data["images"] is not None:
            update_data["images"] = json.dumps(update_data["images"], ensure_ascii=False)

        for field, value in update_data.items():
            setattr(scenic, field, value)

        await db.commit()
        await db.refresh(scenic)
        return ResponseModel(data=scenic.to_dict(), msg="修改成功").model_dump()
    except Exception as e:
        return ResponseModel(code=400, msg=str(e)).model_dump()


@router.delete("/{scenic_id}", summary="删除景点")
async def delete_scenic(
    scenic_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """删除景点（软删除，需要登录认证）"""
    try:
        result = await db.execute(
            select(Scenic).where(Scenic.id == scenic_id, Scenic.is_deleted == False)
        )
        scenic = result.scalar_one_or_none()
        if not scenic:
            return ResponseModel(code=404, msg="景点不存在").model_dump()

        scenic.is_deleted = True
        await db.commit()
        return ResponseModel(msg="删除成功").model_dump()
    except Exception as e:
        return ResponseModel(code=400, msg=str(e)).model_dump()


# ==================== 搜索和查询 ====================

@router.get("/search/list", summary="关键词搜索景点")
async def search_scenic(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    category: Optional[str] = Query(None, description="主分类过滤"),
    subcategory: Optional[str] = Query(None, description="子分类过滤"),
    db: AsyncSession = Depends(get_db),
):
    """根据关键词搜索景点，结果标绘在地图上"""
    try:
        # 同时在名称和描述中搜索
        conditions = [
            Scenic.is_deleted == False,
            Scenic.name.like(f"%{keyword}%"),
        ]
        if category:
            conditions.append(Scenic.category == category)
        if subcategory:
            conditions.append(Scenic.subcategory == subcategory)
        count_query = select(func.count(Scenic.id)).where(*conditions)
        result_count = await db.execute(count_query)
        total = result_count.scalar() or 0

        query = (
            select(Scenic)
            .where(*conditions)
            .offset((page - 1) * size)
            .limit(size)
            .order_by(Scenic.created_at.desc())
        )
        result = await db.execute(query)
        spots = result.scalars().all()

        return {
            "code": 200,
            "msg": "搜索成功",
            "data": [s.to_dict() for s in spots],
            "total": total,
            "page": page,
            "page_size": size,
        }
    except Exception as e:
        logger.error(f"景点搜索失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()


@router.get("/nearby/list", summary="查询附近景点")
async def get_nearby_spots(
    longitude: float = Query(..., description="当前经度"),
    latitude: float = Query(..., description="当前纬度"),
    radius: float = Query(1000.0, ge=0, description="查询半径（米）"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    category: Optional[str] = Query(None, description="景点分类过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询指定坐标附近范围内的景点，按距离升序排列"""
    try:
        query = select(Scenic).where(Scenic.is_deleted == False)
        if category:
            query = query.where(Scenic.category == category)

        result = await db.execute(query)
        all_spots = result.scalars().all()

        # 计算距离并筛选
        spot_distances = []
        for spot in all_spots:
            dist = haversine(longitude, latitude, spot.longitude, spot.latitude)
            if dist <= radius:
                spot_distances.append((spot, round(dist, 2)))

        # 按距离排序
        spot_distances.sort(key=lambda x: x[1])

        total = len(spot_distances)
        start = (page - 1) * size
        end = start + size
        page_data = spot_distances[start:end]

        result_list = []
        for spot, dist in page_data:
            spot_dict = spot.to_dict()
            spot_dict["distance"] = dist
            result_list.append(spot_dict)

        return {
            "code": 200,
            "msg": "查询附近景点成功",
            "data": result_list,
            "total": total,
            "page": page,
            "page_size": size,
        }
    except Exception as e:
        logger.error(f"附近景点查询失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()
