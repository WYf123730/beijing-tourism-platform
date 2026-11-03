"""
综合分析模块接口路由
缓冲区分析、叠置分析（救援信息）
"""
import json
import logging
from math import asin, cos, radians, sin, sqrt
from typing import List

from fastapi import APIRouter, Depends
from shapely.geometry import Point, Polygon as ShapelyPolygon
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import RescueResource
from schemas import BufferAnalysisRequest, OverlayAnalysisRequest, ResponseModel

logger = logging.getLogger("travel_platform.api.analysis")
router = APIRouter(prefix="/api/analysis", tags=["综合分析模块"])


def haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Haversine 公式计算两点间距离（米）"""
    R = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return R * 2 * asin(sqrt(a))


# 预定义的救援区域（多边形围栏），用于叠置分析
# 每个区域包含名称、描述和顶点坐标
RESCUE_ZONES = [
    {
        "name": "天安门区域",
        "description": "天安门广场及周边核心区域",
        "coordinates": [
            [116.380, 39.900], [116.380, 39.920],
            [116.410, 39.920], [116.410, 39.900],
        ],
        "type": "核心保护区",
    },
    {
        "name": "故宫区域",
        "description": "故宫博物院及周边区域",
        "coordinates": [
            [116.385, 39.910], [116.385, 39.925],
            [116.400, 39.925], [116.400, 39.910],
        ],
        "type": "景区",
    },
    {
        "name": "奥林匹克公园区域",
        "description": "鸟巢、水立方及周边区域",
        "coordinates": [
            [116.380, 39.975], [116.380, 39.995],
            [116.400, 39.995], [116.400, 39.975],
        ],
        "type": "景区",
    },
    {
        "name": "王府井商业区",
        "description": "王府井大街及周边商业区",
        "coordinates": [
            [116.400, 39.908], [116.400, 39.920],
            [116.420, 39.920], [116.420, 39.908],
        ],
        "type": "商业区",
    },
    {
        "name": "西单商业区",
        "description": "西单及周边商业区",
        "coordinates": [
            [116.365, 39.905], [116.365, 39.918],
            [116.380, 39.918], [116.380, 39.905],
        ],
        "type": "商业区",
    },
    {
        "name": "海淀高校区",
        "description": "北京大学、清华大学等高校区域",
        "coordinates": [
            [116.300, 39.980], [116.300, 40.005],
            [116.340, 40.005], [116.340, 39.980],
        ],
        "type": "文教区",
    },
    {
        "name": "朝阳CBD区域",
        "description": "国贸、CBD核心区域",
        "coordinates": [
            [116.430, 39.900], [116.430, 39.920],
            [116.470, 39.920], [116.470, 39.900],
        ],
        "type": "商务区",
    },
    {
        "name": "颐和园香山区域",
        "description": "颐和园、香山、植物园等景区",
        "coordinates": [
            [116.180, 39.980], [116.180, 40.010],
            [116.280, 40.010], [116.280, 39.980],
        ],
        "type": "景区",
    },
    {
        "name": "前门大栅栏区域",
        "description": "前门、大栅栏传统商业区",
        "coordinates": [
            [116.385, 39.885], [116.385, 39.900],
            [116.405, 39.900], [116.405, 39.885],
        ],
        "type": "商业区",
    },
    {
        "name": "北京市区",
        "description": "北京市主要城区范围",
        "coordinates": [
            [115.80, 39.60], [115.80, 40.30],
            [116.90, 40.30], [116.90, 39.60],
        ],
        "type": "城区",
    },
]


# ==================== 缓冲区分析 ====================

@router.post("/buffer", summary="缓冲区分析")
async def buffer_analysis(
    req: BufferAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    缓冲区分析——查询事故点缓冲区内的救援资源
    - lat: 事故点纬度
    - lng: 事故点经度
    - radius: 缓冲区半径（米）
    """
    try:
        # 查询所有救援资源
        result = await db.execute(select(RescueResource))
        all_resources = result.scalars().all()

        # 筛选缓冲区内的资源
        buffered_resources = []
        for resource in all_resources:
            dist = haversine(req.lng, req.lat, resource.longitude, resource.latitude)
            if dist <= req.radius:
                res_dict = resource.to_dict()
                res_dict["distance"] = round(dist, 2)
                buffered_resources.append(res_dict)

        # 按距离升序排列
        buffered_resources.sort(key=lambda x: x["distance"])

        # 按类型统计
        type_stats = {}
        for res in buffered_resources:
            rtype = res.get("type", "其他")
            type_stats[rtype] = type_stats.get(rtype, 0) + 1

        return ResponseModel(data={
            "accident_point": {"lat": req.lat, "lng": req.lng},
            "buffer_radius": req.radius,
            "total_count": len(buffered_resources),
            "resources": buffered_resources,
            "type_stats": type_stats,
        }, msg="缓冲区分析成功").model_dump()

    except Exception as e:
        logger.error(f"缓冲区分析失败: {e}")
        return ResponseModel(code=500, msg=f"缓冲区分析失败: {str(e)}").model_dump()


# ==================== 叠置分析 ====================

@router.post("/overlay", summary="叠置分析")
async def overlay_analysis(
    req: OverlayAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    叠置分析——判断事故点落在哪些区域内，并查询附近救援资源
    无论事故点是否在预设区域内，都会返回附近救援资源
    """
    try:
        accident_point = Point(req.lng, req.lat)

        # 获取事故点的地址描述（通过高德逆地理编码）
        location_name = "未知位置"
        try:
            from services.amap_client import amap_client as _ac
            geo = await _ac.parse_reverse_geocode(req.lng, req.lat)
            if geo:
                parts = []
                if geo.get("district"): parts.append(geo["district"])
                if geo.get("formatted_address"): 
                    addr = geo["formatted_address"]
                    # 简化地址，只取街道/地标部分
                    for kw in ["在", "附近", "旁"]:
                        idx = addr.find(kw)
                        if idx > 0:
                            addr = addr[:idx+1]
                            break
                    parts.append(addr)
                if parts: location_name = " ".join(parts)
        except Exception:
            pass

        # 判断事故点落在哪些区域内
        overlapped_zones = []
        for zone in RESCUE_ZONES:
            try:
                polygon = ShapelyPolygon(zone["coordinates"])
                if polygon.contains(accident_point):
                    overlapped_zones.append({
                        "name": zone["name"],
                        "description": zone["description"],
                        "type": zone.get("type", ""),
                        "coordinates": zone["coordinates"],  # 返回坐标供前端绘制
                    })
            except Exception:
                continue

        # 把位置名加到叠置区域第一条
        if overlapped_zones:
            overlapped_zones.insert(0, {
                "name": location_name,
                "description": "事故点位置",
                "type": "精确定位",
            })

        # 查询事故点附近的救援资源
        result = await db.execute(select(RescueResource))
        all_resources = result.scalars().all()

        nearby_resources = []
        for resource in all_resources:
            dist = haversine(req.lng, req.lat, resource.longitude, resource.latitude)
            if dist <= 4000:  # 4公里范围
                res_dict = resource.to_dict()
                res_dict["distance"] = round(dist, 2)
                nearby_resources.append(res_dict)

        nearby_resources.sort(key=lambda x: x["distance"])

        # 如果没有叠置区域，也返回附近资源
        return ResponseModel(data={
            "accident_point": {"lat": req.lat, "lng": req.lng},
            "overlapped_zones": overlapped_zones,
            "zones_count": len(overlapped_zones),
            "nearby_resources": nearby_resources,
            "resources_count": len(nearby_resources),
        }, msg="叠置分析成功").model_dump()

    except Exception as e:
        logger.error(f"叠置分析失败: {e}")
        return ResponseModel(code=500, msg=f"叠置分析失败: {str(e)}").model_dump()
