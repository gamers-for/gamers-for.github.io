#!/usr/bin/env python3
"""
Game8のスクレイプ済みHTMLを解析してJSONデータを生成するスクリプト
入力:  ００００１スプラトゥーン３/raw_html/
出力:  ００００１スプラトゥーン３/parsed_data/
"""

import os
import re
import json
import glob
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "００００１スプラトゥーン３", "raw_html")
OUT_DIR = os.path.join(BASE_DIR, "００００１スプラトゥーン３", "parsed_data")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(OUT_DIR, exist_ok=True)


def load_html(filename):
    """raw_html配下のHTMLを読み込み"""
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


def clean_text(text):
    """テキストを整理"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())


def extract_tables(soup):
    """テーブルを抽出して辞書のリストに変換"""
    results = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [clean_text(th.get_text()) for th in rows[0].find_all(["th", "td"])]
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) == len(headers):
                entry = {}
                for i, cell in enumerate(cells):
                    # テキストとリンクとアイコン画像を取得
                    entry[headers[i]] = {
                        "text": clean_text(cell.get_text()),
                        "link": cell.find("a")["href"] if cell.find("a") else "",
                        "img": cell.find("img")["data-src"] if cell.find("img") and cell.find("img").get("data-src") else
                               (cell.find("img")["src"] if cell.find("img") and cell.find("img").get("src") else ""),
                    }
                results.append(entry)
    return results


def extract_sections(soup):
    """h2/h3セクションごとにテキストを抽出"""
    sections = {}
    current_h2 = ""
    current_h3 = ""

    for tag in soup.find_all(["h2", "h3", "p", "ul", "ol", "table"]):
        if tag.name == "h2":
            current_h2 = clean_text(tag.get_text())
            current_h3 = ""
            if current_h2 not in sections:
                sections[current_h2] = {"text": [], "subsections": {}}
        elif tag.name == "h3":
            current_h3 = clean_text(tag.get_text())
            if current_h2 and current_h3 not in sections.get(current_h2, {}).get("subsections", {}):
                sections.setdefault(current_h2, {"text": [], "subsections": {}})["subsections"][current_h3] = []
        elif tag.name in ("p", "ul", "ol"):
            text = clean_text(tag.get_text())
            if text:
                if current_h3 and current_h2:
                    sections.setdefault(current_h2, {"text": [], "subsections": {}})["subsections"].setdefault(current_h3, []).append(text)
                elif current_h2:
                    sections.setdefault(current_h2, {"text": [], "subsections": {}})["text"].append(text)
    return sections


# =============================================
# 武器名正規化
# =============================================
def normalize_weapon_name(raw_name):
    """Game8タイトルから武器名を抽出・正規化
    例: '【スプラ3】スプラシューターのおすすめギアと立ち回り｜スシ【スプラトゥーン3】'
      → 'スプラシューター'
    """
    name = raw_name
    # 【...】タグを除去
    name = re.sub(r'【[^】]*】', '', name)
    # ｜以降を除去（ニックネーム部分）
    name = re.split(r'[｜|]', name)[0]
    # 「の評価」「のおすすめ」「の立ち回り」以降を除去
    m = re.match(r'(.+?)の(?:評価|おすすめ|立ち回り|使い方|性能)', name)
    if m:
        name = m.group(1)
    return name.strip()


# =============================================
# 武器個別ページ解析
# =============================================
def parse_weapon_page(soup, weapon_name=""):
    """武器個別ページからデータを抽出"""
    data = {"name": weapon_name}

    # ページタイトルから武器名取得
    title_tag = soup.find("h1")
    if title_tag:
        title_text = clean_text(title_tag.get_text())
        extracted = normalize_weapon_name(title_text)
        if extracted and len(extracted) > 1:
            data["name"] = extracted

    # テーブルから性能データ抽出
    tables = extract_tables(soup)
    for table_data in tables:
        for key, val in table_data.items():
            text = val.get("text", "") if isinstance(val, dict) else str(val)
            if "攻撃力" in key or "ダメージ" in key:
                data["damage"] = text
            elif "射程" in key and "試し撃ち" in key:
                data["range"] = text
            elif "射程" in key and "有効" in key:
                data["effective_range"] = text
            elif "確定数" in key:
                data["shots_to_kill"] = text
            elif "スペシャル必要" in key:
                data["special_points"] = text
            elif "解放ランク" in key:
                data["unlock_rank"] = text

    # セクションテキスト抽出
    sections = extract_sections(soup)

    def collect_section_text(sec_data):
        """セクションのテキストをサブセクション含めて収集"""
        texts = list(sec_data.get("text", []))
        for sub_name, sub_texts in sec_data.get("subsections", {}).items():
            texts.append(f"【{sub_name}】")
            texts.extend(sub_texts)
        return " ".join(texts) if texts else ""

    # 評価情報
    for sec_name, sec_data in sections.items():
        if "評価" in sec_name and ("役割" in sec_name or "ランク" in sec_name):
            text = collect_section_text(sec_data)
            if text:
                data["evaluation_text"] = text
        elif "おすすめギア" in sec_name:
            text = collect_section_text(sec_data)
            if text:
                data["recommended_gear_text"] = text
            data["recommended_gear_subsections"] = sec_data.get("subsections", {})
        elif "立ち回り" in sec_name or "使い方" in sec_name:
            text = collect_section_text(sec_data)
            if text:
                data["playstyle_text"] = text
            data["playstyle_subsections"] = sec_data.get("subsections", {})
        elif "対策" in sec_name and "コメント" not in sec_name:
            text = collect_section_text(sec_data)
            if text:
                data["counter_text"] = text
        elif "アップデート" in sec_name:
            update_texts = []
            for sub_name, sub_texts in sec_data.get("subsections", {}).items():
                update_texts.append(f"[{sub_name}]")
                update_texts.extend(sub_texts)
            if not update_texts:
                update_texts = sec_data.get("text", [])
            if update_texts:
                data["update_history"] = update_texts

    # ルール別評価をテーブルから探す（画像alt属性から取得）
    rule_ratings = {}
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) != 2:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        value_cells = rows[1].find_all(["th", "td"])
        if len(header_cells) != 5 or len(value_cells) != 5:
            continue
        headers_text = [clean_text(c.get_text()) for c in header_cells]
        # ナワバリ, エリア, ヤグラ, ホコ, アサリのヘッダーか確認
        if not any("ナワバリ" in h for h in headers_text):
            continue
        rule_map = {}
        for i, h in enumerate(headers_text):
            if "ナワバリ" in h:
                rule_map[i] = "nawabari"
            elif "エリア" in h:
                rule_map[i] = "area"
            elif "ヤグラ" in h:
                rule_map[i] = "yagura"
            elif "ホコ" in h:
                rule_map[i] = "hoko"
            elif "アサリ" in h:
                rule_map[i] = "asari"
        for i, cell in enumerate(value_cells):
            if i in rule_map:
                # まずテキストを試す
                text = clean_text(cell.get_text())
                if not text:
                    # テキストが空なら画像altから取得
                    img = cell.find("img")
                    if img:
                        alt = img.get("alt", "").strip()
                        # 全角→半角変換
                        text = alt.replace("＋", "+")
                rule_ratings[rule_map[i]] = text
    if rule_ratings:
        data["rule_ratings"] = rule_ratings

    # 性能レーダー（星評価）
    star_ratings = {}
    for table_data in tables:
        for key, val in table_data.items():
            text = val.get("text", "") if isinstance(val, dict) else str(val)
            star_count = text.count("★") + text.count("☆") * 0
            if star_count > 0:
                if "塗り" in key:
                    star_ratings["paint"] = star_count
                elif "扱いやすさ" in key:
                    star_ratings["ease"] = star_count
                elif "キル" in key:
                    star_ratings["kill"] = star_count
                elif "防御" in key or "生存" in key:
                    star_ratings["defense"] = star_count
                elif "アシスト" in key:
                    star_ratings["assist"] = star_count
                elif "打開" in key:
                    star_ratings["breakthrough"] = star_count
    if star_ratings:
        data["star_ratings"] = star_ratings

    return data


# =============================================
# ティアリスト解析
# =============================================
# ティア名正規化マップ（全角→半角）
TIER_NORMALIZE = {
    "X": "X", "S＋": "S+", "S": "S", "A＋": "A+", "A": "A",
    "B＋": "B+", "B": "B", "C＋": "C+", "C": "C",
    "評価X": "X", "評価S＋": "S+", "評価S": "S", "評価A＋": "A+",
    "評価A": "A", "評価B＋": "B+", "評価B": "B", "評価C＋": "C+", "評価C": "C",
}


def extract_tier_from_table(table):
    """Game8のティアテーブルからティアと武器名を抽出
    構造: 各行=[td(ティア画像), td(武器画像リンク群)]
    ティアはimg altで判定、武器名もimg altから取得（"〇〇画像"→"〇〇"）
    """
    tiers = {}
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue

        # col 0: ティア画像
        tier_cell = cells[0]
        tier_img = tier_cell.find("img")
        if not tier_img:
            continue
        tier_alt = tier_img.get("alt", "").strip()
        tier_name = TIER_NORMALIZE.get(tier_alt)
        if not tier_name:
            continue

        # col 1: 武器画像リンク群
        weapon_cell = cells[1]
        weapons = []
        for a_tag in weapon_cell.find_all("a"):
            img = a_tag.find("img")
            if img:
                alt = img.get("alt", "").strip()
                # "スプラシューター画像" → "スプラシューター"
                wname = re.sub(r'画像$', '', alt).strip()
                if wname and len(wname) > 1:
                    href = a_tag.get("href", "")
                    weapons.append({"name": wname, "url": href})
        if weapons:
            tiers[tier_name] = weapons

    return tiers


def parse_tier_list(soup, page_type="overall"):
    """ティアリストページからデータ抽出
    Game8のティアテーブルは画像altにティア名と武器名が格納されている
    """
    # ティアテーブルを検出: col 0にティア画像(alt="X","S＋",etc.)を持つテーブル
    best_table = None
    best_count = 0

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        # 最初の行のcol 0にティア画像があるか（th/td両方対応）
        first_cell = rows[0].find(["th", "td"])
        if not first_cell:
            continue
        img = first_cell.find("img")
        if not img:
            continue
        alt = img.get("alt", "").strip()
        if alt not in TIER_NORMALIZE:
            continue
        # ティアテーブルを発見。行数が最も多いものを選ぶ
        if len(rows) > best_count:
            best_count = len(rows)
            best_table = table

    tiers = {}
    if best_table:
        tiers = extract_tier_from_table(best_table)

    return {"type": page_type, "tiers": tiers}


# =============================================
# ステージページ解析
# =============================================
def parse_stage_page(soup, stage_name=""):
    """ステージ個別ページからデータ抽出"""
    data = {"name": stage_name}

    sections = extract_sections(soup)
    for sec_name, sec_data in sections.items():
        if "特徴" in sec_name or "概要" in sec_name:
            data["description"] = " ".join(sec_data.get("text", []))
        elif "おすすめ" in sec_name and "武器" in sec_name:
            data["recommended_weapons"] = " ".join(sec_data.get("text", []))
        elif "攻略" in sec_name or "立ち回り" in sec_name:
            data["strategy"] = " ".join(sec_data.get("text", []))
            data["strategy_subsections"] = sec_data.get("subsections", {})

    # 画像URL取得
    images = []
    for img_tag in soup.find_all("img"):
        src = img_tag.get("data-src") or img_tag.get("src", "")
        if "game8" in src and "splatoon" in src.lower():
            images.append(src)
    data["images"] = images[:5]  # 最大5枚

    return data


# =============================================
# メイン実行
# =============================================
def main():
    print("=== Game8 データ解析開始 ===\n")

    # 既存マスターデータ読み込み
    master_path = os.path.join(DATA_DIR, "splatoon3_master.json")
    if os.path.exists(master_path):
        with open(master_path, "r", encoding="utf-8") as f:
            master = json.load(f)
        print(f"既存マスターデータ読み込み: 武器{len(master.get('weapons', []))}件")
    else:
        master = {"weapons": [], "stages": [], "gear_powers": {}, "salmon_run": {}, "rules": []}

    # 既存武器のname→index マップ
    weapon_index = {w["name"]: i for i, w in enumerate(master["weapons"])}

    # =====================
    # 1. 武器個別ページの解析
    # =====================
    print("\n--- 武器個別ページ解析 ---")
    weapon_files = glob.glob(os.path.join(RAW_DIR, "weapon_*.html"))
    parsed_weapons = {}
    skipped = 0
    for fpath in sorted(weapon_files):
        fname = os.path.basename(fpath)

        # weapon_class_*.htmlはスキップ（武器種別一覧ページ）
        if fname.startswith("weapon_class_"):
            skipped += 1
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")

        # ファイル名から武器名推定（フォールバック用）
        m = re.match(r"weapon_(.+?)_\d+\.html", fname)
        weapon_name_from_file = m.group(1).replace("_", "") if m else fname

        weapon_data = parse_weapon_page(soup, weapon_name_from_file)
        actual_name = weapon_data.get("name", weapon_name_from_file)

        # マスターに存在しない場合、ファイル名の武器名も試す
        if actual_name not in weapon_index and weapon_name_from_file in weapon_index:
            actual_name = weapon_name_from_file
            weapon_data["name"] = actual_name

        parsed_weapons[actual_name] = weapon_data
        print(f"  ✓ {actual_name}")

    print(f"  解析完了: {len(parsed_weapons)}件 (スキップ: {skipped}件)")

    # 武器データをマスターにマージ
    for name, parsed in parsed_weapons.items():
        if name in weapon_index:
            idx = weapon_index[name]
            w = master["weapons"][idx]
            # Game8データで補完・上書き
            if parsed.get("damage") and not w.get("damage"):
                w["damage"] = parsed["damage"]
            if parsed.get("range") and not w.get("range"):
                w["range"] = parsed["range"]
            if parsed.get("effective_range"):
                w["effective_range"] = parsed["effective_range"]
            if parsed.get("shots_to_kill"):
                w["shots_to_kill"] = parsed["shots_to_kill"]
            if parsed.get("special_points"):
                w["special_points"] = parsed["special_points"]
            if parsed.get("rule_ratings"):
                w["rule_ratings"] = parsed["rule_ratings"]
            if parsed.get("star_ratings"):
                w["star_ratings"] = parsed["star_ratings"]
            if parsed.get("evaluation_text"):
                w["evaluation_text"] = parsed["evaluation_text"]
            if parsed.get("recommended_gear_text"):
                w["recommended_gear_text"] = parsed["recommended_gear_text"]
            if parsed.get("playstyle_text"):
                w["playstyle_text"] = parsed["playstyle_text"]
            if parsed.get("counter_text"):
                w["counter_text"] = parsed["counter_text"]
            if parsed.get("update_history"):
                w["update_history"] = parsed["update_history"]
        else:
            print(f"  ⚠ マスターに未登録: {name}")

    # =====================
    # 2. ティアリスト解析
    # =====================
    print("\n--- ティアリスト解析 ---")
    tier_data = {}
    tier_files = {
        "overall": "main_tier_list.html",
        "nawabari": "main_tier_nawabari.html",
        "area": "main_tier_area.html",
        "yagura": "main_tier_yagura.html",
        "hoko": "main_tier_hoko.html",
        "asari": "main_tier_asari.html",
    }
    for tier_type, fname in tier_files.items():
        soup = load_html(fname)
        if soup:
            tier_data[tier_type] = parse_tier_list(soup, tier_type)
            tier_count = sum(len(v) for v in tier_data[tier_type]["tiers"].values())
            print(f"  ✓ {tier_type}: {tier_count}件")

    # 総合ティアをマスター武器に反映
    if "overall" in tier_data:
        for tier, weapons in tier_data["overall"]["tiers"].items():
            for wp in weapons:
                name = wp["name"]
                if name in weapon_index:
                    master["weapons"][weapon_index[name]]["tier"] = tier

    # ルール別ティアも保存
    for rule_key in ["nawabari", "area", "yagura", "hoko", "asari"]:
        if rule_key in tier_data:
            for tier, weapons in tier_data[rule_key]["tiers"].items():
                for wp in weapons:
                    name = wp["name"]
                    if name in weapon_index:
                        master["weapons"][weapon_index[name]].setdefault("rule_tiers", {})[rule_key] = tier

    # =====================
    # 3. ステージ解析
    # =====================
    print("\n--- ステージ解析 ---")
    stage_files = glob.glob(os.path.join(RAW_DIR, "stage_*.html"))
    parsed_stages = {}
    for fpath in sorted(stage_files):
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")

        m = re.match(r"stage_(.+?)\.html", fname)
        stage_name = m.group(1).replace("_", "") if m else fname

        stage_data = parse_stage_page(soup, stage_name)
        parsed_stages[stage_data["name"]] = stage_data
        print(f"  ✓ {stage_data['name']}")

    # ステージデータをマスターにマージ
    stage_index = {s["name"]: i for i, s in enumerate(master.get("stages", []))}
    for name, parsed in parsed_stages.items():
        if name in stage_index:
            idx = stage_index[name]
            if parsed.get("description"):
                master["stages"][idx]["description"] = parsed["description"]
            if parsed.get("strategy"):
                master["stages"][idx]["strategy"] = parsed["strategy"]
            if parsed.get("recommended_weapons"):
                master["stages"][idx]["recommended_weapons"] = parsed["recommended_weapons"]
            if parsed.get("images"):
                master["stages"][idx]["images"] = parsed["images"]

    # =====================
    # 保存
    # =====================

    # 解析済みデータをparsed_dataに保存
    with open(os.path.join(OUT_DIR, "weapons_detail.json"), "w", encoding="utf-8") as f:
        json.dump(parsed_weapons, f, ensure_ascii=False, indent=2)

    with open(os.path.join(OUT_DIR, "tier_data.json"), "w", encoding="utf-8") as f:
        json.dump(tier_data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(OUT_DIR, "stages_detail.json"), "w", encoding="utf-8") as f:
        json.dump(parsed_stages, f, ensure_ascii=False, indent=2)

    # マスターデータ更新
    master_out = os.path.join(OUT_DIR, "splatoon3_master_merged.json")
    with open(master_out, "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    print(f"\n=== 解析完了 ===")
    print(f"武器詳細: {len(parsed_weapons)}件 → weapons_detail.json")
    print(f"ティアデータ: {len(tier_data)}件 → tier_data.json")
    print(f"ステージ詳細: {len(parsed_stages)}件 → stages_detail.json")
    print(f"マスターデータ: → splatoon3_master_merged.json")
    print(f"\n検証後 data/splatoon3_master.json にコピーしてください:")
    print(f"  cp {master_out} {master_path}")


if __name__ == "__main__":
    main()
