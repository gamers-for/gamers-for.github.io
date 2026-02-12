#!/usr/bin/env python3
"""
武器一覧ページ(weapons.md)を自動生成するスクリプト
data/splatoon3_weapons.json からアイコン付きの武器テーブルを生成
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "splatoon3_weapons.json")
WEAPONS_MD = os.path.join(BASE_DIR, "content", "games", "splatoon3", "weapons.md")

# サブ・スペシャルの日本語名→アイコンパスのマッピング
# (JSONデータから構築)


def build_sub_special_map(data):
    """サブ・スペシャルの日本語名→アイコンパスのマッピングを構築"""
    sub_map = {}
    for s in data.get("subs", []):
        if s["icon"]:
            sub_map[s["ja"]] = s["icon"]

    sp_map = {}
    for s in data.get("specials", []):
        if s["icon"]:
            sp_map[s["ja"]] = s["icon"]

    return sub_map, sp_map


def icon_img(path, name, prefix="/gamers-for"):
    """アイコン画像のmarkdownタグを生成"""
    if not path:
        return name
    return f"![{name}]({prefix}{path})"


def generate_weapons_md(data, sub_map, sp_map):
    """weapons.mdの内容を生成"""
    prefix = "/gamers-for"

    # 武器種別にグループ化
    classes = {}
    for w in data["weapons"]:
        cls = w["class"]
        if cls not in classes:
            classes[cls] = []
        classes[cls].append(w)

    # 武器種の表示順
    class_order = [
        "シューター", "ブラスター", "ローラー", "フデ",
        "チャージャー", "スロッシャー", "スピナー",
        "マニューバー", "シェルター", "ストリンガー", "ワイパー"
    ]

    lines = []
    lines.append("---")
    lines.append('title: "【スプラ3】全武器（ブキ）一覧"')
    lines.append('linkTitle: "ブキ一覧"')
    lines.append("weight: 6")
    lines.append("date: 2026-02-11")
    lines.append('categories: ["ブキ一覧"]')
    lines.append('tags: ["スプラトゥーン3", "武器"]')
    lines.append('description: "スプラトゥーン3の全武器（ブキ）一覧。サブウェポン・スペシャルウェポン・アイコン付きで全ブキを掲載。"')
    lines.append("---")
    lines.append("")
    lines.append('{{< update-info date="2026-02-11" >}}')
    lines.append("")
    lines.append("スプラトゥーン3に登場する**全武器（ブキ）**をアイコン付きで一覧にまとめました。")
    lines.append("")

    for cls in class_order:
        weapons = classes.get(cls, [])
        if not weapons:
            continue

        lines.append(f"## {cls}")
        lines.append("")
        lines.append("| 武器 | 名前 | サブ | スペシャル |")
        lines.append("|------|------|------|-----------|")

        for w in weapons:
            weapon_icon = icon_img(w["icon"], w["ja"], prefix) if w["icon"] else w["ja"]
            sub_icon_path = sub_map.get(w["sub"], "")
            sub_cell = icon_img(sub_icon_path, w["sub"], prefix) if sub_icon_path else w["sub"]
            sp_icon_path = sp_map.get(w["special"], "")
            sp_cell = icon_img(sp_icon_path, w["special"], prefix) if sp_icon_path else w["special"]

            lines.append(f"| {weapon_icon} | {w['ja']} | {sub_cell} {w['sub']} | {sp_cell} {w['special']} |")

        lines.append("")

    return "\n".join(lines)


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    sub_map, sp_map = build_sub_special_map(data)

    print(f"サブアイコン: {len(sub_map)}件")
    print(f"スペシャルアイコン: {len(sp_map)}件")

    content = generate_weapons_md(data, sub_map, sp_map)

    with open(WEAPONS_MD, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"生成完了: {WEAPONS_MD}")
    print(f"武器数: {len(data['weapons'])}件")


if __name__ == "__main__":
    main()
