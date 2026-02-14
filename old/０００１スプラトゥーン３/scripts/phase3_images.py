#!/usr/bin/env python3
"""
フェーズ3 画像加工パイプライン
- スクレイプした画像から武器アイコンを特定
- WebP→PNG変換、統一サイズ、透かし追加
- static/images/games/splatoon3/ に配置
"""

import json
import os
import re
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_data"
HUGO_DIR = Path("/mnt/ubuntu22-home/robot/work_space/project_blog/gamers-for")
OUTPUT_DIR = HUGO_DIR / "static" / "images" / "games" / "splatoon3"
CLEAN_DATA = RAW_DIR / "clean_weapons.json"

# アイコンサイズ
ICON_SIZE = (96, 96)
BANNER_SIZE = (600, 315)


def slug(name):
    s = name.lower()
    s = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or "item"


def add_watermark(img, text="GAMERS-FOR", opacity=35):
    """薄い透かしを追加"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # フォントサイズを画像サイズに合わせる
    font_size = max(8, min(img.size) // 8)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()

    # テキストのバウンディングボックスを取得
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 右下に配置
    x = img.size[0] - text_w - 4
    y = img.size[1] - text_h - 4

    # 半透明の白で描画
    draw.text((x, y), text, fill=(255, 255, 255, opacity), font=font)
    return Image.alpha_composite(img, overlay)


def process_icon(src_path, dst_path, size=ICON_SIZE):
    """アイコン画像を加工して保存"""
    try:
        img = Image.open(src_path)

        # RGBA変換
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # リサイズ（アスペクト比維持、余白追加）
        img.thumbnail(size, Image.LANCZOS)

        # 正方形キャンバスに配置
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        offset = ((size[0] - img.size[0]) // 2, (size[1] - img.size[1]) // 2)
        canvas.paste(img, offset, img)

        # 軽い色味調整（独自性のため）
        enhancer = ImageEnhance.Brightness(canvas)
        canvas = enhancer.enhance(1.03)
        enhancer = ImageEnhance.Contrast(canvas)
        canvas = enhancer.enhance(1.05)

        # 透かし追加
        canvas = add_watermark(canvas, "GF", opacity=30)

        # 角丸風の薄いボーダー
        draw = ImageDraw.Draw(canvas)
        draw.rectangle(
            [(0, 0), (size[0]-1, size[1]-1)],
            outline=(100, 100, 100, 60), width=1
        )

        # WebPで保存（形式変更）
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        canvas.save(dst_path, "WEBP", quality=85)
        return True
    except Exception as e:
        print(f"  [ERROR] {src_path}: {e}")
        return False


def process_banner(src_path, dst_path, size=BANNER_SIZE):
    """バナー画像を加工して保存"""
    try:
        img = Image.open(src_path)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # リサイズ
        img = img.resize(size, Image.LANCZOS)
        img = img.convert("RGBA")

        # 軽い色味調整
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.02)

        # 透かし追加
        img = add_watermark(img, "GAMERS-FOR", opacity=40)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        img.save(dst_path, "WEBP", quality=80)
        return True
    except Exception as e:
        print(f"  [ERROR] {src_path}: {e}")
        return False


def find_weapon_icon_mapping():
    """HTMLから武器名→アイコンファイルのマッピングを作成"""
    from bs4 import BeautifulSoup
    mapping = {}

    # アルテマの武器一覧HTMLを解析（一番きれい）
    html_path = RAW_DIR / "altema" / "html" / "weapon_list.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # テーブルの各行から武器名とアイコンを対応付け
        for a_tag in soup.find_all("a"):
            text = a_tag.get_text(strip=True)
            img = a_tag.find("img")
            if img and text and 2 < len(text) < 40:
                src = img.get("data-src") or img.get("src") or ""
                if src and not src.startswith("data:"):
                    # URLからファイル名を逆引き
                    fname = src.split("?")[0].split("/")[-1]
                    mapping[text] = {"altema": fname, "url": src}

    # GameWithの武器一覧HTMLも解析
    html_path = RAW_DIR / "gamewith" / "html" / "weapon_list.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        for a_tag in soup.find_all("a"):
            text = a_tag.get_text(strip=True)
            img = a_tag.find("img")
            if img and text and 2 < len(text) < 40:
                src = img.get("data-src") or img.get("src") or ""
                if src and not src.startswith("data:"):
                    fname = src.split("?")[0].split("/")[-1]
                    if text not in mapping:
                        mapping[text] = {}
                    mapping[text]["gamewith"] = fname
                    mapping[text]["gw_url"] = src

    return mapping


def find_icon_file(fname, sites=("altema", "gamewith", "game8")):
    """ファイル名からローカルパスを探す"""
    for site in sites:
        for subdir in ("icons", "images"):
            path = RAW_DIR / site / subdir / fname
            if path.exists() and path.stat().st_size > 100:
                return path
    return None


def generate_placeholder_icon(weapon_name, dst_path, size=ICON_SIZE):
    """アイコンが見つからない場合のプレースホルダー生成"""
    img = Image.new("RGBA", size, (30, 30, 60, 255))
    draw = ImageDraw.Draw(img)

    # 武器名の頭文字を大きく表示
    initial = weapon_name[0] if weapon_name else "?"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except (OSError, IOError):
        font = ImageFont.load_default()
        small_font = font

    bbox = draw.textbbox((0, 0), initial, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size[0]-tw)//2, (size[1]-th)//2 - 5), initial, fill=(200, 200, 255, 200), font=font)

    # 透かし
    img = add_watermark(img, "GF", opacity=30)

    # ボーダー
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (size[0]-1, size[1]-1)], outline=(80, 80, 120, 100), width=1)

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    img.save(dst_path, "WEBP", quality=85)


def main():
    print("=" * 60)
    print("フェーズ3: 画像加工パイプライン")
    print("=" * 60)

    # 武器データ読み込み
    with open(CLEAN_DATA, "r", encoding="utf-8") as f:
        weapons = json.load(f)["weapons"]
    print(f"武器数: {len(weapons)}")

    # 武器名→アイコンマッピング
    print("\n--- アイコンマッピング構築 ---")
    icon_map = find_weapon_icon_mapping()
    print(f"マッピング数: {len(icon_map)}")

    # 武器アイコン生成
    print("\n--- 武器アイコン加工 ---")
    weapons_dir = OUTPUT_DIR / "weapons"
    ok_count = 0
    placeholder_count = 0

    for w in weapons:
        name = w["name"]
        dst = str(weapons_dir / f"{slug(name)}.webp")

        if os.path.exists(dst):
            ok_count += 1
            continue

        # マッピングからアイコンを探す
        found = False
        if name in icon_map:
            info = icon_map[name]
            for key in ("altema", "gamewith"):
                if key in info:
                    src_path = find_icon_file(info[key])
                    if src_path:
                        if process_icon(str(src_path), dst):
                            ok_count += 1
                            found = True
                            break

        if not found:
            # 名前が部分一致するアイコンを探す
            for map_name, info in icon_map.items():
                if name in map_name or map_name in name:
                    for key in ("altema", "gamewith"):
                        if key in info:
                            src_path = find_icon_file(info[key])
                            if src_path:
                                if process_icon(str(src_path), dst):
                                    ok_count += 1
                                    found = True
                                    break
                    if found:
                        break

        if not found:
            generate_placeholder_icon(name, dst)
            placeholder_count += 1

    print(f"  加工済み: {ok_count}, プレースホルダー: {placeholder_count}")

    # バナー画像（サイト共通の大きめ画像を加工）
    print("\n--- バナー画像加工 ---")
    banner_dir = OUTPUT_DIR / "banners"
    banner_count = 0

    # GameWithの大きい画像からバナーを生成
    gw_images_dir = RAW_DIR / "gamewith" / "images"
    if gw_images_dir.exists():
        for f in sorted(os.listdir(gw_images_dir)):
            src = gw_images_dir / f
            try:
                im = Image.open(src)
                # バナーサイズの画像だけ使う
                if im.size[0] >= 300 and im.size[1] >= 150:
                    dst = str(banner_dir / f"banner_{banner_count:03d}.webp")
                    if not os.path.exists(dst):
                        process_banner(str(src), dst)
                    banner_count += 1
                    if banner_count >= 30:
                        break
            except Exception:
                pass

    print(f"  バナー: {banner_count}枚")

    # UIアイコン（ティアバッジ）生成
    print("\n--- ティアバッジ生成 ---")
    tier_dir = OUTPUT_DIR / "tiers"
    tier_colors = {
        "S+": (255, 23, 68), "S": (255, 87, 34), "A+": (255, 152, 0), "A": (255, 193, 7),
        "B+": (139, 195, 74), "B": (76, 175, 80), "C+": (33, 150, 243), "C": (158, 158, 158),
    }
    for tier, color in tier_colors.items():
        badge_path = str(tier_dir / f"{tier.replace('+','plus').lower()}.webp")
        if os.path.exists(badge_path):
            continue
        badge = Image.new("RGBA", (64, 32), (*color, 220))
        draw = ImageDraw.Draw(badge)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        except (OSError, IOError):
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), tier, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((64-tw)//2, (32-th)//2 - 1), tier, fill=(255, 255, 255, 255), font=font)
        os.makedirs(os.path.dirname(badge_path), exist_ok=True)
        badge.save(badge_path, "WEBP", quality=90)
    print(f"  ティアバッジ: {len(tier_colors)}個")

    # 統計
    total = 0
    for root, dirs, files in os.walk(str(OUTPUT_DIR)):
        total += len(files)
    print(f"\n{'='*60}")
    print(f"画像加工完了!")
    print(f"{'='*60}")
    print(f"出力先: {OUTPUT_DIR}")
    print(f"総ファイル数: {total}")


if __name__ == "__main__":
    main()
