"""
高德地图 API 工具模块
封装高德地图 Web 服务 API 调用，提供地理编码、天气查询、驾车路径规划等功能
"""
import logging
from typing import Optional

import httpx

from config import settings

# 禁用SSL警告（Windows上证书问题）
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("travel_platform.amap")

AMAP_BASE_URL = "https://restapi.amap.com/v3"
TIMEOUT = 10
MAX_RETRIES = 2


class AmapClient:
    """高德地图 Web 服务 API 客户端"""

    def __init__(self):
        self._key = settings.AMAP_WEB_KEY
        if not self._key:
            logger.warning("高德地图 API Key 未配置，请检查 .env 文件中的 AMAP_WEB_KEY")

    async def _request(self, api: str, params: dict, retry: int = MAX_RETRIES) -> dict:
        """发送 HTTP 请求到高德 API（含重试机制）"""
        params["key"] = self._key
        params["output"] = "JSON"
        url = f"{AMAP_BASE_URL}{api}"

        for attempt in range(retry + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT, verify=False) as client:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get("status") != "1":
                        logger.warning(f"高德 API 返回错误 [api={api}]: {data.get('info', '未知错误')}")
                        return data
                    return data

            except httpx.TimeoutException:
                logger.warning(f"高德 API 请求超时 [api={api}]，第 {attempt + 1} 次重试")
                if attempt == retry:
                    raise
            except httpx.HTTPStatusError as e:
                logger.error(f"高德 API HTTP 错误 [api={api}]: {e}")
                if attempt == retry:
                    raise
            except Exception as e:
                logger.exception(f"高德 API 请求异常 [api={api}]: {e}")
                if attempt == retry:
                    raise
        return {}

    # ==================== 地理编码 ====================

    async def geocode(self, address: str, city: str = "北京") -> dict:
        """地理编码 —— 地址转经纬度"""
        return await self._request("/geocode/geo", {"address": address, "city": city})

    async def reverse_geocode(self, longitude: float, latitude: float) -> dict:
        """逆地理编码 —— 经纬度转地址"""
        return await self._request("/geocode/regeo", {"location": f"{longitude},{latitude}"})

    async def parse_geocode(self, address: str, city: str = "北京") -> Optional[dict]:
        """解析地址为经纬度（高层封装）"""
        result = await self.geocode(address, city)
        if result.get("status") == "1" and result.get("geocodes"):
            geocode = result["geocodes"][0]
            location = geocode.get("location", "")
            if location and "," in location:
                lng_str, lat_str = location.split(",", 1)
                return {
                    "longitude": float(lng_str),
                    "latitude": float(lat_str),
                    "formatted_address": geocode.get("formatted_address", address),
                    "level": geocode.get("level", ""),
                }
        logger.warning(f"地址解析失败: {address}")
        return None

    async def parse_reverse_geocode(self, longitude: float, latitude: float) -> Optional[dict]:
        """解析坐标为地址（高层封装）"""
        result = await self.reverse_geocode(longitude, latitude)
        if result.get("status") == "1" and result.get("regeocode"):
            regeo = result["regeocode"]
            return {
                "formatted_address": regeo.get("formatted_address", ""),
                "country": regeo.get("addressComponent", {}).get("country", ""),
                "province": regeo.get("addressComponent", {}).get("province", ""),
                "city": regeo.get("addressComponent", {}).get("city", ""),
                "district": regeo.get("addressComponent", {}).get("district", ""),
            }
        logger.warning(f"坐标解析失败: {longitude},{latitude}")
        return None

    # ==================== POI 搜索 ====================

    async def search_poi(self, keywords: str, city: str = "北京", page: int = 1, page_size: int = 20) -> dict:
        """POI 关键词搜索"""
        return await self._request("/place/text", {
            "keywords": keywords,
            "city": city,
            "offset": page_size,
            "page": page,
            "extensions": "all",
        })

    async def search_around(self, longitude: float, latitude: float, keywords: str = "",
                            radius: int = 1000, page: int = 1, page_size: int = 20) -> dict:
        """周边搜索"""
        params = {
            "location": f"{longitude},{latitude}",
            "radius": radius,
            "offset": page_size,
            "page": page,
            "extensions": "all",
        }
        if keywords:
            params["keywords"] = keywords
        return await self._request("/place/around", params)

    # ==================== 天气查询 ====================

    async def get_weather(self, city_code: str, extensions: str = "base") -> dict:
        """
        天气查询
        Args:
            city_code: 城市编码（adcode）
            extensions: base=实时天气, all=预报天气
        """
        return await self._request("/weather/weatherInfo", {
            "city": city_code,
            "extensions": extensions,
        })

    # ==================== 驾车路径规划 ====================

    async def get_driving_route(self, origin: str, destination: str, strategy: int = 0) -> dict:
        """
        驾车路径规划
        Args:
            origin: 起点坐标 "经度,纬度"
            destination: 终点坐标 "经度,纬度"
            strategy: 驾车策略 0=速度优先
        """
        return await self._request("/direction/driving", {
            "origin": origin,
            "destination": destination,
            "strategy": strategy,
            "extensions": "all",
        })

    # ==================== 公交路径规划 ====================

    async def get_bus_route(self, origin: str, destination: str, city: str = "北京",
                            strategy: int = 0) -> dict:
        """
        公交换乘查询（使用高德API）
        Args:
            origin: 起点坐标 "经度,纬度"
            destination: 终点坐标 "经度,纬度"
            city: 城市
            strategy: 0=较快捷, 1=少换乘, 2=少步行, 3=不坐地铁
        """
        return await self._request("/transit/integrated", {
            "origin": origin,
            "destination": destination,
            "city": city,
            "strategy": strategy,
        })


# 全局单例
amap_client = AmapClient()
