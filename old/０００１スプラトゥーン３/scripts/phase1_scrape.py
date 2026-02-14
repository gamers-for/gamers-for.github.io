#!/usr/bin/env python3
"""
フェーズ1: Game8/GameWith/アルテマからスプラトゥーン3の全素材を取得
HTML, CSS, アイコン, 画像を raw_data/ に保存する

urls.json から正しいURLを読み込んで使用
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_data"
URLS_FILE = Path(__file__).resolve().parent / "urls.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

PAGE_INTERVAL = 5
IMG_INTERVAL = 0.3


def safe_filename(url_or_name):
    name = url_or_name.split("?")[0].split("#")[0].rstrip("/").split("/")[-1]
    if not name:
        name = hashlib.md5(url_or_name.encode()).hexdigest()[:12]
    name = re.sub(r'[<>:"|?*\\]', '_', name)
    return name[:200]


def fetch_url(url, session, binary=False):
    for attempt in range(3):
        try:
            resp = session.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                return resp.content if binary else resp.text
            elif resp.status_code in (403, 429):
                wait = 10 * (attempt + 1)
                print(f"  [{resp.status_code}] {url} - {wait}秒待機後リトライ {attempt+1}/3")
                time.sleep(wait)
            elif resp.status_code == 404:
                print(f"  [404] {url}")
                return None
            else:
                print(f"  [{resp.status_code}] {url} - リトライ {attempt+1}/3")
                time.sleep(5)
        except Exception as e:
            print(f"  [ERROR] {url}: {e}")
            time.sleep(5)
    return None


def save_file(path, content, binary=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if binary:
        with open(path, "wb") as f:
            f.write(content)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def download_image(url, save_dir, session, filename=None):
    if not url or url.startswith("data:"):
        return None
    url = url.split("?")[0]
    fname = filename or safe_filename(url)
    if not fname:
        return None
    save_path = os.path.join(save_dir, fname)
    if os.path.exists(save_path) and os.path.getsize(save_path) > 100:
        return fname
    data = fetch_url(url, session, binary=True)
    if data and len(data) > 100:
        save_file(save_path, data, binary=True)
        time.sleep(IMG_INTERVAL)
        return fname
    return None


def extract_css(soup, base_url, save_dir, session):
    css_files = []
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href", "")
        if not href:
            continue
        css_url = urllib.parse.urljoin(base_url, href)
        fname = safe_filename(css_url)
        if not fname.endswith(".css"):
            fname += ".css"
        fpath = os.path.join(save_dir, fname)
        if os.path.exists(fpath):
            css_files.append(fname)
            continue
        css_content = fetch_url(css_url, session)
        if css_content:
            save_file(fpath, css_content)
            css_files.append(fname)
            time.sleep(0.5)
    for i, style in enumerate(soup.find_all("style")):
        if style.string and len(style.string.strip()) > 10:
            fname = f"inline_{i}.css"
            save_file(os.path.join(save_dir, fname), style.string)
            css_files.append(fname)
    return css_files


def extract_images(soup, base_url, icons_dir, images_dir, session, max_icons=200, max_images=50):
    icon_count = 0
    image_count = 0
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
        if not src or src.startswith("data:"):
            continue
        img_url = urllib.parse.urljoin(base_url, src)
        classes = " ".join(img.get("class", []))
        alt = img.get("alt", "")

        is_icon = ("icon" in classes.lower() or "icon" in src.lower()
                    or "thumb" in classes.lower() or "thumb" in src.lower()
                    or "weapon" in src.lower() or "chara" in src.lower())

        if is_icon and icon_count < max_icons:
            result = download_image(img_url, icons_dir, session)
            if result:
                icon_count += 1
        elif not is_icon and image_count < max_images:
            result = download_image(img_url, images_dir, session)
            if result:
                image_count += 1
    return icon_count, image_count


def analyze_structure(soup, page_name, url):
    structure = {
        "page_name": page_name,
        "url": url,
        "title": "",
        "headings": [],
        "sections": [],
        "tables_count": 0,
        "images_count": 0,
    }
    title = soup.find("title")
    if title:
        structure["title"] = title.get_text(strip=True)
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = h.get_text(strip=True)
        if text:
            structure["headings"].append({"level": int(h.name[1]), "text": text[:100]})
    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)
        if text:
            structure["sections"].append(text[:100])
    structure["tables_count"] = len(soup.find_all("table"))
    structure["images_count"] = len(soup.find_all("img"))
    return structure


def extract_tier_data(soup, source_name):
    """ティアリストページからランキングデータを抽出"""
    weapons = []
    current_tier = ""

    for elem in soup.find_all(["h2", "h3", "h4", "tr", "li", "a", "div"]):
        text = elem.get_text(strip=True)

        # ティアランク検出
        if elem.name in ("h2", "h3", "h4"):
            for tier in ["SS", "S+", "S", "A+", "A", "B+", "B", "C+", "C", "D"]:
                if tier == text or (tier in text and any(kw in text for kw in ["ランク", "ティア", "Tier", "tier"])):
                    current_tier = tier
                    break

        # テーブル行からデータ取得
        if elem.name == "tr" and current_tier:
            cells = elem.find_all(["td", "th"])
            if cells:
                name = cells[0].get_text(strip=True)
                if name and 2 < len(name) < 40:
                    icon_img = cells[0].find("img")
                    icon_url = ""
                    if icon_img:
                        icon_url = icon_img.get("src") or icon_img.get("data-src") or ""
                    weapons.append({
                        "name": name, "tier": current_tier,
                        "icon_url": icon_url, "source": source_name
                    })

        # リストアイテムからデータ取得
        if elem.name == "li" and current_tier:
            link = elem.find("a")
            if link:
                name = link.get_text(strip=True)
                if name and 2 < len(name) < 40:
                    icon_img = elem.find("img")
                    icon_url = ""
                    if icon_img:
                        icon_url = icon_img.get("src") or icon_img.get("data-src") or ""
                    weapons.append({
                        "name": name, "tier": current_tier,
                        "icon_url": icon_url, "source": source_name
                    })

    # 重複除去
    seen = set()
    unique = []
    for w in weapons:
        key = w["name"]
        if key not in seen:
            seen.add(key)
            unique.append(w)
    return unique


def extract_weapon_list(soup, source_name):
    """武器一覧ページからデータ抽出"""
    weapons = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue
        # ヘッダー解析
        header = rows[0]
        header_cells = [c.get_text(strip=True) for c in header.find_all(["th", "td"])]

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            name = cells[0].get_text(strip=True)
            if not name or len(name) > 50 or len(name) < 2:
                continue
            weapon = {"name": name, "source": source_name}
            icon_img = cells[0].find("img")
            if icon_img:
                weapon["icon_url"] = icon_img.get("src") or icon_img.get("data-src") or ""
            for i, cell in enumerate(cells[1:], 1):
                col_name = header_cells[i] if i < len(header_cells) else f"col{i}"
                weapon[col_name] = cell.get_text(strip=True)
            weapons.append(weapon)

    # 重複除去
    seen = set()
    unique = []
    for w in weapons:
        if w["name"] not in seen:
            seen.add(w["name"])
            unique.append(w)
    return unique


def scrape_site(site_name, urls, session):
    """1サイト分を全スクレイピング"""
    site_dir = RAW_DIR / site_name
    print(f"\n{'='*60}")
    print(f"{site_name} スクレイピング開始 ({len(urls)}ページ)")
    print(f"{'='*60}")

    all_data = {}

    for page_name, url in urls.items():
        print(f"\n--- [{site_name}] {page_name}: {url} ---")

        # HTMLキャッシュチェック
        html_path = str(site_dir / "html" / f"{page_name}.html")
        if os.path.exists(html_path) and os.path.getsize(html_path) > 1000:
            print(f"  [cache] HTML already exists ({os.path.getsize(html_path)} bytes)")
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
        else:
            html = fetch_url(url, session)
            if not html:
                print(f"  [SKIP] 取得失敗")
                continue
            save_file(html_path, html)
            print(f"  [ok] HTML保存 ({len(html)} bytes)")

        soup = BeautifulSoup(html, "html.parser")

        # CSS（TOPページのみ）
        if page_name == "top":
            css_files = extract_css(soup, url, str(site_dir / "css"), session)
            print(f"  CSS: {len(css_files)}ファイル")

        # 画像・アイコン
        icons, images = extract_images(
            soup, url, str(site_dir / "icons"), str(site_dir / "images"), session
        )
        print(f"  アイコン: {icons}, 画像: {images}")

        # 構造分析
        structure = analyze_structure(soup, page_name, url)
        all_data[page_name] = structure

        # ティアデータ抽出
        if "tier" in page_name:
            tier_weapons = extract_tier_data(soup, site_name)
            if tier_weapons:
                all_data[f"{page_name}_weapons"] = tier_weapons
                print(f"  ティアデータ: {len(tier_weapons)}武器")

        # 武器一覧データ抽出
        if "weapon_list" in page_name:
            weapon_data = extract_weapon_list(soup, site_name)
            if weapon_data:
                all_data["all_weapons"] = weapon_data
                print(f"  武器一覧: {len(weapon_data)}武器")

        time.sleep(PAGE_INTERVAL)

    # structure.json 保存
    save_file(str(site_dir / "structure.json"), json.dumps(all_data, ensure_ascii=False, indent=2))
    print(f"\n{site_name} 完了!")
    return all_data


def merge_data(all_site_data):
    """3サイトのデータを統合"""
    merged = {
        "game_name": "スプラトゥーン3",
        "game_slug": "splatoon3",
        "sources": list(all_site_data.keys()),
        "weapons": {},
        "sections_union": set(),
        "pages": {},
    }

    for site_name, site_data in all_site_data.items():
        for key, val in site_data.items():
            # 構造データ
            if isinstance(val, dict) and "sections" in val:
                page = val.get("page_name", key)
                for s in val["sections"]:
                    merged["sections_union"].add(s)
                if page not in merged["pages"]:
                    merged["pages"][page] = {}
                merged["pages"][page][site_name] = val

            # 武器ティアデータ
            if isinstance(val, list) and val and isinstance(val[0], dict) and "tier" in val[0]:
                for w in val:
                    name = w.get("name", "").strip()
                    if not name:
                        continue
                    if name not in merged["weapons"]:
                        merged["weapons"][name] = {"name": name, "tiers": {}, "icon_urls": {}}
                    if w.get("tier"):
                        merged["weapons"][name]["tiers"][site_name] = w["tier"]
                    if w.get("icon_url"):
                        merged["weapons"][name]["icon_urls"][site_name] = w["icon_url"]

            # 武器一覧データ
            if key == "all_weapons" and isinstance(val, list):
                for w in val:
                    name = w.get("name", "").strip()
                    if not name:
                        continue
                    if name not in merged["weapons"]:
                        merged["weapons"][name] = {"name": name, "tiers": {}, "icon_urls": {}}
                    # 追加情報マージ
                    for k, v in w.items():
                        if k not in ("name", "source", "icon_url", "tier"):
                            merged["weapons"][name].setdefault("info", {})[f"{site_name}_{k}"] = v
                    if w.get("icon_url"):
                        merged["weapons"][name]["icon_urls"][site_name] = w["icon_url"]

    # set → list に変換
    merged["sections_union"] = sorted(merged["sections_union"])
    merged["weapons"] = list(merged["weapons"].values())
    merged["weapon_count"] = len(merged["weapons"])

    return merged


def main():
    print("=" * 60)
    print("フェーズ1: スプラトゥーン3 3サイトスクレイピング")
    print("=" * 60)

    # URL読み込み
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        all_urls = json.load(f)

    session = requests.Session()
    all_site_data = {}

    for site_name in ["game8", "gamewith", "altema"]:
        urls = all_urls.get(site_name, {})
        if urls:
            data = scrape_site(site_name, urls, session)
            all_site_data[site_name] = data

    # データ統合
    print(f"\n{'='*60}")
    print("データ統合中...")
    merged = merge_data(all_site_data)
    save_file(str(RAW_DIR / "merged_data.json"), json.dumps(merged, ensure_ascii=False, indent=2))

    # 統計出力
    print(f"\n{'='*60}")
    print("フェーズ1 完了!")
    print(f"{'='*60}")
    print(f"統合武器数: {merged['weapon_count']}")
    print(f"セクション数（和集合）: {len(merged['sections_union'])}")

    for site in ["game8", "gamewith", "altema"]:
        site_dir = RAW_DIR / site
        html_c = len(list((site_dir / "html").glob("*.html"))) if (site_dir / "html").exists() else 0
        css_c = len(list((site_dir / "css").glob("*"))) if (site_dir / "css").exists() else 0
        icon_c = len(list((site_dir / "icons").glob("*"))) if (site_dir / "icons").exists() else 0
        img_c = len(list((site_dir / "images").glob("*"))) if (site_dir / "images").exists() else 0
        print(f"  {site}: HTML={html_c}, CSS={css_c}, アイコン={icon_c}, 画像={img_c}")

    print(f"\n保存先: {RAW_DIR / 'merged_data.json'}")


if __name__ == "__main__":
    main()
