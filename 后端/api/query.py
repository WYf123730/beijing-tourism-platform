"""
空间查询模块接口路由
POI 分类查询、点/矩形/圆形/多边形范围查询
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from shapely.geometry import Point, Polygon as ShapelyPolygon
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from math import radians, cos

from core.security import get_current_user_id
from database import get_db
from models import POI
from schemas import (
    CircleQuery, PointQuery, POICreate, POIUpdate, PolygonQuery, RectQuery,
    ResponseModel,
)

logger = logging.getLogger("travel_platform.api.query")
router = APIRouter(prefix="/api/poi", tags=["空间查询模块"])


def haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Haversine 公式计算两点间距离（米）"""
    from math import asin, sin, sqrt
    R = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return R * 2 * asin(sqrt(a))


def shapely_distance_meters(point1: Point, point2: Point) -> float:
    """使用 Shapely 计算两点间的近似距离（米）"""
    avg_lat = (point1.y + point2.y) / 2
    degree_dist = point1.distance(point2)
    return degree_dist * 111320 * cos(radians(avg_lat))


def point_in_polygon(lng: float, lat: float, polygon_coords: list) -> bool:
    """判断点是否在多边形内（使用 Shapely）"""
    point = Point(lng, lat)
    polygon = ShapelyPolygon(polygon_coords)
    return polygon.contains(point)


# ==================== POI 分类查询 ====================

@router.get("/categories", summary="按类别查询POI")
async def get_poi_by_category(
    category: Optional[str] = Query(None, description="POI类别过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    """按类别查询POI，支持分页。不传category返回全部。"""
    try:
        conditions = []
        if category:
            conditions.append(POI.category == category)

        count_query = select(func.count(POI.id)).where(*conditions)
        result_count = await db.execute(count_query)
        total = result_count.scalar() or 0

        query = (
            select(POI)
            .where(*conditions)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(POI.id.desc())
        )
        result = await db.execute(query)
        pois = result.scalars().all()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": [p.to_dict() for p in pois],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(f"POI查询失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()


@router.delete("/delete/{poi_id}", summary="删除POI")
async def delete_poi(
    poi_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """删除POI（需要登录认证）"""
    try:
        result = await db.execute(select(POI).where(POI.id == poi_id))
        poi = result.scalar_one_or_none()
        if not poi:
            return ResponseModel(code=404, msg="POI不存在").model_dump()
        await db.delete(poi)
        await db.commit()
        return ResponseModel(msg="删除成功").model_dump()
    except Exception as e:
        logger.error(f"删除POI失败: {e}")
        return ResponseModel(code=400, msg=str(e)).model_dump()


# ==================== 点+半径查询 ====================

@router.post("/query/point", summary="点加半径查询POI")
async def query_poi_by_point(req: PointQuery, db: AsyncSession = Depends(get_db)):
    """
    点加半径查询POI
    - lat: 中心点纬度
    - lng: 中心点经度
    - radius: 查询半径（米）
    - category: POI类别过滤（选填）
    - page: 页码
    - page_size: 每页条数
    """
    try:
        conditions = []
        if req.category:
            conditions.append(POI.category == req.category)

        query = select(POI).where(*conditions)
        result = await db.execute(query)
        all_pois = result.scalars().all()

        # 使用 Haversine 筛选范围内 POI
        center_point = Point(req.lng, req.lat)
        filtered = []
        for poi in all_pois:
            dist = haversine(req.lng, req.lat, poi.longitude, poi.latitude)
            if dist <= req.radius:
                poi_dict = poi.to_dict()
                poi_dict["distance"] = round(dist, 2)
                filtered.append(poi_dict)

        filtered.sort(key=lambda x: x["distance"])

        total = len(filtered)
        start = (req.page - 1) * req.page_size
        end = start + req.page_size
        page_data = filtered[start:end]

        return {
            "code": 200,
            "msg": "点查询成功",
            "data": page_data,
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }
    except Exception as e:
        logger.error(f"点查询POI失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()


# ==================== 矩形范围查询 ====================

@router.post("/query/rect", summary="矩形范围查询POI")
async def query_poi_by_rect(req: RectQuery, db: AsyncSession = Depends(get_db)):
    """
    矩形范围查询POI
    - min_lat/min_lng/max_lat/max_lng: 矩形范围
    """
    try:
        conditions = [
            POI.longitude >= req.min_lng,
            POI.longitude <= req.max_lng,
            POI.latitude >= req.min_lat,
            POI.latitude <= req.max_lat,
        ]
        if req.category:
            conditions.append(POI.category == req.category)

        count_query = select(func.count(POI.id)).where(*conditions)
        result_count = await db.execute(count_query)
        total = result_count.scalar() or 0

        query = (
            select(POI)
            .where(*conditions)
            .offset((req.page - 1) * req.page_size)
            .limit(req.page_size)
        )
        result = await db.execute(query)
        pois = result.scalars().all()

        return {
            "code": 200,
            "msg": "矩形查询成功",
            "data": [p.to_dict() for p in pois],
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }
    except Exception as e:
        logger.error(f"矩形查询POI失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()


# ==================== 圆形范围查询 ====================

@router.post("/query/circle", summary="圆形范围查询POI")
async def query_poi_by_circle(req: CircleQuery, db: AsyncSession = Depends(get_db)):
    """
    圆形范围查询POI
    - lat/lng: 圆心坐标
    - radius: 半径（米）
    """
    try:
        conditions = []
        if req.category:
            conditions.append(POI.category == req.category)

        query = select(POI).where(*conditions)
        result = await db.execute(query)
        all_pois = result.scalars().all()

        # 筛选在圆内的POI
        filtered = []
        for poi in all_pois:
            dist = haversine(req.lng, req.lat, poi.longitude, poi.latitude)
            if dist <= req.radius:
                poi_dict = poi.to_dict()
                poi_dict["distance"] = round(dist, 2)
                filtered.append(poi_dict)

        filtered.sort(key=lambda x: x["distance"])

        total = len(filtered)
        start = (req.page - 1) * req.page_size
        end = start + req.page_size
        page_data = filtered[start:end]

        return {
            "code": 200,
            "msg": "圆形查询成功",
            "data": page_data,
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }
    except Exception as e:
        logger.error(f"圆形查询POI失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()


# ==================== 多边形范围查询 ====================

@router.post("/query/polygon", summary="多边形范围查询POI")
async def query_poi_by_polygon(req: PolygonQuery, db: AsyncSession = Depends(get_db)):
    """
    多边形范围查询POI
    - coordinates: 多边形顶点坐标列表 [[lng,lat], ...]
    """
    try:
        if len(req.coordinates) < 3:
            return ResponseModel(code=400, msg="多边形至少需要3个顶点").model_dump()

        # 构建 Shapely 多边形
        polygon = ShapelyPolygon(req.coordinates)
        if not polygon.is_valid:
            return ResponseModel(code=400, msg="无效的多边形").model_dump()

        conditions = []
        if req.category:
            conditions.append(POI.category == req.category)

        query = select(POI).where(*conditions)
        result = await db.execute(query)
        all_pois = result.scalars().all()

        # 判断哪些POI在多边形内
        filtered = []
        for poi in all_pois:
            point = Point(poi.longitude, poi.latitude)
            if polygon.contains(point):
                filtered.append(poi.to_dict())

        total = len(filtered)
        start = (req.page - 1) * req.page_size
        end = start + req.page_size
        page_data = filtered[start:end]

        return {
            "code": 200,
            "msg": "多边形查询成功",
            "data": page_data,
            "total": total,
            "page": req.page,
            "page_size": req.page_size,
        }
    except Exception as e:
        logger.error(f"多边形查询POI失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()

@router.post("/create", summary="新增POI")
async def create_poi(
    req: POICreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """新增POI（需要登录认证）"""
    try:
        poi = POI(name=req.name, category=req.category, address=req.address or "",
                  longitude=req.longitude, latitude=req.latitude, phone=req.phone or "")
        db.add(poi)
        await db.commit()
        await db.refresh(poi)
        return ResponseModel(data=poi.to_dict(), msg="新增POI成功").model_dump()
    except Exception as e:
        return ResponseModel(code=400, msg=str(e)).model_dump()


@router.put("/update/{poi_id}", summary="修改POI")
async def update_poi(
    poi_id: int,
    req: POIUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """修改POI（需要登录认证）"""
    try:
        result = await db.execute(select(POI).where(POI.id == poi_id))
        poi = result.scalar_one_or_none()
        if not poi:
            return ResponseModel(code=404, msg="POI不存在").model_dump()
        update_data = req.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(poi, field, value)
        await db.commit()
        await db.refresh(poi)
        return ResponseModel(data=poi.to_dict(), msg="修改成功").model_dump()
    except Exception as e:
        return ResponseModel(code=400, msg=str(e)).model_dump()


@router.get("/detail/{poi_id}", summary="POI详情")
async def get_poi_detail(
    poi_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取POI详情"""
    result = await db.execute(select(POI).where(POI.id == poi_id))
    poi = result.scalar_one_or_none()
    if not poi:
        return ResponseModel(code=404, msg="POI不存在").model_dump()
    return ResponseModel(data=poi.to_dict()).model_dump()
