#!/usr/bin/env python3
"""
Altema Splatoon 3 weapon data extractor.

Parses the weapon list HTML and weapon tier HTML from Altema,
extracts weapon names, types, sub weapons, special weapons, and tier rankings,
then merges everything into a clean JSON file.
"""

import json
import os
import re
from bs4 import BeautifulSoup, NavigableString

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEAPON_LIST_HTML = os.path.join(BASE_DIR, "raw_data", "altema", "html", "weapon_list.html")
WEAPON_TIER_HTML = os.path.join(BASE_DIR, "raw_data", "altema", "html", "weapon_tier.html")
OUTPUT_JSON = os.path.join(BASE_DIR, "raw_data", "clean_weapons.json")


def clean_text(text):
    """Clean extracted text: remove whitespace, newlines, and normalize."""
    if not text:
        return ""
    # Replace <br> artifacts and newlines with nothing, then strip
    text = re.sub(r'\s+', '', text)
    return text.strip()


def extract_cell_text(td):
    """
    Extract the meaningful weapon/sub/special name from a <td> cell.
    The name is typically in the link text after the <img> tag.
    We get all text content from <a> tags, stripping image alt text noise.
    """
    # Find all <a> tags in the cell
    links = td.find_all('a')
    if not links:
        return ""

    # Get text from the last (or only) link - this handles cases where
    # there are multiple <a> tags
    best_text = ""
    for link in links:
        # Get direct text content, ignoring <noscript> and <img> elements
        texts = []
        for child in link.children:
            if isinstance(child, NavigableString):
                t = child.strip()
                if t:
                    texts.append(t)
            elif child.name == 'span':
                # Some specials are wrapped in <span>
                span_text = child.get_text(strip=True)
                if span_text:
                    texts.append(span_text)
            elif child.name == 'br':
                pass  # skip line breaks
            elif child.name not in ('img', 'noscript'):
                t = child.get_text(strip=True)
                if t:
                    texts.append(t)

        combined = ''.join(texts)
        if combined:
            best_text = combined

    return clean_text(best_text)


def parse_weapon_list(html_path):
    """
    Parse the weapon list HTML.
    Returns a list of dicts: {name, type, sub, special}

    Structure:
    - <h3 id="shooter">シューター</h3>
    - <table> with rows of 3 cols: weapon, sub, special
    - Each section ends before the next <h3> or end of content
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')

    weapons = []

    # Map of h3 IDs to weapon type names
    type_map = {
        'shooter': 'シューター',
        'roller': 'ローラー',
        'charger': 'チャージャー',
        'slosher': 'スロッシャー',
        'splatling': 'スピナー',
        'dualies': 'マニューバー',
        'brella': 'シェルター',
        'blaster': 'ブラスター',
        'fude': 'フデ',
        'stringer': 'ストリンガー',
        'waiper': 'ワイパー',
    }

    for h3_id, weapon_type in type_map.items():
        h3 = soup.find('h3', id=h3_id)
        if not h3:
            print(f"  WARNING: Could not find h3#{h3_id} for {weapon_type}")
            continue

        # Find the next table after this h3
        table = h3.find_next('table')
        if not table:
            print(f"  WARNING: No table found after h3#{h3_id}")
            continue

        # Process each row (skip header row with <th>)
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 3:
                continue  # Skip header rows or incomplete rows

            weapon_name = extract_cell_text(cells[0])
            sub_name = extract_cell_text(cells[1])
            special_name = extract_cell_text(cells[2])

            if not weapon_name:
                continue

            weapons.append({
                'name': weapon_name,
                'type': weapon_type,
                'sub': sub_name,
                'special': special_name,
            })

    return weapons


def parse_weapon_tiers(html_path):
    """
    Parse the weapon tier HTML.
    Returns a dict: {weapon_name: tier_rank}

    Structure:
    - The main ranking table has class "img-kadomaru tableLine"
    - Tier headers are <th> rows containing <img alt="S+"> etc.
    - Weapon entries are <td> cells with <a> containing <img alt="FULL_NAME"> and short display text
    - We use the alt attribute of <img> inside <a> for the full weapon name
    - B+ and below tiers are inside a collapsible <dl class="acMenu"> section
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')

    tiers = {}

    # Valid tier names
    valid_tiers = {'S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C'}

    # Find the section: "最強武器ランキング早見表"
    h2 = soup.find('h2', id='01')
    if not h2:
        print("  WARNING: Could not find h2#01 (ranking table)")
        return tiers

    # Find all tables with class "img-kadomaru tableLine" after h2#01
    # The main table is right after h2#01, and B+ below is in an acMenu
    tables = []

    # Main table (S+ through A)
    main_table = h2.find_next('table', class_='img-kadomaru')
    if main_table:
        tables.append(main_table)

    # B+ and below table (inside acMenu)
    ac_menu = h2.find_next('dl', class_='acMenu')
    if ac_menu:
        sub_table = ac_menu.find('table', class_='img-kadomaru')
        if sub_table:
            tables.append(sub_table)

    for table in tables:
        current_tier = None
        rows = table.find_all('tr')

        for row in rows:
            # Check if this is a tier header row
            th_cells = row.find_all('th')
            if th_cells:
                # Extract tier from <img alt="..."> in the <th>
                for th in th_cells:
                    img = th.find('img', alt=True)
                    if img and img['alt'] in valid_tiers:
                        current_tier = img['alt']
                    else:
                        # Also check <noscript> img
                        noscript = th.find('noscript')
                        if noscript:
                            ns_img = noscript.find('img', alt=True)
                            if ns_img and ns_img['alt'] in valid_tiers:
                                current_tier = ns_img['alt']
                continue

            if not current_tier:
                continue

            # Process weapon cells in this row
            cells = row.find_all('td')
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                if cell_text == '-' or not cell_text:
                    continue

                # Get the full weapon name from <img alt="..."> inside <a>
                link = cell.find('a')
                if not link:
                    continue

                # Try to get the alt text from images (this has the full name)
                full_name = None
                imgs = link.find_all('img', alt=True)
                for img in imgs:
                    alt = img.get('alt', '')
                    if alt and alt not in valid_tiers:
                        full_name = alt
                        break

                # Also check noscript
                if not full_name:
                    noscript = link.find('noscript')
                    if noscript:
                        ns_img = noscript.find('img', alt=True)
                        if ns_img:
                            full_name = ns_img.get('alt', '')

                if full_name:
                    full_name = clean_text(full_name)
                    if full_name:
                        tiers[full_name] = current_tier

    return tiers


def normalize_name(name):
    """
    Normalize weapon name for matching between list and tier pages.
    Remove common suffixes/prefixes and handle known aliases.
    """
    # Remove half-width/full-width dots at the beginning
    name = re.sub(r'^[.．]', '', name)
    # Remove hyphens for comparison (LACT-450 vs LACT450)
    name = name.replace('-', '')
    return name


# Manual alias map: weapon_list_name -> tier_page_alt_name
# These are known mismatches between the two Altema pages
WEAPON_ALIASES = {
    'プロモデラーRG': '金モデラー',
    'R-PEN/5H': 'ロケットえんぴつ',
    'LACT-450': 'LACT450',
    'LACT-450デコ': 'LACT450デコ',
    'スプラニューバーコラボ': 'スプラマニューバーコラボ',
}


def match_tier(weapon_name, tier_map):
    """
    Try to match a weapon name from the weapon list to a tier entry.
    The tier page uses alt text from images which may differ slightly.
    """
    # Direct match
    if weapon_name in tier_map:
        return tier_map[weapon_name]

    # Alias match
    alias = WEAPON_ALIASES.get(weapon_name)
    if alias and alias in tier_map:
        return tier_map[alias]

    # Normalized match (removes hyphens, leading dots)
    norm = normalize_name(weapon_name)
    for tier_name, tier_val in tier_map.items():
        tier_norm = normalize_name(tier_name)
        if norm == tier_norm:
            return tier_val

    # Substring match: if weapon_name is contained in a tier key or vice versa
    for tier_name, tier_val in tier_map.items():
        if weapon_name in tier_name or tier_name in weapon_name:
            return tier_val

    return None


def main():
    print("=" * 60)
    print("Altema Splatoon 3 Weapon Data Extractor")
    print("=" * 60)

    # Step 1: Parse weapon list
    print(f"\n[1/3] Parsing weapon list: {WEAPON_LIST_HTML}")
    weapons = parse_weapon_list(WEAPON_LIST_HTML)
    print(f"  Found {len(weapons)} weapons")

    # Show per-type counts
    type_counts = {}
    for w in weapons:
        t = w['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in type_counts.items():
        print(f"    {t}: {c}")

    # Step 2: Parse tier rankings
    print(f"\n[2/3] Parsing tier rankings: {WEAPON_TIER_HTML}")
    tier_map = parse_weapon_tiers(WEAPON_TIER_HTML)
    print(f"  Found {len(tier_map)} tier entries")

    # Show tier distribution
    tier_dist = {}
    for name, tier in tier_map.items():
        tier_dist[tier] = tier_dist.get(tier, 0) + 1
    for tier_name in ['S+', 'S', 'A+', 'A', 'B+', 'B', 'C+', 'C']:
        if tier_name in tier_dist:
            print(f"    {tier_name}: {tier_dist[tier_name]}")

    # Step 3: Merge and output
    print(f"\n[3/3] Merging data and writing to: {OUTPUT_JSON}")
    matched = 0
    unmatched = []

    for w in weapons:
        tier = match_tier(w['name'], tier_map)
        if tier:
            w['tier'] = tier
            matched += 1
        else:
            w['tier'] = None
            unmatched.append(w['name'])

    print(f"  Matched tiers: {matched}/{len(weapons)}")
    if unmatched:
        print(f"  Unmatched weapons ({len(unmatched)}):")
        for name in unmatched:
            print(f"    - {name}")

    # Build output
    output = {
        "source": "altema.jp/splatoon3",
        "weapon_count": len(weapons),
        "weapons": weapons
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  Output written to: {OUTPUT_JSON}")
    print(f"  Total weapons: {len(weapons)}")

    # Print a few sample entries
    print("\n  Sample entries:")
    for w in weapons[:5]:
        print(f"    {w['name']} ({w['type']}) - Sub: {w['sub']}, Special: {w['special']}, Tier: {w['tier']}")

    print("\nDone!")


if __name__ == '__main__':
    main()
