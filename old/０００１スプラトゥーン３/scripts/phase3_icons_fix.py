#!/usr/bin/env python3
"""
フェーズ3 アイコン修正 - data-lazy-src対応
1. AltemaのHTMLからdata-lazy-srcで正しいアイコンURLを取得
2. 不足アイコンをダウンロード
3. 全武器アイコンを加工して static/ に配置
"""

import json
import os
import re
import time
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_data"
HUGO_DIR = Path("/mnt/ubuntu22-home/robot/work_space/project_blog/gamers-for")
OUTPUT_DIR = HUGO_DIR / "static" / "images" / "games" / "splatoon3"
CLEAN_DATA = RAW_DIR / "clean_weapons.json"
ICON_DL_DIR = RAW_DIR / "weapon_icons"  # 新たにDLするアイコン保存先

ICON_SIZE = (96, 96)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def slug(name):
    s = name.lower()
    s = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or "item"


def add_watermark(img, text="GF", opacity=30):
    """薄い透かしを追加"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_size = max(8, min(img.size) // 8)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = img.size[0] - text_w - 4
    y = img.size[1] - text_h - 4
    draw.text((x, y), text, fill=(255, 255, 255, opacity), font=font)
    return Image.alpha_composite(img, overlay)


def process_icon(src_path, dst_path):
    """アイコン画像を加工して保存"""
    try:
        img = Image.open(src_path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        img.thumbnail(ICON_SIZE, Image.LANCZOS)
        canvas = Image.new("RGBA", ICON_SIZE, (0, 0, 0, 0))
        offset = ((ICON_SIZE[0] - img.size[0]) // 2, (ICON_SIZE[1] - img.size[1]) // 2)
        canvas.paste(img, offset, img)
        enhancer = ImageEnhance.Brightness(canvas)
        canvas = enhancer.enhance(1.03)
        enhancer = ImageEnhance.Contrast(canvas)
        canvas = enhancer.enhance(1.05)
        canvas = add_watermark(canvas, "GF", opacity=30)
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([(0, 0), (ICON_SIZE[0]-1, ICON_SIZE[1]-1)],
                        outline=(100, 100, 100, 60), width=1)
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        canvas.save(dst_path, "WEBP", quality=85)
        return True
    except Exception as e:
        print(f"  [ERROR] process_icon {src_path}: {e}")
        return False


def generate_placeholder_icon(weapon_name, dst_path):
    """プレースホルダーアイコン生成"""
    img = Image.new("RGBA", ICON_SIZE, (30, 30, 60, 255))
    draw = ImageDraw.Draw(img)
    initial = weapon_name[0] if weapon_name else "?"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except (OSError, IOError):
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initial, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((ICON_SIZE[0]-tw)//2, (ICON_SIZE[1]-th)//2 - 5), initial,
              fill=(200, 200, 255, 200), font=font)
    img = add_watermark(img, "GF", opacity=30)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (ICON_SIZE[0]-1, ICON_SIZE[1]-1)],
                    outline=(80, 80, 120, 100), width=1)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    img.save(dst_path, "WEBP", quality=85)


def build_icon_mapping_from_html():
    """HTMLからdata-lazy-src, alt属性で武器名→アイコンURLマッピング構築"""
    mapping = {}

    # Altema: weapon_list と tierlist のHTMLを解析
    for html_name in os.listdir(RAW_DIR / "altema" / "html"):
        html_path = RAW_DIR / "altema" / "html" / html_name
        if not html_path.suffix == ".html":
            continue
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except Exception:
            continue

        for img_tag in soup.find_all("img"):
            alt = img_tag.get("alt", "").strip()
            if not alt or len(alt) < 2 or len(alt) > 40:
                continue

            # data-lazy-src が本当のURL
            url = img_tag.get("data-lazy-src") or ""
            if not url or "1x1.trans" in url:
                url = img_tag.get("src") or ""
            if not url or "1x1.trans" in url or url.startswith("data:"):
                continue

            # 武器アイコンっぽいURLのみ (splatoon3ディレクトリ)
            if "splatoon3" in url and ("uploads" in url or "icon" in url.lower()):
                if alt not in mapping:
                    mapping[alt] = url

    # GameWith: 同様に解析
    for html_name in os.listdir(RAW_DIR / "gamewith" / "html"):
        html_path = RAW_DIR / "gamewith" / "html" / html_name
        if not html_path.suffix == ".html":
            continue
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except Exception:
            continue

        for img_tag in soup.find_all("img"):
            alt = img_tag.get("alt", "").strip()
            if not alt or len(alt) < 2 or len(alt) > 40:
                continue
            url = img_tag.get("data-src") or img_tag.get("data-lazy-src") or img_tag.get("src") or ""
            if not url or url.startswith("data:") or "1x1" in url:
                continue
            if ("splatoon" in url.lower() or "gamewith" in url.lower()) and alt not in mapping:
                mapping[alt] = url

    return mapping


def download_icon(url, save_path, retries=2):
    """アイコンをURLからダウンロード"""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
    return False


def find_local_icon(fname):
    """既存のローカルアイコンファイルを探す"""
    for site in ("altema", "gamewith", "game8"):
        for subdir in ("icons", "images"):
            path = RAW_DIR / site / subdir / fname
            if path.exists() and path.stat().st_size > 200:
                return path
    # weapon_iconsにもチェック
    path = ICON_DL_DIR / fname
    if path.exists() and path.stat().st_size > 200:
        return path
    return None


def main():
    print("=" * 60)
    print("フェーズ3: アイコン修正（data-lazy-src対応）")
    print("=" * 60)

    # 武器データ
    with open(CLEAN_DATA, "r", encoding="utf-8") as f:
        weapons = json.load(f)["weapons"]
    weapon_names = [w["name"] for w in weapons]
    print(f"武器数: {len(weapons)}")

    # サブウェポン・スペシャルの名前も収集
    sub_names = set()
    sp_names = set()
    for w in weapons:
        if w.get("sub"):
            sub_names.add(w["sub"])
        if w.get("special"):
            sp_names.add(w["special"])
    all_needed = set(weapon_names) | sub_names | sp_names
    print(f"必要なアイコン総数: {len(all_needed)}（武器:{len(weapon_names)}, サブ:{len(sub_names)}, SP:{len(sp_names)}）")

    # HTMLからマッピング構築
    print("\n--- HTMLからアイコンURL解析 ---")
    icon_map = build_icon_mapping_from_html()
    print(f"マッピング取得数: {len(icon_map)}")

    # 武器名とマッチするものを確認
    matched = 0
    unmatched = []
    for name in all_needed:
        if name in icon_map:
            matched += 1
        else:
            # 部分一致チェック
            found = False
            for map_name in icon_map:
                if name in map_name or map_name in name:
                    found = True
                    break
            if not found:
                unmatched.append(name)
    print(f"  完全一致: {matched}, 未マッチ: {len(unmatched)}")
    if unmatched[:10]:
        print(f"  未マッチ例: {unmatched[:10]}")

    # アイコンダウンロード
    print("\n--- アイコンダウンロード ---")
    os.makedirs(ICON_DL_DIR, exist_ok=True)
    dl_count = 0
    skip_count = 0
    fail_count = 0

    for name in sorted(all_needed):
        url = icon_map.get(name)
        if not url:
            # 部分一致を試す
            for map_name, map_url in icon_map.items():
                if name in map_name or map_name in name:
                    url = map_url
                    break

        if not url:
            continue

        # URLからファイル名を生成
        ext = url.split("?")[0].split(".")[-1]
        if ext not in ("png", "jpg", "jpeg", "webp", "gif"):
            ext = "png"
        safe_name = slug(name)
        save_path = ICON_DL_DIR / f"{safe_name}.{ext}"

        if save_path.exists() and save_path.stat().st_size > 200:
            skip_count += 1
            continue

        # ダウンロード
        if download_icon(url, str(save_path)):
            dl_count += 1
            if dl_count % 10 == 0:
                print(f"  DL: {dl_count}...")
            time.sleep(0.3)
        else:
            fail_count += 1

    print(f"  ダウンロード: {dl_count}, スキップ(既存): {skip_count}, 失敗: {fail_count}")

    # 武器アイコン加工
    print("\n--- 武器アイコン加工 ---")
    weapons_dir = OUTPUT_DIR / "weapons"
    ok_count = 0
    placeholder_count = 0

    for name in sorted(all_needed):
        safe = slug(name)
        dst = str(weapons_dir / f"{safe}.webp")

        # 既存の加工済みファイルがプレースホルダーでないかチェック
        # ダウンロード済みのアイコンがあれば再加工
        src_path = None

        # DLしたアイコンを最優先
        for ext in ("png", "jpg", "jpeg", "webp"):
            candidate = ICON_DL_DIR / f"{safe}.{ext}"
            if candidate.exists() and candidate.stat().st_size > 200:
                src_path = candidate
                break

        # ローカルの既存ファイルも検索
        if not src_path:
            url = icon_map.get(name)
            if url:
                fname = url.split("?")[0].split("/")[-1]
                src_path = find_local_icon(fname)

        if src_path:
            if process_icon(str(src_path), dst):
                ok_count += 1
            else:
                generate_placeholder_icon(name, dst)
                placeholder_count += 1
        else:
            generate_placeholder_icon(name, dst)
            placeholder_count += 1

    print(f"  加工済み: {ok_count}, プレースホルダー: {placeholder_count}")

    # サブウェポンとスペシャル用のディレクトリも作成
    subs_dir = OUTPUT_DIR / "subs"
    specials_dir = OUTPUT_DIR / "specials"

    print("\n--- サブウェポンアイコン整理 ---")
    for name in sorted(sub_names):
        safe = slug(name)
        src = weapons_dir / f"{safe}.webp"
        dst = subs_dir / f"{safe}.webp"
        os.makedirs(str(subs_dir), exist_ok=True)
        if src.exists():
            import shutil
            shutil.copy2(str(src), str(dst))

    print(f"  サブウェポン: {len(sub_names)}")

    print("\n--- スペシャルアイコン整理 ---")
    for name in sorted(sp_names):
        safe = slug(name)
        src = weapons_dir / f"{safe}.webp"
        dst = specials_dir / f"{safe}.webp"
        os.makedirs(str(specials_dir), exist_ok=True)
        if src.exists():
            import shutil
            shutil.copy2(str(src), str(dst))

    print(f"  スペシャル: {len(sp_names)}")

    # 統計
    total = 0
    for root, dirs, files in os.walk(str(OUTPUT_DIR)):
        total += len(files)
    print(f"\n{'='*60}")
    print(f"アイコン修正完了!")
    print(f"{'='*60}")
    print(f"出力先: {OUTPUT_DIR}")
    print(f"総ファイル数: {total}")


if __name__ == "__main__":
    main()
