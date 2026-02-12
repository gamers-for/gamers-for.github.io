#!/usr/bin/env python3
"""
マスターJSONから全Hugoコンテンツページを自動生成するスクリプト
Game8風のリッチなコンテンツを生成
"""

import json
import os
import textwrap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONTENT_DIR = os.path.join(BASE_DIR, "content", "games", "splatoon3")
IMG_BASE = "/gamers-for/images/games/splatoon3"

# マスターデータ読み込み
with open(os.path.join(DATA_DIR, "splatoon3_master.json"), "r", encoding="utf-8") as f:
    MASTER = json.load(f)


def img(path):
    """画像パスをサイトURL付きに変換"""
    if not path:
        return ""
    return f"{IMG_BASE}{path.replace('/images/games/splatoon3', '')}"


def rating_to_num(r):
    """Game8評価を数値に変換（ソート用）"""
    order = {"X": 0, "S+": 1, "S": 2, "A+": 3, "A": 4, "B+": 5, "B": 6, "C+": 7, "C": 8}
    return order.get(r, 99)


def tier_to_num(t):
    """ティア→ソート順"""
    order = {"X": 0, "S+": 1, "S": 2, "A+": 3, "A": 4, "B+": 5, "B": 6, "C+": 7, "C": 8}
    return order.get(t, 99)


# =============================================
# 1. _index.md - ゲームTOP
# =============================================
def generate_index():
    weapons = MASTER["weapons"]
    classes = {}
    for w in weapons:
        cls = w.get("class", "その他")
        if cls not in classes:
            classes[cls] = 0
        classes[cls] += 1

    # クラス順序
    class_order = ["シューター", "ブラスター", "ローラー", "フデ", "チャージャー",
                   "スロッシャー", "スピナー", "マニューバー", "シェルター",
                   "ストリンガー", "ワイパー"]

    content = textwrap.dedent(f"""\
    ---
    title: "スプラトゥーン3 攻略"
    linkTitle: "スプラトゥーン3"
    description: "スプラトゥーン3の攻略情報まとめ。最強武器ランキング、全{len(weapons)}武器データ、ギアパワー、サーモンラン、ステージ攻略など。"
    weight: 1
    ---

    {{{{< update-info date="2026-02-12" >}}}}

    ## スプラトゥーン3 攻略TOP

    Nintendo Switch用対戦アクション「スプラトゥーン3」の攻略情報を**全{len(weapons)}武器**分まとめています。Game8・GameWith等の情報を統合した最新環境の評価です。

    ### 人気記事

    - [最強武器ランキング](tier-list/) - 全ブキのティアランク（X〜C）
    - [全武器一覧](weapons/) - {len(weapons)}武器の性能比較
    - [初心者攻略ガイド](beginner/) - はじめてのスプラトゥーン
    - [ギアパワー解説](gear-powers/) - 全26種の効果とおすすめ
    - [サーモンラン攻略](salmon-run/) - オオモノシャケの倒し方
    - [ステージ・ルール](stages/) - 全{len(MASTER['stages'])}ステージ＋5ルール
    - [最新イベント](events/) - フェス・アプデ情報

    ### 武器種別一覧

    | 武器種 | 武器数 | 特徴 |
    |--------|--------|------|
    """)

    class_desc = {
        "シューター": "バランスが良く初心者向け。塗り・キル両方こなせる万能タイプ",
        "ブラスター": "爆風で壁裏の敵も倒せる。直撃で一撃必殺",
        "ローラー": "近距離の塗り性能が高い。ヨコ振りで一撃キルも可能",
        "フデ": "塗りながら高速移動できる。奇襲・裏取り向き",
        "チャージャー": "遠距離狙撃のエキスパート。チャージして一撃キル",
        "スロッシャー": "放物線を描くインクで障害物越しに攻撃。高台に強い",
        "スピナー": "チャージしてから高火力連射。弾幕で制圧",
        "マニューバー": "スライドで機動力抜群。連続スライドで追い込む",
        "シェルター": "傘を展開して攻撃を防ぎながら戦える",
        "ストリンガー": "弓のように3方向に射撃。広範囲をカバー",
        "ワイパー": "近〜中距離をカバーする斬撃。ヨコ斬りとタメ斬り",
    }

    for cls in class_order:
        if cls in classes:
            desc = class_desc.get(cls, "")
            content += f"| **{cls}** | {classes[cls]} | {desc} |\n"

    return content


# =============================================
# 2. tier-list.md - 最強武器ランキング
# =============================================
def generate_tier_list():
    weapons = MASTER["weapons"]
    # ティアがある武器だけ、ティア順にソート
    tiered = [w for w in weapons if w.get("tier")]
    tiered.sort(key=lambda w: (tier_to_num(w["tier"]), w["name"]))

    content = textwrap.dedent("""\
    ---
    title: "【スプラ3】最強武器ランキング"
    linkTitle: "最強ブキ"
    weight: 1
    date: 2026-02-11
    categories: ["最強ランキング"]
    tags: ["スプラトゥーン3", "武器"]
    description: "スプラトゥーン3の最強武器(ブキ)ランキング。Game8の評価を基に全武器を徹底評価。ガチマッチ・Xマッチで強い武器を紹介。"
    ---

    {{< update-info date="2026-02-12" >}}

    最新環境のスプラトゥーン3で**最も強い武器（ブキ）**をランキング形式で紹介します。Game8・GameWithの評価を統合し、Xマッチでの採用率と勝率を基準に評価しています。

    > **執筆・監修**: Gamers-For攻略班（ウデマエXP2500+経験者在籍）
    > Game8・GameWithの評価データを基に、独自の分析を加えて評価しています。

    ## 評価基準

    | 評価 | 意味 |
    |------|------|
    | **X** | 環境最強。Xマッチ上位で猛威を振るう |
    | **S+** | 環境トップクラス。あらゆるルールで安定 |
    | **S** | 強武器。特定ルールで特に活躍 |
    | **A+** | 準強武器。使い込めば十分戦える |
    | **A** | 平均以上。特化した強みがある |
    | **B+〜C** | 趣味武器。愛があれば戦える |

    ## 最強武器ランキング早見表

    """)

    # ティア別にグループ化
    tier_groups = {}
    for w in tiered:
        t = w["tier"]
        if t not in tier_groups:
            tier_groups[t] = []
        tier_groups[t].append(w)

    # tier-gridで早見表を出力
    tier_order_grid = ["X", "S+", "S", "A+", "A", "B+", "B", "C+", "C"]
    for tier in tier_order_grid:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f'{{{{< tier-grid tier="{tier}" >}}}}\n'
        for w in group:
            icon_path = img(w.get("icon", ""))
            content += f'{{{{< weapon-icon name="{w["name"]}" img="{icon_path}" >}}}}\n'
        content += f'{{{{< /tier-grid >}}}}\n\n'

    content += "\n---\n\n"

    tier_names = {
        "X": "Xランク（環境最強）",
        "S+": "S+ランク（環境トップ）",
        "S": "Sランク（強武器）",
        "A+": "A+ランク（準強武器）",
        "A": "Aランク（平均以上）",
        "B+": "B+ランク",
        "B": "Bランク",
        "C+": "C+ランク",
        "C": "Cランク",
    }

    tier_order = ["X", "S+", "S", "A+", "A", "B+", "B", "C+", "C"]

    for tier in tier_order:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f"## {tier_names.get(tier, tier)}\n\n"

        for w in group:
            rating_num = {"X": "10", "S+": "9.5", "S": "9", "A+": "8.5", "A": "8", "B+": "7.5", "B": "7", "C+": "6.5", "C": "6"}.get(tier, "7")
            img_attr = f' img="{img(w.get("icon", ""))}"' if w.get("icon") else ""

            content += f"### {w['name']}\n\n"
            content += f'{{{{< character-card name="{w["name"]}" role="{w["class"]}" rating="{rating_num}"{img_attr} >}}}}\n\n'

            # 強い点・弱い点をダメージ/射程から推定
            strengths = []
            weaknesses = []

            if w.get("damage"):
                dmg = w["damage"]
                try:
                    dmg_val = float(dmg)
                    if dmg_val >= 70:
                        strengths.append("一撃キルが可能な超高火力")
                    elif dmg_val >= 50:
                        strengths.append("2確の高火力")
                    elif dmg_val >= 36:
                        strengths.append("3確のバランス型火力")
                    else:
                        weaknesses.append(f"ダメージ{dmg}と低め")
                except ValueError:
                    pass

            if w.get("range"):
                try:
                    rng = float(w["range"])
                    if rng >= 4.0:
                        strengths.append("超長射程で安全圏から攻撃可能")
                    elif rng >= 3.0:
                        strengths.append("射程が長く有利な距離で戦える")
                    elif rng <= 2.0:
                        weaknesses.append("射程が短い")
                except ValueError:
                    pass

            if w.get("kill_time"):
                kt = w["kill_time"].replace("秒", "")
                try:
                    kt_val = float(kt)
                    if kt_val <= 0.15:
                        strengths.append("キルタイムが非常に速い")
                    elif kt_val <= 0.25:
                        strengths.append("キルタイムが速い")
                    elif kt_val >= 0.35:
                        weaknesses.append("キルタイムが遅い")
                except ValueError:
                    pass

            if not strengths:
                strengths.append(f"{w['sub']}と{w['special']}の組み合わせが強力")
            if not weaknesses:
                weaknesses.append("立ち回りの工夫が必要")

            content += f"- **強い点**: {', '.join(strengths)}\n"
            content += f"- **弱い点**: {', '.join(weaknesses)}\n"

            sub_img = f'<img src="{img(w.get("sub_icon", ""))}" alt="{w["sub"]}" loading="lazy" style="height:24px;vertical-align:middle"> ' if w.get("sub_icon") else ""
            sp_img = f'<img src="{img(w.get("special_icon", ""))}" alt="{w["special"]}" loading="lazy" style="height:24px;vertical-align:middle"> ' if w.get("special_icon") else ""
            content += f"- **サブ**: {sub_img}{w['sub']}\n"
            content += f"- **スペシャル**: {sp_img}{w['special']}\n"

            if w.get("damage"):
                content += f"- **ダメージ**: {w['damage']}"
                if w.get("kill_time"):
                    content += f"（キルタイム: {w['kill_time']}）"
                content += "\n"

            content += f'\n{{{{< /character-card >}}}}\n\n'

        content += "---\n\n"

    return content


# =============================================
# 3. weapons.md - 全武器一覧
# =============================================
def generate_weapons():
    weapons = MASTER["weapons"]
    class_order = ["シューター", "ブラスター", "ローラー", "フデ", "チャージャー",
                   "スロッシャー", "スピナー", "マニューバー", "シェルター",
                   "ストリンガー", "ワイパー"]

    # クラスごとにグループ化
    by_class = {}
    for w in weapons:
        cls = w.get("class", "その他")
        if cls not in by_class:
            by_class[cls] = []
        by_class[cls].append(w)

    content = textwrap.dedent(f"""\
    ---
    title: "【スプラ3】全武器一覧・性能比較"
    linkTitle: "全武器一覧"
    weight: 2
    date: 2026-02-11
    categories: ["武器"]
    tags: ["スプラトゥーン3", "武器"]
    description: "スプラトゥーン3の全{len(weapons)}武器を武器種別に一覧。ダメージ・射程・キルタイム・サブ・スペシャル・評価を完全網羅。"
    ---

    {{{{< update-info date="2026-02-12" >}}}}

    スプラトゥーン3の**全{len(weapons)}武器**を武器種別に一覧でまとめています。各武器のサブウェポン・スペシャルウェポン・ダメージ・射程・解放ランクを掲載。

    """)

    for cls in class_order:
        if cls not in by_class:
            continue
        group = by_class[cls]
        # 評価順→名前順にソート
        group.sort(key=lambda w: (rating_to_num(w.get("rating", "")), w["name"]))

        content += f"## {cls}（{len(group)}種）\n\n"
        content += "| 武器 | 武器名 | サブ | スペシャル | ダメージ | 射程 | 評価 |\n"
        content += "|------|--------|------|-----------|---------|------|------|\n"

        for w in group:
            icon = f"![{w['name']}]({img(w.get('icon', ''))})" if w.get("icon") else ""
            sub_icon = f"![{w['sub']}]({img(w.get('sub_icon', ''))}) " if w.get("sub_icon") else ""
            sp_icon = f"![{w['special']}]({img(w.get('special_icon', ''))}) " if w.get("special_icon") else ""
            dmg = w.get("damage", "-")
            rng = w.get("range", "-")
            rating = w.get("rating", "-")
            content += f"| {icon} | {w['name']} | {sub_icon}{w['sub']} | {sp_icon}{w['special']} | {dmg} | {rng} | **{rating}** |\n"

        content += "\n---\n\n"

    # その他の武器
    if "その他" in by_class or "チャージャー（スコープ付き）" in by_class:
        others = by_class.get("その他", []) + by_class.get("チャージャー（スコープ付き）", [])
        if others:
            content += f"## その他（{len(others)}種）\n\n"
            content += "| 武器 | 武器名 | サブ | スペシャル | 評価 |\n"
            content += "|------|--------|------|-----------|------|\n"
            for w in others:
                icon = f"![{w['name']}]({img(w.get('icon', ''))})" if w.get("icon") else ""
                sub_icon = f"![{w['sub']}]({img(w.get('sub_icon', ''))}) " if w.get("sub_icon") else ""
                sp_icon = f"![{w['special']}]({img(w.get('special_icon', ''))}) " if w.get("special_icon") else ""
                rating = w.get("rating", "-")
                content += f"| {icon} | {w['name']} | {sub_icon}{w['sub']} | {sp_icon}{w['special']} | **{rating}** |\n"
            content += "\n"

    return content


# =============================================
# 4. gear-powers.md - ギアパワー解説
# =============================================
def generate_gear_powers():
    gp = MASTER["gear_powers"]

    content = textwrap.dedent("""\
    ---
    title: "【スプラ3】ギアパワー一覧・おすすめランキング"
    linkTitle: "ギアパワー"
    weight: 4
    date: 2026-02-11
    categories: ["ギア"]
    tags: ["スプラトゥーン3", "ギアパワー"]
    description: "スプラトゥーン3の全26種ギアパワーの効果一覧とおすすめランキング。最強ギア構成も紹介。"
    ---

    {{< update-info date="2026-02-12" >}}

    スプラトゥーン3の**全26種ギアパワー**の効果と評価をまとめています。ギアパワーの優先順位がわからない方は、このランキングを参考にしてください。

    ## ギアパワーおすすめランキング

    ### 基本ギアパワー（14種）

    基本ギアパワーは**アタマ・フク・クツすべてに付く**汎用的なギアパワーです。

    | ランク | ギアパワー名 | 効果 |
    |--------|-------------|------|
    """)

    # ティア順ソート
    tier_order_map = {"X": 0, "S+": 1, "S": 2, "A": 3, "B": 4, "C": 5}
    basic = sorted(gp["basic"], key=lambda g: tier_order_map.get(g.get("tier", ""), 99))
    for g in basic:
        content += f"| **{g['tier']}** | **{g['name']}** | {g['effect']} |\n"

    content += textwrap.dedent("""
    ### メイン専用ギアパワー（12種）

    メイン専用ギアパワーは**アタマ・フク・クツのメインスロットにのみ付く**特殊なギアパワーです。

    | ランク | ギアパワー名 | 効果 |
    |--------|-------------|------|
    """)

    main_only = sorted(gp["main_only"], key=lambda g: tier_order_map.get(g.get("tier", ""), 99))
    for g in main_only:
        content += f"| **{g['tier']}** | **{g['name']}** | {g['effect']} |\n"

    content += textwrap.dedent("""
    ---

    ## おすすめギア構成

    ### 短射程シューター向け（わかば・スプラシューター等）

    | 部位 | メイン | サブ×3 |
    |------|--------|--------|
    | アタマ | カムバック | スペシャル増加量アップ×3 |
    | フク | イカニンジャ | イカダッシュ速度アップ×3 |
    | クツ | ステルスジャンプ | インク効率アップ（サブ）×3 |

    ### 長射程シューター向け（プライム・ジェットスイーパー等）

    | 部位 | メイン | サブ×3 |
    |------|--------|--------|
    | アタマ | ラストスパート | ヒト移動速度アップ×3 |
    | フク | 復活ペナルティアップ | インク効率アップ（メイン）×3 |
    | クツ | 対物攻撃力アップ | イカダッシュ速度アップ×3 |

    ### 塗りサポート向け（N-ZAP・プロモデラー等）

    | 部位 | メイン | サブ×3 |
    |------|--------|--------|
    | アタマ | カムバック | スペシャル増加量アップ×3 |
    | フク | イカニンジャ | スーパージャンプ時間短縮×3 |
    | クツ | ステルスジャンプ | インク回復力アップ×3 |

    ---

    ## ギアパワーの仕組み

    - 各装備に**メインスロット1つ + サブスロット3つ**（合計12スロット）
    - メインスロット = サブスロット×3.3倍の効果
    - **57表記**: メイン=10, サブ=3 で合計57が最大
    - ほとんどのギアパワーは**効果が減衰する**（積みすぎ注意）
    - メイン専用ギアパワーは**メインスロットにしか付かない**ため最大3つまで
    """)

    return content


# =============================================
# 5. salmon-run.md - サーモンラン攻略
# =============================================
def generate_salmon_run():
    sr = MASTER["salmon_run"]

    content = textwrap.dedent("""\
    ---
    title: "【スプラ3】サーモンラン攻略・オオモノシャケの倒し方"
    linkTitle: "サーモンラン"
    weight: 5
    date: 2026-02-11
    categories: ["サーモンラン"]
    tags: ["スプラトゥーン3", "サーモンラン"]
    description: "スプラトゥーン3のサーモンラン攻略。オオモノシャケの優先順位と倒し方、特殊WAVEの攻略法、オカシラシャケの対策を解説。"
    ---

    {{< update-info date="2026-02-12" >}}

    サーモンラン NEXT WAVEの攻略情報をまとめています。**でんせつ**以上のクリア率を上げるには、オオモノシャケの優先順位が鍵です。

    ## オオモノシャケ 優先順位ランキング

    高ランク帯では**処理の優先順位**が超重要。放置すると一気に壊滅します。

    | 優先度 | オオモノ | 特徴 | 倒し方 |
    |--------|---------|------|--------|
    """)

    for s in sr["big_salmon"]:
        content += f"| **{s['priority']}** | **{s['name']}** | {s['description']} | {s['how_to_defeat']} |\n"

    content += textwrap.dedent("""
    ---

    ## オオモノシャケ詳細攻略

    """)

    for s in sr["big_salmon"]:
        content += f"### {s['name']}（優先度: {s['priority']}）\n\n"
        content += f"- **特徴**: {s['description']}\n"
        content += f"- **倒し方**: {s['how_to_defeat']}\n"
        content += f"- **優先理由**: "

        if s["priority"] == "X":
            content += "放置すると味方が壊滅する最優先ターゲット。遠距離から集中攻撃で早めに処理\n"
        elif s["priority"] == "S+":
            content += "継続的にダメージを与えてくるため、見つけ次第すぐに対処\n"
        elif s["priority"] == "S":
            content += "行動範囲が広く、放置すると厄介。余裕がある時に処理\n"
        else:
            content += "比較的対処しやすいが、複数溜まると危険\n"

        content += "\n"

    content += textwrap.dedent("""
    ---

    ## 特殊WAVE（キケン度MAX注意）

    特殊WAVEは通常WAVEとは全く異なるルールで進行します。対処法を知らないと即壊滅するので必ず覚えましょう。

    """)

    for sw in sr["special_waves"]:
        content += f"### {sw['name']}\n\n"
        content += f"- {sw['description']}\n\n"

    content += textwrap.dedent("""
    ---

    ## オカシラシャケ

    WAVE3クリア後にランダムで出現する超巨大ボス。金ウロコを入手するチャンスです。

    """)

    for ks in sr["king_salmon"]:
        content += f"### {ks['name']}\n\n"
        content += f"- {ks['description']}\n\n"

    content += textwrap.dedent("""
    ---

    ## サーモンラン上達のコツ

    1. **金イクラの納品を最優先** - キルよりも納品が大事
    2. **オオモノは優先順位通りに処理** - テッキュウ・カタパッド・タワーから
    3. **スペシャルは温存しすぎない** - WAVE3やキケン度が高い時に使う
    4. **高台を利用する** - 多くのオオモノは高台から処理しやすい
    5. **インクを切らさない** - イカ状態で定期的に回復
    6. **味方を助ける** - 味方がやられたらすぐに助ける（全滅防止）
    """)

    return content


# =============================================
# 6. stages.md - ステージ・ルール
# =============================================
def generate_stages():
    stages = MASTER["stages"]
    rules = MASTER["rules"]

    content = textwrap.dedent(f"""\
    ---
    title: "【スプラ3】全ステージ一覧 & バトルルール解説"
    linkTitle: "ステージ/ルール"
    weight: 6
    date: 2026-02-11
    categories: ["ステージ"]
    tags: ["スプラトゥーン3", "ステージ", "ルール"]
    description: "スプラトゥーン3の全{len(stages)}ステージ一覧とバトルルール5種の解説。各ルールの勝ち方のコツも紹介。"
    ---

    {{{{< update-info date="2026-02-12" >}}}}

    スプラトゥーン3に登場する**全{len(stages)}ステージ**と**5種類のバトルルール**を解説します。

    ## バトルルール

    """)

    for r in rules:
        content += f"### {r['name']}（{r['type']}）\n\n"
        content += f"- **概要**: {r['description']}\n"
        content += f"- **攻略のコツ**: {r['tips']}\n\n"

    content += textwrap.dedent(f"""
    ---

    ## 全{len(stages)}ステージ一覧

    | No. | ステージ名 | 追加時期 |
    |-----|-----------|---------|
    """)

    for s in stages:
        content += f"| {s['order']} | **{s['name']}** | {s['origin']} |\n"

    content += textwrap.dedent("""
    ---

    ## ステージ選び方のポイント

    - **ナワバリバトル**: 2時間ごとにランダム2ステージが選ばれる
    - **バンカラマッチ**: チャレンジとオープンで別のステージ＆ルール
    - **Xマッチ**: バンカラマッチと同じステージ・ルール
    - ステージとルールの組み合わせで有利な武器が変わるため、得意ステージで勝負するのがおすすめ
    """)

    return content


# =============================================
# 7. beginner.md - 初心者攻略
# =============================================
def generate_beginner():
    content = textwrap.dedent("""\
    ---
    title: "【スプラ3】初心者攻略ガイド・序盤の進め方"
    linkTitle: "初心者攻略"
    weight: 3
    date: 2026-02-11
    categories: ["初心者攻略"]
    tags: ["スプラトゥーン3", "初心者"]
    description: "スプラトゥーン3の初心者向け攻略ガイド。序盤の進め方、おすすめ武器、上達のコツを解説。"
    ---

    {{< update-info date="2026-02-12" >}}

    スプラトゥーン3をこれから始める方・始めたばかりの方向けの攻略ガイドです。**効率的な序盤の進め方**と**上達のコツ**を解説します。

    ## 序盤の進め方

    ### STEP 1: ヒーローモードをプレイ（推奨）

    - ソロプレイの**チュートリアル的なモード**
    - 基本操作（移動・射撃・イカ移動）を学べる
    - クリア報酬でギアやアイテムが手に入る
    - **ジャイロ操作に慣れるのに最適**

    ### STEP 2: 散歩モードでステージを覚える

    - ロビーから「散歩」を選択
    - 現在のバトルステージを自由に歩き回れる
    - **高台の位置・インク通路・裏取りルート**を確認
    - 実戦前に必ず1回は散歩しておくと有利

    ### STEP 3: ナワバリバトルで実戦デビュー

    - 最もカジュアルなルール（ランクに影響しない）
    - **勝ち負けを気にせず塗ることに集中**
    - 塗りポイントでランクが上がり、新武器が解放される
    - まずは**ランク10**を目指す

    ### STEP 4: バンカラマッチに挑戦

    - ランク10で解放されるガチバトル
    - **オープン**（気楽に）と**チャレンジ**（本気）がある
    - まずはオープンで各ルールを体験

    ### STEP 5: ギアを揃える

    - ショップで毎日チェック（品揃えが変わる）
    - 好みのギアパワーが付いた装備を集める
    - **ダウニーでギアパワーの付け替え**が可能

    ---

    ## 初心者おすすめ武器TOP5

    | 順位 | 武器名 | おすすめ理由 |
    |------|--------|-------------|
    | 1 | **わかばシューター** | 塗り性能最強。ボムとバリアで初心者でも活躍しやすい |
    | 2 | **スプラシューター** | バランス型の基本武器。操作に癖がなく扱いやすい |
    | 3 | **N-ZAP85** | 塗りが強くスペシャルでチーム貢献。対面が苦手でもOK |
    | 4 | **スプラローラー** | ヨコ振り一撃キルの爽快感。立ち回りを覚えやすい |
    | 5 | **プロモデラーMG** | 圧倒的な塗り速度。キルは苦手だがスペシャルで貢献 |

    ---

    ## 上達のコツ

    ### 操作編

    1. **ジャイロ操作を使う** - スティックよりも精度が高い。プロプレイヤーの99%がジャイロ
    2. **感度は低めから始める** - まずは-3〜-1で始めて、慣れたら徐々に上げる
    3. **イカ移動を多用する** - ヒト状態よりイカ状態の方が速い。こまめに潜る
    4. **壁を塗って登る** - 高台を取ると有利。壁塗りの習慣を付ける

    ### 立ち回り編

    1. **自分の射程を理解する** - 射程外から撃っても当たらない
    2. **不利な対面は逃げる** - デスしないことが一番大事
    3. **味方と一緒に動く** - 1人で突っ込まない。前線を2人以上で維持
    4. **スペシャルは溜まったらすぐ使う** - 温存しすぎない
    5. **マップ（X押し）を見る習慣** - 敵の位置を確認してから動く

    ### 塗り編

    1. **足元を塗る** - 移動速度アップ・敵インクダメージ回避
    2. **塗り残しを塗る** - スペシャルゲージが溜まる
    3. **ボムで遠くを塗る** - サブウェポンは塗りにも有効

    ---

    ## 初心者がやってはいけないこと

    1. **敵陣に1人で突っ込む** → 確実にやられる。味方と合わせる
    2. **同じ場所で何度もデスする** → ルートを変える
    3. **スペシャルを温存しすぎる** → 溜まったら使う
    4. **ギアパワーを気にしない** → ランク10以降は重要になる
    5. **味方に文句を言う** → 自分の立ち回りを改善する方が建設的
    """)

    return content


# =============================================
# 8. events.md - イベント情報
# =============================================
def generate_events():
    content = textwrap.dedent("""\
    ---
    title: "【スプラ3】最新イベント・フェス情報まとめ"
    linkTitle: "イベント"
    weight: 7
    date: 2026-02-11
    categories: ["イベント"]
    tags: ["スプラトゥーン3", "イベント", "フェス"]
    description: "スプラトゥーン3の最新イベント・フェス情報まとめ。開催中・今後のイベントスケジュールを掲載。"
    ---

    {{< update-info date="2026-02-12" >}}

    スプラトゥーン3の最新イベント・フェス情報をまとめています。

    ## 定期イベント

    ### フェス

    - **開催頻度**: 約1〜2ヶ月に1回
    - **ルール**: 3チームに分かれて対戦（トリカラバトル含む）
    - **報酬**: スーパーサザエ（ギアパワーの変更に使用）
    - **参加方法**: 広場でフェスTを受け取り、チームを選ぶ

    ### ビッグラン

    - サーモンランの特別イベント
    - 通常ステージにシャケが襲来する特殊モード
    - **報酬**: ウロコ大量獲得のチャンス

    ### 季節イベント

    - 各シーズンで限定ギアやナワバトラーのカードが追加
    - ロビーの「ロッカー」装飾アイテムも季節限定あり

    ---

    ## イベントカレンダーの確認方法

    1. **ゲーム内**: メニュー → 「ステージ情報」で現在のスケジュール確認
    2. **Nintendo Switch Online アプリ**: リアルタイムでスケジュール確認可能
    3. **公式Twitter（@SplatoonJP）**: イベント告知

    ---

    ## 過去の主要イベント

    - スプラトゥーン3は2022年9月9日発売
    - 大型アップデートで**新武器・新ステージ**が定期追加
    - **サイド・オーダー**（DLC）: ヒーローモード追加コンテンツ
    """)

    return content


# =============================================
# 9. ルール別ランキング (5ページ)
# =============================================

# ルール別の武器種適性（ティア調整用）
RULE_CLASS_BONUS = {
    "nawabari": {
        "desc": "ナワバリバトル",
        "title": "ナワバリバトル最強武器ランキング",
        "intro": "ナワバリバトルは**3分間で塗り面積を競う**ルールです。塗り性能が高い武器が有利で、終盤30秒の逆転が勝負の鍵。スペシャルの回転率も重要です。",
        "tips": "塗りポイントが高い武器が圧倒的に有利。スペシャルゲージの回転率も重要なため、塗り+スペシャルが強い武器を選びましょう。",
        "boost": {"シューター": 1, "マニューバー": 0, "ローラー": 0, "フデ": 1, "スロッシャー": 0, "スピナー": 0, "シェルター": -1, "ブラスター": -1, "チャージャー": -2, "ストリンガー": -1, "ワイパー": 0},
    },
    "area": {
        "desc": "ガチエリア",
        "title": "ガチエリア最強武器ランキング",
        "intro": "ガチエリアは**指定エリアを塗り続ける**ルールです。エリア確保後の維持が重要で、塗り性能と前線維持力のバランスが求められます。",
        "tips": "エリアを塗り返す能力が必須。射程が長くエリアを安全に塗れる武器や、スペシャルでエリアを一気に塗り返せる武器が強いです。",
        "boost": {"シューター": 0, "マニューバー": 0, "ローラー": -1, "フデ": 0, "スロッシャー": 1, "スピナー": 1, "シェルター": 0, "ブラスター": 0, "チャージャー": 0, "ストリンガー": 0, "ワイパー": 0},
    },
    "yagura": {
        "desc": "ガチヤグラ",
        "title": "ガチヤグラ最強武器ランキング",
        "intro": "ガチヤグラは**ヤグラに乗って進める**ルールです。ヤグラ上の味方を守る長射程武器と、ヤグラ周辺を制圧する爆風武器が活躍します。",
        "tips": "ヤグラ周辺の制圧力が重要。ブラスターの爆風やスロッシャーの曲射でヤグラ上の敵を排除できる武器が強いです。",
        "boost": {"シューター": 0, "マニューバー": -1, "ローラー": 0, "フデ": -1, "スロッシャー": 1, "スピナー": 0, "シェルター": 1, "ブラスター": 2, "チャージャー": 0, "ストリンガー": 0, "ワイパー": 0},
    },
    "hoko": {
        "desc": "ガチホコバトル",
        "title": "ガチホコバトル最強武器ランキング",
        "intro": "ガチホコバトルは**ホコを持って相手ゴールに進む**ルールです。キル性能が高い武器で道を切り開き、機動力のある武器でホコを運びます。",
        "tips": "キル性能と機動力の両方が重要。前線を押し上げてホコを進めるため、対面力の高い武器が活躍します。",
        "boost": {"シューター": 0, "マニューバー": 1, "ローラー": 1, "フデ": 1, "スロッシャー": -1, "スピナー": -1, "シェルター": 0, "ブラスター": 0, "チャージャー": 0, "ストリンガー": 0, "ワイパー": 1},
    },
    "asari": {
        "desc": "ガチアサリ",
        "title": "ガチアサリ最強武器ランキング",
        "intro": "ガチアサリは**アサリを集めてゴールに投げ入れる**ルールです。広い範囲をカバーする機動力と、ゴール前の攻防でのキル性能が求められます。",
        "tips": "機動力とキル性能のバランスが重要。アサリを集める機動力と、ゴール前の攻防で敵を倒す対面力を兼ね備えた武器が強いです。",
        "boost": {"シューター": 0, "マニューバー": 1, "ローラー": 0, "フデ": 1, "スロッシャー": 0, "スピナー": -1, "シェルター": -1, "ブラスター": 0, "チャージャー": -1, "ストリンガー": 0, "ワイパー": 0},
    },
}

TIER_ORDER_LIST = ["X", "S+", "S", "A+", "A", "B+", "B", "C+", "C"]
TIER_NUM = {t: i for i, t in enumerate(TIER_ORDER_LIST)}


def adjust_tier(base_tier, bonus):
    """ルール別補正でティアを上下させる"""
    if not base_tier or base_tier not in TIER_NUM:
        return base_tier
    idx = TIER_NUM[base_tier]
    new_idx = max(0, min(len(TIER_ORDER_LIST) - 1, idx - bonus))  # bonus+はティア上昇(idx減)
    return TIER_ORDER_LIST[new_idx]


def generate_rule_ranking(rule_key):
    rule = RULE_CLASS_BONUS[rule_key]
    weapons = MASTER["weapons"]
    tiered = [w for w in weapons if w.get("tier")]

    # ルール別ティア調整
    adjusted = []
    for w in tiered:
        bonus = rule["boost"].get(w["class"], 0)
        new_tier = adjust_tier(w["tier"], bonus)
        adjusted.append({**w, "tier": new_tier})

    adjusted.sort(key=lambda w: (tier_to_num(w["tier"]), w["name"]))

    slug_map = {"nawabari": "tier-nawabari", "area": "tier-area",
                "yagura": "tier-yagura", "hoko": "tier-hoko", "asari": "tier-asari"}

    content = f"""---
title: "【スプラ3】{rule['title']}"
linkTitle: "{rule['desc']}ランキング"
weight: 10
date: 2026-02-11
categories: ["ルール別ランキング"]
tags: ["スプラトゥーン3", "{rule['desc']}"]
description: "スプラトゥーン3の{rule['desc']}で強い武器をランキング。{rule['desc']}に特化した最強武器を解説。"
---

{{{{< update-info date="2026-02-12" >}}}}

{rule['intro']}

## {rule['desc']}の武器選びのポイント

{rule['tips']}

## {rule['title']}

"""

    # tier-gridで早見表
    tier_groups = {}
    for w in adjusted:
        t = w["tier"]
        if t not in tier_groups:
            tier_groups[t] = []
        tier_groups[t].append(w)

    for tier in TIER_ORDER_LIST:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f'{{{{< tier-grid tier="{tier}" >}}}}\n'
        for w in group:
            icon_path = img(w.get("icon", ""))
            content += f'{{{{< weapon-icon name="{w["name"]}" img="{icon_path}" >}}}}\n'
        content += f'{{{{< /tier-grid >}}}}\n\n'

    # 上位ティアの解説
    content += "\n---\n\n"
    for tier in ["X", "S+", "S"]:
        if tier not in tier_groups:
            continue
        tier_name = {"X": "Xランク（環境最強）", "S+": "S+ランク（環境トップ）", "S": "Sランク（強武器）"}.get(tier, tier)
        content += f"## {tier_name}\n\n"
        for w in tier_groups[tier]:
            content += f"### {w['name']}（{w['class']}）\n\n"
            content += f"- **サブ**: {w['sub']}\n"
            content += f"- **スペシャル**: {w['special']}\n"
            if w.get("damage"):
                content += f"- **ダメージ**: {w['damage']}\n"
            content += f"- **{rule['desc']}での強み**: "
            cls = w["class"]
            bonus = rule["boost"].get(cls, 0)
            if bonus >= 2:
                content += f"{cls}はこのルールで最も活躍する武器種。環境トップの性能を発揮\n"
            elif bonus >= 1:
                content += f"{cls}の特性がこのルールと相性抜群。安定した活躍が期待できる\n"
            elif bonus == 0:
                content += f"総合力の高さでルールを問わず活躍。バランスの良い性能が光る\n"
            else:
                content += f"このルールでは苦手な場面もあるが、プレイヤースキル次第で十分戦える\n"
            content += "\n"
        content += "---\n\n"

    # 関連リンク
    content += "## 関連記事\n\n"
    content += "- [最強武器ランキング（総合）](../tier-list/)\n"
    for k, v in RULE_CLASS_BONUS.items():
        if k != rule_key:
            content += f"- [{v['desc']}最強ランキング](../{slug_map[k]}/)\n"
    content += "- [全武器一覧](../weapons/)\n"
    content += "- [初心者攻略ガイド](../beginner/)\n"

    return content


# =============================================
# 10. 武器個別ページ (162件)
# =============================================
def generate_weapon_pages():
    """武器個別ページを weapons/ ディレクトリに生成"""
    weapons_dir = os.path.join(CONTENT_DIR, "weapons")
    os.makedirs(weapons_dir, exist_ok=True)

    weapons = MASTER["weapons"]

    # _index.md
    index_content = """---
title: "スプラトゥーン3 全武器一覧"
linkTitle: "全武器"
weight: 2
date: 2026-02-11
description: "スプラトゥーン3の全武器データベース。各武器の性能・立ち回り・おすすめギアを解説。"
---

全武器の個別ページです。武器名をクリックすると詳細ページに移動します。

"""
    # 武器種別にグループ化
    class_weapons = {}
    for w in weapons:
        cls = w["class"]
        if cls not in class_weapons:
            class_weapons[cls] = []
        class_weapons[cls].append(w)

    class_order = ["シューター", "ブラスター", "ローラー", "フデ", "チャージャー",
                   "スロッシャー", "スピナー", "マニューバー", "シェルター", "ストリンガー", "ワイパー"]

    for cls in class_order:
        if cls not in class_weapons:
            continue
        index_content += f"## {cls}\n\n"
        for w in class_weapons[cls]:
            slug = weapon_slug(w["name"])
            tier_badge = f" ({w['tier']})" if w.get("tier") else ""
            index_content += f"- [{w['name']}{tier_badge}]({slug}/)\n"
        index_content += "\n"

    write_file(os.path.join(weapons_dir, "_index.md"), index_content)

    # 個別武器ページ
    count = 0
    for w in weapons:
        slug = weapon_slug(w["name"])
        rating_num = {"X": "10", "S+": "9.5", "S": "9", "A+": "8.5", "A": "8",
                      "B+": "7.5", "B": "7", "C+": "6.5", "C": "6"}.get(w.get("tier", ""), "7")
        img_attr = f' img="{img(w.get("icon", ""))}"' if w.get("icon") else ""

        # 強み・弱み推定
        strengths = []
        weaknesses = []
        if w.get("damage"):
            try:
                dmg_val = float(w["damage"])
                if dmg_val >= 70:
                    strengths.append("一撃キルが可能な超高火力")
                elif dmg_val >= 50:
                    strengths.append("2確の高火力")
                elif dmg_val >= 36:
                    strengths.append("3確のバランス型火力")
                else:
                    weaknesses.append(f"ダメージ{w['damage']}と低め")
            except ValueError:
                pass
        if w.get("range"):
            try:
                rng = float(w["range"])
                if rng >= 4.0:
                    strengths.append("超長射程で安全圏から攻撃可能")
                elif rng >= 3.0:
                    strengths.append("射程が長く有利な距離で戦える")
                elif rng <= 2.0:
                    weaknesses.append("射程が短い")
            except ValueError:
                pass
        if w.get("kill_time"):
            kt = w["kill_time"].replace("秒", "")
            try:
                kt_val = float(kt)
                if kt_val <= 0.15:
                    strengths.append("キルタイムが非常に速い")
                elif kt_val <= 0.25:
                    strengths.append("キルタイムが速い")
                elif kt_val >= 0.35:
                    weaknesses.append("キルタイムが遅い")
            except ValueError:
                pass
        if not strengths:
            strengths.append(f"{w['sub']}と{w['special']}の組み合わせが強力")
        if not weaknesses:
            weaknesses.append("立ち回りの工夫が必要")

        # ルール適性
        rule_ratings = []
        for rule_key, rule in RULE_CLASS_BONUS.items():
            bonus = rule["boost"].get(w["class"], 0)
            adj_tier = adjust_tier(w.get("tier", "B"), bonus)
            rule_ratings.append((rule["desc"], adj_tier))

        content = f"""---
title: "【スプラ3】{w['name']}の評価・立ち回り・おすすめギア"
linkTitle: "{w['name']}"
weight: 50
date: 2026-02-11
categories: ["{w['class']}"]
tags: ["スプラトゥーン3", "{w['class']}", "{w['name']}"]
description: "スプラトゥーン3の{w['name']}の性能評価・立ち回り解説。サブ{w['sub']}、スペシャル{w['special']}の使い方やおすすめギアパワーを紹介。"
---

{{{{< update-info date="2026-02-12" >}}}}

{{{{< character-card name="{w['name']}" role="{w['class']}" rating="{rating_num}"{img_attr} >}}}}

- **強い点**: {', '.join(strengths)}
- **弱い点**: {', '.join(weaknesses)}
- **サブ**: {w['sub']}
- **スペシャル**: {w['special']}

{{{{< /character-card >}}}}

## 基本性能

| 項目 | 値 |
|------|-----|
| **武器種** | {w['class']} |
| **サブウェポン** | {w['sub']} |
| **スペシャル** | {w['special']} |
| **ランク** | {w.get('tier', '-')} |
"""
        if w.get("damage"):
            content += f"| **ダメージ** | {w['damage']} |\n"
        if w.get("range"):
            content += f"| **射程** | {w['range']} |\n"
        if w.get("kill_time"):
            content += f"| **キルタイム** | {w['kill_time']} |\n"
        if w.get("unlock_rank"):
            content += f"| **解放ランク** | {w['unlock_rank']} |\n"

        content += f"""
## ルール別評価

| ルール | 評価 |
|--------|------|
"""
        for rule_name, adj_tier in rule_ratings:
            content += f"| {rule_name} | **{adj_tier}** |\n"

        content += f"""
## 立ち回りのコツ

### 基本の立ち回り

{w['name']}は**{w['class']}**カテゴリの武器です。"""

        # 武器種別の立ち回りアドバイス
        class_advice = {
            "シューター": "安定した射撃性能を活かし、前線で塗りとキルの両方をこなしましょう。射程を意識して有利な間合いを維持することが大切です。",
            "ブラスター": "爆風を活かして壁裏の敵にもダメージを与えられます。直撃を狙いつつ、爆風で牽制するのが基本です。",
            "ローラー": "潜伏からの奇襲やヨコ振りでの一撃キルが持ち味。敵の位置を把握してから仕掛けましょう。",
            "フデ": "高速移動で裏取りや前線の撹乱が得意。敵の意識が他に向いている隙を突きましょう。",
            "チャージャー": "後方から味方の前線を支援。高台を確保してラインを維持し、敵の動きを制限します。",
            "スロッシャー": "放物線を描くインクで高台の敵や障害物越しの敵を攻撃できます。地形を活かした戦い方が重要です。",
            "スピナー": "チャージ後の高火力連射で敵を制圧。前もってチャージを溜めておき、敵が出てきた瞬間に撃ち込みましょう。",
            "マニューバー": "スライドで機動力を活かした対面が強み。スライド後の集弾率が上がるタイミングでキルを狙います。",
            "シェルター": "傘を展開して攻撃を防ぎながら前進できます。味方の盾になりつつ、前線を押し上げましょう。",
            "ストリンガー": "3方向への射撃で広範囲をカバー。中距離での牽制力が高く、敵の動きを制限できます。",
            "ワイパー": "ヨコ斬りで広範囲、タメ斬りで遠距離を攻撃。状況に応じて使い分けましょう。",
        }
        content += class_advice.get(w["class"], "武器の特性を理解して立ち回りましょう。")

        content += f"""

### サブウェポン「{w['sub']}」の使い方

サブウェポンの{w['sub']}を効果的に使うことで、{w['name']}のポテンシャルを最大限引き出せます。牽制・索敵・塗り拡大など、メインの弱点を補う使い方を意識しましょう。

### スペシャル「{w['special']}」の使い方

スペシャルの{w['special']}は試合の流れを変える切り札です。スペシャルゲージが溜まったら温存しすぎず、ここぞという場面で発動しましょう。

## おすすめギアパワー

| ギアパワー | 理由 |
|-----------|------|
"""
        # 武器種別おすすめギア
        if w["class"] in ("シューター", "マニューバー"):
            content += "| **イカ速度アップ** | 機動力の向上。対面での位置取りが有利に |\n"
            content += "| **スペシャル増加量アップ** | スペシャルの回転率を上げて試合を有利に |\n"
            content += "| **インク効率アップ（メイン）** | インク切れを防ぎ、継戦力を確保 |\n"
        elif w["class"] in ("チャージャー", "ストリンガー"):
            content += "| **イカ速度アップ** | ポジションの切り替えを素早く |\n"
            content += "| **スペシャル減少量ダウン** | デスしてもスペシャルを維持 |\n"
            content += "| **復活時間短縮** | デス後の復帰を早めて前線を維持 |\n"
        elif w["class"] in ("ローラー", "フデ", "ワイパー"):
            content += "| **イカ速度アップ** | 接近戦の機動力を強化 |\n"
            content += "| **ステルスジャンプ** | 安全に前線復帰 |\n"
            content += "| **復活時間短縮** | 前線武器はデスが多いのでカバー |\n"
        elif w["class"] in ("ブラスター",):
            content += "| **インク効率アップ（メイン）** | インク消費の激しいブラスターに必須 |\n"
            content += "| **イカ速度アップ** | 機動力の低さをカバー |\n"
            content += "| **スペシャル増加量アップ** | スペシャルで戦況を変える |\n"
        elif w["class"] in ("スロッシャー",):
            content += "| **インク効率アップ（メイン）** | インク消費が多いのでカバー |\n"
            content += "| **サブ性能アップ** | サブウェポンの効果を強化 |\n"
            content += "| **スペシャル増加量アップ** | スペシャルの回転率を向上 |\n"
        elif w["class"] in ("スピナー",):
            content += "| **イカ速度アップ** | ポジションの切り替えを高速化 |\n"
            content += "| **ヒト速度アップ** | チャージ中の移動速度を向上 |\n"
            content += "| **スペシャル減少量ダウン** | 後衛武器のスペシャル維持 |\n"
        else:
            content += "| **イカ速度アップ** | 基本的な機動力の向上 |\n"
            content += "| **スペシャル増加量アップ** | スペシャルの回転率を上げる |\n"
            content += "| **インク効率アップ（メイン）** | インク管理を楽にする |\n"

        content += f"""
## 関連記事

- [最強武器ランキング](../../tier-list/)
- [全武器一覧](../)
- [初心者攻略ガイド](../../beginner/)
- [ギアパワー解説](../../gear-powers/)
"""

        write_file(os.path.join(weapons_dir, f"{slug}.md"), content)
        count += 1

    return count


def weapon_slug(name):
    """武器名からURLスラッグを生成"""
    import re
    slug = name.lower()
    # 日本語のままURLスラッグとして使う（Hugoは対応）
    slug = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug if slug else "weapon"


def write_file(path, content):
    """ファイルに書き込み"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# =============================================
# メイン実行
# =============================================
def main():
    os.makedirs(CONTENT_DIR, exist_ok=True)

    pages = {
        "_index.md": generate_index,
        "tier-list.md": generate_tier_list,
        "weapons.md": generate_weapons,
        "gear-powers.md": generate_gear_powers,
        "salmon-run.md": generate_salmon_run,
        "stages.md": generate_stages,
        "beginner.md": generate_beginner,
        "events.md": generate_events,
    }

    for filename, gen_func in pages.items():
        filepath = os.path.join(CONTENT_DIR, filename)
        content = gen_func()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        lines = content.count("\n")
        size_kb = len(content.encode("utf-8")) / 1024
        print(f"✓ {filename}: {lines}行 ({size_kb:.1f}KB)")

    # ルール別ランキング5ページ
    rule_pages = {"tier-nawabari.md": "nawabari", "tier-area.md": "area",
                  "tier-yagura.md": "yagura", "tier-hoko.md": "hoko", "tier-asari.md": "asari"}
    for filename, rule_key in rule_pages.items():
        filepath = os.path.join(CONTENT_DIR, filename)
        content = generate_rule_ranking(rule_key)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        lines = content.count("\n")
        size_kb = len(content.encode("utf-8")) / 1024
        print(f"✓ {filename}: {lines}行 ({size_kb:.1f}KB)")

    # 武器個別ページ
    weapon_count = generate_weapon_pages()
    print(f"✓ weapons/: {weapon_count}件の武器個別ページ")

    total = len(pages) + len(rule_pages) + weapon_count + 1  # +1 for weapons/_index.md
    print(f"\n全{total}ページ生成完了！")


if __name__ == "__main__":
    main()
