"""
公交换乘算法模块
使用 BFS（广度优先搜索）和 Dijkstra 算法实现公交换乘查询
"""
import logging
import math
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import BusRoute, BusStation

logger = logging.getLogger("travel_platform.bus_algorithm")


def haversine(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Haversine 公式计算两点间距离（米）"""
    R = 6371000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


class BusTransferFinder:
    """公交换乘查询器，使用 BFS + Dijkstra 混合算法"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._stations: Dict[str, dict] = {}  # station_name -> {lat, lng, routes}
        self._station_graph: Dict[str, List[Tuple[str, str, float]]] = {}  # station -> [(next_station, route_name, dist)]
        self._loaded = False

    async def load_data(self):
        """加载公交站点和线路数据到内存"""
        if self._loaded:
            return

        # 加载所有站点
        result = await self.db.execute(select(BusStation))
        stations = result.scalars().all()
        for s in stations:
            self._stations[s.name] = {
                "lat": s.latitude,
                "lng": s.longitude,
                "routes": s.routes if isinstance(s.routes, list) else [],
            }

        # 加载所有线路，构建站点邻接图
        result = await self.db.execute(select(BusRoute))
        routes = result.scalars().all()

        for route in routes:
            stations_list = route.stations if isinstance(route.stations, list) else []
            coords_list = route.station_coords if isinstance(route.station_coords, list) else []

            # 同一条线路上相邻站点间建立连接
            for i in range(len(stations_list) - 1):
                s1 = stations_list[i]
                s2 = stations_list[i + 1]

                if s1 not in self._station_graph:
                    self._station_graph[s1] = []
                if s2 not in self._station_graph:
                    self._station_graph[s2] = []

                # 计算距离
                if i < len(coords_list) - 1:
                    c1 = coords_list[i]
                    c2 = coords_list[i + 1]
                    if isinstance(c1, dict) and isinstance(c2, dict):
                        dist = haversine(c1.get("lng", 0), c1.get("lat", 0),
                                         c2.get("lng", 0), c2.get("lat", 0))
                    else:
                        dist = 100  # 默认距离
                else:
                    dist = 100

                # 双向连接（同一条线路可以来回）
                self._station_graph[s1].append((s2, route.route_name, dist))
                self._station_graph[s2].append((s1, route.route_name, dist))

        self._loaded = True
        logger.info(f"公交数据加载完成: {len(self._stations)} 站点, {len(routes)} 线路")

    def _find_nearest_station(self, lat: float, lng: float) -> Optional[str]:
        """查找距离指定坐标最近的公交站"""
        nearest = None
        min_dist = float("inf")
        for name, info in self._stations.items():
            dist = haversine(lng, lat, info["lng"], info["lat"])
            if dist < min_dist:
                min_dist = dist
                nearest = name
        return nearest

    async def find_transfer_bfs(self, start_lat: float, start_lng: float,
                                end_lat: float, end_lng: float) -> dict:
        """
        使用 BFS 算法查找最少换乘方案
        Returns:
            {"found": bool, "paths": [...], "message": "..."}
        """
        await self.load_data()

        start_station = self._find_nearest_station(start_lat, start_lng)
        end_station = self._find_nearest_station(end_lat, end_lng)

        if not start_station or not end_station:
            return {"found": False, "paths": [], "message": "未找到附近公交站"}

        if start_station == end_station:
            return {"found": True, "paths": [{
                "stations": [start_station],
                "route_changes": [],
                "total_distance": 0,
            }], "message": "起点和终点在同一站点"}

        # BFS 搜索最少换乘路径
        queue = deque()
        queue.append((start_station, [(start_station, None, 0)]))  # (当前站点, 路径)
        visited = {start_station}

        results = []

        while queue and len(results) < 5:  # 最多返回5条方案
            current, path = queue.popleft()

            if current == end_station:
                results.append(path)
                continue

            for neighbor, route_name, dist in self._station_graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [(neighbor, route_name, dist)]
                    queue.append((neighbor, new_path))

        if not results:
            # BFS 没找到，尝试 Dijkstra
            return await self._find_transfer_dijkstra(start_lat, start_lng, end_lat, end_lng)

        # 格式化结果
        formatted = []
        for path in results[:3]:
            stations_path = [p[0] for p in path]
            # 每段详细路线（含乘坐哪路车）
            segments = []
            current_route = None
            for i, step in enumerate(path):
                station = step[0]
                route = step[1]
                if route:
                    if route != current_route:
                        if current_route is not None:
                            segments[-1]['to'] = station
                        segments.append({
                            'from': station,
                            'to': '',
                            'route': route,
                        })
                        current_route = route
                    else:
                        # 同一条路线继续行驶
                        pass
            # 补全最后一段的终点
            if segments and segments[-1]['to'] == '':
                segments[-1]['to'] = stations_path[-1]

            total_dist = sum(p[2] for p in path)
            formatted.append({
                "stations": stations_path,
                "segments": segments,
                "total_distance": round(total_dist, 2),
                "transfer_count": max(0, len(segments) - 1) if segments else 0,
            })

        return {
            "found": True,
            "paths": formatted,
            "message": f"找到 {len(formatted)} 条换乘方案",
        }

    async def _find_transfer_dijkstra(self, start_lat: float, start_lng: float,
                                       end_lat: float, end_lng: float) -> dict:
        """
        使用 Dijkstra 算法查找最短距离换乘方案
        作为 BFS 的补充，当 BFS 无法连通时尝试全局搜索
        """
        await self.load_data()

        start_station = self._find_nearest_station(start_lat, start_lng)
        end_station = self._find_nearest_station(end_lat, end_lng)

        if not start_station or not end_station:
            return {"found": False, "paths": [], "message": "未找到附近公交站"}

        # Dijkstra
        import heapq
        pq = [(0, start_station, [(start_station, None, 0)])]
        distances = {start_station: 0}

        results = []

        while pq and len(results) < 3:
            dist, current, path = heapq.heappop(pq)

            if current == end_station:
                results.append(path)
                continue

            if dist > distances.get(current, float("inf")):
                continue

            for neighbor, route_name, edge_dist in self._station_graph.get(current, []):
                new_dist = dist + edge_dist
                if new_dist < distances.get(neighbor, float("inf")):
                    distances[neighbor] = new_dist
                    new_path = path + [(neighbor, route_name, edge_dist)]
                    heapq.heappush(pq, (new_dist, neighbor, new_path))

        if not results:
            return {"found": False, "paths": [], "message": "未找到可行的换乘方案"}

        formatted = []
        for path in results[:3]:
            stations_path = [p[0] for p in path]
            total_dist = sum(p[2] for p in path)

            segments = []
            current_route = None
            for step in path:
                station = step[0]
                route = step[1]
                if route:
                    if route != current_route:
                        if current_route is not None:
                            segments[-1]['to'] = station
                        segments.append({
                            'from': station,
                            'to': '',
                            'route': route,
                        })
                        current_route = route
            if segments and segments[-1]['to'] == '':
                segments[-1]['to'] = stations_path[-1]

            formatted.append({
                "stations": stations_path,
                "segments": segments,
                "total_distance": round(total_dist, 2),
                "transfer_count": max(0, len(segments) - 1) if segments else 0,
            })

        return {
            "found": True,
            "paths": formatted,
            "message": f"找到 {len(formatted)} 条换乘方案（Dijkstra最短路径）",
        }

    async def get_all_stations(self) -> List[dict]:
        """获取所有公交站点"""
        await self.load_data()
        return [
            {"name": name, "latitude": info["lat"], "longitude": info["lng"], "routes": info["routes"]}
            for name, info in self._stations.items()
        ]

    async def get_station_by_name(self, name: str) -> Optional[dict]:
        """根据名称查找站点"""
        await self.load_data()
        info = self._stations.get(name)
        if info:
            return {"name": name, "latitude": info["lat"], "longitude": info["lng"], "routes": info["routes"]}
        return None
