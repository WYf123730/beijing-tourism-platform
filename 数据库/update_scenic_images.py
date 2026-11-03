"""
Update scenic spots with image URLs
"""
import json
import asyncio
import sys
import os

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import AsyncSessionLocal
from models import Scenic
from sqlalchemy import select

SCENIC_IMAGES = {
    "故宫博物院": ["/app/images/scenic/beijing_1.jpg", "/app/images/scenic/spot_1.jpg"],
    "天安门广场": ["/app/images/scenic/spot_2.jpg", "/app/images/scenic/beijing_2.jpg"],
    "颐和园": ["/app/images/scenic/spot_3.jpg", "/app/images/scenic/spot_4.jpg"],
    "八达岭长城": ["/app/images/scenic/spot_5.jpg", "/app/images/scenic/spot_6.jpg"],
    "天坛公园": ["/app/images/scenic/spot_7.jpg", "/app/images/scenic/beijing_3.jpg"],
    "北海公园": ["/app/images/scenic/spot_8.jpg", "/app/images/scenic/spot_9.jpg"],
    "雍和宫": ["/app/images/scenic/spot_10.jpg", "/app/images/scenic/spot_11.jpg"],
    "圆明园遗址公园": ["/app/images/scenic/spot_12.jpg", "/app/images/scenic/spot_13.jpg"],
    "鸟巢（国家体育场）": ["/app/images/scenic/spot_14.jpg", "/app/images/scenic/spot_15.jpg"],
    "水立方（国家游泳中心）": ["/app/images/scenic/spot_16.jpg", "/app/images/scenic/spot_17.jpg"],
    "国家博物馆": ["/app/images/scenic/spot_18.jpg", "/app/images/scenic/spot_19.jpg"],
    "景山公园": ["/app/images/scenic/spot_20.jpg", "/app/images/scenic/spot_21.jpg"],
    "香山公园": ["/app/images/scenic/spot_1.jpg", "/app/images/scenic/spot_4.jpg"],
    "恭王府": ["/app/images/scenic/beijing_1.jpg", "/app/images/scenic/spot_11.jpg"],
    "798艺术区": ["/app/images/scenic/spot_13.jpg", "/app/images/scenic/spot_15.jpg"],
    "南锣鼓巷": ["/app/images/scenic/spot_17.jpg", "/app/images/scenic/spot_19.jpg"],
    "什刹海": ["/app/images/scenic/spot_20.jpg", "/app/images/scenic/spot_21.jpg"],
    "北京大学": ["/app/images/scenic/spot_2.jpg", "/app/images/scenic/spot_5.jpg"],
    "清华大学": ["/app/images/scenic/spot_7.jpg", "/app/images/scenic/spot_8.jpg"],
    "奥林匹克森林公园": ["/app/images/scenic/spot_9.jpg", "/app/images/scenic/spot_10.jpg"],
}

async def update_images():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Scenic).where(Scenic.is_deleted == False))
        spots = result.scalars().all()

        updated = 0
        for spot in spots:
            if spot.name in SCENIC_IMAGES:
                spot.images = json.dumps(SCENIC_IMAGES[spot.name], ensure_ascii=False)
                updated += 1
                print(f"[OK] {spot.name}")

        await db.commit()
        print(f"\n[Done] Updated {updated}/{len(spots)} scenic spots")

if __name__ == "__main__":
    asyncio.run(update_images())
