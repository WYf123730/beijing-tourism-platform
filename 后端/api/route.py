"""
路径规划模块接口路由
驾车路径规划、旅行商分析、公交换乘查询
"""
import logging
import math
from itertools import permutations
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import BusRouteRequest, DriveRouteRequest, ResponseModel, TSPRequest
from services.amap_client import amap_client
from services.bus_algorithm import BusTransferFinder

logger = logging.getLogger("travel_platform.api.route")
router = APIRouter(prefix="/api/route", tags=["路径规划模块"])


def haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Haversine 公式计算两点间距离（米）"""
    from math import asin, cos, radians, sin, sqrt
    R = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return R * 2 * asin(sqrt(a))


# ==================== 驾车路径规划 ====================

@router.post("/drive", summary="驾车路径规划")
async def plan_drive_route(req: DriveRouteRequest):
    """
    驾车路径规划，调用高德驾车路径规划API
    - origin_lat/origin_lng: 起点坐标
    - dest_lat/dest_lng: 终点坐标
    """
    try:
        origin = f"{req.origin_lng},{req.origin_lat}"
        destination = f"{req.dest_lng},{req.dest_lat}"

        result = await amap_client.get_driving_route(origin, destination)

        if result.get("status") != "1":
            return ResponseModel(code=400, msg=f"路径规划失败: {result.get('info', '未知错误')}").model_dump()

        route_data = result.get("route", {})
        paths = route_data.get("paths", [])

        if not paths:
            return ResponseModel(code=400, msg="未找到可行路线").model_dump()

        # 格式化返回结果
        formatted_paths = []
        for path in paths[:3]:  # 最多返回3条路线
            steps = path.get("steps", [])
            formatted_steps = []
            for step in steps:
                formatted_steps.append({
                    "instruction": step.get("instruction", ""),
                    "road": step.get("road", ""),
                    "distance": step.get("distance", 0),
                    "duration": step.get("duration", 0),
                    "polyline": step.get("polyline", ""),
                })

            formatted_paths.append({
                "distance": path.get("distance", 0),
                "duration": path.get("duration", 0),
                "tolls": path.get("tolls", 0),
                "steps": formatted_steps,
                # 抽取所有坐标点用于前端绘制路线
                "polyline_points": _extract_polyline_points([path]),
            })

        return ResponseModel(data={
            "origin": {"lat": req.origin_lat, "lng": req.origin_lng},
            "destination": {"lat": req.dest_lat, "lng": req.dest_lng},
            "paths": formatted_paths,
            "count": len(formatted_paths),
        }, msg="驾车路径规划成功").model_dump()

    except Exception as e:
        logger.error(f"驾车路径规划失败: {e}")
        return ResponseModel(code=500, msg=f"驾车路径规划失败: {str(e)}").model_dump()


def _extract_polyline_points(paths: list) -> list:
    """从高德返回的路径中提取经纬度坐标点列表"""
    points = []
    if not paths:
        return points
    for path in paths:
        steps = path.get("steps", [])
        for step in steps:
            polyline = step.get("polyline", "")
            if polyline:
                for point_str in polyline.split(";"):
                    if point_str and "," in point_str:
                        parts = point_str.split(",")
                        if len(parts) >= 2:
                            try:
                                points.append([float(parts[0]), float(parts[1])])
                            except ValueError:
                                continue
    return points


# ==================== 旅行商分析（TSP） ====================

@router.post("/tsp", summary="旅行商分析")
async def plan_tsp_route(req: TSPRequest):
    """
    旅行商分析——多景点最优游览顺序
    - origin_lat/origin_lng: 起点坐标
    - spots: 景点坐标列表 [{"lat": ..., "lng": ..., "name": "..."}]
    使用穷举法计算最短路径（适用于景点数量≤8的场景）
    """
    try:
        if len(req.spots) < 2:
            return ResponseModel(code=400, msg="至少需要2个景点").model_dump()

        if len(req.spots) > 8:
            return ResponseModel(code=400, msg="景点数量过多（最多8个），请减少景点数量").model_dump()

        origin = (req.origin_lng, req.origin_lat)
        spots = req.spots

        # 构建距离矩阵
        num_spots = len(spots)
        indices = list(range(num_spots))

        # 计算起点到每个景点的距离
        dist_matrix = [[0] * num_spots for _ in range(num_spots)]
        for i in range(num_spots):
            for j in range(num_spots):
                if i != j:
                    dist_matrix[i][j] = haversine(
                        spots[i]["lng"], spots[i]["lat"],
                        spots[j]["lng"], spots[j]["lat"],
                    )

        # 计算从起点到每个景点的距离
        dist_from_origin = [
            haversine(origin[0], origin[1], spots[i]["lng"], spots[i]["lat"])
            for i in range(num_spots)
        ]

        # 使用穷举法求解TSP（景点数≤8时可行）
        best_order = None
        best_distance = float("inf")

        for perm in permutations(indices):
            total_dist = dist_from_origin[perm[0]]  # 起点到第一个景点
            for i in range(len(perm) - 1):
                total_dist += dist_matrix[perm[i]][perm[i + 1]]
            # 无需返回起点

            if total_dist < best_distance:
                best_distance = total_dist
                best_order = perm

        # 格式化结果
        ordered_spots = []
        route_coords = [[origin[0], origin[1]]]  # 起点
        for idx in best_order:
            spot = spots[idx]
            ordered_spots.append({
                "name": spot.get("name", f"景点{idx + 1}"),
                "latitude": spot["lat"],
                "longitude": spot["lng"],
                "order": len(ordered_spots) + 1,
            })
            route_coords.append([spot["lng"], spot["lat"]])

        return ResponseModel(data={
            "origin": {"lat": req.origin_lat, "lng": req.origin_lng},
            "total_distance": round(best_distance, 2),
            "spots_count": len(ordered_spots),
            "ordered_spots": ordered_spots,
            "route_coords": route_coords,  # 用于前端绘制路线
        }, msg="旅行商分析成功").model_dump()

    except Exception as e:
        logger.error(f"旅行商分析失败: {e}")
        return ResponseModel(code=500, msg=f"旅行商分析失败: {str(e)}").model_dump()


# ==================== 公交换乘查询 ====================

@router.post("/bus", summary="公交换乘查询")
async def query_bus_route(
    req: BusRouteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    公交换乘查询
    使用 BFS + Dijkstra 算法查找最优换乘方案
    - start_lat/start_lng: 起点坐标
    - end_lat/end_lng: 终点坐标
    """
    try:
        # 使用本地公交算法查询
        finder = BusTransferFinder(db)
        result = await finder.find_transfer_bfs(req.start_lat, req.start_lng, req.end_lat, req.end_lng)

        if not result.get("found"):
            # BFS没找到，尝试调用高德API
            logger.info("本地算法未找到公交换乘方案，尝试调用高德API")
            origin = f"{req.start_lng},{req.start_lat}"
            destination = f"{req.end_lng},{req.end_lat}"
            try:
                amap_result = await amap_client.get_bus_route(origin, destination)

                if amap_result.get("status") == "1":
                    return ResponseModel(data={
                        "source": "amap",
                        "transits": amap_result.get("route", {}).get("transits", []),
                    }, msg="公交换乘查询成功（高德API）").model_dump()
            except Exception as e:
                logger.warning(f"高德公交API调用失败: {e}")

            return ResponseModel(code=400, msg="未找到换乘方案。提示：当前公交数据有限，建议使用驾车或TSP路径规划").model_dump()

        return ResponseModel(data={
            "source": "local",
            "paths": result["paths"],
        }, msg=result["message"]).model_dump()

    except Exception as e:
        logger.error(f"公交换乘查询失败: {e}")
        return ResponseModel(code=500, msg=f"公交换乘查询失败: {str(e)}").model_dump()


@router.get("/bus/stations", summary="获取所有公交站点")
async def get_bus_stations(db: AsyncSession = Depends(get_db)):
    """获取所有公交站点列表"""
    try:
        finder = BusTransferFinder(db)
        stations = await finder.get_all_stations()
        return ResponseModel(data=stations, msg="获取成功").model_dump()
    except Exception as e:
        logger.error(f"获取公交站点失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()
