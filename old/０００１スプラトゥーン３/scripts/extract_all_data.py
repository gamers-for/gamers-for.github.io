#!/usr/bin/env python3
"""
Comprehensive data extractor for Splatoon 3 content from Altema, GameWith, and Game8.

Parses ALL HTML files from all three sites and extracts:
- Stages, events, updates, gear info, weapon evaluations,
  beginner tips, salmon run info, fes info, and all misc sections.

Outputs a single merged JSON: raw_data/extracted_content.json
"""

import json
import os
import re
from bs4 import BeautifulSoup

# ============================================================
# Paths
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA = os.path.join(BASE_DIR, "raw_data")

SITES = {
    "altema": os.path.join(RAW_DATA, "altema", "html"),
    "gamewith": os.path.join(RAW_DATA, "gamewith", "html"),
    "game8": os.path.join(RAW_DATA, "game8", "html"),
}

OUTPUT_JSON = os.path.join(RAW_DATA, "extracted_content.json")


# ============================================================
# Text cleaning utilities
# ============================================================
def clean(text):
    """Normalize whitespace and strip."""
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def is_noise(text):
    """Return True if a text block is boilerplate / navigation noise."""
    if not text:
        return True
    noise_patterns = [
        r'^(ログイン|ホーム|Game8|ゲームウィズ|アルテマ)',
        r'^(この記事を書いた人)',
        r'^(書き込み)',
        r'^(関連記事|おすすめ記事|人気記事|最新記事)',
        r'^(Copyright|All Rights Reserved)',
        r'^(シェア|ツイート|LINE|はてブ)',
        r'^(攻略TOP|トップ|トップページ)',
        r'^[\s\-]+$',
        r'^\d+$',
        r'^(前の記事|次の記事)',
        r'^(広告)',
        r'^(ダークモード)',
    ]
    for p in noise_patterns:
        if re.match(p, text):
            return True
    return len(text) < 3


# ============================================================
# Table extraction
# ============================================================
def extract_tables(soup):
    """Extract all tables as list of dicts with headers and rows."""
    results = []
    for table in soup.find_all('table'):
        rows_data = []
        headers = []
        for tr in table.find_all('tr'):
            ths = tr.find_all('th')
            tds = tr.find_all('td')
            if ths and not tds:
                headers = [clean(th.get_text()) for th in ths]
            elif tds:
                row = [clean(td.get_text()) for td in tds]
                if any(cell for cell in row if cell and cell != '-'):
                    rows_data.append(row)
        if rows_data:
            results.append({
                "headers": headers if headers else None,
                "rows": rows_data
            })
    return results


# ============================================================
# Section-based extraction (heading + following content)
# ============================================================
def extract_sections(soup):
    """
    Walk headings h2-h4 and gather the text content that follows
    each heading until the next heading of equal or higher level.
    Returns a list of {heading, level, content, lists, tables}.
    """
    # Remove nav, sidebar, footer, ads, scripts, styles
    for tag_name in ['nav', 'footer', 'script', 'style', 'noscript', 'svg', 'iframe']:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    for cls in ['side', 'sidebar', 'footer', 'gNavi', 'koukoku', 'ad-wrapper',
                'l-breadcrumb', 'p-archiveHeader__info', 'a-announce',
                'a-outline', 'comment', 'ad_', 'ads_']:
        for tag in soup.find_all(class_=lambda c: c and any(x in str(c) for x in [cls])):
            tag.decompose()

    headings = soup.find_all(re.compile(r'^h[1-6]$'))
    sections = []

    for i, heading in enumerate(headings):
        level = int(heading.name[1])
        heading_text = clean(heading.get_text())
        if not heading_text or is_noise(heading_text):
            continue

        # Collect content between this heading and the next heading of same or higher level
        content_parts = []
        list_items = []
        tables_in_section = []

        sibling = heading.next_sibling
        while sibling:
            if hasattr(sibling, 'name'):
                # Stop at next heading of same or higher level
                if sibling.name and re.match(r'^h[1-6]$', sibling.name):
                    sib_level = int(sibling.name[1])
                    if sib_level <= level:
                        break

                # Extract paragraph text
                if sibling.name == 'p':
                    txt = clean(sibling.get_text())
                    if txt and not is_noise(txt):
                        content_parts.append(txt)

                # Extract list items
                if sibling.name in ('ul', 'ol'):
                    for li in sibling.find_all('li'):
                        li_text = clean(li.get_text())
                        if li_text and not is_noise(li_text):
                            list_items.append(li_text)

                # Extract tables
                if sibling.name == 'table':
                    rows_data = []
                    table_headers = []
                    for tr in sibling.find_all('tr'):
                        ths = tr.find_all('th')
                        tds = tr.find_all('td')
                        if ths and not tds:
                            table_headers = [clean(th.get_text()) for th in ths]
                        elif tds:
                            row = [clean(td.get_text()) for td in tds]
                            if any(c for c in row if c and c != '-'):
                                rows_data.append(row)
                    if rows_data:
                        tables_in_section.append({
                            "headers": table_headers if table_headers else None,
                            "rows": rows_data
                        })

                # Also look inside divs for nested content
                if sibling.name == 'div':
                    for p in sibling.find_all('p'):
                        txt = clean(p.get_text())
                        if txt and not is_noise(txt):
                            content_parts.append(txt)
                    for li in sibling.find_all('li'):
                        li_text = clean(li.get_text())
                        if li_text and not is_noise(li_text):
                            list_items.append(li_text)
                    for tbl in sibling.find_all('table'):
                        rows_data = []
                        table_headers = []
                        for tr in tbl.find_all('tr'):
                            ths = tr.find_all('th')
                            tds = tr.find_all('td')
                            if ths and not tds:
                                table_headers = [clean(th.get_text()) for th in ths]
                            elif tds:
                                row = [clean(td.get_text()) for td in tds]
                                if any(c for c in row if c and c != '-'):
                                    rows_data.append(row)
                        if rows_data:
                            tables_in_section.append({
                                "headers": table_headers if table_headers else None,
                                "rows": rows_data
                            })

            sibling = sibling.next_sibling

        section = {
            "heading": heading_text,
            "level": level,
        }
        if content_parts:
            section["content"] = content_parts
        if list_items:
            section["list_items"] = list_items
        if tables_in_section:
            section["tables"] = tables_in_section

        # Only keep sections with actual content
        if content_parts or list_items or tables_in_section:
            sections.append(section)

    return sections


# ============================================================
# Page title extraction
# ============================================================
def get_page_title(soup):
    """Extract page title from h1 or <title>."""
    h1 = soup.find('h1')
    if h1:
        return clean(h1.get_text())
    title = soup.find('title')
    if title:
        return clean(title.get_text())
    return ""


# ============================================================
# Keyword-based content categorization
# ============================================================
STAGE_KEYWORDS = ['ステージ', 'マップ', 'stage']
EVENT_KEYWORDS = ['フェス', 'イベント', 'シーズン', 'event', 'フェスティバル']
UPDATE_KEYWORDS = ['アップデート', 'アプデ', 'パッチ', 'Ver.', 'ver.', 'バージョン', '更新']
GEAR_KEYWORDS = ['ギアパワー', 'ギア', 'gear', 'ブランド']
WEAPON_KEYWORDS = ['武器', 'ブキ', 'weapon', 'ランキング', 'ティア', 'tier', '最強']
BEGINNER_KEYWORDS = ['初心者', '始め方', '基本', 'ビギナー', 'beginner', '入門']
SALMON_KEYWORDS = ['サーモンラン', 'バイト', 'salmon']
FES_KEYWORDS = ['フェス', 'フェスティバル', 'fes']
SUB_KEYWORDS = ['サブウェポン', 'サブ']
SPECIAL_KEYWORDS = ['スペシャル', 'スペシャルウェポン']


def matches_keywords(text, keywords):
    """Check if text contains any keyword."""
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


# ============================================================
# Weapon evaluation extractor (specific to tier pages)
# ============================================================
def extract_weapon_tier_data(soup, site_name):
    """
    Extract weapon tier data: weapon names mapped to their tier rank
    and any evaluation text nearby.
    """
    evaluations = {}

    # Strategy: find tier header images or text, then collect weapon names in each tier
    # For altema: tier images have alt="S+", etc.
    # For game8/gamewith: tier headers in th or specific class patterns

    # Generic: Look for tables with weapon-like entries grouped by tier
    tier_names = ['SS', 'S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D']
    current_tier = None

    # Walk through all tables
    for table in soup.find_all('table'):
        for tr in table.find_all('tr'):
            # Check if row is a tier header
            ths = tr.find_all('th')
            for th in ths:
                th_text = clean(th.get_text())
                # Check for tier names in th text
                for t in tier_names:
                    if t == th_text or th_text.startswith(t + ' ') or th_text.endswith(' ' + t):
                        current_tier = t
                        break
                # Check for tier images
                for img in th.find_all('img', alt=True):
                    alt = img.get('alt', '')
                    if alt in tier_names:
                        current_tier = alt

            if current_tier:
                tds = tr.find_all('td')
                for td in tds:
                    # Extract weapon names from links or images
                    weapon_name = None
                    for a in td.find_all('a'):
                        # Check img alt first
                        for img in a.find_all('img', alt=True):
                            alt = clean(img.get('alt', ''))
                            if alt and alt not in tier_names and len(alt) > 1:
                                # Remove trailing "画像" from game8
                                alt = re.sub(r'画像$', '', alt)
                                if alt:
                                    weapon_name = alt
                        # Fallback to link text
                        if not weapon_name:
                            link_text = clean(a.get_text())
                            if link_text and link_text != '-' and len(link_text) > 1:
                                weapon_name = link_text

                    if not weapon_name:
                        td_text = clean(td.get_text())
                        if td_text and td_text != '-' and len(td_text) > 1:
                            weapon_name = td_text

                    if weapon_name:
                        evaluations[weapon_name] = {
                            "tier": current_tier,
                            "site": site_name
                        }

    return evaluations


# ============================================================
# Known Splatoon 3 stage names (ground truth for filtering)
# ============================================================
KNOWN_STAGES = [
    'ユノハナ大渓谷', 'ゴンズイ地区', 'ヤガラ市場', 'マテガイ放水路',
    'ナメロウ金属', 'クサヤ温泉', 'キンメダイ美術館', 'マヒマヒリゾート&スパ',
    'マヒマヒリゾート＆スパ', 'マサバ海峡大橋', 'ヒラメが丘団地',
    'チョウザメ造船', 'スメーシーワールド', 'タカアシ経済特区',
    'ザトウマーケット', 'マンタマリア号', '海女美術大学', '海女美術館',
    'タラポートショッピングパーク', 'コンブトラック', 'ネギトロ炭鉱',
    'カジキ空港', 'オヒョウ海運', 'バイガイ亭', 'あすなろグリーンヒルズ',
    'うめたてドリームランド', 'ナンプラー遺跡', 'イリコニウム',
    'アラマキ砦', 'リュウグウターミナル', 'デカライン高架下',
    'すじこジャンクション跡', 'カクトスエーアガイツ', 'カクトスウンヴェッタ',
    'カクトスエモレギア', 'カクトスクラフト', 'カクトスゲダイエン',
    'カクトスシュプリンゲン', 'カクトスズィッヘル', 'カクトスズィーゲン',
    'カクトスゼーレ', 'カクトスヒンメル', 'カクトスプリオン',
    'カクトスプリーマ', 'カクトスヘルリヒ', 'カクトスベギールデ',
    # Salmon run stages
    'シェケナダム', 'ムニ・エール海洋発電所', '難破船ドンブラコ',
    'どんぴこ闘技場', 'ながいきヤングニュータウン', 'みらいユートピアランド',
]

# ============================================================
# Stage name extractor
# ============================================================
def extract_stage_names(soup):
    """
    Extract stage names from stage_list pages.
    Uses a combination of known stage names and context-aware extraction
    to avoid pulling in navigation/sidebar noise.
    """
    stages_found = []

    # First, collect from known stages in the page text
    full_text = soup.get_text()
    for stage in KNOWN_STAGES:
        if stage in full_text:
            if stage not in stages_found:
                stages_found.append(stage)

    # Second, look for stage names in the main content area only
    # Focus on: tables with stage images, headings mentioning stage names
    # For game8: look in main content div
    main_content = soup.find('div', class_='archive-style-wrapper')
    if not main_content:
        # For altema: look in article content area
        main_content = soup.find('div', id='article-body')
    if not main_content:
        main_content = soup.find('div', class_='article_body')
    if not main_content:
        # fallback to whole page but be more strict
        main_content = soup

    # Look for stage name patterns in image alts within main content
    for img in main_content.find_all('img', alt=True):
        alt = clean(img.get('alt', ''))
        if alt and '画像' in alt:
            name = re.sub(r'画像$', '', alt).strip()
            if name and len(name) >= 3 and len(name) <= 20:
                # Additional filter: must contain kanji/katakana typical of stage names
                if re.search(r'[\u30A0-\u30FF\u4E00-\u9FFF]', name):
                    if name not in stages_found:
                        stages_found.append(name)

    # Look for headings (h3, h4) that are stage names
    for h in main_content.find_all(re.compile(r'^h[3-4]$')):
        h_text = clean(h.get_text())
        if h_text and len(h_text) >= 3 and len(h_text) <= 20:
            # Check against known stages
            for known in KNOWN_STAGES:
                if known in h_text or h_text in known:
                    if known not in stages_found:
                        stages_found.append(known)

    return stages_found


# ============================================================
# Known gear power names for filtering
# ============================================================
KNOWN_GEAR_POWERS = [
    'インク効率アップ（メイン）', 'インク効率アップ（サブ）', 'インク効率アップ(メイン)', 'インク効率アップ(サブ)',
    'インク回復力アップ', 'インク回復量アップ', 'ヒト移動速度アップ',
    'イカダッシュ速度アップ', 'スペシャル増加量アップ', 'スペシャル減少量ダウン',
    'スペシャル性能アップ', 'サブ性能アップ', 'サブ影響軽減', '相手インク影響軽減',
    'アクション強化', 'イカニンジャ', 'リベンジ', 'サーマルインク',
    'スタートダッシュ', 'ラストスパート', 'カムバック', '復活時間短縮',
    'スーパージャンプ時間短縮', '復活ペナルティアップ', '逆境強化',
    'ステルスジャンプ', '追加ギアパワー倍化', '対物攻撃力アップ',
    '受け身術',
]


# ============================================================
# Gear power extractor
# ============================================================
def extract_gear_powers(soup):
    """Extract gear power names and descriptions from gear pages."""
    gear_powers = []
    seen_names = set()

    # Strategy: Find tables that have gear power names in them
    # Filter strictly to avoid picking up navigation/weapon entries
    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        is_gear_table = False

        for tr in rows:
            ths = tr.find_all('th')
            tds = tr.find_all('td')

            # Check if this table header mentions gear powers
            if ths:
                header_text = ' '.join([clean(th.get_text()) for th in ths])
                if 'ギアパワー' in header_text:
                    is_gear_table = True
                    continue

            if tds and len(tds) >= 2:
                name_cell = tds[0]
                desc_cell = tds[1] if len(tds) > 1 else None

                name = clean(name_cell.get_text())
                desc = clean(desc_cell.get_text()) if desc_cell else ""

                # Remove "画像" from name
                name = re.sub(r'画像', '', name).strip()

                if not name or len(name) < 3:
                    continue

                # Only include if it's a known gear power or table is confirmed as gear table
                is_known = False
                for known in KNOWN_GEAR_POWERS:
                    if name in known or known in name:
                        is_known = True
                        name = known  # normalize to known name
                        break

                if (is_known or is_gear_table) and name not in seen_names:
                    # Additional filter: skip if name looks like a weapon or brand
                    if len(name) > 2 and not re.match(r'^(52|96|H3|L3|R-|N-|\.)', name):
                        gear_powers.append({
                            "name": name,
                            "description": desc
                        })
                        seen_names.add(name)

    return gear_powers


# ============================================================
# Version / date extractor
# ============================================================
def extract_versions_and_dates(text):
    """Extract version numbers and dates from text."""
    versions = re.findall(r'Ver\.?\s*[\d.]+', text, re.IGNORECASE)
    dates = re.findall(
        r'(\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}[日]?)',
        text
    )
    return {
        "versions": list(set(versions)),
        "dates": list(set(dates))
    }


# ============================================================
# Main processing
# ============================================================
def process_html_file(filepath, site_name, filename):
    """Process a single HTML file and return structured data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    title = get_page_title(soup)

    # Get full text for date/version extraction
    full_text = soup.get_text()

    # Rebuild soup for section extraction (it modifies the tree)
    soup2 = BeautifulSoup(html, 'html.parser')
    sections = extract_sections(soup2)

    # Rebuild for tables
    soup3 = BeautifulSoup(html, 'html.parser')
    all_tables = extract_tables(soup3)

    # Extract dates and versions
    ver_dates = extract_versions_and_dates(full_text)

    result = {
        "site": site_name,
        "filename": filename,
        "title": title,
        "sections": sections,
        "tables_count": len(all_tables),
        "all_tables": all_tables,
    }

    if ver_dates["versions"]:
        result["versions_mentioned"] = ver_dates["versions"]
    if ver_dates["dates"]:
        result["dates_mentioned"] = ver_dates["dates"]

    return result


def categorize_file(filename, title):
    """Determine the category of an HTML file by filename and title."""
    combined = (filename + " " + title).lower()
    categories = []

    if any(k in combined for k in ['stage', 'ステージ', 'マップ']):
        categories.append('stages')
    if any(k in combined for k in ['tier', 'ティア', 'ランキング', '最強']):
        categories.append('weapon_evaluations')
    if any(k in combined for k in ['gear', 'ギア', 'ブランド']):
        categories.append('gear_info')
    if any(k in combined for k in ['salmon', 'サーモン', 'バイト']):
        categories.append('salmon_run_info')
    if any(k in combined for k in ['beginner', '初心者', '始め方']):
        categories.append('beginner_tips')
    if any(k in combined for k in ['weapon', 'ブキ', '武器']):
        categories.append('weapon_evaluations')
    if any(k in combined for k in ['special', 'スペシャル']):
        categories.append('weapon_evaluations')
    if any(k in combined for k in ['sub', 'サブ']):
        categories.append('weapon_evaluations')
    if any(k in combined for k in ['fes', 'フェス']):
        categories.append('fes_info')
    if any(k in combined for k in ['update', 'アプデ', 'アップデート']):
        categories.append('updates')
    if any(k in combined for k in ['event', 'イベント']):
        categories.append('events')
    if any(k in combined for k in ['top', 'トップ']):
        categories.append('top_page')

    return categories if categories else ['misc']


def main():
    print("=" * 70)
    print("Splatoon 3 Comprehensive Data Extractor")
    print("Sources: Altema, GameWith, Game8")
    print("=" * 70)

    # ---- Output structure ----
    output = {
        "stages": [],
        "events": [],
        "updates": [],
        "gear_info": [],
        "weapon_evaluations": {},
        "beginner_tips": [],
        "salmon_run_info": [],
        "fes_info": [],
        "misc_sections": {},
        "_metadata": {
            "sites_processed": {},
            "total_files": 0,
            "total_sections": 0,
            "total_tables": 0,
            "all_versions": [],
            "all_dates": [],
        }
    }

    all_versions = set()
    all_dates = set()
    total_sections = 0
    total_tables = 0

    for site_name, html_dir in SITES.items():
        if not os.path.isdir(html_dir):
            print(f"\n  WARNING: {html_dir} not found, skipping {site_name}")
            continue

        html_files = sorted([f for f in os.listdir(html_dir) if f.endswith('.html')])
        print(f"\n{'='*50}")
        print(f"  Site: {site_name} ({len(html_files)} HTML files)")
        print(f"{'='*50}")

        output["_metadata"]["sites_processed"][site_name] = html_files
        output["_metadata"]["total_files"] += len(html_files)

        for html_file in html_files:
            filepath = os.path.join(html_dir, html_file)
            print(f"\n  Processing: {site_name}/{html_file}")

            data = process_html_file(filepath, site_name, html_file)
            categories = categorize_file(html_file, data.get("title", ""))

            print(f"    Title: {data['title'][:80]}...")
            print(f"    Sections: {len(data['sections'])}")
            print(f"    Tables: {data['tables_count']}")
            print(f"    Categories: {categories}")

            total_sections += len(data['sections'])
            total_tables += data['tables_count']

            # Collect versions and dates
            for v in data.get("versions_mentioned", []):
                all_versions.add(v)
            for d in data.get("dates_mentioned", []):
                all_dates.add(d)

            # ---- Route data into categories ----

            # Stage data
            if 'stages' in categories or 'stage' in html_file:
                # Extract stage names
                with open(filepath, 'r', encoding='utf-8') as f:
                    stage_soup = BeautifulSoup(f.read(), 'html.parser')
                stage_names = extract_stage_names(stage_soup)
                if stage_names:
                    output["stages"].append({
                        "site": site_name,
                        "file": html_file,
                        "stage_names": stage_names,
                        "sections": data["sections"],
                    })
                    print(f"    -> Stages found: {len(stage_names)}")

            # Gear data
            if 'gear_info' in categories:
                with open(filepath, 'r', encoding='utf-8') as f:
                    gear_soup = BeautifulSoup(f.read(), 'html.parser')
                gear_powers = extract_gear_powers(gear_soup)
                output["gear_info"].append({
                    "site": site_name,
                    "file": html_file,
                    "title": data["title"],
                    "gear_powers": gear_powers,
                    "sections": data["sections"],
                })
                print(f"    -> Gear powers found: {len(gear_powers)}")

            # Weapon evaluations / tier data
            if 'weapon_evaluations' in categories:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tier_soup = BeautifulSoup(f.read(), 'html.parser')
                weapon_tiers = extract_weapon_tier_data(tier_soup, site_name)

                for wname, wdata in weapon_tiers.items():
                    if wname not in output["weapon_evaluations"]:
                        output["weapon_evaluations"][wname] = {}
                    if site_name not in output["weapon_evaluations"][wname]:
                        output["weapon_evaluations"][wname][site_name] = {}
                    output["weapon_evaluations"][wname][site_name]["tier"] = wdata.get("tier")
                    output["weapon_evaluations"][wname][site_name]["source_file"] = html_file

                # Also store section-level text for evaluation context
                for section in data["sections"]:
                    heading = section.get("heading", "")
                    content = section.get("content", [])
                    if content and matches_keywords(heading, WEAPON_KEYWORDS):
                        # Try to match weapon names in headings
                        for wname in list(output["weapon_evaluations"].keys()):
                            if wname in heading:
                                if site_name not in output["weapon_evaluations"][wname]:
                                    output["weapon_evaluations"][wname][site_name] = {}
                                output["weapon_evaluations"][wname][site_name]["evaluation"] = ' '.join(content)

                print(f"    -> Weapon tiers found: {len(weapon_tiers)}")

            # Beginner tips
            if 'beginner_tips' in categories:
                output["beginner_tips"].append({
                    "site": site_name,
                    "file": html_file,
                    "title": data["title"],
                    "sections": data["sections"],
                })

            # Salmon run
            if 'salmon_run_info' in categories:
                output["salmon_run_info"].append({
                    "site": site_name,
                    "file": html_file,
                    "title": data["title"],
                    "sections": data["sections"],
                })

            # Fes info
            if 'fes_info' in categories:
                output["fes_info"].append({
                    "site": site_name,
                    "file": html_file,
                    "title": data["title"],
                    "sections": data["sections"],
                })

            # Updates
            if 'updates' in categories:
                output["updates"].append({
                    "site": site_name,
                    "file": html_file,
                    "title": data["title"],
                    "sections": data["sections"],
                    "versions": data.get("versions_mentioned", []),
                    "dates": data.get("dates_mentioned", []),
                })

            # Events
            if 'events' in categories:
                output["events"].append({
                    "site": site_name,
                    "file": html_file,
                    "title": data["title"],
                    "sections": data["sections"],
                })

            # Misc sections (store ALL sections for every file)
            file_key = f"{site_name}/{html_file}"
            output["misc_sections"][file_key] = []
            for section in data["sections"]:
                output["misc_sections"][file_key].append({
                    "heading": section.get("heading", ""),
                    "content": ' '.join(section.get("content", [])),
                    "list_items": section.get("list_items", []),
                    "tables": section.get("tables", []),
                })

    # ---- Finalize metadata ----
    output["_metadata"]["total_sections"] = total_sections
    output["_metadata"]["total_tables"] = total_tables
    output["_metadata"]["all_versions"] = sorted(all_versions)
    output["_metadata"]["all_dates"] = sorted(all_dates)

    # ---- Write output ----
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # ---- Summary ----
    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"  Output file: {OUTPUT_JSON}")
    print(f"  Total HTML files processed: {output['_metadata']['total_files']}")
    print(f"  Total sections extracted: {total_sections}")
    print(f"  Total tables extracted: {total_tables}")
    print(f"\n  Category counts:")
    print(f"    Stages entries:           {len(output['stages'])}")
    print(f"    Events entries:           {len(output['events'])}")
    print(f"    Updates entries:          {len(output['updates'])}")
    print(f"    Gear info entries:        {len(output['gear_info'])}")
    print(f"    Weapon evaluations:       {len(output['weapon_evaluations'])} unique weapons")
    print(f"    Beginner tips entries:    {len(output['beginner_tips'])}")
    print(f"    Salmon run entries:       {len(output['salmon_run_info'])}")
    print(f"    Fes info entries:         {len(output['fes_info'])}")
    print(f"    Misc section files:       {len(output['misc_sections'])}")
    print(f"\n  Versions mentioned: {len(output['_metadata']['all_versions'])}")
    for v in sorted(output['_metadata']['all_versions']):
        print(f"      {v}")
    print(f"\n  Dates mentioned: {len(output['_metadata']['all_dates'])}")
    for d in sorted(output['_metadata']['all_dates'])[:20]:
        print(f"      {d}")
    if len(output['_metadata']['all_dates']) > 20:
        print(f"      ... and {len(output['_metadata']['all_dates']) - 20} more")

    # Show some stage names
    all_stages = set()
    for entry in output['stages']:
        for s in entry.get('stage_names', []):
            all_stages.add(s)
    if all_stages:
        print(f"\n  Unique stage names found: {len(all_stages)}")
        for s in sorted(all_stages):
            print(f"      {s}")

    # Show weapon evaluation stats per site
    site_weapon_counts = {}
    for wname, wdata in output["weapon_evaluations"].items():
        for site in wdata:
            site_weapon_counts[site] = site_weapon_counts.get(site, 0) + 1
    if site_weapon_counts:
        print(f"\n  Weapon evaluations per site:")
        for site, count in sorted(site_weapon_counts.items()):
            print(f"      {site}: {count} weapons")

    # Show tier distribution across all sites
    tier_dist = {}
    for wname, wdata in output["weapon_evaluations"].items():
        for site, sdata in wdata.items():
            tier = sdata.get("tier", "unknown")
            tier_dist[tier] = tier_dist.get(tier, 0) + 1
    if tier_dist:
        print(f"\n  Tier distribution (all sites combined):")
        for tier in ['SS', 'S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'unknown']:
            if tier in tier_dist:
                print(f"      {tier}: {tier_dist[tier]}")

    # Show gear power stats
    all_gear_names = set()
    for entry in output['gear_info']:
        for gp in entry.get('gear_powers', []):
            all_gear_names.add(gp['name'])
    if all_gear_names:
        print(f"\n  Unique gear powers found: {len(all_gear_names)}")
        for g in sorted(all_gear_names)[:30]:
            print(f"      {g}")

    # Show beginner tips sections
    beginner_section_count = 0
    for entry in output['beginner_tips']:
        beginner_section_count += len(entry.get('sections', []))
    print(f"\n  Beginner tip sections: {beginner_section_count}")

    # Salmon run section count
    salmon_section_count = 0
    for entry in output['salmon_run_info']:
        salmon_section_count += len(entry.get('sections', []))
    print(f"  Salmon run sections: {salmon_section_count}")

    # Output file size
    file_size = os.path.getsize(OUTPUT_JSON)
    print(f"\n  Output file size: {file_size / 1024:.1f} KB")

    print("\nDone!")


if __name__ == '__main__':
    main()
