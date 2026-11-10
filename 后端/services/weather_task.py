"""
天气定时任务模块
使用 APScheduler 定时从高德地图 API 获取天气数据并缓存到数据库
"""
import asyncio
import json
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import Scenic, WeatherCache
from services.amap_client import amap_client

logger = logging.getLogger("travel_platform.weather_task")

# 北京热门景区城市编码（adcode）
ATTRACTIONS_CITIES = [
    {"city": "北京", "adcode": "110000"},
    {"city": "东城区", "adcode": "110101"},
    {"city": "西城区", "adcode": "110102"},
    {"city": "朝阳区", "adcode": "110105"},
    {"city": "海淀区", "adcode": "110108"},
    {"city": "丰台区", "adcode": "110106"},
    {"city": "石景山区", "adcode": "110107"},
    {"city": "通州区", "adcode": "110112"},
    {"city": "大兴区", "adcode": "110115"},
    {"city": "顺义区", "adcode": "110113"},
    {"city": "昌平区", "adcode": "110114"},
    {"city": "延庆区", "adcode": "110119"},
    {"city": "怀柔区", "adcode": "110116"},
    {"city": "密云区", "adcode": "110118"},
    {"city": "平谷区", "adcode": "110117"},
    {"city": "房山区", "adcode": "110111"},
    {"city": "门头沟区", "adcode": "110109"},
]


async def fetch_and_cache_weather(city: str, adcode: str):
    """
    获取城市天气并缓存到数据库
    Args:
        city: 城市名称
        adcode: 城市编码
    """
    try:
        # 获取实时天气
        result = await amap_client.get_weather(adcode, extensions="base")
        if result.get("status") != "1":
            logger.warning(f"天气获取失败 [{city}]: {result.get('info', '未知错误')}")
            return False

        lives = result.get("lives", [])
        if not lives:
            logger.warning(f"天气数据为空 [{city}]")
            return False

        weather_info = lives[0]

        # 也获取预报天气
        forecast_result = await amap_client.get_weather(adcode, extensions="all")
        forecast = forecast_result.get("forecasts", [{}])[0] if forecast_result.get("status") == "1" else {}

        weather_data = {
            "city": weather_info.get("city", city),
            "adcode": adcode,
            "weather": weather_info.get("weather", ""),
            "temperature": weather_info.get("temperature", ""),
            "winddirection": weather_info.get("winddirection", ""),
            "windpower": weather_info.get("windpower", ""),
            "humidity": weather_info.get("humidity", ""),
            "reporttime": weather_info.get("reporttime", ""),
            "forecast": forecast.get("casts", []) if forecast else [],
        }

        # 缓存到数据库（weather_data 字段是 JSON 列，交给 SQLAlchemy 序列化，
        # 不要再手工 json.dumps，否则会写成「JSON 的 JSON」，读的时候要解两层）
        async with AsyncSessionLocal() as db:
            async with db.begin():
                result = await db.execute(
                    select(WeatherCache).where(WeatherCache.adcode == adcode)
                )
                existing = result.scalars().first()

                if existing:
                    existing.weather_data = weather_data
                    existing.updated_at = datetime.now()
                else:
                    cache = WeatherCache(
                        city=city,
                        adcode=adcode,
                        weather_data=weather_data,
                    )
                    db.add(cache)

            await db.commit()

        logger.info(f"天气缓存更新成功 [{city}]: {weather_info.get('weather', '')} {weather_info.get('temperature', '')}°C")
        return True

    except Exception as e:
        logger.error(f"天气获取失败 [{city}]: {e}")
        return False


async def fetch_all_attractions_weather():
    """获取所有景区天气（定时任务调用）"""
    logger.info("开始定时拉取所有景区天气数据...")

    # 获取数据库中的景点，提取城市信息
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Scenic).where(Scenic.is_deleted == False))
            spots = result.scalars().all()

        # 先拉取预定义的北京各区天气
        ok, fail = 0, 0
        for city_info in ATTRACTIONS_CITIES:
            city, adcode = city_info["city"], city_info["adcode"]
            done = await fetch_and_cache_weather(city, adcode)
            if not done:
                await asyncio.sleep(1.5)     # 可能是被限流，退让后重试一次
                done = await fetch_and_cache_weather(city, adcode)
            if done:
                ok += 1
            else:
                fail += 1
            # 高德天气接口有 QPS 限制，连续快速请求会触发 CUQPS_HAS_EXCEEDED_THE_LIMIT。
            # 一旦失败，该区缓存就停在上一次成功的值（出现过朝阳区沿用三个月前数据、
            # 地图上 34℃ 与 3℃ 并存的情况），因此必须留出间隔。
            await asyncio.sleep(0.6)

        logger.info(f"定时天气拉取完成：成功 {ok} 个，失败 {fail} 个")
    except Exception as e:
        logger.error(f"定时天气拉取失败: {e}")


def setup_weather_scheduler():
    """
    设置天气定时任务
    每天早上6:00自动拉取天气数据
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_all_attractions_weather,
        trigger="cron",
        hour=6,
        minute=0,
        id="weather_fetch_daily",
        name="每日天气数据拉取",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("天气定时任务已启动（每天 06:00 自动拉取天气数据）")
    return scheduler
