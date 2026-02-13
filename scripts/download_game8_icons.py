#!/usr/bin/env python3
"""
download_game8_icons.py
========================
Game8のraw HTMLからアイコンURLを抽出し、ダウンロードして透かし加工する。
Inkipediaアイコンを置き換えて、Game8と完全同一のアイコンを使用する。
"""

import json
import os
import re
import time
import unicodedata
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import io

# ─── パス設定 ─────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "０００１スプラトゥーン３"
if not DATA_DIR.exists():
    DATA_DIR = PROJECT_ROOT / "００００１スプラトゥーン３"
RAW_HTML_DIR = DATA_DIR / "raw_html"
STATIC_IMG = PROJECT_ROOT / "static" / "images" / "games" / "splatoon3"

# ─── 透かし設定 ─────────────────────────────────
WATERMARK_TEXT = "GF"
WATERMARK_OPACITY = 80  # 0-255


def get_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def add_watermark(img):
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    w, h = img.size
    font_size = max(8, int(h * 0.15))
    font = get_font(font_size)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    margin = max(1, int(min(w, h) * 0.03))
    x = margin
    y = h - text_h - margin - bbox[1]
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, WATERMARK_OPACITY))
    return Image.alpha_composite(img, overlay)


def download_image(url):
    """URLから画像をダウンロードしてPIL Imageで返す"""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data))
    except (URLError, HTTPError, Exception) as e:
        print(f"  ✗ ダウンロード失敗: {url}: {e}")
        return None


def save_icon(img, output_path):
    """透かし加工して保存（PNG）"""
    img_wm = add_watermark(img)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # PNG保存（透過対応）
    img_wm.save(output_path, "PNG")


# ─── alt→ローカルファイル名のマッピング ─────────────────

# サブウェポン
SUB_ICON_MAP = {
    "カーリングボム": "subs/curling-bomb.png",
    "キューバンボム": "subs/suction-bomb.png",
    "クイックボム": "subs/burst-bomb.png",
    "ジャンプビーコン": "subs/squid-beakon.png",
    "スプラッシュシールド": "subs/splash-wall.png",
    "スプラッシュボム": "subs/splat-bomb.png",
    "スプリンクラー": "subs/sprinkler.png",
    "スミナガシート": "subs/ink-vac.png",  # ver.10
    "タンサンボム": "subs/fizzy-bomb.png",
    "トラップ": "subs/ink-mine.png",
    "トーピード": "subs/torpedo.png",
    "ポイズンミスト": "subs/toxic-mist.png",
    "ポイントセンサー": "subs/point-sensor.png",
    "ラインマーカー": "subs/angle-shooter.png",
    "ロボットボム": "subs/autobomb.png",
}

# スペシャルウェポン
SPECIAL_ICON_MAP = {
    "アメフラシ": "specials/ink-storm.png",
    "ウルトラショット": "specials/trizooka.png",
    "ウルトラハンコ": "specials/ultra-stamp.png",
    "エナジースタンド": "specials/tacticooler.png",
    "カニタンク": "specials/crab-tank.png",
    "キューインキ": "specials/ink-vac.png",
    "グレートバリア": "specials/big-bubbler.png",
    "サメライド": "specials/reefslider.png",
    "ショクワンダー": "specials/zipcaster.png",
    "ジェットパック": "specials/inkjet.png",
    "テイオウイカ": "specials/kraken-royale.png",
    "デコイチラシ": "specials/wave-breaker.png",
    "トリプルトルネード": "specials/triple-inkstrike.png",
    "ナイスダマ": "specials/booyah-bomb.png",
    "ホップソナー": "specials/wave-breaker-hop.png",
    "マルチミサイル": "specials/tenta-missiles.png",
    "メガホンレーザー5.1ch": "specials/killer-wail-5-1.png",
    "スーパーチャクチ": "specials/super-chump.png",
}

# ギアパワー
GEAR_POWER_ICON_MAP = {
    "アクション強化": "gear-powers/intensify-action.png",
    "イカダッシュ速度アップ": "gear-powers/swim-speed-up.png",
    "イカニンジャ": "gear-powers/ninja-squid.png",
    "インク効率アップ（サブ）": "gear-powers/ink-saver-sub.png",
    "インク効率アップ（メイン）": "gear-powers/ink-saver-main.png",
    "インク回復力アップ": "gear-powers/ink-recovery-up.png",
    "カムバック": "gear-powers/comeback.png",
    "サブ影響軽減": "gear-powers/sub-resistance-up.png",
    "サブ性能アップ": "gear-powers/sub-power-up.png",
    "サーマルインク": "gear-powers/thermal-ink.png",
    "スタートダッシュ": "gear-powers/opening-gambit.png",
    "ステルスジャンプ": "gear-powers/stealth-jump.png",
    "スペシャル増加量アップ": "gear-powers/special-charge-up.png",
    "スペシャル性能アップ": "gear-powers/special-power-up.png",
    "スペシャル減少量ダウン": "gear-powers/special-saver.png",
    "スーパージャンプ時間短縮": "gear-powers/quick-super-jump.png",
    "ヒト移動速度アップ": "gear-powers/run-speed-up.png",
    "ラストスパート": "gear-powers/last-ditch-effort.png",
    "リベンジ": "gear-powers/haunt.png",
    "受け身術": "gear-powers/drop-roller.png",
    "対物攻撃力アップ": "gear-powers/object-shredder.png",
    "復活ペナルティアップ": "gear-powers/respawn-punisher.png",
    "復活時間短縮": "gear-powers/quick-respawn.png",
    "相手インク影響軽減": "gear-powers/ink-resistance-up.png",
    "逆境強化": "gear-powers/tenacity.png",
    "追加ギアパワー倍化": "gear-powers/ability-doubler.png",
}

# ティアランク
TIER_ICON_MAP = {
    "X": "tiers/x.png",
    "S＋": "tiers/splus.png",
    "S": "tiers/s.png",
    "A＋": "tiers/aplus.png",
    "A": "tiers/a.png",
    "B＋": "tiers/bplus.png",
    "B": "tiers/b.png",
    "C＋": "tiers/cplus.png",
    "C": "tiers/c.png",
}

# 星評価
STAR_ICON_MAP = {
    "星1": "stars/star1.png",
    "星2": "stars/star2.png",
    "星3": "stars/star3.png",
    "星4": "stars/star4.png",
    "星5": "stars/star5.png",
}

# ルール
RULE_ICON_MAP = {
    "スプラトゥーン3のナワバリバトル": "rules/turf-war.png",
    "スプラトゥーン3のガチエリア": "rules/splat-zones.png",
    "スプラトゥーン3のガチヤグラ": "rules/tower-control.png",
    "スプラトゥーン3のガチホコバトル": "rules/rainmaker.png",
    "スプラトゥーン3のガチアサリ": "rules/clam-blitz.png",
}

# マーカー（強い点/弱い点）
MARKER_ICON_MAP = {
    "強い点": "markers/check.png",
    "弱い点": "markers/cross.png",
}

# ブランド
BRAND_ICON_MAP = {
    "アイロニック": "brands/annaki.png",
    "アナアキ": "brands/anaki.png",
    "アロメ": "brands/zekko.png",
    "エゾッコ": "brands/ezokko.png",
    "エゾッコリー": "brands/ezokkori.png",
    "エンペリー": "brands/enperry.png",
    "クラーゲス": "brands/krak-on.png",
    "シチリン": "brands/shichirin.png",
    "ジモン": "brands/jimon.png",
    "タタキケンサキ": "brands/takoroka.png",
    "バトロイカ": "brands/splash-mob.png",
    "バラズシ": "brands/barazushi.png",
    "フォーリマ": "brands/forge.png",
    "ホタックス": "brands/toni-kensa.png",
    "ホッコリー": "brands/hokkori.png",
    "ヤコ": "brands/inkline.png",
    "ロッケンベルグ": "brands/rockenberg.png",
}

# 武器種
WEAPON_CLASS_ICON_MAP = {
    "シェルター": "weapon_class/brella.png",
    "シューター": "weapon_class/shooter.png",
    "ストリンガー": "weapon_class/stringer.png",
    "スピナー": "weapon_class/splatling.png",
    "スロッシャー": "weapon_class/slosher.png",
    "チャージャー": "weapon_class/charger.png",
    "フデ": "weapon_class/brush.png",
    "ブラスター": "weapon_class/blaster.png",
    "マニューバー": "weapon_class/dualie.png",
    "ローラー": "weapon_class/roller.png",
    "ワイパー": "weapon_class/splatana.png",
}

# Switchボタン
BUTTON_ICON_MAP = {
    "Nintendo SwitchのBボタン": "buttons/b-button.png",
    "Nintendo SwitchのXボタン": "buttons/x-button.png",
    "Nintendo SwitchのYボタン": "buttons/y-button.png",
    "Nintendo SwitchのZLボタン": "buttons/zl-button.png",
    "Nintendo SwitchのZRボタン": "buttons/zr-button.png",
    "Nintendo SwitchのLスティック": "buttons/l-stick.png",
    "Nintendo SwitchのRスティック": "buttons/r-stick.png",
}


def extract_icon_urls_from_html():
    """全raw HTMLファイルからアイコンURLを抽出"""
    # alt_text → game8_url のマッピング
    icon_urls = {}

    for html_path in sorted(RAW_HTML_DIR.iterdir()):
        if not html_path.name.endswith(".html"):
            continue

        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        for img in soup.find_all("img"):
            data_src = img.get("data-src", "")
            src = img.get("src", "")
            alt = img.get("alt", "")
            url = data_src or src

            if not url or "game8.jp" not in url:
                continue
            if not alt:
                continue

            # 「画像」を除去して正規化
            clean_alt = unicodedata.normalize("NFKC", alt)
            clean_alt = re.sub(r'(の)?画像$', '', clean_alt)

            # 既に登録済みならスキップ
            if clean_alt in icon_urls:
                continue

            icon_urls[clean_alt] = url

    return icon_urls


def load_weapon_icon_urls():
    """武器アイコンのURLを抽出（マスターデータのファイル名と対応）"""
    parsed_dir = DATA_DIR / "parsed_data"
    with open(parsed_dir / "splatoon3_master_merged.json", "r") as f:
        master = json.load(f)

    weapon_urls = {}
    for html_path in sorted(RAW_HTML_DIR.iterdir()):
        if not html_path.name.startswith("weapon_"):
            continue
        if html_path.name.startswith("weapon_class"):
            continue

        match = re.match(r'weapon_(.+?)_(\d+)\.html', html_path.name)
        if not match:
            continue

        weapon_name = match.group(1)

        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # 最初の大きい武器アイコンを探す（width=80のもの）
        for img in soup.find_all("img"):
            data_src = img.get("data-src", "")
            alt = img.get("alt", "")
            width = img.get("width", "")

            if not data_src or "game8.jp" not in data_src:
                continue

            clean_alt = unicodedata.normalize("NFKC", alt)
            clean_alt = re.sub(r'(の)?画像$', '', clean_alt)

            if clean_alt == weapon_name and width in ("80", "50", "60"):
                weapon_urls[weapon_name] = data_src
                break

    return weapon_urls, master["weapons"]


def main():
    print("=" * 60)
    print("Game8アイコンダウンロード＋透かし加工")
    print("=" * 60)

    # HTMLからURL抽出
    print("\n📦 HTMLからアイコンURL抽出中...")
    icon_urls = extract_icon_urls_from_html()
    print(f"  {len(icon_urls)} 個のユニークalt発見")

    # 各カテゴリーを処理
    all_maps = [
        ("サブウェポン", SUB_ICON_MAP),
        ("スペシャル", SPECIAL_ICON_MAP),
        ("ギアパワー", GEAR_POWER_ICON_MAP),
        ("ティア", TIER_ICON_MAP),
        ("星", STAR_ICON_MAP),
        ("ルール", RULE_ICON_MAP),
        ("マーカー", MARKER_ICON_MAP),
        ("ブランド", BRAND_ICON_MAP),
        ("武器種", WEAPON_CLASS_ICON_MAP),
        ("ボタン", BUTTON_ICON_MAP),
    ]

    total = 0
    for category_name, mapping in all_maps:
        print(f"\n--- {category_name} ---")
        count = 0
        for alt_key, local_file in mapping.items():
            # URLを探す
            url = icon_urls.get(alt_key)
            if not url:
                # NFKC正規化も試す
                nfkc_key = unicodedata.normalize("NFKC", alt_key)
                url = icon_urls.get(nfkc_key)
            if not url:
                # 半角括弧→全角括弧も試す
                alt_fw = alt_key.replace("(", "（").replace(")", "）")
                url = icon_urls.get(alt_fw)
            if not url:
                print(f"  ⚠️ URL見つからず: {alt_key}")
                continue

            output_path = STATIC_IMG / local_file
            # 既にダウンロード済みかチェック（強制再ダウンロード）
            img = download_image(url)
            if img is None:
                continue

            save_icon(img, str(output_path))
            count += 1
            print(f"  ✅ {alt_key} → {local_file}")
            time.sleep(0.1)  # サーバー負荷軽減

        print(f"  {count}/{len(mapping)} ダウンロード完了")
        total += count

    # 武器アイコン
    print(f"\n--- 武器アイコン ---")
    weapon_urls, weapons = load_weapon_icon_urls()
    weapon_count = 0

    # 武器名→iconパスのマッピング（マスターデータから）
    weapon_icon_paths = {}
    for w in weapons:
        name = w["name"]
        icon = w.get("icon", "")
        if icon:
            # /images/games/splatoon3/weapons/xxx.png → weapons/xxx.png
            local = icon.replace("/images/games/splatoon3/", "")
            weapon_icon_paths[name] = local

    for weapon_name, url in weapon_urls.items():
        local_file = weapon_icon_paths.get(weapon_name)
        if not local_file:
            print(f"  ⚠️ ローカルパス不明: {weapon_name}")
            continue

        output_path = STATIC_IMG / local_file

        img = download_image(url)
        if img is None:
            continue

        save_icon(img, str(output_path))
        weapon_count += 1
        if weapon_count % 20 == 0:
            print(f"  ... {weapon_count} 武器ダウンロード済み")
        time.sleep(0.05)

    print(f"  {weapon_count}/{len(weapon_urls)} 武器アイコンダウンロード完了")
    total += weapon_count

    # ティアのWebP版も生成（build_from_game8_html.pyがwebpを参照）
    print(f"\n--- ティアWebP変換 ---")
    tier_dir = STATIC_IMG / "tiers"
    for png_file in tier_dir.glob("*.png"):
        webp_file = png_file.with_suffix(".webp")
        try:
            img = Image.open(png_file)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.save(str(webp_file), "WEBP", quality=85)
            print(f"  ✅ {png_file.name} → {webp_file.name}")
        except Exception as e:
            print(f"  ✗ {png_file.name}: {e}")

    print(f"\n{'='*60}")
    print(f"合計: {total} アイコンダウンロード＋透かし加工完了")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
