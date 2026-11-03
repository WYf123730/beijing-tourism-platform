"""Generate scenic spot images with names"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

IMG_DIR = os.path.join(os.path.dirname(__file__), "前端", "images", "scenic")
os.makedirs(IMG_DIR, exist_ok=True)

# Scenic spots with their colors (based on category)
SPOTS = [
    ("故宫博物院", "cultural", (198, 40, 40), 9.5),
    ("天安门广场", "cultural", (211, 47, 47), 9.2),
    ("颐和园", "cultural", (46, 125, 50), 9.0),
    ("八达岭长城", "cultural", (78, 52, 46), 9.1),
    ("天坛公园", "cultural", (21, 101, 192), 8.8),
    ("北海公园", "cultural", (0, 105, 92), 8.2),
    ("雍和宫", "cultural", (245, 127, 23), 8.5),
    ("圆明园遗址公园", "cultural", (93, 64, 55), 8.4),
    ("鸟巢（国家体育场）", "urban", (55, 71, 79), 8.6),
    ("水立方（国家游泳中心）", "urban", (2, 119, 189), 8.3),
    ("国家博物馆", "cultural", (40, 53, 147), 9.1),
    ("景山公园", "cultural", (51, 105, 30), 8.1),
    ("香山公园", "natural", (85, 139, 47), 8.3),
    ("恭王府", "cultural", (106, 27, 154), 8.6),
    ("798艺术区", "urban", (230, 81, 0), 8.5),
    ("南锣鼓巷", "urban", (78, 52, 46), 8.0),
    ("什刹海", "cultural", (0, 131, 143), 8.5),
    ("北京大学", "cultural", (26, 35, 126), 9.0),
    ("清华大学", "cultural", (130, 119, 23), 9.0),
    ("奥林匹克森林公园", "natural", (27, 94, 32), 8.7),
]

CAT_EMOJI = {"cultural": "🏛", "urban": "🏙", "natural": "🌿"}

W, H = 800, 600

try:
    font_big = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 48)
    font_mid = ImageFont.truetype("C:/Windows/Fonts/msyhl.ttc", 24)
    font_small = ImageFont.truetype("C:/Windows/Fonts/msyhl.ttc", 18)
except:
    font_big = ImageFont.load_default()
    font_mid = ImageFont.load_default()
    font_small = ImageFont.load_default()

for name, cat, color, rating in SPOTS:
    img = Image.new("RGB", (W, H), color)
    draw = ImageDraw.Draw(img)

    # Gradient overlay
    for y in range(H):
        alpha = int(60 + 60 * (y / H))
        r = min(255, color[0] + alpha)
        g = min(255, color[1] + alpha)
        b = min(255, color[2] + alpha)
        overlay = Image.new("RGB", (W, 1), (r, g, b))
        img.paste(overlay, (0, y))

    # Dark overlay for readability
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.blend(img, dark, 0.30)

    draw = ImageDraw.Draw(img)

    # Category indicator strip
    draw.rectangle([0, 0, W, 6], fill=(255, 255, 255, 80))

    # Emoji icon (large)
    emoji = CAT_EMOJI.get(cat, "📍")
    icon_size = 80
    # Draw circle background for icon
    cx, cy = W // 2, H // 2 - 60
    draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=(255, 255, 255, 30), outline=(255, 255, 255, 60), width=3)
    try:
        font_icon = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 48)
    except:
        font_icon = font_big
    draw.text((cx, cy), emoji, fill="white", font=font_icon, anchor="mm")

    # Spot name
    draw.text((W // 2, H // 2 + 30), name, fill="white", font=font_big, anchor="mm")

    # Stars
    stars = "★" * int(rating) + "☆" * (10 - int(rating))
    draw.text((W // 2, H // 2 + 85), f"{stars}  {rating}", fill="#FFD54F", font=font_mid, anchor="mm")

    # Category label
    cat_labels = {"cultural": "人文古迹", "urban": "城市地标", "natural": "自然风光"}
    draw.text((W // 2, H - 30), f"{cat_labels.get(cat, cat)}  ·  北京", fill=(255, 255, 255, 160), font=font_small, anchor="mm")

    # Save
    safe_name = name.replace("（", "(").replace("）", ")")
    fpath = os.path.join(IMG_DIR, f"{safe_name}.jpg")
    img.save(fpath, "JPEG", quality=85)
    print(f"[OK] {name} -> {fpath}")

print(f"\nDone! Generated {len(SPOTS)} images")
