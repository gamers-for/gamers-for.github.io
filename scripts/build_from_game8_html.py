#!/usr/bin/env python3
"""
build_from_game8_html.py
========================
Game8のスクレイプ済みHTMLをそのままコピーし、以下のみ変更:
1. アイコン画像 → ローカルパスに差し替え
2. 大きい画像（著作物） → プレースホルダーに差し替え
3. 文章 → 要約して口調を統一（コピペ禁止）
4. HTMLタグ・構成は完全に同一を維持
"""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag
from text_rewriter import rewrite_paragraph, rewrite_short_phrase

# ─── パス設定 ─────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "０００１スプラトゥーン３"
if not DATA_DIR.exists():
    DATA_DIR = PROJECT_ROOT / "００００１スプラトゥーン３"
RAW_HTML_DIR = DATA_DIR / "raw_html"
PARSED_DIR = DATA_DIR / "parsed_data"
CONTENT_DIR = PROJECT_ROOT / "content" / "games" / "splatoon3"
STATIC_IMG = PROJECT_ROOT / "static" / "images" / "games" / "splatoon3"

# Hugo baseURL prefix (for GitHub Pages)
BASE_URL_PREFIX = ""

# ─── マスターデータ読み込み ──────────────────────────
def load_master_data():
    with open(PARSED_DIR / "splatoon3_master_merged.json", "r") as f:
        return json.load(f)

def load_url_map():
    with open(RAW_HTML_DIR / "_url_map.json", "r") as f:
        return json.load(f)


# ─── 画像マッピング構築 ──────────────────────────────
def build_image_mappings(master_data):
    """alt属性ベースで Game8 画像 → ローカルパスのマッピングを構築"""
    weapons = master_data["weapons"]

    # 武器名 → 武器アイコン
    weapon_icon_map = {}
    for w in weapons:
        name = w["name"]
        icon = w.get("icon", "")
        if icon:
            weapon_icon_map[name] = BASE_URL_PREFIX + icon

    # サブ名 → サブアイコン
    sub_icon_map = {}
    for w in weapons:
        sub = w.get("sub", "")
        sub_icon = w.get("sub_icon", "")
        if sub and sub_icon and sub not in sub_icon_map:
            sub_icon_map[sub] = BASE_URL_PREFIX + sub_icon

    # スペシャル名 → スペシャルアイコン
    special_icon_map = {}
    for w in weapons:
        sp = w.get("special", "")
        sp_icon = w.get("special_icon", "")
        if sp and sp_icon and sp not in special_icon_map:
            special_icon_map[sp] = BASE_URL_PREFIX + sp_icon

    # ティアバッジ
    tier_map = {
        "X": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/x.webp",
        "S＋": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/splus.webp",
        "S+": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/splus.webp",
        "S": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/s.webp",
        "A＋": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/aplus.webp",
        "A+": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/aplus.webp",
        "A": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/a.webp",
        "B＋": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/bplus.webp",
        "B+": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/bplus.webp",
        "B": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/b.webp",
        "C＋": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/cplus.webp",
        "C+": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/cplus.webp",
        "C": f"{BASE_URL_PREFIX}/images/games/splatoon3/tiers/c.webp",
    }

    return weapon_icon_map, sub_icon_map, special_icon_map, tier_map


# ─── ギアパワー画像マッピング ─────────────────────────
GEAR_POWER_ICONS = {
    "インク効率アップ（メイン）": "gear-powers/ink-saver-main.png",
    "インク効率アップ(メイン)": "gear-powers/ink-saver-main.png",
    "インク効率アップ（サブ）": "gear-powers/ink-saver-sub.png",
    "インク効率アップ(サブ)": "gear-powers/ink-saver-sub.png",
    "インク回復力アップ": "gear-powers/ink-recovery-up.png",
    "ヒト移動速度アップ": "gear-powers/run-speed-up.png",
    "イカダッシュ速度アップ": "gear-powers/swim-speed-up.png",
    "スペシャル増加量アップ": "gear-powers/special-charge-up.png",
    "スペシャル減少量ダウン": "gear-powers/special-saver.png",
    "スペシャル性能アップ": "gear-powers/special-power-up.png",
    "復活時間短縮": "gear-powers/quick-respawn.png",
    "スーパージャンプ時間短縮": "gear-powers/quick-super-jump.png",
    "サブ性能アップ": "gear-powers/sub-power-up.png",
    "相手インク影響軽減": "gear-powers/ink-resistance-up.png",
    "サブ影響軽減": "gear-powers/sub-resistance-up.png",
    "アクション強化": "gear-powers/intensify-action.png",
    "スタートダッシュ": "gear-powers/opening-gambit.png",
    "ラストスパート": "gear-powers/last-ditch-effort.png",
    "逆境強化": "gear-powers/tenacity.png",
    "カムバック": "gear-powers/comeback.png",
    "イカニンジャ": "gear-powers/ninja-squid.png",
    "リベンジ": "gear-powers/haunt.png",
    "サーマルインク": "gear-powers/thermal-ink.png",
    "復活ペナルティアップ": "gear-powers/respawn-punisher.png",
    "追加ギアパワー倍化": "gear-powers/ability-doubler.png",
    "ステルスジャンプ": "gear-powers/stealth-jump.png",
    "対物攻撃力アップ": "gear-powers/object-shredder.png",
    "受け身術": "gear-powers/drop-roller.png",
}

# ─── 星評価画像マッピング ─────────────────────────
STAR_ICONS = {
    "星1": "stars/star1.png",
    "星2": "stars/star2.png",
    "星3": "stars/star3.png",
    "星4": "stars/star4.png",
    "星5": "stars/star5.png",
}

# ─── ルールアイコンマッピング ─────────────────────────
RULE_ICONS = {
    "スプラトゥーン3のナワバリバトル": "rules/turf-war.png",
    "スプラトゥーン3のナワバリ": "rules/turf-war.png",
    "スプラトゥーン2のナワバリ": "rules/turf-war.png",
    "ナワバリバトル": "rules/turf-war.png",
    "ナワバリ": "rules/turf-war.png",
    "スプラトゥーン3のガチエリア": "rules/splat-zones.png",
    "スプラトゥーン2のガチエリア": "rules/splat-zones.png",
    "ガチエリア": "rules/splat-zones.png",
    "スプラトゥーン3のガチヤグラ": "rules/tower-control.png",
    "スプラトゥーン2のガチヤグラ": "rules/tower-control.png",
    "ガチヤグラ": "rules/tower-control.png",
    "スプラトゥーン3のガチホコバトル": "rules/rainmaker.png",
    "スプラトゥーン3のガチホコ": "rules/rainmaker.png",
    "スプラトゥーン2のガチホコ": "rules/rainmaker.png",
    "ガチホコ": "rules/rainmaker.png",
    "スプラトゥーン3のガチアサリ": "rules/clam-blitz.png",
    "スプラトゥーン2のガチアサリ": "rules/clam-blitz.png",
    "ガチアサリ": "rules/clam-blitz.png",
}

# ─── マーカーアイコンマッピング ────────────────────────
MARKER_ICONS = {
    "強い点": "markers/check.png",
    "弱い点": "markers/cross.png",
    "ポイント": "markers/check.png",
    "NG行動": "markers/cross.png",
    "残念ポイント": "markers/cross.png",
    "注意": "markers/point.png",
}

# ─── ブランドアイコンマッピング ────────────────────────
BRAND_ICONS = {
    "アイロニック": "brands/annaki.png",
    "エンペリー": "brands/enperry.png",
    "クラーゲス": "brands/krak-on.png",
    "シグレニ": "brands/barazushi.png",
    "ジモン": "brands/jimon.png",
    "タタキケンサキ": "brands/takoroka.png",
    "バトロイカ": "brands/splash-mob.png",
    "フォーリマ": "brands/forge.png",
    "ホタックス": "brands/toni-kensa.png",
    "ロッケンベルグ": "brands/rockenberg.png",
    "アロメ": "brands/zekko.png",
    "ヤコ": "brands/inkline.png",
    "ジュナイパー": "brands/zink.png",
    "クマサン商会": "brands/grizzco.png",
    "amiibo": "brands/amiibo.png",
    "アタリメイド": "brands/cuttlegear.png",
    "アナアキ": "brands/anaki.png",
    "エゾッコ": "brands/ezokko.png",
    "エゾッコリー": "brands/ezokkori.png",
    "ホッコリー": "brands/hokkori.png",
    "バラズシ": "brands/barazushi.png",
    "シチリン": "brands/shichirin.png",
}

# ─── Switchボタンアイコンマッピング ────────────────────────
BUTTON_ICONS = {
    "Nintendo SwitchのBボタン": "buttons/b-button.png",
    "Nintendo SwitchのXボタン": "buttons/x-button.png",
    "Nintendo SwitchのYボタン": "buttons/y-button.png",
    "Nintendo SwitchのZLボタン": "buttons/zl-button.png",
    "Nintendo SwitchのZRボタン": "buttons/zr-button.png",
    "Nintendo SwitchのLスティック": "buttons/l-stick.png",
    "Nintendo SwitchのRスティック": "buttons/r-stick.png",
}

# ─── 武器種アイコンマッピング ─────────────────────────
WEAPON_CLASS_ICONS = {
    "シューター": "weapon_class/shooter.png",
    "ブラスター": "weapon_class/blaster.png",
    "ローラー": "weapon_class/roller.png",
    "フデ": "weapon_class/brush.png",
    "チャージャー": "weapon_class/charger.png",
    "スロッシャー": "weapon_class/slosher.png",
    "スピナー": "weapon_class/splatling.png",
    "マニューバー": "weapon_class/dualie.png",
    "シェルター": "weapon_class/brella.png",
    "ストリンガー": "weapon_class/stringer.png",
    "ワイパー": "weapon_class/splatana.png",
}


# ─── HTMLクリーンアップ ──────────────────────────────
def extract_article_content(html_text):
    """HTMLから .archive-style-wrapper の中身を抽出"""
    soup = BeautifulSoup(html_text, "html.parser")
    wrapper = soup.find(class_="archive-style-wrapper")
    if not wrapper:
        return None, None

    # タイトルを取得
    title_tag = soup.find("title")
    title = ""
    if title_tag:
        title = title_tag.get_text()
        # 「｜ゲームエイト」を除去
        title = re.sub(r'[｜|]\s*ゲームエイト.*$', '', title)
        title = title.strip()

    return wrapper, title


def remove_unwanted_elements(wrapper):
    """不要な要素を除去（広告・トラッキング・スクリプトのみ）

    目次(a-outline)、▶︎リンク、関連記事、空のpは全て残す。
    """
    # Video要素（game8の動画）→ <img>プレースホルダーに変換（テキスト漏れ防止）
    for video in wrapper.find_all("video"):
        soup_root = video
        while soup_root.parent:
            soup_root = soup_root.parent
        placeholder_img = soup_root.new_tag("img",
            src=f"{BASE_URL_PREFIX}/images/games/splatoon3/placeholder-icon.png",
            alt="動画", width="50", height="50",
            **{"class": "a-img", "loading": "lazy"})
        video.replace_with(placeholder_img)

    # 広告ラッパー
    for el in wrapper.find_all(class_="ad-wrapper"):
        el.decompose()

    # トラッキングリンク
    for el in wrapper.find_all("a", class_="track_mario"):
        el.decompose()
    for el in wrapper.find_all("a", class_="premium-plan-link"):
        el.decompose()

    # scriptタグ
    for el in wrapper.find_all("script"):
        el.decompose()

    # noscript
    for el in wrapper.find_all("noscript"):
        el.decompose()

    # div.ad-* (広告系div)
    for el in wrapper.find_all("div", class_=re.compile(r"ad[-_]")):
        el.decompose()

    # googletag系
    for el in wrapper.find_all("div", id=re.compile(r"^div-gpt")):
        el.decompose()


def process_images(wrapper, weapon_icon_map, sub_icon_map, special_icon_map, tier_map, weapon_name=""):
    """画像をローカルパスに差し替え。

    重要: <img>タグは絶対に<span>や<div>に変換しない。
    全ての<img>は<img>のまま維持し、srcのみ変更する。
    大きい画像（width>200）のみプレースホルダーdivに変換。
    """
    IMG_PREFIX = f"{BASE_URL_PREFIX}/images/games/splatoon3/"

    # BeautifulSoup objectを取得（new_tag用）
    soup = wrapper
    while soup.parent:
        soup = soup.parent

    for img in wrapper.find_all("img"):
        alt = img.get("alt", "")
        width_str = img.get("width", "")
        data_src = img.get("data-src", "")
        src = img.get("src", "")
        actual_src = data_src or src

        try:
            width = int(width_str) if width_str else 0
        except ValueError:
            width = 0

        # data-src → src に移動
        if data_src:
            img["src"] = data_src
            del img["data-src"]

        # lazy クラスを loading="lazy" に変換
        classes = img.get("class", [])
        if "lazy" in classes:
            classes = [c for c in classes if c not in ("lazy", "lazy-non-square")]
            img["class"] = classes
            img["loading"] = "lazy"

        # style属性のpadding-bottom hack を除去
        style = img.get("style", "")
        if "padding-bottom" in style:
            del img["style"]

        # --- 大きい画像 (hero, width>200) → <img>のままsrcをプレースホルダーに ---
        if width > 200 or (width == 0 and "original" in actual_src):
            img["src"] = IMG_PREFIX + "placeholder-icon.png"
            img["loading"] = "lazy"
            if "img-placeholder" not in img.get("class", []):
                current_classes = img.get("class", [])
                if isinstance(current_classes, str):
                    current_classes = [current_classes]
                img["class"] = current_classes + ["img-placeholder"]
            continue

        # --- ティアバッジ (S, S+, A, etc.) ---
        normalized_alt = alt.replace("＋", "+")
        if normalized_alt in tier_map:
            img["src"] = tier_map[normalized_alt]
            img["loading"] = "lazy"
            continue

        # --- 「画像」を除去してマッチ ---
        # Ⅴ(ローマ数字)→V、全角→半角 等のNFKC正規化
        normalized_name = unicodedata.normalize("NFKC", alt)
        clean_alt = re.sub(r'画像$', '', normalized_name)

        # --- 武器名マッチ ---
        if clean_alt in weapon_icon_map:
            img["src"] = weapon_icon_map[clean_alt]
            img["loading"] = "lazy"
            continue

        # --- サブ名マッチ ---
        if clean_alt in sub_icon_map:
            img["src"] = sub_icon_map[clean_alt]
            img["loading"] = "lazy"
            continue

        # --- スペシャル名マッチ ---
        if clean_alt in special_icon_map:
            img["src"] = special_icon_map[clean_alt]
            img["loading"] = "lazy"
            continue

        # --- ギアパワーアイコン ---
        if clean_alt in GEAR_POWER_ICONS:
            img["src"] = IMG_PREFIX + GEAR_POWER_ICONS[clean_alt]
            img["loading"] = "lazy"
            continue

        # --- 星評価画像 ---
        star_match = re.match(r'星(\d+)', clean_alt)
        if star_match:
            star_key = f"星{star_match.group(1)}"
            if star_key in STAR_ICONS:
                img["src"] = IMG_PREFIX + STAR_ICONS[star_key]
                img["loading"] = "lazy"
                continue

        # --- ルールアイコン ---
        if alt in RULE_ICONS:
            img["src"] = IMG_PREFIX + RULE_ICONS[alt]
            img["loading"] = "lazy"
            continue

        # --- マーカーアイコン (強い点/弱い点/ポイント/NG行動) ---
        if alt in MARKER_ICONS:
            img["src"] = IMG_PREFIX + MARKER_ICONS[alt]
            img["loading"] = "lazy"
            continue

        # --- ブランドアイコン ---
        if clean_alt in BRAND_ICONS:
            img["src"] = IMG_PREFIX + BRAND_ICONS[clean_alt]
            img["loading"] = "lazy"
            continue

        # --- 武器種アイコン ---
        if clean_alt in WEAPON_CLASS_ICONS:
            img["src"] = IMG_PREFIX + WEAPON_CLASS_ICONS[clean_alt]
            img["loading"] = "lazy"
            continue

        # --- Switchボタンアイコン ---
        if alt in BUTTON_ICONS:
            img["src"] = IMG_PREFIX + BUTTON_ICONS[alt]
            img["loading"] = "lazy"
            continue

        # --- その他のGame8画像 → <img>のまま、汎用プレースホルダー画像に ---
        if "game8.jp" in actual_src or "img.game8.jp" in actual_src:
            img["src"] = IMG_PREFIX + "placeholder-icon.png"
            img["loading"] = "lazy"
            continue


def process_links(wrapper, url_map):
    """リンクをサイト内リンクに変換"""
    weapons_urls = url_map.get("weapons", {})
    stages_urls = url_map.get("stages", {})
    main_urls = url_map.get("main", {})

    # URL → サイト内パスのマッピング
    url_to_local = {}

    for name, url in weapons_urls.items():
        slug = weapon_name_to_slug(name)
        url_to_local[url] = f"{BASE_URL_PREFIX}/games/splatoon3/weapons/{slug}/"

    for name, url in stages_urls.items():
        slug = name.lower()
        url_to_local[url] = f"{BASE_URL_PREFIX}/games/splatoon3/stages/{slug}/"

    for key, url in main_urls.items():
        # メインページのマッピング
        main_page_map = {
            "tier_list": "tier-list",
            "tier_nawabari": "tier-nawabari",
            "tier_area": "tier-area",
            "tier_yagura": "tier-yagura",
            "tier_hoko": "tier-hoko",
            "tier_asari": "tier-asari",
            "stage_list": "stages",
            "gear_power_ranking": "gear-powers",
            "gear_power_list": "gear-powers",
            "gear_list": "gear",
            "salmon_run": "salmon-run",
        }
        if key in main_page_map:
            url_to_local[url] = f"{BASE_URL_PREFIX}/games/splatoon3/{main_page_map[key]}/"

    for a in wrapper.find_all("a"):
        href = a.get("href", "")

        # Game8の絶対URL
        if "game8.jp" in href:
            full_url = href
            # URLマップからマッチ
            matched = False
            for g8_url, local_path in url_to_local.items():
                if g8_url in full_url or full_url in g8_url:
                    a["href"] = local_path
                    matched = True
                    break
            if not matched:
                # マッチしないGame8リンク → <a>タグ維持、href="#"に
                a["href"] = "#"
            continue

        # Game8の相対URL (/splatoon3/xxxx)
        if href.startswith("/splatoon3/"):
            # IDで検索
            article_id = href.split("/")[-1]
            matched = False
            for g8_url, local_path in url_to_local.items():
                if article_id in g8_url:
                    a["href"] = local_path
                    matched = True
                    break
            if not matched:
                a["href"] = "#"
            continue

        # その他の外部リンク → <a>タグ維持、href="#"に
        if href.startswith("http"):
            a["href"] = "#"
            continue

    # トラッキング属性を除去
    for a in wrapper.find_all("a"):
        for attr in list(a.attrs.keys()):
            if attr.startswith("data-track"):
                del a[attr]


def _rewrite_text_nodes(element, weapon_name, base_idx, use_short=False):
    """要素内の全テキストノードを再帰的にリライト（<b>, <strong>等の中も含む）"""
    idx = base_idx
    for child in list(element.children):
        if isinstance(child, NavigableString):
            original = str(child)
            if original.strip() and len(original.strip()) > 3:
                if use_short:
                    rewritten = rewrite_short_phrase(original, weapon_name, idx)
                else:
                    rewritten = rewrite_paragraph(original, weapon_name, idx)
                child.replace_with(NavigableString(rewritten))
                idx += 1
        elif isinstance(child, Tag) and child.name in ("b", "strong", "em", "span", "a", "div"):
            # インライン要素＋div（強い点/弱い点の.align div）の中も再帰的にリライト
            idx = _rewrite_text_nodes(child, weapon_name, idx, use_short)
    return idx


def rewrite_text(wrapper, weapon_name=""):
    """テキストを本格的にリライト（定型文置換＋文構造変換＋口調変換）

    全テキストノードを対象（<b>, <strong>内も含む）
    """
    idx = 0

    # --- パラグラフ（p.a-paragraph）のリライト ---
    for p in wrapper.find_all("p", class_="a-paragraph"):
        # テーブル内のpは除外（テーブルは別途処理）
        if p.find_parent("table"):
            continue
        text = p.get_text(strip=True)
        if not text:
            continue
        idx = _rewrite_text_nodes(p, weapon_name, idx)

    # --- テーブル内テキスト（ギア理由、強い点/弱い点など）のリライト ---
    for td in wrapper.find_all("td"):
        text = td.get_text(strip=True)
        if not text or len(text) < 4:
            continue
        # thの隣にあるデータセル（数値や武器名のみ）はスキップ
        # ギア理由、強い点/弱い点などの説明テキストのみリライト
        idx = _rewrite_text_nodes(td, weapon_name, 1000 + idx)

    # --- リスト内テキストのリライト ---
    for li in wrapper.find_all("li"):
        if li.find_parent("ul", class_="a-outline"):
            continue  # 目次はスキップ
        idx = _rewrite_text_nodes(li, weapon_name, 2000 + idx, use_short=True)


# ─── 武器名 → slug 変換 ─────────────────────────────
def weapon_name_to_slug(name):
    """武器名をURL用slugに変換"""
    slug = name.lower()
    # 全角→半角
    slug = unicodedata.normalize("NFKC", slug)
    # スペース/記号をハイフンに
    slug = re.sub(r'[\s/・]+', '-', slug)
    # 特殊文字除去
    slug = re.sub(r'[^\w\-ぁ-んァ-ヶ一-龥々]', '', slug)
    return slug


# ─── ベース武器マッピング ────────────────────────────
def build_base_weapon_map(weapons):
    """HTMLなし武器のベース武器を特定"""
    base_map = {}

    # 武器名パターンから基本武器を推定
    weapon_names = [w["name"] for w in weapons]

    variant_patterns = [
        # 煌、爪、冥、耀、蹄、封、繚、角、惑、幕、圧、彗、艶、彩
        (r'^(.+?)(煌|爪|冥|耀|蹄|封|繚|角|惑|幕|圧|彗|艶|彩)$', None),
        # ANGL, CREM, GECK, COBR, OWL, WNTR, ASH, FRZN, ROSE, PYTN, FRST, RUST, MILK, BRNZ, SNAK
        (r'^(.+?)(ANGL|CREM|GECK|COBR|OWL|WNTR|ASH|FRZN|ROSE|PYTN|FRST|RUST|MILK|BRNZ|SNAK)$', None),
        # ヒュー
        (r'^(.+?)(ヒュー)$', None),
        # スミ
        (r'^(.+?)(スミ)$', None),
        # 燈
        (r'^(.+?)(燈)$', None),
    ]

    # 特定の手動マッピング
    manual_map = {
        ".96ガロン爪": "96ガロン",
        "H3リールガンSNAK": "H3リールガン",
        "L3リールガン箔": "L3リールガン",
        "LACT-450MILK": "LACT-450",
        "LACT-450デコ": "LACT-450",
        "R-PEN/5B": "R-PEN/5H",
        "RブラスターエリートWNTR": "Rブラスターエリート",
        "カーボンローラーANGL": "カーボンローラー",
        "キャンピングシェルターCREM": "キャンピングシェルター",
        "シャープマーカーGECK": "シャープマーカー",
        "ジェットスイーパーCOBR": "ジェットスイーパー",
        "ジムワイパー封": "ジムワイパー",
        "スパイガジェット繚": "スパイガジェット",
        "スパッタリーOWL": "スパッタリー",
        "スプラシューター煌": "スプラシューター",
        "スプラスコープFRST": "スプラスコープ",
        "スプラスピナーPYTN": "スプラスピナー",
        "スプラチャージャーFRST": "スプラチャージャー",
        "スプラマニューバー耀": "スプラマニューバー",
        "スペースシューターコラボ": "スペースシューター",
        "ダイナモローラー冥": "ダイナモローラー",
        "デュアルスイーパー蹄": "デュアルスイーパー",
        "デンタルワイパースミ": "デンタルワイパーミント",
        "トライストリンガーコラボ": "トライストリンガー",
        "トライストリンガー燈": "トライストリンガー",
        "ドライブワイパーRUST": "ドライブワイパー",
        "ドライブワイパーデコ": "ドライブワイパー",
        "ハイドラント圧": "ハイドラント",
        "バレルスピナーROSE": "バレルスピナー",
        "パブロヒュー": "パブロ",
        "パラシェルター幕": "パラシェルター",
        "ヒッセンASH": "ヒッセン",
        "フィンセント": "フィンセントヒュー",
        "フィンセントBRNZ": "フィンセントヒュー",
        "フィンセントヒュー": None,  # 自身がHTMLある場合はskip
        "フルイドV": "LACT-450",
        "フルイドVカスタム": "LACT-450",
        "プライムシューターFRZN": "プライムシューター",
        "プロモデラー彩": "プロモデラーMG",
        "ホクサイヒュー": "ホクサイ",
        "ホクサイ彗": "ホクサイ",
        "ホットブラスター艶": "ホットブラスター",
        "モップリン角": "モップリン",
        "ワイドローラー惑": "ワイドローラー",
    }

    return manual_map


# ─── フロントマター生成 ────────────────────────────
def generate_front_matter(weapon_data, title=""):
    """Hugo用フロントマターを生成"""
    name = weapon_data["name"]
    weapon_class = weapon_data.get("class", "")
    sub = weapon_data.get("sub", "")
    special = weapon_data.get("special", "")
    tier = weapon_data.get("tier", "")

    if not title:
        title = f"【スプラ3】{name}の評価・立ち回り・おすすめギア"

    # descriptionを自動生成
    desc = f"スプラトゥーン3の{name}の性能評価・立ち回り解説。"
    if sub:
        desc += f"サブ{sub}、"
    if special:
        desc += f"スペシャル{special}の使い方や"
    desc += "おすすめギアパワーを紹介。"

    # ティアからweight算出
    tier_weights = {"X": 10, "S+": 20, "S＋": 20, "S": 30, "A+": 40, "A＋": 40,
                    "A": 50, "B+": 60, "B＋": 60, "B": 70, "C+": 80, "C＋": 80, "C": 90}
    weight = tier_weights.get(tier, 50)

    fm = f"""---
title: "{title}"
linkTitle: "{name}"
weight: {weight}
date: 2026-02-13
categories: ["{weapon_class}"]
tags: ["スプラトゥーン3", "{weapon_class}", "{name}"]
description: "{desc}"
---

"""
    return fm


# ─── メインページ用フロントマター ─────────────────────
MAIN_PAGE_CONFIG = {
    "main_tier_list.html": {
        "path": "tier-list.md",
        "title": "【スプラ3】最強武器ランキング・ティアリスト",
        "desc": "スプラトゥーン3の最強武器ランキング。全武器のティア評価を掲載。",
        "weight": 1,
    },
    "main_tier_nawabari.html": {
        "path": "tier-nawabari.md",
        "title": "【スプラ3】ナワバリバトル最強武器ランキング",
        "desc": "スプラトゥーン3のナワバリバトルにおける最強武器ランキング。",
        "weight": 2,
    },
    "main_tier_area.html": {
        "path": "tier-area.md",
        "title": "【スプラ3】ガチエリア最強武器ランキング",
        "desc": "スプラトゥーン3のガチエリアにおける最強武器ランキング。",
        "weight": 3,
    },
    "main_tier_yagura.html": {
        "path": "tier-yagura.md",
        "title": "【スプラ3】ガチヤグラ最強武器ランキング",
        "desc": "スプラトゥーン3のガチヤグラにおける最強武器ランキング。",
        "weight": 4,
    },
    "main_tier_hoko.html": {
        "path": "tier-hoko.md",
        "title": "【スプラ3】ガチホコ最強武器ランキング",
        "desc": "スプラトゥーン3のガチホコにおける最強武器ランキング。",
        "weight": 5,
    },
    "main_tier_asari.html": {
        "path": "tier-asari.md",
        "title": "【スプラ3】ガチアサリ最強武器ランキング",
        "desc": "スプラトゥーン3のガチアサリにおける最強武器ランキング。",
        "weight": 6,
    },
    "main_stage_list.html": {
        "path": "stages.md",
        "title": "【スプラ3】ステージ一覧と評価",
        "desc": "スプラトゥーン3のステージ一覧。各ステージの特徴と攻略情報。",
        "weight": 10,
    },
    "main_gear_power_ranking.html": {
        "path": "gear-powers.md",
        "title": "【スプラ3】ギアパワーランキング・おすすめ一覧",
        "desc": "スプラトゥーン3のギアパワーランキング。おすすめギアパワーと効果を解説。",
        "weight": 15,
    },
    "main_gear_power_list.html": {
        "path": "gear-tier.md",
        "title": "【スプラ3】ギアパワー一覧と効果",
        "desc": "スプラトゥーン3の全ギアパワー一覧。各ギアの効果を解説。",
        "weight": 16,
    },
    "main_gear_list.html": {
        "path": "gear/index.md",
        "title": "【スプラ3】ギア一覧",
        "desc": "スプラトゥーン3のギア一覧。",
        "weight": 17,
    },
    "main_salmon_run.html": {
        "path": "salmon-run.md",
        "title": "【スプラ3】サーモンランの攻略と立ち回り",
        "desc": "スプラトゥーン3のサーモンラン攻略。立ち回りとコツを解説。",
        "weight": 20,
    },
    "main_beginner_guide.html": {
        "path": "beginner.md",
        "title": "【スプラ3】初心者向け攻略ガイド",
        "desc": "スプラトゥーン3の初心者向け攻略ガイド。基本操作から立ち回りまで。",
        "weight": 25,
    },
    "main_beginner_weapons.html": {
        "path": "beginner/index.md",
        "title": "【スプラ3】初心者におすすめの武器",
        "desc": "スプラトゥーン3の初心者におすすめの武器を紹介。",
        "weight": 26,
    },
}


# ─── ステージ用フロントマター ─────────────────────────
def generate_stage_front_matter(stage_name, title=""):
    if not title:
        title = f"【スプラ3】{stage_name}の攻略とおすすめ武器"
    desc = f"スプラトゥーン3の{stage_name}の攻略情報。おすすめ武器やルール別の立ち回りを解説。"

    fm = f"""---
title: "{title}"
linkTitle: "{stage_name}"
weight: 50
date: 2026-02-13
categories: ["ステージ"]
tags: ["スプラトゥーン3", "ステージ", "{stage_name}"]
description: "{desc}"
---

"""
    return fm


# ─── メイン処理関数 ──────────────────────────────
def process_weapon_html(html_path, weapon_data, weapon_icon_map, sub_icon_map,
                         special_icon_map, tier_map, url_map):
    """1つの武器HTMLを処理して .md ファイルの内容を返す"""

    with open(html_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    wrapper, title = extract_article_content(html_text)
    if not wrapper:
        print(f"  ⚠️ archive-style-wrapper not found in {html_path.name}")
        return None

    # クリーンアップ
    remove_unwanted_elements(wrapper)

    # 画像処理
    process_images(wrapper, weapon_icon_map, sub_icon_map, special_icon_map,
                   tier_map, weapon_data["name"])

    # リンク処理
    process_links(wrapper, url_map)

    # テキスト書き直し
    rewrite_text(wrapper, weapon_data["name"])

    # wrapperdivを除去して中身だけ取得
    inner_html = wrapper.decode_contents()

    # Game8名称の最終チェック・除去
    inner_html = remove_forbidden_names(inner_html)

    # フロントマター生成
    front_matter = generate_front_matter(weapon_data, title)

    return front_matter + inner_html


def process_generic_html(html_path, front_matter_str, weapon_icon_map, sub_icon_map,
                          special_icon_map, tier_map, url_map):
    """汎用HTMLページ（ステージ、メイン）を処理"""

    with open(html_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    wrapper, title = extract_article_content(html_text)
    if not wrapper:
        print(f"  ⚠️ archive-style-wrapper not found in {html_path.name}")
        return None

    remove_unwanted_elements(wrapper)
    process_images(wrapper, weapon_icon_map, sub_icon_map, special_icon_map, tier_map)
    process_links(wrapper, url_map)
    rewrite_text(wrapper, "generic_page")

    inner_html = wrapper.decode_contents()
    inner_html = remove_forbidden_names(inner_html)

    return front_matter_str + inner_html


def generate_variant_weapon(base_html_path, variant_data, base_data,
                             weapon_icon_map, sub_icon_map, special_icon_map,
                             tier_map, url_map):
    """HTMLなし武器：ベース武器のHTMLをコピーして名前/サブ/スペを変更"""

    with open(base_html_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    wrapper, _ = extract_article_content(html_text)
    if not wrapper:
        return None

    remove_unwanted_elements(wrapper)
    process_images(wrapper, weapon_icon_map, sub_icon_map, special_icon_map,
                   tier_map, variant_data["name"])
    process_links(wrapper, url_map)
    rewrite_text(wrapper, variant_data["name"])

    inner_html = wrapper.decode_contents()

    # ベース武器名 → バリアント武器名に置換
    base_name = base_data["name"]
    variant_name = variant_data["name"]
    inner_html = inner_html.replace(base_name, variant_name)

    # サブ・スペシャル名も置換
    if base_data.get("sub") != variant_data.get("sub"):
        inner_html = inner_html.replace(base_data["sub"], variant_data["sub"])
        # サブアイコンパスも置換
        if base_data.get("sub_icon") and variant_data.get("sub_icon"):
            inner_html = inner_html.replace(
                BASE_URL_PREFIX + base_data["sub_icon"],
                BASE_URL_PREFIX + variant_data["sub_icon"]
            )

    if base_data.get("special") != variant_data.get("special"):
        inner_html = inner_html.replace(base_data["special"], variant_data["special"])
        if base_data.get("special_icon") and variant_data.get("special_icon"):
            inner_html = inner_html.replace(
                BASE_URL_PREFIX + base_data["special_icon"],
                BASE_URL_PREFIX + variant_data["special_icon"]
            )

    # 武器アイコンも置換
    if base_data.get("icon") and variant_data.get("icon"):
        inner_html = inner_html.replace(
            BASE_URL_PREFIX + base_data["icon"],
            BASE_URL_PREFIX + variant_data["icon"]
        )

    inner_html = remove_forbidden_names(inner_html)

    front_matter = generate_front_matter(variant_data)
    return front_matter + inner_html


def remove_forbidden_names(html):
    """禁止ワードの最終除去"""
    # まずURLを除去（ワード置換前に実行しないとURLが壊れる）
    html = re.sub(r'https?://[a-z.]*game8\.jp[^\s"\'<>]*', '', html)
    html = re.sub(r'https?://img\.game8\.jp[^\s"\'<>]*', '', html)
    html = re.sub(r'https?://[a-z.]*gamewith[^\s"\'<>]*', '', html)
    html = re.sub(r'https?://[a-z.]*altema[^\s"\'<>]*', '', html)

    # 壊れたURLも除去 (img..jp等)
    html = re.sub(r'https?://img\.[a-z.]*\.jp[^\s"\'<>]*', '', html)

    # 空のsrc属性を持つ要素を処理（<img>タグは維持、srcのみ変更）
    IMG_PREFIX = f"{BASE_URL_PREFIX}/images/games/splatoon3/"
    html = re.sub(r'<source[^>]*src=""[^>]*/?>', '', html)
    html = re.sub(r'<video[^>]*>\s*</video>', '', html)
    html = re.sub(r'src=""', f'src="{IMG_PREFIX}placeholder-icon.png"', html)

    # テキスト中の禁止ワード除去
    forbidden = [
        "Game8", "game8", "GameWith", "gamewith", "Altema", "altema",
        "ゲームエイト", "ゲーム8", "ゲームウィズ", "アルテマ",
        "3サイト", "攻略班",
    ]
    for word in forbidden:
        html = html.replace(word, "")

    return html


# ─── エントリーポイント ──────────────────────────────
def main():
    print("=" * 60)
    print("Game8 HTML → Hugo コンテンツ生成")
    print("=" * 60)

    # データ読み込み
    master_data = load_master_data()
    url_map = load_url_map()
    weapons = master_data["weapons"]
    weapons_by_name = {w["name"]: w for w in weapons}

    # 画像マッピング構築
    weapon_icon_map, sub_icon_map, special_icon_map, tier_map = build_image_mappings(master_data)

    # ベース武器マップ
    base_weapon_map = build_base_weapon_map(weapons)

    # HTMLファイルのインデックス構築
    html_files = {}
    for f in RAW_HTML_DIR.iterdir():
        if f.name.startswith("weapon_") and not f.name.startswith("weapon_class"):
            match = re.match(r'weapon_(.+?)_(\d+)\.html', f.name)
            if match:
                weapon_name = match.group(1)
                html_files[weapon_name] = f

    # ─── 武器ページ生成 ────────────────────
    weapons_dir = CONTENT_DIR / "weapons"
    weapons_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    skip_count = 0
    variant_count = 0

    print(f"\n📦 武器ページ生成 ({len(weapons)} weapons)")
    print("-" * 40)

    for weapon in weapons:
        name = weapon["name"]
        slug = weapon_name_to_slug(name)
        output_path = weapons_dir / f"{slug}.md"

        if name in html_files:
            # HTMLあり → 直接処理
            result = process_weapon_html(
                html_files[name], weapon,
                weapon_icon_map, sub_icon_map, special_icon_map, tier_map, url_map
            )
            if result:
                output_path.write_text(result, encoding="utf-8")
                success_count += 1
                print(f"  ✅ {name} → {slug}.md")
            else:
                skip_count += 1
                print(f"  ❌ {name} (処理失敗)")
        elif name in base_weapon_map and base_weapon_map[name]:
            # HTMLなし → ベース武器から生成
            base_name = base_weapon_map[name]
            if base_name in html_files and base_name in weapons_by_name:
                result = generate_variant_weapon(
                    html_files[base_name], weapon, weapons_by_name[base_name],
                    weapon_icon_map, sub_icon_map, special_icon_map, tier_map, url_map
                )
                if result:
                    output_path.write_text(result, encoding="utf-8")
                    variant_count += 1
                    print(f"  🔄 {name} (← {base_name}) → {slug}.md")
                else:
                    skip_count += 1
                    print(f"  ❌ {name} (ベース処理失敗)")
            else:
                skip_count += 1
                print(f"  ⚠️ {name} (ベース {base_name} のHTMLなし)")
        else:
            skip_count += 1
            print(f"  ⚠️ {name} (HTMLなし、ベース武器不明)")

    print(f"\n武器ページ: {success_count} 成功, {variant_count} バリアント, {skip_count} スキップ")

    # ─── ステージページ生成 ──────────────────
    stages_dir = CONTENT_DIR / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)

    stage_count = 0
    print(f"\n📦 ステージページ生成")
    print("-" * 40)

    for f in sorted(RAW_HTML_DIR.iterdir()):
        if f.name.startswith("stage_"):
            stage_name = f.name.replace("stage_", "").replace(".html", "")
            fm = generate_stage_front_matter(stage_name)
            result = process_generic_html(
                f, fm, weapon_icon_map, sub_icon_map, special_icon_map, tier_map, url_map
            )
            if result:
                slug = stage_name.lower()
                output_path = stages_dir / f"{slug}.md"
                output_path.write_text(result, encoding="utf-8")
                stage_count += 1
                print(f"  ✅ {stage_name} → {slug}.md")

    print(f"\nステージページ: {stage_count} 生成")

    # ─── メインページ生成 ──────────────────
    main_count = 0
    print(f"\n📦 メインページ生成")
    print("-" * 40)

    for html_name, config in MAIN_PAGE_CONFIG.items():
        html_path = RAW_HTML_DIR / html_name
        if not html_path.exists():
            print(f"  ⚠️ {html_name} が見つかりません")
            continue

        fm = f"""---
title: "{config['title']}"
weight: {config['weight']}
date: 2026-02-13
description: "{config['desc']}"
---

"""
        result = process_generic_html(
            html_path, fm, weapon_icon_map, sub_icon_map, special_icon_map, tier_map, url_map
        )
        if result:
            output_path = CONTENT_DIR / config["path"]
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result, encoding="utf-8")
            main_count += 1
            print(f"  ✅ {html_name} → {config['path']}")

    print(f"\nメインページ: {main_count} 生成")

    # ─── サマリー ──────────────────────────
    print("\n" + "=" * 60)
    print("生成完了!")
    print(f"  武器: {success_count + variant_count}")
    print(f"  ステージ: {stage_count}")
    print(f"  メイン: {main_count}")
    print(f"  合計: {success_count + variant_count + stage_count + main_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
