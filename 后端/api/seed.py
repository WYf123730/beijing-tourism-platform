"""
数据初始化接口路由
提供景点、POI、公交数据初始化导入功能
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user_id
from database import get_db, AsyncSessionLocal
from models import Scenic, POI, BusRoute, BusStation, RescueResource, User
from schemas import ResponseModel

logger = logging.getLogger("travel_platform.api.seed")
router = APIRouter(prefix="/api/seed", tags=["数据初始化"])

# ==================== 景点图片映射（每个景点对应独立图片） ====================
SCENIC_IMAGE_MAP = {
    "故宫博物院": ["/app/images/scenic/故宫博物院.jpg"],
    "天安门广场": ["/app/images/scenic/天安门广场.jpg"],
    "颐和园": ["/app/images/scenic/颐和园.jpg"],
    "八达岭长城": ["/app/images/scenic/八达岭长城.jpg"],
    "天坛公园": ["/app/images/scenic/天坛公园.jpg"],
    "北海公园": ["/app/images/scenic/北海公园.jpg"],
    "雍和宫": ["/app/images/scenic/雍和宫.jpg"],
    "圆明园遗址公园": ["/app/images/scenic/圆明园遗址公园.jpg"],
    "鸟巢（国家体育场）": ["/app/images/scenic/鸟巢(国家体育场).jpg"],
    "水立方（国家游泳中心）": ["/app/images/scenic/水立方(国家游泳中心).jpg"],
    "国家博物馆": ["/app/images/scenic/国家博物馆.jpg"],
    "景山公园": ["/app/images/scenic/景山公园.jpg"],
    "香山公园": ["/app/images/scenic/香山公园.jpg"],
    "恭王府": ["/app/images/scenic/恭王府.jpg"],
    "798艺术区": ["/app/images/scenic/798艺术区.jpg"],
    "南锣鼓巷": ["/app/images/scenic/南锣鼓巷.jpg"],
    "什刹海": ["/app/images/scenic/什刹海.jpg"],
    "北京大学": ["/app/images/scenic/北京大学.jpg"],
    "清华大学": ["/app/images/scenic/清华大学.jpg"],
    "奥林匹克森林公园": ["/app/images/scenic/奥林匹克森林公园.jpg"],
}

# ==================== 北京景点数据 ====================
SEED_SCENIC = [
    {"name": "故宫博物院", "description": "北京故宫是中国明清两代的皇家宫殿，旧称紫禁城，位于北京中轴线的中心。", "address": "北京市东城区景山前街4号", "longitude": 116.397128, "latitude": 39.916527, "category": "cultural", "subcategory": "palace", "phone": "010-85007422", "open_time": "08:30-17:00（周一闭馆）", "ticket_price": "60元", "rating": 9.5},
    {"name": "天安门广场", "description": "天安门广场位于北京市中心，南北长880米，东西宽500米，面积达44万平方米。", "address": "北京市东城区长安街", "longitude": 116.397500, "latitude": 39.905000, "category": "cultural", "subcategory": "landmark", "phone": "010-63095745", "open_time": "全天开放", "ticket_price": "免费", "rating": 9.2},
    {"name": "颐和园", "description": "颐和园，中国清朝时期皇家园林，前身为清漪园，坐落在北京西郊。", "address": "北京市海淀区新建宫门路19号", "longitude": 116.276000, "latitude": 39.999000, "category": "cultural", "subcategory": "park", "phone": "010-62881144", "open_time": "06:30-20:00", "ticket_price": "30元", "rating": 9.0},
    {"name": "八达岭长城", "description": "八达岭长城位于北京市延庆区军都山关沟古道北口。史称天下九塞之一。", "address": "北京市延庆区G6京藏高速58号出口", "longitude": 115.988000, "latitude": 40.354000, "category": "cultural", "subcategory": "landmark", "phone": "010-69121474", "open_time": "07:30-17:30", "ticket_price": "40元", "rating": 9.1},
    {"name": "天坛公园", "description": "天坛是明清两代皇帝祭天、祈谷和祈雨的场所。", "address": "北京市东城区天坛内东里7号", "longitude": 116.407000, "latitude": 39.882000, "category": "cultural", "subcategory": "park", "phone": "010-67028866", "open_time": "08:00-17:30", "ticket_price": "15元", "rating": 8.8},
    {"name": "北海公园", "description": "北海公园位于北京市中心区，是中国现存最古老、最完整的皇家园林之一。", "address": "北京市西城区文津街1号", "longitude": 116.389000, "latitude": 39.924000, "category": "cultural", "subcategory": "park", "phone": "010-64033225", "open_time": "06:30-20:00", "ticket_price": "10元", "rating": 8.2},
    {"name": "雍和宫", "description": "雍和宫是北京最大的藏传佛教寺院，建于清康熙三十三年。", "address": "北京市东城区雍和宫大街12号", "longitude": 116.418000, "latitude": 39.947000, "category": "cultural", "subcategory": "temple", "phone": "010-64044499", "open_time": "09:00-17:00", "ticket_price": "25元", "rating": 8.5},
    {"name": "圆明园遗址公园", "description": "圆明园是清代大型皇家园林，由圆明园、长春园和绮春园组成。", "address": "北京市海淀区清华西路28号", "longitude": 116.303000, "latitude": 39.995000, "category": "cultural", "subcategory": "park", "phone": "010-62637561", "open_time": "07:00-19:00", "ticket_price": "10元", "rating": 8.4},
    {"name": "鸟巢（国家体育场）", "description": "国家体育场是2008年北京奥运会的主体育场，因其独特的外观被称为\"鸟巢\"。", "address": "北京市朝阳区国家体育场南路1号", "longitude": 116.391000, "latitude": 39.993000, "category": "urban", "subcategory": "landmark", "phone": "010-84373008", "open_time": "09:00-21:00", "ticket_price": "50元", "rating": 8.6},
    {"name": "水立方（国家游泳中心）", "description": "国家游泳中心是2008年北京奥运会主游泳馆。", "address": "北京市朝阳区天辰东路11号", "longitude": 116.383000, "latitude": 39.995000, "category": "urban", "subcategory": "landmark", "phone": "010-84370123", "open_time": "09:00-21:00", "ticket_price": "30元", "rating": 8.3},
    {"name": "国家博物馆", "description": "中国国家博物馆是代表国家收藏、研究、展示、阐释中华文化代表性物证的最高历史文化艺术殿堂。", "address": "北京市东城区东长安街16号", "longitude": 116.395000, "latitude": 39.909000, "category": "cultural", "subcategory": "museum", "phone": "010-65116400", "open_time": "09:00-17:00（周一闭馆）", "ticket_price": "免费", "rating": 9.1},
    {"name": "景山公园", "description": "景山公园位于北京城南北中轴线的中心点上，南依故宫，西靠北海。", "address": "北京市西城区景山西街44号", "longitude": 116.396000, "latitude": 39.925000, "category": "cultural", "subcategory": "park", "phone": "010-64044071", "open_time": "06:30-20:00", "ticket_price": "2元", "rating": 8.1},
    {"name": "香山公园", "description": "香山公园位于北京西郊，是一座具有皇家园林特色的大型山林公园，以红叶闻名。", "address": "北京市海淀区买卖街40号", "longitude": 116.192000, "latitude": 39.992000, "category": "natural", "subcategory": "park", "phone": "010-62591155", "open_time": "06:00-18:30", "ticket_price": "10元", "rating": 8.3},
    {"name": "恭王府", "description": "恭王府位于北京市西城区柳荫街，是清代规模最大的一座王府。", "address": "北京市西城区柳荫街甲14号", "longitude": 116.384000, "latitude": 39.937000, "category": "cultural", "subcategory": "palace", "phone": "010-83288149", "open_time": "08:00-17:00", "ticket_price": "40元", "rating": 8.6},
    {"name": "798艺术区", "description": "798艺术区原为国营798厂等电子工业老厂区，现成为北京都市文化的新地标。", "address": "北京市朝阳区酒仙桥路4号", "longitude": 116.495000, "latitude": 39.986000, "category": "urban", "subcategory": "other", "phone": "", "open_time": "全天开放", "ticket_price": "免费", "rating": 8.5},
    {"name": "南锣鼓巷", "description": "南锣鼓巷是北京最古老的街区之一。", "address": "北京市东城区南锣鼓巷", "longitude": 116.403000, "latitude": 39.937000, "category": "urban", "subcategory": "street", "phone": "", "open_time": "全天开放", "ticket_price": "免费", "rating": 8.0},
    {"name": "什刹海", "description": "什刹海是北京市历史文化旅游风景区，包括前海、后海和西海。", "address": "北京市西城区什刹海", "longitude": 116.385000, "latitude": 39.936000, "category": "cultural", "subcategory": "park", "phone": "", "open_time": "全天开放", "ticket_price": "免费", "rating": 8.5},
    {"name": "北京大学", "description": "北京大学是中国近代第一所国立综合性大学。", "address": "北京市海淀区颐和园路5号", "longitude": 116.306000, "latitude": 39.986000, "category": "cultural", "subcategory": "school", "phone": "010-62752114", "open_time": "对外开放（需预约）", "ticket_price": "免费", "rating": 9.0},
    {"name": "清华大学", "description": "清华大学是中国著名高等学府。", "address": "北京市海淀区双清路30号", "longitude": 116.347000, "latitude": 40.006000, "category": "cultural", "subcategory": "school", "phone": "010-62785001", "open_time": "对外开放（需预约）", "ticket_price": "免费", "rating": 9.0},
    {"name": "奥林匹克森林公园", "description": "奥林匹克森林公园是北京最大的城市公园。", "address": "北京市朝阳区科荟路33号", "longitude": 116.393000, "latitude": 40.019000, "category": "natural", "subcategory": "park", "phone": "010-64529060", "open_time": "06:00-21:00", "ticket_price": "免费", "rating": 8.7},
]


@router.get("/init", summary="初始化数据库样本数据")
async def seed_database(db: AsyncSession = Depends(get_db)):
    """
    向数据库中导入样本数据（景点、POI、公交数据、救援资源）。
    已存在的数据不会重复插入。
    """
    results = {}

    try:
        # 1. 检查是否已有景点数据
        result = await db.execute(select(Scenic).limit(1))
        existing = result.scalar_one_or_none()
        if existing:
            # 统计现有数据
            count_result = await db.execute(select(Scenic).where(Scenic.is_deleted == False))
            scenic_count = len(count_result.scalars().all())
            results["scenic"] = f"已有 {scenic_count} 个景点，跳过导入"
        else:
            # 导入景点数据（含本地图片）
            count = 0
            for s in SEED_SCENIC:
                images = json.dumps(SCENIC_IMAGE_MAP.get(s["name"], []), ensure_ascii=False)
                scenic = Scenic(**s, images=images)
                db.add(scenic)
                count += 1
            await db.commit()
            results["scenic"] = f"成功导入 {count} 个景点"

        # 2. 检查POI数据
        result = await db.execute(select(POI).limit(1))
        if result.scalar_one_or_none():
            results["poi"] = "POI数据已存在，跳过导入"
        else:
            results["poi"] = "请使用 init_db.sql 导入POI数据（数据量较大）"

        # 3. 检查公交线路
        result = await db.execute(select(BusRoute).limit(1))
        if result.scalar_one_or_none():
            results["bus_routes"] = "公交线路数据已存在"
        else:
            results["bus_routes"] = "请使用 init_db.sql 导入公交线路数据"

        # 4. 检查公交站点
        result = await db.execute(select(BusStation).limit(1))
        if result.scalar_one_or_none():
            results["bus_stations"] = "公交站点数据已存在"
        else:
            results["bus_stations"] = "请使用 init_db.sql 导入公交站点数据"

        # 5. 检查救援资源
        result = await db.execute(select(RescueResource).limit(1))
        if result.scalar_one_or_none():
            results["rescue"] = "救援资源数据已存在"
        else:
            results["rescue"] = "请使用 init_db.sql 导入救援资源数据"

        return ResponseModel(data=results, msg="数据库初始化检查完成").model_dump()

    except Exception as e:
        logger.error(f"数据初始化失败: {e}")
        return ResponseModel(code=500, msg=f"数据初始化失败: {str(e)}").model_dump()


@router.get("/status", summary="查看数据库数据统计")
async def db_status(db: AsyncSession = Depends(get_db)):
    """查看当前数据库中各表的数据量"""
    try:
        tables = {
            "users": User,
            "scenic": Scenic,
            "pois": POI,
            "bus_routes": BusRoute,
            "bus_stations": BusStation,
            "rescue_resources": RescueResource,
        }
        stats = {}
        for name, model in tables.items():
            result = await db.execute(select(model))
            rows = result.scalars().all()
            stats[name] = len(rows)
        return ResponseModel(data=stats, msg="数据统计完成").model_dump()
    except Exception as e:
        return ResponseModel(code=500, msg=str(e)).model_dump()
