#!/usr/bin/env python3
"""
プレースホルダー画像を生成するスクリプト
ステージ画像、ギアアイテム画像、サーモンランボス画像等
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3")
DATA_DIR = os.path.join(BASE_DIR, "data")

# サイトカラー
BG_COLOR = (45, 45, 55)       # ダークグレー
TEXT_COLOR = (200, 200, 210)   # ライトグレー
ACCENT_COLOR = (230, 80, 80)  # 赤（サイトアクセント）
SUB_TEXT_COLOR = (140, 140, 150)

# 画像サイズ
STAGE_SIZE = (800, 450)
BOSS_SIZE = (400, 400)
GEAR_SIZE = (200, 200)
BANNER_SIZE = (1200, 400)


def get_font(size):
    """日本語フォントを取得"""
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
        "/usr/share/fonts/truetype/ipafont-gothic/ipagp.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_placeholder(size, main_text, sub_text="画像準備中", filename="placeholder.webp", output_dir=None):
    """プレースホルダー画像を生成"""
    w, h = size
    img = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 枠線
    draw.rectangle([(2, 2), (w - 3, h - 3)], outline=(80, 80, 90), width=2)

    # 斜めストライプ（デザイン要素）
    for i in range(-h, w + h, 40):
        draw.line([(i, 0), (i + h, h)], fill=(50, 50, 60), width=1)

    # メインテキスト
    main_font_size = max(16, min(w, h) // 10)
    main_font = get_font(main_font_size)
    bbox = draw.textbbox((0, 0), main_text, font=main_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (w - text_w) // 2
    y = (h - text_h) // 2 - main_font_size // 2
    draw.text((x, y), main_text, font=main_font, fill=TEXT_COLOR)

    # サブテキスト
    sub_font_size = max(12, main_font_size // 2)
    sub_font = get_font(sub_font_size)
    bbox2 = draw.textbbox((0, 0), sub_text, font=sub_font)
    sub_w = bbox2[2] - bbox2[0]
    x2 = (w - sub_w) // 2
    y2 = y + text_h + sub_font_size
    draw.text((x2, y2), sub_text, font=sub_font, fill=SUB_TEXT_COLOR)

    # GFロゴ（右下）
    gf_font = get_font(max(12, min(w, h) // 15))
    draw.text((w - 50, h - 30), "GF", font=gf_font, fill=(255, 255, 255, 100))

    # 保存
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, filename)
    else:
        path = filename
    img.save(path, "WEBP", quality=85)
    return path


def main():
    print("=== プレースホルダー画像生成 ===\n")

    # マスターデータ読み込み
    master_path = os.path.join(DATA_DIR, "splatoon3_master.json")
    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    count = 0

    # 1. ステージ画像（25枚）
    print("--- ステージ画像 ---")
    stages_dir = os.path.join(IMG_DIR, "stages")
    os.makedirs(stages_dir, exist_ok=True)
    for stage in master.get("stages", []):
        name = stage["name"]
        # ファイル名をASCII安全にする
        import re
        safe_name = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', name)
        filename = f"{safe_name}.webp"
        create_placeholder(
            STAGE_SIZE, name, "ステージ画像準備中",
            filename, stages_dir
        )
        print(f"  ✓ {name}")
        count += 1

    # 2. サーモンランボス画像
    print("\n--- サーモンランボス画像 ---")
    sr_dir = os.path.join(IMG_DIR, "salmon-run")
    os.makedirs(sr_dir, exist_ok=True)
    for boss in master.get("salmon_run", {}).get("big_salmon", []):
        name = boss["name"]
        import re
        safe_name = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', name)
        filename = f"{safe_name}.webp"
        create_placeholder(
            BOSS_SIZE, name, "オオモノシャケ画像準備中",
            filename, sr_dir
        )
        print(f"  ✓ {name}")
        count += 1

    # オカシラシャケ
    for king in master.get("salmon_run", {}).get("king_salmon", []):
        name = king["name"]
        import re
        safe_name = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', name)
        filename = f"king_{safe_name}.webp"
        create_placeholder(
            BOSS_SIZE, name, "オカシラシャケ画像準備中",
            filename, sr_dir
        )
        print(f"  ✓ {name} (オカシラ)")
        count += 1

    # 3. バナー画像
    print("\n--- バナー画像 ---")
    banners_dir = os.path.join(IMG_DIR, "banners")
    os.makedirs(banners_dir, exist_ok=True)

    banners = [
        ("tier-list-banner", "最強武器ランキング"),
        ("salmon-run-banner", "サーモンラン攻略"),
        ("beginner-banner", "初心者ガイド"),
        ("gear-banner", "ギアパワー解説"),
        ("stage-banner", "ステージ攻略"),
    ]
    for fname, title in banners:
        create_placeholder(
            BANNER_SIZE, title, "Gamers-For スプラトゥーン3攻略",
            f"{fname}.webp", banners_dir
        )
        print(f"  ✓ {title}")
        count += 1

    # 4. ギア画像プレースホルダー（カテゴリ別）
    print("\n--- ギア画像 ---")
    gear_dir = os.path.join(IMG_DIR, "gear")
    os.makedirs(gear_dir, exist_ok=True)
    gear_categories = ["head", "clothing", "shoes"]
    gear_names = {"head": "アタマ", "clothing": "フク", "shoes": "クツ"}
    for cat in gear_categories:
        create_placeholder(
            GEAR_SIZE, gear_names[cat], "ギア画像準備中",
            f"gear_{cat}_placeholder.webp", gear_dir
        )
        print(f"  ✓ ギア: {gear_names[cat]}")
        count += 1

    print(f"\n=== 完了: {count}枚生成 ===")


if __name__ == "__main__":
    main()
