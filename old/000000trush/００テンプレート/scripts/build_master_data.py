#!/usr/bin/env python3
"""
汎用マスターデータビルダー
game_config.json を読み込み、raw_data/ のMarkdownファイルを解析して
Hugo data/ にJSONマスターデータを出力する。

使い方:
  python build_master_data.py /path/to/０１ゲーム名/game_config.json
"""

import json
import os
import re
import sys
import importlib.util


def load_config(config_path):
    """game_config.json を読み込む"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_md_table(text, skip_headers=True):
    """Markdownテーブルをパースしてリストのリストに変換

    Args:
        text: テーブルを含むMarkdownテキスト
        skip_headers: ヘッダー行をスキップするか

    Returns:
        list[list[str]]: セルの2次元リスト
    """
    rows = []
    is_first_data = True
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        # セパレータ行はスキップ
        if re.match(r"^\|[\s\-:]+\|$", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        # ヘッダー行スキップ
        if skip_headers and is_first_data:
            is_first_data = False
            continue
        rows.append(cells)
    return rows


def extract_section(text, heading, level=2):
    """Markdownテキストから指定見出しのセクションを抽出

    Args:
        text: Markdownテキスト全体
        heading: 見出しテキスト（#を除く）
        level: 見出しレベル（2 = ##, 3 = ### 等）

    Returns:
        str: セクションの内容（見出し行を含む）。見つからなければ空文字
    """
    prefix = "#" * level + " "
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(prefix) and heading in line:
            start = i
            continue
        if start is not None and line.strip().startswith(prefix):
            return "\n".join(lines[start:i])
    if start is not None:
        return "\n".join(lines[start:])
    return ""


def build_entities_from_tables(config, raw_dir):
    """raw_data/ 内のMarkdownテーブルからエンティティ（武器/キャラ等）リストを構築

    game_config.json の raw_data_files 設定に従い、ファイルを読み込む。
    各ファイルの entity_table セクションからデータを抽出する。
    """
    entities = []
    entity_type = config["entity_type"]
    fields = entity_type["fields"]

    raw_files = config.get("raw_data_files", [])

    for file_conf in raw_files:
        filepath = os.path.join(raw_dir, file_conf["filename"])
        if not os.path.exists(filepath):
            print(f"  [skip] {file_conf['filename']} not found")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # entity_tables: テーブルデータの抽出設定
        for table_conf in file_conf.get("entity_tables", []):
            section_name = table_conf.get("section", "")
            class_name = table_conf.get("class", "")
            column_map = table_conf.get("column_map", {})

            if section_name:
                section_text = extract_section(text, section_name, table_conf.get("level", 2))
            else:
                section_text = text

            rows = parse_md_table(section_text)
            for cells in rows:
                entity = {}
                for field_name, col_idx in column_map.items():
                    if isinstance(col_idx, int) and col_idx < len(cells):
                        entity[field_name] = cells[col_idx]
                    elif isinstance(col_idx, str):
                        entity[field_name] = col_idx  # 固定値

                if class_name:
                    entity.setdefault("class", class_name)

                # 最低限 name フィールドが必要
                if entity.get("name"):
                    entities.append(entity)

        # tier_tables: ティアデータの抽出設定
        for tier_conf in file_conf.get("tier_tables", []):
            section_name = tier_conf.get("section", "")
            name_col = tier_conf.get("name_column", 0)
            tier_value = tier_conf.get("tier", "")

            if section_name:
                section_text = extract_section(text, section_name, tier_conf.get("level", 2))
            else:
                section_text = text

            rows = parse_md_table(section_text)
            for cells in rows:
                if name_col < len(cells):
                    weapon_name = cells[name_col]
                    # 既存エンティティのtierを更新
                    for e in entities:
                        if e.get("name") == weapon_name:
                            e["tier"] = tier_value
                            break

    return entities


def build_extra_data(config, raw_dir):
    """ゲーム固有の追加データを構築（custom plugin経由）"""
    extra = {}
    plugin_dir = config.get("custom_plugin_dir", "./custom")
    config_dir = os.path.dirname(os.path.abspath(config.get("_config_path", ".")))
    plugin_path = os.path.join(config_dir, plugin_dir, "build_extensions.py")

    if os.path.exists(plugin_path):
        spec = importlib.util.spec_from_file_location("build_extensions", plugin_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "build_extra_data"):
            extra = mod.build_extra_data(config, raw_dir)
            print(f"  [plugin] build_extensions.py: {len(extra)} extra data keys loaded")

    return extra


def merge_icon_data(entities, config, hugo_dir):
    """既存のアイコンデータがあればマージ"""
    game_slug = config["game_slug"]
    data_dir = os.path.join(hugo_dir, "data")
    icon_file = os.path.join(data_dir, f"{game_slug}_weapons.json")

    if not os.path.exists(icon_file):
        return

    with open(icon_file, "r", encoding="utf-8") as f:
        icon_data = json.load(f)

    # アイコンマッピング構築
    icon_map = {}
    for category in ["weapons", "subs", "specials"]:
        for item in icon_data.get(category, []):
            name_key = item.get("ja", item.get("name", ""))
            if name_key:
                icon_map[name_key] = item.get("icon", "")

    for e in entities:
        if not e.get("icon") and e.get("name") in icon_map:
            e["icon"] = icon_map[e["name"]]


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_master_data.py /path/to/game_config.json")
        sys.exit(1)

    config_path = os.path.abspath(sys.argv[1])
    config = load_config(config_path)
    config["_config_path"] = config_path

    config_dir = os.path.dirname(config_path)
    raw_dir = os.path.join(config_dir, config.get("raw_data_dir", "./raw_data"))
    hugo_dir = os.path.join(config_dir, config.get("hugo_site_dir", "../gamers-for"))
    data_dir = os.path.join(hugo_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    game_slug = config["game_slug"]
    entity_name = config["entity_type"]["name"]

    print(f"=== {config['game_name']} マスターデータ生成 ===")
    print(f"raw_data: {raw_dir}")
    print(f"出力先: {data_dir}")

    # 1. エンティティ構築
    entities = build_entities_from_tables(config, raw_dir)
    print(f"\n{entity_name}数: {len(entities)}")

    # 2. アイコンデータマージ
    merge_icon_data(entities, config, hugo_dir)

    # 3. 追加データ構築（プラグイン）
    extra = build_extra_data(config, raw_dir)

    # 4. 出力
    master = {
        config["entity_type"]["slug_prefix"]: entities,
        **extra,
    }

    output_path = os.path.join(data_dir, f"{game_slug}_master.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)

    # 5. 統計
    if entities:
        classes = {}
        for e in entities:
            cls = e.get("class", "不明")
            classes[cls] = classes.get(cls, 0) + 1

        print(f"\n{entity_name}種別:")
        for cls, count in sorted(classes.items(), key=lambda x: -x[1]):
            print(f"  {cls}: {count}")

    for key, val in extra.items():
        if isinstance(val, list):
            print(f"{key}: {len(val)}件")
        elif isinstance(val, dict):
            total = sum(len(v) if isinstance(v, list) else 1 for v in val.values())
            print(f"{key}: {total}件")

    print(f"\n保存先: {output_path}")


if __name__ == "__main__":
    main()
