#!/usr/bin/env python3
"""全ジャンル網羅テンプレート: ダミーコンテンツ生成"""
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "games", "sample-game")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  {path}")

def page(path, title, ltitle, wt, cat, desc, body):
    w(path, f"""---
title: "{title}"
linkTitle: "{ltitle}"
weight: {wt}
date: 2026-02-11
categories: ["{cat}"]
description: "{desc}"
---

{{{{< update-info date="2026-02-12" >}}}}

{body}
""")

# ========== カテゴリ定義 ==========
# 各ジャンルのページを以下で定義していく
# Part 1: トップページ + RPG基本
# Part 2: ソシャゲ + 恋愛シミュ + 格闘
# Part 3: カードゲーム + 音ゲー + ストラテジー
# Part 4: レース + パズル/ボード + サバイバル
# Part 5: 育成/牧場 + FPS + スポーツ + 共通
# Part 6: MOBA + ローグライク + オープンワールド + ホラー等
# Part 7: バトロワ + TD + オートバトラー + MMO + 放置等
# Part 8: モンスター収集 + ハクスラ + 脱出 + 経営 + サンドボックス + VR + 麻雀 + 落ちゲー + MMO生産 + GvG

exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part1_top_rpg.py")).read())
exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part2_social_romance_fighting.py")).read())
exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part3_card_rhythm_strategy.py")).read())
exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part4_race_puzzle_survival.py")).read())
exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part5_farm_fps_sports_common.py")).read())
exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part6_moba_rogue_openworld_etc.py")).read())
exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part7_br_td_auto_mmo_etc.py")).read())
exec(open(os.path.join(os.path.dirname(__file__), "_gen_parts", "part8_monster_hack_escape_etc.py")).read())

print(f"\n=== 全ジャンル網羅テンプレート生成完了 ===")
