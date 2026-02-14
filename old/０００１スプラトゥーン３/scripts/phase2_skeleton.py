#!/usr/bin/env python3
"""
フェーズ2: 3サイトの項目を全て網羅した骨組みHTML/コンテンツを作成
- Hugo layouts (baseof, single, list, partials, shortcodes)
- CSS (3サイト融合)
- content skeleton (全ページ・全武器の枠、解説文は空)
"""

import json
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
HUGO_DIR = Path("/mnt/ubuntu22-home/robot/work_space/project_blog/gamers-for")
CONTENT_DIR = HUGO_DIR / "content" / "games" / "splatoon3"
CLEAN_DATA = BASE_DIR / "raw_data" / "clean_weapons.json"

GAME_NAME = "スプラトゥーン3"
GAME_SLUG = "splatoon3"

TIER_ORDER = ["S+", "S", "A+", "A", "B+", "B", "C+", "C"]
TIER_COLORS = {
    "S+": "#ff1744", "S": "#ff5722", "A+": "#ff9800", "A": "#ffc107",
    "B+": "#8bc34a", "B": "#4caf50", "C+": "#2196f3", "C": "#9e9e9e",
}

WEAPON_TYPES = [
    {"name": "シューター", "slug": "shooter", "desc": "インクを連射して戦う基本武器"},
    {"name": "ローラー", "slug": "roller", "desc": "塗りながら移動、至近距離で高火力"},
    {"name": "チャージャー", "slug": "charger", "desc": "チャージして遠距離を狙撃"},
    {"name": "ブラスター", "slug": "blaster", "desc": "爆発する弾で範囲攻撃"},
    {"name": "スロッシャー", "slug": "slosher", "desc": "バケツからインクをぶちまける"},
    {"name": "スピナー", "slug": "spinner", "desc": "チャージ後に高速連射"},
    {"name": "マニューバー", "slug": "maneuver", "desc": "スライドしながら二丁拳銃"},
    {"name": "シェルター", "slug": "shelter", "desc": "傘でガードしながら戦う"},
    {"name": "フデ", "slug": "brush", "desc": "高速で塗りながら移動"},
    {"name": "ストリンガー", "slug": "stringer", "desc": "弓型の新武器種"},
    {"name": "ワイパー", "slug": "wiper", "desc": "剣型の新武器種"},
]


def slug(name):
    s = name.lower()
    s = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or "item"


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  -> {os.path.relpath(path, HUGO_DIR)}")


def load_weapons():
    with open(CLEAN_DATA, "r", encoding="utf-8") as f:
        return json.load(f)["weapons"]


# ============================================================
# コンテンツ骨組み生成
# ============================================================

def gen_game_top(weapons):
    """ゲームTOPページ"""
    types_count = {}
    for w in weapons:
        t = w.get("type", "?")
        types_count[t] = types_count.get(t, 0) + 1

    content = f"""---
title: "{GAME_NAME} 攻略"
linkTitle: "スプラ3"
description: "{GAME_NAME}の攻略情報まとめ。武器ランキング、初心者ガイド、サーモンラン、ギア情報を網羅。"
weight: 1
---

## {GAME_NAME} 攻略TOP

<!-- フェーズ3で記入: サイト紹介文 -->

### 最強ランキング

- [最強武器ランキング](tier-list/) - 全{len(weapons)}武器を徹底評価
- [ガチエリア最強武器](rule-tier/area/)
- [ガチヤグラ最強武器](rule-tier/yagura/)
- [ガチホコ最強武器](rule-tier/hoko/)
- [ガチアサリ最強武器](rule-tier/asari/)
- [ナワバリ最強武器](rule-tier/nawabari/)
- [最強スペシャルランキング](special-tier/)
- [最強ギアパワーランキング](gear-tier/)

### 武器（ブキ）情報

- [全武器一覧](weapons/) - {len(weapons)}武器の性能比較
"""
    for wt in WEAPON_TYPES:
        c = types_count.get(wt["name"], 0)
        content += f'- [{wt["name"]}一覧](weapons/{wt["slug"]}/) - {c}種\n'

    content += f"""
### サブ・スペシャル

- [サブウェポン一覧](sub-weapons/)
- [スペシャルウェポン一覧](special-weapons/)

### バトル攻略

- [ガチエリア攻略](battle/area/)
- [ガチヤグラ攻略](battle/yagura/)
- [ガチホコ攻略](battle/hoko/)
- [ガチアサリ攻略](battle/asari/)
- [ナワバリバトル攻略](battle/nawabari/)
- [Xマッチ攻略](battle/xmatch/)

### サーモンラン

- [サーモンラン攻略まとめ](salmon-run/)

### ギア・ギアパワー

- [ギアパワー一覧](gear/)
- [最強ギアパワーランキング](gear-tier/)
- [ギア厳選のやり方](gear/selection/)

### 初心者攻略

- [初心者がやるべきこと](beginner/)
- [初心者おすすめ武器](beginner/weapons/)
- [操作方法・感度設定](beginner/controls/)

### ステージ

- [ステージ一覧](stages/)

### フェス

- [フェス最新情報](fes/)

### ヒーローモード

- [ヒーローモード攻略](hero-mode/)

### サイドオーダー

- [サイドオーダー攻略](side-order/)

### ナワバトラー

- [ナワバトラー攻略](nawabattler/)

### 武器種別一覧

| 武器種 | 武器数 | 特徴 |
|--------|--------|------|
"""
    for wt in WEAPON_TYPES:
        c = types_count.get(wt["name"], 0)
        content += f'| **{wt["name"]}** | {c} | {wt["desc"]} |\n'

    write(str(CONTENT_DIR / "_index.md"), content)


def gen_tier_list(weapons):
    """最強武器ランキング"""
    tiered = [w for w in weapons if w.get("tier")]
    tiered.sort(key=lambda w: (TIER_ORDER.index(w["tier"]) if w["tier"] in TIER_ORDER else 99, w["name"]))

    content = f"""---
title: "【{GAME_NAME}】最強武器ランキング"
linkTitle: "最強武器"
weight: 2
date: 2026-02-12
categories: ["最強ランキング"]
tags: ["{GAME_NAME}", "武器"]
description: "{GAME_NAME}の最強武器ランキング。全{len(tiered)}武器を{len(TIER_ORDER)}段階で評価。"
---

## 最強武器ランキング早見表

<!-- フェーズ3で記入: ランキングの評価基準・更新日 -->

"""
    # ティアごとのグリッド
    tier_groups = {}
    for w in tiered:
        tier_groups.setdefault(w["tier"], []).append(w)

    for tier in TIER_ORDER:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f"### {tier}ランク（{len(group)}武器）\n\n"
        content += "| 武器名 | 武器種 | サブ | スペシャル |\n"
        content += "|--------|--------|------|----------|\n"
        for w in group:
            content += f'| **{w["name"]}** | {w.get("type","-")} | {w.get("sub","-")} | {w.get("special","-")} |\n'
        content += "\n<!-- フェーズ3で記入: 各武器の評価コメント -->\n\n---\n\n"

    # ティア別詳細
    content += "## 各武器の詳細評価\n\n"
    for tier in TIER_ORDER:
        if tier not in tier_groups:
            continue
        content += f"### {tier}ランクの武器詳細\n\n"
        for w in tier_groups[tier]:
            content += f"#### {w['name']}\n\n"
            content += f"- **武器種**: {w.get('type','-')}\n"
            content += f"- **サブ**: {w.get('sub','-')}\n"
            content += f"- **スペシャル**: {w.get('special','-')}\n"
            content += f"- **ティア**: {tier}\n\n"
            content += f"<!-- フェーズ3で記入: {w['name']}の評価コメント・強い点・弱い点 -->\n\n"

    content += """## 関連記事

- [全武器一覧](../weapons/)
- [初心者おすすめ武器](../beginner/weapons/)
- [ガチエリア最強武器](../rule-tier/area/)
- [ガチヤグラ最強武器](../rule-tier/yagura/)
- [ガチホコ最強武器](../rule-tier/hoko/)
- [ガチアサリ最強武器](../rule-tier/asari/)
"""
    write(str(CONTENT_DIR / "tier-list.md"), content)


def gen_weapon_list(weapons):
    """全武器一覧 + 武器種別一覧"""
    # _index.md
    content = f"""---
title: "【{GAME_NAME}】全武器一覧"
linkTitle: "全武器一覧"
weight: 3
date: 2026-02-12
description: "{GAME_NAME}の全{len(weapons)}武器を一覧。サブ・スペシャル・評価を完全網羅。"
---

## 全{len(weapons)}武器一覧

<!-- フェーズ3で記入: 武器一覧の説明文 -->

"""
    by_type = {}
    for w in weapons:
        by_type.setdefault(w.get("type", "その他"), []).append(w)

    for wt in WEAPON_TYPES:
        group = by_type.get(wt["name"], [])
        if not group:
            continue
        group.sort(key=lambda w: (TIER_ORDER.index(w["tier"]) if w.get("tier") in TIER_ORDER else 99, w["name"]))
        content += f'## {wt["name"]}（{len(group)}種）\n\n'
        content += "| 武器名 | サブ | スペシャル | ティア |\n"
        content += "|--------|------|----------|--------|\n"
        for w in group:
            tier = w.get("tier", "-")
            content += f'| [{w["name"]}]({slug(w["name"])}/) | {w.get("sub","-")} | {w.get("special","-")} | **{tier}** |\n'
        content += "\n---\n\n"

    write(str(CONTENT_DIR / "weapons" / "_index.md"), content)

    # 武器種別ページ
    for wt in WEAPON_TYPES:
        group = by_type.get(wt["name"], [])
        if not group:
            continue
        wt_content = f"""---
title: "【{GAME_NAME}】{wt['name']}一覧"
linkTitle: "{wt['name']}"
date: 2026-02-12
description: "{GAME_NAME}の{wt['name']}{len(group)}種を一覧。"
---

## {wt['name']}一覧（{len(group)}種）

<!-- フェーズ3で記入: {wt['name']}の特徴説明 -->

| 武器名 | サブ | スペシャル | ティア |
|--------|------|----------|--------|
"""
        for w in group:
            tier = w.get("tier", "-")
            wt_content += f'| [{w["name"]}](../{slug(w["name"])}/) | {w.get("sub","-")} | {w.get("special","-")} | **{tier}** |\n'

        wt_content += "\n<!-- フェーズ3で記入: 各武器の簡易コメント -->\n"
        write(str(CONTENT_DIR / "weapons" / wt["slug"] / "_index.md"), wt_content)


def gen_individual_weapons(weapons):
    """個別武器ページ（全110武器）"""
    for w in weapons:
        s = slug(w["name"])
        tier = w.get("tier", "未評価")
        content = f"""---
title: "【{GAME_NAME}】{w['name']}の評価と立ち回り"
linkTitle: "{w['name']}"
date: 2026-02-12
categories: ["{w.get('type','')}"]
tags: ["{GAME_NAME}", "{w.get('type','')}", "{w['name']}"]
description: "{GAME_NAME}の{w['name']}の評価・立ち回り・おすすめギアを解説。"
---

## {w['name']}

### 基本情報

| 項目 | 値 |
|------|-----|
| **武器種** | {w.get('type','-')} |
| **サブ** | {w.get('sub','-')} |
| **スペシャル** | {w.get('special','-')} |
| **ティア** | {tier} |

### 総合評価

<!-- フェーズ3で記入: 3サイト+SNSの情報を統合した評価まとめ -->

### 強い点

<!-- フェーズ3で記入 -->

### 弱い点

<!-- フェーズ3で記入 -->

### 立ち回りのコツ

<!-- フェーズ3で記入: ナワバリ/ガチエリア/ガチヤグラ/ガチホコ/ガチアサリそれぞれ -->

### おすすめギア構成

| ギアパワー | 理由 |
|-----------|------|
| <!-- フェーズ3で記入 --> | |

### おすすめのサブ・スペシャルの使い方

<!-- フェーズ3で記入: {w.get('sub','')}と{w.get('special','')}の活用法 -->

### SNSでの評判

<!-- フェーズ3で記入: Twitterなどの生の声 -->

### 関連記事

- [最強武器ランキング](../../tier-list/)
- [全武器一覧](../)
- [{w.get('type','')}一覧](../{[wt['slug'] for wt in WEAPON_TYPES if wt['name']==w.get('type','')][0] if w.get('type') in [wt['name'] for wt in WEAPON_TYPES] else ''}/)
- [初心者おすすめ武器](../../beginner/weapons/)
"""
        write(str(CONTENT_DIR / "weapons" / f"{s}.md"), content)


def gen_rule_tiers():
    """ルール別最強武器ランキング"""
    rules = [
        ("area", "ガチエリア"),
        ("yagura", "ガチヤグラ"),
        ("hoko", "ガチホコ"),
        ("asari", "ガチアサリ"),
        ("nawabari", "ナワバリバトル"),
    ]
    # _index.md
    idx = f"""---
title: "【{GAME_NAME}】ルール別最強武器ランキング"
linkTitle: "ルール別最強武器"
date: 2026-02-12
description: "{GAME_NAME}のルール別最強武器ランキング。"
---

## ルール別最強武器

"""
    for rslug, rname in rules:
        idx += f"- [{rname}最強武器]({rslug}/)\n"
    write(str(CONTENT_DIR / "rule-tier" / "_index.md"), idx)

    for rslug, rname in rules:
        content = f"""---
title: "【{GAME_NAME}】{rname}最強武器ランキング"
linkTitle: "{rname}最強"
date: 2026-02-12
categories: ["最強ランキング", "{rname}"]
description: "{GAME_NAME}の{rname}で最強の武器をランキング。"
---

## {rname}最強武器ランキング

<!-- フェーズ3で記入: 3サイトの{rname}ランキングを統合 -->

### S+ランク

<!-- フェーズ3で記入 -->

### Sランク

<!-- フェーズ3で記入 -->

### A+ランク

<!-- フェーズ3で記入 -->

### Aランク

<!-- フェーズ3で記入 -->

### B+ランク

<!-- フェーズ3で記入 -->

### 関連記事

- [最強武器ランキング（総合）](../../tier-list/)
- [全武器一覧](../../weapons/)
"""
        write(str(CONTENT_DIR / "rule-tier" / rslug / "_index.md"), content)


def gen_beginner():
    """初心者攻略"""
    idx = f"""---
title: "【{GAME_NAME}】初心者攻略ガイド"
linkTitle: "初心者攻略"
weight: 4
date: 2026-02-12
categories: ["初心者攻略"]
description: "{GAME_NAME}の初心者向け攻略ガイド。序盤にやるべきことを解説。"
---

## 初心者がやるべきこと

<!-- フェーズ3で記入: 3サイトの初心者ガイドを統合した内容 -->

### STEP1: チュートリアルをクリアする

<!-- フェーズ3で記入 -->

### STEP2: ナワバリバトルで操作に慣れる

<!-- フェーズ3で記入 -->

### STEP3: 自分に合った武器を見つける

<!-- フェーズ3で記入 -->

### STEP4: ギアパワーを理解する

<!-- フェーズ3で記入 -->

### STEP5: バンカラマッチに挑戦する

<!-- フェーズ3で記入 -->

### おすすめ設定

<!-- フェーズ3で記入: ジャイロ感度、画面設定等 -->

- [おすすめ武器](weapons/)
- [操作方法・感度設定](controls/)
"""
    write(str(CONTENT_DIR / "beginner" / "_index.md"), idx)

    # おすすめ武器
    wpn = f"""---
title: "【{GAME_NAME}】初心者おすすめ武器"
linkTitle: "おすすめ武器"
date: 2026-02-12
description: "{GAME_NAME}の初心者におすすめの武器を紹介。"
---

## 初心者おすすめ武器ランキング

<!-- フェーズ3で記入: 3サイトのおすすめ武器を統合 -->

| 順位 | 武器名 | 武器種 | おすすめ理由 |
|------|--------|--------|------------|
| 1 | <!-- フェーズ3 --> | | |
| 2 | <!-- フェーズ3 --> | | |
| 3 | <!-- フェーズ3 --> | | |
| 4 | <!-- フェーズ3 --> | | |
| 5 | <!-- フェーズ3 --> | | |

### 関連記事

- [最強武器ランキング](../../tier-list/)
- [全武器一覧](../../weapons/)
"""
    write(str(CONTENT_DIR / "beginner" / "weapons.md"), wpn)

    # 操作方法
    ctrl = f"""---
title: "【{GAME_NAME}】操作方法・おすすめ感度設定"
linkTitle: "操作方法"
date: 2026-02-12
description: "{GAME_NAME}の操作方法とおすすめジャイロ感度を解説。"
---

## 操作方法

<!-- フェーズ3で記入 -->

## おすすめ感度設定

<!-- フェーズ3で記入 -->

## ジャイロとスティックどっちがいい？

<!-- フェーズ3で記入 -->
"""
    write(str(CONTENT_DIR / "beginner" / "controls.md"), ctrl)


def gen_salmon_run():
    """サーモンラン"""
    content = f"""---
title: "【{GAME_NAME}】サーモンラン攻略まとめ"
linkTitle: "サーモンラン"
date: 2026-02-12
categories: ["サーモンラン"]
description: "{GAME_NAME}のサーモンラン攻略。オオモノシャケの倒し方、報酬、立ち回りを解説。"
---

## サーモンラン攻略まとめ

<!-- フェーズ3で記入: 概要 -->

### オオモノシャケの倒し方一覧

| オオモノ | 倒し方 | 優先度 |
|---------|--------|--------|
| <!-- フェーズ3で記入 --> | | |

### 特殊ウェーブ一覧

<!-- フェーズ3で記入 -->

### 立ち回りのコツ

<!-- フェーズ3で記入 -->

### 報酬一覧

<!-- フェーズ3で記入 -->

### ランクと評価

<!-- フェーズ3で記入 -->

### 関連記事

- [最強武器ランキング](../tier-list/)
- [初心者攻略](../beginner/)
"""
    write(str(CONTENT_DIR / "salmon-run.md"), content)


def gen_gear():
    """ギア・ギアパワー"""
    content = f"""---
title: "【{GAME_NAME}】ギアパワー一覧"
linkTitle: "ギア"
date: 2026-02-12
description: "{GAME_NAME}のギアパワー一覧と効果を解説。"
---

## ギアパワー一覧

<!-- フェーズ3で記入: 各ギアパワーの説明 -->

| ギアパワー | 効果 | おすすめ度 |
|-----------|------|----------|
| <!-- フェーズ3で記入 --> | | |

### ギア厳選のやり方

<!-- フェーズ3で記入 -->

### おすすめギア構成

<!-- フェーズ3で記入: 武器種別のおすすめギア -->

### 関連記事

- [最強ギアパワーランキング](../gear-tier/)
- [最強武器ランキング](../tier-list/)
"""
    write(str(CONTENT_DIR / "gear" / "_index.md"), content)


def gen_special_gear_tier():
    """最強スペシャル・最強ギアパワーランキング"""
    for name, link, desc in [
        ("スペシャル", "special-tier", "スペシャルウェポン"),
        ("ギアパワー", "gear-tier", "ギアパワー"),
    ]:
        content = f"""---
title: "【{GAME_NAME}】最強{name}ランキング"
linkTitle: "最強{name}"
date: 2026-02-12
categories: ["最強ランキング"]
description: "{GAME_NAME}の最強{desc}ランキング。"
---

## 最強{name}ランキング

<!-- フェーズ3で記入: 3サイトのランキングを統合 -->

### S+ランク

<!-- フェーズ3で記入 -->

### Sランク

<!-- フェーズ3で記入 -->

### Aランク

<!-- フェーズ3で記入 -->

### 関連記事

- [最強武器ランキング](../tier-list/)
- [全武器一覧](../weapons/)
"""
        write(str(CONTENT_DIR / f"{link}.md"), content)


def gen_stages():
    """ステージ一覧"""
    content = f"""---
title: "【{GAME_NAME}】ステージ一覧"
linkTitle: "ステージ"
date: 2026-02-12
description: "{GAME_NAME}のステージ一覧と攻略情報。"
---

## ステージ一覧

<!-- フェーズ3で記入: 全ステージの一覧と特徴 -->

| ステージ名 | 特徴 | おすすめ武器 |
|-----------|------|------------|
| <!-- フェーズ3で記入 --> | | |

### 関連記事

- [最強武器ランキング](../tier-list/)
- [バトル攻略](../battle/)
"""
    write(str(CONTENT_DIR / "stages.md"), content)


def gen_sub_special():
    """サブ・スペシャル一覧"""
    for kind, kslug in [("サブウェポン", "sub-weapons"), ("スペシャルウェポン", "special-weapons")]:
        content = f"""---
title: "【{GAME_NAME}】{kind}一覧"
linkTitle: "{kind}"
date: 2026-02-12
description: "{GAME_NAME}の{kind}一覧と使い方。"
---

## {kind}一覧

<!-- フェーズ3で記入: 各{kind}の説明と評価 -->

| {kind} | 効果 | おすすめ度 |
|--------|------|----------|
| <!-- フェーズ3で記入 --> | | |
"""
        write(str(CONTENT_DIR / f"{kslug}.md"), content)


def gen_battle():
    """バトル攻略"""
    idx = f"""---
title: "【{GAME_NAME}】バトル攻略"
linkTitle: "バトル攻略"
date: 2026-02-12
description: "{GAME_NAME}のバトルルール攻略。"
---

## バトル攻略

- [ガチエリア](area/)
- [ガチヤグラ](yagura/)
- [ガチホコ](hoko/)
- [ガチアサリ](asari/)
- [ナワバリバトル](nawabari/)
- [Xマッチ](xmatch/)
"""
    write(str(CONTENT_DIR / "battle" / "_index.md"), idx)

    rules = [
        ("area", "ガチエリア"), ("yagura", "ガチヤグラ"),
        ("hoko", "ガチホコ"), ("asari", "ガチアサリ"),
        ("nawabari", "ナワバリバトル"), ("xmatch", "Xマッチ"),
    ]
    for rslug, rname in rules:
        content = f"""---
title: "【{GAME_NAME}】{rname}攻略"
linkTitle: "{rname}"
date: 2026-02-12
description: "{GAME_NAME}の{rname}のルール・立ち回り・おすすめ武器を解説。"
---

## {rname}のルール

<!-- フェーズ3で記入 -->

## 勝つためのコツ

<!-- フェーズ3で記入 -->

## おすすめ武器

<!-- フェーズ3で記入 -->

### 関連記事

- [{rname}最強武器](../../rule-tier/{rslug}/)
- [最強武器ランキング](../../tier-list/)
"""
        write(str(CONTENT_DIR / "battle" / rslug / "_index.md"), content)


def gen_misc():
    """フェス、ヒーローモード、サイドオーダー、ナワバトラー"""
    pages = [
        ("fes", "フェス最新情報", "フェスの投票・報酬・攻略情報まとめ。"),
        ("hero-mode", "ヒーローモード攻略", "ヒーローモードの攻略情報まとめ。"),
        ("side-order", "サイドオーダー攻略", "サイドオーダーの攻略情報まとめ。"),
        ("nawabattler", "ナワバトラー攻略", "ナワバトラーの攻略・最強デッキ情報。"),
    ]
    for pslug, ptitle, pdesc in pages:
        content = f"""---
title: "【{GAME_NAME}】{ptitle}"
linkTitle: "{ptitle.replace('攻略','').replace('最新情報','')}"
date: 2026-02-12
description: "{GAME_NAME}の{pdesc}"
---

## {ptitle}

<!-- フェーズ3で記入: 3サイトの情報を統合 -->

### 関連記事

- [最強武器ランキング](../tier-list/)
- [初心者攻略](../beginner/)
"""
        write(str(CONTENT_DIR / f"{pslug}.md"), content)


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 60)
    print("フェーズ2: 骨組みコンテンツ生成")
    print("=" * 60)

    weapons = load_weapons()
    print(f"武器データ: {len(weapons)}武器\n")

    print("--- ゲームTOP ---")
    gen_game_top(weapons)

    print("\n--- 最強武器ランキング ---")
    gen_tier_list(weapons)

    print("\n--- 全武器一覧 + 武器種別 ---")
    gen_weapon_list(weapons)

    print("\n--- 個別武器ページ ---")
    gen_individual_weapons(weapons)

    print("\n--- ルール別ランキング ---")
    gen_rule_tiers()

    print("\n--- 初心者攻略 ---")
    gen_beginner()

    print("\n--- サーモンラン ---")
    gen_salmon_run()

    print("\n--- ギア ---")
    gen_gear()

    print("\n--- 最強スペシャル・ギアパワー ---")
    gen_special_gear_tier()

    print("\n--- ステージ ---")
    gen_stages()

    print("\n--- サブ・スペシャル一覧 ---")
    gen_sub_special()

    print("\n--- バトル攻略 ---")
    gen_battle()

    print("\n--- その他（フェス・ヒーロー・サイドオーダー・ナワバトラー） ---")
    gen_misc()

    # 統計
    total_files = 0
    for root, dirs, files in os.walk(str(CONTENT_DIR)):
        total_files += len([f for f in files if f.endswith(".md")])

    print(f"\n{'='*60}")
    print(f"フェーズ2 完了!")
    print(f"{'='*60}")
    print(f"生成ファイル数: {total_files}")
    print(f"コンテンツディレクトリ: {CONTENT_DIR}")


if __name__ == "__main__":
    main()
