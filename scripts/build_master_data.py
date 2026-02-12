#!/usr/bin/env python3
"""
raw_data/ のスクレイピングデータを読み込み、
data/ に構造化JSONを出力するスクリプト
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def parse_md_table(text, headers=None):
    """Markdownテーブルをパースしてリストのリストに変換"""
    rows = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", line):
            continue  # separator row
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if headers and cells == headers:
            continue  # header row
        rows.append(cells)
    return rows


def build_weapons():
    """Game8の武器データからマスターJSONを構築"""
    # Game8のraw_dataを読み込み
    with open(os.path.join(RAW_DIR, "game8_weapons.md"), "r", encoding="utf-8") as f:
        game8_text = f.read()

    # additional_dataからステータスを読み込み
    with open(os.path.join(RAW_DIR, "additional_data.md"), "r", encoding="utf-8") as f:
        additional_text = f.read()

    # 既存のInkipediaアイコンデータ
    icon_data_path = os.path.join(DATA_DIR, "splatoon3_weapons.json")
    if os.path.exists(icon_data_path):
        with open(icon_data_path, "r", encoding="utf-8") as f:
            icon_data = json.load(f)
    else:
        icon_data = {"weapons": [], "subs": [], "specials": []}

    # アイコンの日本語名→パスマッピング
    weapon_icon_map = {w["ja"]: w.get("icon", "") for w in icon_data.get("weapons", [])}
    sub_icon_map = {s["ja"]: s.get("icon", "") for s in icon_data.get("subs", [])}
    sp_icon_map = {s["ja"]: s.get("icon", "") for s in icon_data.get("specials", [])}

    # ステータスデータのパース
    stats_map = {}
    stats_section = additional_text.split("# 武器ステータスデータ")
    if len(stats_section) > 1:
        current_class = ""
        for line in stats_section[1].split("\n"):
            line = line.strip()
            if line.startswith("## "):
                current_class = line[3:].strip()
            elif line.startswith("|") and not line.startswith("|---") and not line.startswith("| ブキ"):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 3:
                    name = cells[0]
                    stats_map[name] = {
                        "range": cells[1] if len(cells) > 1 else "",
                        "damage": cells[2] if len(cells) > 2 else "",
                        "kill_time": cells[3] if len(cells) > 3 else "",
                    }

    # Game8武器テーブルのパース
    weapons = []
    current_class = ""
    in_table = False

    for line in game8_text.split("\n"):
        line = line.strip()

        # 武器種の見出し検出
        if line.startswith("## ") and not line.startswith("## X") and not line.startswith("## S"):
            class_name = line[3:].strip()
            if class_name in ["シューター", "ブラスター", "ローラー", "フデ", "チャージャー",
                            "スロッシャー", "スピナー", "マニューバー", "シェルター",
                            "ストリンガー", "ワイパー", "その他の武器"]:
                current_class = class_name
                in_table = True
                continue

        # テーブル行の処理
        if in_table and line.startswith("|") and not line.startswith("|--") and not line.startswith("| 武器名"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 4:
                name = cells[0]
                sub = cells[1]
                special = cells[2]

                # 解放ランクと評価の位置がテーブルによって異なる
                if len(cells) >= 5:
                    rank = cells[3]
                    rating = cells[4]
                else:
                    rank = "-"
                    rating = cells[3] if len(cells) >= 4 else ""

                # ステータス情報
                stats = stats_map.get(name, {})

                weapon = {
                    "name": name,
                    "class": current_class if current_class != "その他の武器" else "",
                    "sub": sub,
                    "special": special,
                    "unlock_rank": rank,
                    "rating": rating,
                    "range": stats.get("range", ""),
                    "damage": stats.get("damage", ""),
                    "kill_time": stats.get("kill_time", ""),
                    "icon": weapon_icon_map.get(name, ""),
                    "sub_icon": sub_icon_map.get(sub, ""),
                    "special_icon": sp_icon_map.get(special, ""),
                }

                # 武器種を推定（その他の武器の場合）
                if not weapon["class"]:
                    if "スピナー" in name or "イグザミナー" in name:
                        weapon["class"] = "スピナー"
                    elif "マニューバー" in name or "ガエン" in name:
                        weapon["class"] = "マニューバー"
                    elif "PEN" in name or "R-PEN" in name:
                        weapon["class"] = "シューター"
                    else:
                        weapon["class"] = "その他"

                weapons.append(weapon)

        # ティアリストのパース
        if line.startswith("# 第2部"):
            in_table = False

    # ティアリストの読み込み
    tier_map = {}
    current_tier = ""
    for line in game8_text.split("\n"):
        line = line.strip()
        if "ティア" in line and line.startswith("## "):
            tier_name = line.split("ティア")[0].replace("## ", "").strip()
            current_tier = tier_name
        elif current_tier and line.startswith("|") and not line.startswith("|--") and not line.startswith("| 武器名"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 1:
                tier_map[cells[0]] = current_tier

    # ティア情報を武器に追加
    for w in weapons:
        w["tier"] = tier_map.get(w["name"], "")

    # バンカラコレクションの新武器もパース
    new_weapons = []
    in_new = False
    current_collection = ""
    for line in game8_text.split("\n"):
        line = line.strip()
        if "バンカラコレクション" in line and line.startswith("## "):
            current_collection = line[3:].strip()
            in_new = True
            continue
        if in_new and line.startswith("| ") and not line.startswith("|--") and not line.startswith("| No."):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 5:
                new_weapons.append({
                    "name": cells[1],
                    "class": cells[2],
                    "sub": cells[3],
                    "special": cells[4],
                    "unlock_rank": "-",
                    "rating": "",
                    "range": "",
                    "damage": "",
                    "kill_time": "",
                    "icon": "",
                    "sub_icon": sub_icon_map.get(cells[3], ""),
                    "special_icon": sp_icon_map.get(cells[4], ""),
                    "tier": "",
                    "collection": current_collection,
                })

    # 既存武器名のセット
    existing_names = {w["name"] for w in weapons}

    # 新武器を追加（重複しないもの）
    for nw in new_weapons:
        if nw["name"] not in existing_names:
            weapons.append(nw)
            existing_names.add(nw["name"])

    return weapons


def build_stages():
    """ステージデータを構築"""
    stages = [
        {"name": "ユノハナ大渓谷", "origin": "スプラ3", "order": 1},
        {"name": "ゴンズイ地区", "origin": "スプラ3", "order": 2},
        {"name": "ヤガラ市場", "origin": "スプラ3", "order": 3},
        {"name": "マテガイ放水路", "origin": "スプラ3", "order": 4},
        {"name": "ナメロウ金属", "origin": "スプラ3", "order": 5},
        {"name": "マサバ海峡大橋", "origin": "スプラ1復活", "order": 6},
        {"name": "キンメダイ美術館", "origin": "スプラ1復活", "order": 7},
        {"name": "マヒマヒリゾート＆スパ", "origin": "スプラ1復活", "order": 8},
        {"name": "海女美術大学", "origin": "スプラ2続投", "order": 9},
        {"name": "チョウザメ造船", "origin": "スプラ2続投", "order": 10},
        {"name": "ザトウマーケット", "origin": "スプラ2続投", "order": 11},
        {"name": "スメーシーワールド", "origin": "スプラ2続投", "order": 12},
        {"name": "クサヤ温泉", "origin": "アプデ追加", "order": 13},
        {"name": "ヒラメが丘団地", "origin": "アプデ追加", "order": 14},
        {"name": "ナンプラー遺跡", "origin": "アプデ追加", "order": 15},
        {"name": "マンタマリア号", "origin": "アプデ追加", "order": 16},
        {"name": "タラポートショッピングパーク", "origin": "アプデ追加", "order": 17},
        {"name": "コンブトラック", "origin": "アプデ追加", "order": 18},
        {"name": "タカアシ経済特区", "origin": "アプデ追加", "order": 19},
        {"name": "オヒョウ海運", "origin": "アプデ追加", "order": 20},
        {"name": "バイガイ亭", "origin": "アプデ追加", "order": 21},
        {"name": "ネギトロ炭鉱", "origin": "アプデ追加", "order": 22},
        {"name": "カジキ空港", "origin": "アプデ追加", "order": 23},
        {"name": "リュウグウターミナル", "origin": "アプデ追加", "order": 24},
        {"name": "デカライン高架下", "origin": "アプデ追加", "order": 25},
    ]
    return stages


def build_gear_powers():
    """ギアパワーデータを構築"""
    gear_powers = {
        "basic": [
            {"name": "インク効率アップ（メイン）", "effect": "メインウェポンの消費インク量が少なくなる", "tier": "S+"},
            {"name": "インク効率アップ（サブ）", "effect": "サブウェポンの消費インク量が少なくなる", "tier": "S+"},
            {"name": "インク回復力アップ", "effect": "インクタンク回復速度がアップ", "tier": "X"},
            {"name": "ヒト移動速度アップ", "effect": "ヒト状態の移動速度がアップ", "tier": "S+"},
            {"name": "イカダッシュ速度アップ", "effect": "イカダッシュ時の移動速度がアップ", "tier": "X"},
            {"name": "スペシャル増加量アップ", "effect": "スペシャルゲージの増加量がアップ", "tier": "S+"},
            {"name": "スペシャル減少量ダウン", "effect": "やられた時のスペシャルゲージ減少量がダウン", "tier": "X"},
            {"name": "スペシャル性能アップ", "effect": "スペシャルウェポンの性能がアップ", "tier": "A"},
            {"name": "復活時間短縮", "effect": "連続でやられた時の復活時間が短縮", "tier": "S+"},
            {"name": "スーパージャンプ時間短縮", "effect": "スーパージャンプにかかる時間が短縮", "tier": "X"},
            {"name": "サブ性能アップ", "effect": "サブウェポンの性能がアップ（飛距離など）", "tier": "A"},
            {"name": "相手インク影響軽減", "effect": "相手インクを踏んだ時のダメージと速度低下を軽減", "tier": "X"},
            {"name": "サブ影響軽減", "effect": "サブウェポンの影響を軽減", "tier": "A"},
            {"name": "アクション強化", "effect": "イカロール・イカノボリの性能向上、ジャンプ撃ちのブレ軽減", "tier": "S+"},
        ],
        "main_only": [
            {"name": "スタートダッシュ", "effect": "試合開始後30秒間、移動速度アップ", "tier": "B"},
            {"name": "ラストスパート", "effect": "試合残り30秒、インク効率がアップ", "tier": "S+"},
            {"name": "逆境強化", "effect": "味方が少ない時、スペシャルゲージが徐々に増加", "tier": "B"},
            {"name": "カムバック", "effect": "復活後20秒間、複数のステータスが向上", "tier": "X"},
            {"name": "イカニンジャ", "effect": "イカダッシュ時のインク飛沫を隠す（速度は低下）", "tier": "S+"},
            {"name": "リベンジ", "effect": "自分を倒した相手を一定時間マーキング", "tier": "B"},
            {"name": "サーマルインク", "effect": "メインの弾を当てた相手を一定時間表示", "tier": "A"},
            {"name": "復活ペナルティアップ", "effect": "自分が倒した相手の復活時間とスペシャル減少を増加", "tier": "S+"},
            {"name": "追加ギアパワー倍化", "effect": "追加ギアパワーの効果を倍にする（1つ分）", "tier": "A"},
            {"name": "ステルスジャンプ", "effect": "スーパージャンプの着地マーカーを遠距離から見えなくする", "tier": "X"},
            {"name": "対物攻撃力アップ", "effect": "プレイヤー以外のオブジェクトへのダメージが増加", "tier": "A"},
            {"name": "受け身術", "effect": "スーパージャンプ着地時に前転して隙を減らす", "tier": "A"},
        ],
    }
    return gear_powers


def build_salmon_run():
    """サーモンランデータを構築"""
    salmon = {
        "big_salmon": [
            {"name": "テッキュウ", "priority": "X", "description": "砲弾を撃ってくる装甲敵", "how_to_defeat": "遠距離から集中攻撃"},
            {"name": "カタパッド", "priority": "S+", "description": "ミサイルを飛ばす", "how_to_defeat": "開いた時にボムを入れる（左右のフタに1つずつ）"},
            {"name": "タワー", "priority": "S+", "description": "高所から弾幕を張る", "how_to_defeat": "鍋部分を撃って倒す"},
            {"name": "ヘビ", "priority": "S", "description": "蛇のように追いかけてくる", "how_to_defeat": "尻尾の操縦席を攻撃"},
            {"name": "コウモリ", "priority": "S", "description": "雨弾を飛ばす", "how_to_defeat": "吐き出した弾を打ち返す"},
            {"name": "ハシラ", "priority": "S", "description": "柱に登って攻撃してくる", "how_to_defeat": "柱に登って倒す"},
            {"name": "バクダン", "priority": "A", "description": "爆弾を投げてくる", "how_to_defeat": "膨らんだ弱点を狙う"},
            {"name": "テッパン", "priority": "A", "description": "シールド付きで突進する", "how_to_defeat": "背面の弱点を攻撃"},
            {"name": "モグラ", "priority": "A", "description": "地中から追いかけてくる", "how_to_defeat": "ボムを食べさせる"},
            {"name": "ダイバー", "priority": "A", "description": "インクに潜って攻撃", "how_to_defeat": "インクで着地点を塗って倒す"},
            {"name": "ナベブタ", "priority": "A", "description": "UFO型の飛行物体", "how_to_defeat": "下から撃つ"},
        ],
        "special_waves": [
            {"name": "ヒカリバエ（ラッシュ）", "description": "大量のシャケが猛スピードで襲来。標的プレイヤーに集まる"},
            {"name": "霧", "description": "視界が制限され、全方位からシャケが攻撃してくる"},
            {"name": "グリル発進", "description": "1人を追い続けるグリルが出現。終盤は2体に増加"},
            {"name": "ドスコイ大量発生", "description": "干上がった土地からドスコイが無数に出現。キャノンが使用可能"},
            {"name": "キンシャケ探し", "description": "間欠泉が現れ、キンシャケがどれかに隠れている"},
            {"name": "ハコビヤ襲来", "description": "空からシャケたちが襲来。箱を爆発させてイクラ回収"},
            {"name": "ドロシャケ噴出", "description": "間欠泉からドロシャケが現れ、口からザコシャケが湧く"},
            {"name": "巨大タツマキ", "description": "沖に巨大竜巻が発生。金イクラ箱が落ちてくる"},
        ],
        "king_salmon": [
            {"name": "ヨコヅナ", "description": "巨大シャケ"},
            {"name": "タツ", "description": "竜型オカシラ"},
            {"name": "ジョー", "description": "地中から攻撃するオカシラ。弱点は背中の赤い半球"},
        ],
    }
    return salmon


def build_rules():
    """バトルルールデータを構築"""
    rules = [
        {
            "name": "ナワバリバトル",
            "description": "3分間でステージをたくさん塗ったチームが勝利",
            "type": "レギュラーマッチ",
            "tips": "塗りを広げてスペシャルゲージを貯める。残り30秒が勝負の分かれ目",
        },
        {
            "name": "ガチエリア",
            "description": "指定エリアを塗って確保し、カウントを0にしたチームが勝利",
            "type": "バンカラマッチ",
            "tips": "エリア確保後の維持が重要。塗り武器が活躍しやすい",
        },
        {
            "name": "ガチヤグラ",
            "description": "ヤグラに乗って相手ゴールまで運ぶ。カウントが少ない方が勝利",
            "type": "バンカラマッチ",
            "tips": "ヤグラに乗る人と護衛の役割分担が重要",
        },
        {
            "name": "ガチホコバトル",
            "description": "ガチホコを持って相手のゴールに運ぶ",
            "type": "バンカラマッチ",
            "tips": "ホコを持つ人のルート選択が勝敗を分ける",
        },
        {
            "name": "ガチアサリ",
            "description": "アサリを集めてガチアサリを作り、相手のゴールに投入する",
            "type": "バンカラマッチ",
            "tips": "アサリ10個でガチアサリに。ゴール破壊後のカウントダウンが勝負",
        },
    ]
    return rules


def main():
    # 武器マスターデータ
    weapons = build_weapons()
    with open(os.path.join(DATA_DIR, "splatoon3_master.json"), "w", encoding="utf-8") as f:
        json.dump({
            "weapons": weapons,
            "stages": build_stages(),
            "gear_powers": build_gear_powers(),
            "salmon_run": build_salmon_run(),
            "rules": build_rules(),
        }, f, ensure_ascii=False, indent=2)

    # 統計
    classes = {}
    for w in weapons:
        cls = w.get("class", "不明")
        classes[cls] = classes.get(cls, 0) + 1

    print("=== マスターデータ生成完了 ===")
    print(f"総武器数: {len(weapons)}")
    print(f"武器種別:")
    for cls, count in sorted(classes.items(), key=lambda x: -x[1]):
        print(f"  {cls}: {count}")
    print(f"ステージ数: {len(build_stages())}")
    print(f"ギアパワー数: {len(build_gear_powers()['basic']) + len(build_gear_powers()['main_only'])}")
    print(f"オオモノシャケ数: {len(build_salmon_run()['big_salmon'])}")
    print(f"保存先: {os.path.join(DATA_DIR, 'splatoon3_master.json')}")


if __name__ == "__main__":
    main()
