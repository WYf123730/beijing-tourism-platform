"""
Update scenic spots with CORRECT images matching each spot
"""
import json, asyncio, os, sys

os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import AsyncSessionLocal
from models import Scenic
from sqlalchemy import select

# Each scenic spot gets its OWN named image
SCENIC_IMAGES_V2 = {
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

async def update():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Scenic).where(Scenic.is_deleted == False))
        spots = result.scalars().all()
        updated = 0
        for spot in spots:
            if spot.name in SCENIC_IMAGES_V2:
                spot.images = json.dumps(SCENIC_IMAGES_V2[spot.name], ensure_ascii=False)
                updated += 1
                print(f"[OK] {spot.name}")
        await db.commit()
        print(f"\n[Done] Updated {updated}/{len(spots)} scenic spots")

if __name__ == "__main__":
    asyncio.run(update())
