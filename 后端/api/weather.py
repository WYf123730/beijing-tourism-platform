"""
天气查询模块接口路由
城市天气查询、景区天气查询（从缓存或实时获取）
支持按景区所在区/县返回独立天气数据
"""
import json
import logging
import re

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, get_db
from models import Scenic, WeatherCache
from schemas import ResponseModel
from services.amap_client import amap_client
from services.weather_task import ATTRACTIONS_CITIES

logger = logging.getLogger("travel_platform.api.weather")
router = APIRouter(prefix="/api/weather", tags=["天气模块"])

# 常见城市名 → adcode 映射（用于实时查询）
CITY_ADCODES = {c["city"]: c["adcode"] for c in ATTRACTIONS_CITIES}
CITY_ADCODES.update({
    "北京": "110000", "上海": "310000", "广州": "440100",
    "深圳": "440300", "天津": "120000", "重庆": "500000",
})

# 北京各区地名关键词 → adcode 映射（用于从景点地址中提取区名）
DISTRICT_KEYWORDS = {
    "东城区": "110101", "西城区": "110102", "朝阳区": "110105",
    "丰台区": "110106", "石景山区": "110107", "海淀区": "110108",
    "门头沟区": "110109", "房山区": "110111", "通州区": "110112",
    "顺义区": "110113", "昌平区": "110114", "大兴区": "110115",
    "怀柔区": "110116", "平谷区": "110117", "密云区": "110118",
    "延庆区": "110119",
}


def extract_district_from_address(address: str) -> str:
    """从地址中提取区名，如 '北京市海淀区...' -> '海淀区'"""
    if not address:
        return "北京"
    for district in DISTRICT_KEYWORDS:
        if district in address:
            return district
    return "北京"


async def get_weather_for_location(district: str, db: AsyncSession) -> dict:
    """获取指定区/县的实时天气（按区独立从高德获取）"""
    # 使用区县对应的 adcode 独立查询高德 API
    adcode = DISTRICT_KEYWORDS.get(district, "110000")

    # 优先实时获取该区天气
    try:
        result = await amap_client.get_weather(adcode, extensions="base")
        if result.get("status") == "1" and result.get("lives"):
            w = result["lives"][0]
            weather_data = {
                "city": district,
                "adcode": adcode,
                "weather": w.get("weather", ""),
                "temperature": w.get("temperature", ""),
                "winddirection": w.get("winddirection", ""),
                "windpower": w.get("windpower", ""),
                "humidity": w.get("humidity", ""),
                "reporttime": w.get("reporttime", ""),
            }
            # 后台更新缓存
            try:
                async with AsyncSessionLocal() as cache_db:
                    existing = await cache_db.execute(
                        select(WeatherCache).where(WeatherCache.adcode == adcode)
                    )
                    existing_row = existing.scalar_one_or_none()
                    if existing_row:
                        existing_row.weather_data = json.dumps(weather_data, ensure_ascii=False)
                    else:
                        cache_db.add(WeatherCache(
                            city=district, adcode=adcode,
                            weather_data=json.dumps(weather_data, ensure_ascii=False)
                        ))
                    await cache_db.commit()
            except Exception as e:
                logger.warning(f"天气缓存更新失败 [{district}]: {e}")
            return weather_data
    except Exception as e:
        logger.warning(f"实时天气获取失败 [{district}]: {e}")

    # 实时失败，降级用该区缓存
    try:
        result = await db.execute(
            select(WeatherCache).where(WeatherCache.adcode == adcode)
        )
        cached = result.scalar_one_or_none()
        if cached:
            wd = cached.weather_data
            if isinstance(wd, str):
                try:
                    wd = json.loads(wd)
                except (json.JSONDecodeError, TypeError):
                    wd = {}
            if wd and isinstance(wd, dict) and wd.get("weather"):
                return wd
    except Exception:
        pass

    return {}


@router.get("/{city}", summary="查询城市天气")
async def get_city_weather(city: str, db: AsyncSession = Depends(get_db)):
    """
    查询城市天气（实时获取，不依赖缓存）
    - city: 城市名称（如 "北京"、"海淀区"）
    """
    try:
        adcode = CITY_ADCODES.get(city, "")
        if not adcode:
            adcode = DISTRICT_KEYWORDS.get(city, "110000")

        # 获取实时天气（extensions=base 返回 lives 数据）
        result = await amap_client.get_weather(adcode, extensions="base")
        if result.get("status") != "1":
            return ResponseModel(code=500, msg="高德天气服务暂时不可用").model_dump()

        lives = result.get("lives", [])

        # 获取预报天气（extensions=all 返回 forecasts）
        forecast_result = await amap_client.get_weather(adcode, extensions="all")
        forecasts = forecast_result.get("forecasts", [{}])[0] if forecast_result.get("status") == "1" else {}

        weather_data = {}
        if lives:
            w = lives[0]
            weather_data = {
                "city": w.get("city", city),
                "adcode": adcode,
                "weather": w.get("weather", ""),
                "temperature": w.get("temperature", ""),
                "winddirection": w.get("winddirection", ""),
                "windpower": w.get("windpower", ""),
                "humidity": w.get("humidity", ""),
                "reporttime": w.get("reporttime", ""),
                "forecast": forecasts.get("casts", []),
            }

        # 异步更新缓存（不阻塞返回）
        try:
            async with AsyncSessionLocal() as cache_db:
                cached = await cache_db.execute(
                    select(WeatherCache).where(WeatherCache.city == city)
                )
                existing = cached.scalar_one_or_none()
                if existing:
                    existing.weather_data = json.dumps(weather_data, ensure_ascii=False)
                else:
                    cache_db.add(WeatherCache(city=city, adcode=adcode,
                        weather_data=json.dumps(weather_data, ensure_ascii=False)))
                await cache_db.commit()
        except Exception as cache_err:
            logger.warning(f"天气缓存更新失败: {cache_err}")

        return ResponseModel(data={
            "source": "realtime",
            "city": city,
            "adcode": adcode,
            "weather_data": weather_data,
            "updated_at": weather_data.get("reporttime") if weather_data else None,
        }, msg="获取成功（实时更新）").model_dump()

    except Exception as e:
        logger.error(f"获取天气失败 [{city}]: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()


@router.get("/attractions/all", summary="查询各景区独立天气")
async def get_attractions_weather(db: AsyncSession = Depends(get_db)):
    """
    查询每个景区所在区/县的独立天气信息
    全部实时从高德API获取，每个景区返回所在区的实际天气
    """
    try:
        # 获取所有景点
        result = await db.execute(
            select(Scenic).where(Scenic.is_deleted == False)
        )
        spots = result.scalars().all()

        attractions_weather = []
        fetched_districts = {}  # adcode -> weather_data 已实时获取过的区

        for spot in spots:
            district = extract_district_from_address(spot.address or "")
            adcode = DISTRICT_KEYWORDS.get(district, "110000")

            # 每个区最多实时请求一次
            if adcode not in fetched_districts:
                realtime = await get_weather_for_location(district, db)
                if realtime and realtime.get("weather"):
                    fetched_districts[adcode] = realtime
                else:
                    fetched_districts[adcode] = None

            district_weather = fetched_districts.get(adcode) or {}

            attractions_weather.append({
                "id": spot.id,
                "name": spot.name,
                "latitude": spot.latitude,
                "longitude": spot.longitude,
                "address": spot.address,
                "district": district,
                "source": "realtime",
                "weather": district_weather,
            })

        return ResponseModel(data={
            "count": len(attractions_weather),
            "attractions": attractions_weather,
        }, msg="获取景区天气成功（实时数据）").model_dump()

    except Exception as e:
        logger.error(f"获取景区天气失败: {e}")
        return ResponseModel(code=500, msg=str(e)).model_dump()
        return ResponseModel(code=500, msg=str(e)).model_dump()
