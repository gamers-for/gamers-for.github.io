#!/usr/bin/env python3
"""
スプラトゥーン3 全武器・サブ・スペシャルのアイコン一括取得スクリプト
Inkipedia (splatoonwiki.org) のMediaWiki APIを使用
"""

import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "weapons")
SUB_ICON_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "subs")
SP_ICON_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "specials")
DATA_DIR = os.path.join(BASE_DIR, "data")

API_URL = "https://splatoonwiki.org/w/api.php"

# ========== 全武器データ (日本語名, 英語名, 武器種, サブ, スペシャル) ==========
WEAPONS = [
    # シューター
    ("ボールドマーカー", "Sploosh-o-matic", "シューター", "カーリングボム", "ウルトラショット"),
    ("ボールドマーカーネオ", "Neo Sploosh-o-matic", "シューター", "キューバンボム", "トリプルトルネード"),
    ("わかばシューター", "Splattershot Jr.", "シューター", "スプラッシュボム", "グレートバリア"),
    ("もみじシューター", "Custom Splattershot Jr.", "シューター", "トーピード", "アメフラシ"),
    ("シャープマーカー", "Splash-o-matic", "シューター", "キューバンボム", "カニタンク"),
    ("シャープマーカーネオ", "Neo Splash-o-matic", "シューター", "クイックボム", "トリプルトルネード"),
    ("プロモデラーMG", "Aerospray MG", "シューター", "タンサンボム", "サメライド"),
    ("プロモデラーRG", "Aerospray RG", "シューター", "スプリンクラー", "ナイスダマ"),
    ("スプラシューター", "Splattershot", "シューター", "キューバンボム", "ウルトラショット"),
    ("スプラシューターコラボ", "Tentatek Splattershot", "シューター", "スプラッシュボム", "トリプルトルネード"),
    ("52ガロン", ".52 Gal", "シューター", "スプラッシュシールド", "メガホンレーザー5.1ch"),
    ("52ガロンデコ", ".52 Gal Deco", "シューター", "カーリングボム", "テイオウイカ"),
    ("N-ZAP85", "N-ZAP '85", "シューター", "キューバンボム", "エナジースタンド"),
    ("N-ZAP89", "N-ZAP '89", "シューター", "ロボボム", "デコイチラシ"),
    ("プライムシューター", "Splattershot Pro", "シューター", "ポイントセンサー", "カニタンク"),
    ("プライムシューターコラボ", "Forge Splattershot Pro", "シューター", "トーピード", "ホップソナー"),
    ("96ガロン", ".96 Gal", "シューター", "スプリンクラー", "インクアーマー"),
    ("96ガロンデコ", ".96 Gal Deco", "シューター", "スプラッシュシールド", "テイオウイカ"),
    ("ジェットスイーパー", "Jet Squelcher", "シューター", "ポイズンミスト", "アメフラシ"),
    ("ジェットスイーパーカスタム", "Custom Jet Squelcher", "シューター", "クイックボム", "ウルトラショット"),
    ("スペースシューター", "Splattershot Nova", "シューター", "ポイントセンサー", "ショクワンダー"),
    ("スペースシューターコラボ", "Annaki Splattershot Nova", "シューター", "インクマイン", "サメライド"),
    ("L3リールガン", "L-3 Nozzlenose", "シューター", "カーリングボム", "カニタンク"),
    ("L3リールガンD", "L-3 Nozzlenose D", "シューター", "クイックボム", "ウルトラショット"),
    ("H3リールガン", "H-3 Nozzlenose", "シューター", "ポイントセンサー", "マルチミサイル"),
    ("H3リールガンD", "H-3 Nozzlenose D", "シューター", "キューバンボム", "エナジースタンド"),
    ("ボトルガイザー", "Squeezer", "シューター", "スプラッシュボム", "アメフラシ"),
    ("ボトルガイザーフォイル", "Foil Squeezer", "シューター", "スプラッシュシールド", "ウルトラショット"),

    # ブラスター
    ("ノヴァブラスター", "Luna Blaster", "ブラスター", "スプラッシュボム", "マルチミサイル"),
    ("ノヴァブラスターネオ", "Luna Blaster Neo", "ブラスター", "タンサンボム", "テイオウイカ"),
    ("ホットブラスター", "Blaster", "ブラスター", "ロボボム", "ウルトラショット"),
    ("ホットブラスターカスタム", "Custom Blaster", "ブラスター", "ポイントセンサー", "トリプルトルネード"),
    ("ロングブラスター", "Range Blaster", "ブラスター", "キューバンボム", "ウルトラハンコ"),
    ("ロングブラスターカスタム", "Custom Range Blaster", "ブラスター", "タンサンボム", "デコイチラシ"),
    ("クラッシュブラスター", "Clash Blaster", "ブラスター", "スプラッシュボム", "ウルトラショット"),
    ("クラッシュブラスターネオ", "Clash Blaster Neo", "ブラスター", "カーリングボム", "マルチミサイル"),
    ("ラピッドブラスター", "Rapid Blaster", "ブラスター", "トーピード", "トリプルトルネード"),
    ("ラピッドブラスターデコ", "Rapid Blaster Deco", "ブラスター", "キューバンボム", "ジェットパック"),

    # ローラー
    ("カーボンローラー", "Carbon Roller", "ローラー", "ロボボム", "ショクワンダー"),
    ("カーボンローラーデコ", "Carbon Roller Deco", "ローラー", "クイックボム", "ウルトラショット"),
    ("スプラローラー", "Splat Roller", "ローラー", "カーリングボム", "グレートバリア"),
    ("スプラローラーコラボ", "Krak-On Splat Roller", "ローラー", "キューバンボム", "テイオウイカ"),
    ("ダイナモローラー", "Dynamo Roller", "ローラー", "スプリンクラー", "ホップソナー"),
    ("ダイナモローラーテスラ", "Gold Dynamo Roller", "ローラー", "スプラッシュボム", "アメフラシ"),
    ("ヴァリアブルローラー", "Flingza Roller", "ローラー", "インクマイン", "マルチミサイル"),
    ("ヴァリアブルローラーフォイル", "Foil Flingza Roller", "ローラー", "スプラッシュシールド", "メガホンレーザー5.1ch"),
    ("ワイドローラー", "Big Swig Roller", "ローラー", "スプラッシュシールド", "ナイスダマ"),
    ("ワイドローラーコラボ", "Big Swig Roller Express", "ローラー", "タンサンボム", "ウルトラショット"),

    # フデ
    ("パブロ", "Inkbrush", "フデ", "スプラッシュボム", "ショクワンダー"),
    ("パブロ・ヒュー", "Inkbrush Nouveau", "フデ", "インクマイン", "ウルトラショット"),
    ("ホクサイ", "Octobrush", "フデ", "キューバンボム", "ショクワンダー"),
    ("ホクサイ・ヒュー", "Octobrush Nouveau", "フデ", "タンサンボム", "エナジースタンド"),

    # チャージャー
    ("スクイックリンα", "Classic Squiffer", "チャージャー", "ポイントセンサー", "グレートバリア"),
    ("スクイックリンβ", "New Squiffer", "チャージャー", "ロボボム", "アメフラシ"),
    ("スプラチャージャー", "Splat Charger", "チャージャー", "スプラッシュボム", "メガホンレーザー5.1ch"),
    ("スプラチャージャーコラボ", "Z+F Splat Charger", "チャージャー", "スプラッシュシールド", "トリプルトルネード"),
    ("スプラスコープ", "Splatterscope", "チャージャー", "スプラッシュボム", "メガホンレーザー5.1ch"),
    ("スプラスコープコラボ", "Z+F Splatterscope", "チャージャー", "スプラッシュシールド", "トリプルトルネード"),
    ("リッター4K", "E-liter 4K", "チャージャー", "トーピード", "ホップソナー"),
    ("4Kスコープ", "E-liter 4K Scope", "チャージャー", "トーピード", "ホップソナー"),
    ("14式竹筒銃・甲", "Bamboozler 14 Mk I", "チャージャー", "トーピード", "マルチミサイル"),
    ("14式竹筒銃・乙", "Bamboozler 14 Mk II", "チャージャー", "タンサンボム", "エナジースタンド"),
    ("ソイチューバー", "Goo Tuber", "チャージャー", "トーピード", "テイオウイカ"),
    ("ソイチューバーカスタム", "Custom Goo Tuber", "チャージャー", "カーリングボム", "ウルトラショット"),
    ("LACT-450", "Snipewriter 5H", "チャージャー", "カーリングボム", "マルチミサイル"),
    ("LACT-450デコ", "Snipewriter 5B", "チャージャー", "スプラッシュボム", "テイオウイカ"),

    # スロッシャー
    ("バケットスロッシャー", "Slosher", "スロッシャー", "スプラッシュボム", "トリプルトルネード"),
    ("バケットスロッシャーデコ", "Slosher Deco", "スロッシャー", "スプリンクラー", "デコイチラシ"),
    ("ヒッセン", "Tri-Slosher", "スロッシャー", "クイックボム", "ウルトラショット"),
    ("ヒッセン・ヒュー", "Tri-Slosher Nouveau", "スロッシャー", "ロボボム", "ナイスダマ"),
    ("スクリュースロッシャー", "Sloshing Machine", "スロッシャー", "タンサンボム", "サメライド"),
    ("スクリュースロッシャーネオ", "Sloshing Machine Neo", "スロッシャー", "ポイントセンサー", "トリプルトルネード"),
    ("オーバーフロッシャー", "Bloblobber", "スロッシャー", "スプリンクラー", "アメフラシ"),
    ("オーバーフロッシャーデコ", "Bloblobber Deco", "スロッシャー", "アングルシューター", "カニタンク"),
    ("エクスプロッシャー", "Explosher", "スロッシャー", "ポイントセンサー", "アメフラシ"),
    ("エクスプロッシャーカスタム", "Custom Explosher", "スロッシャー", "インクマイン", "ウルトラショット"),
    ("モップリン", "Dread Wringer", "スロッシャー", "キューバンボム", "ナイスダマ"),
    ("モップリンD", "Dread Wringer D", "スロッシャー", "トーピード", "ホップソナー"),

    # スピナー
    ("スプラスピナー", "Mini Splatling", "スピナー", "クイックボム", "ウルトラショット"),
    ("スプラスピナーコラボ", "Zink Mini Splatling", "スピナー", "トーピード", "マルチミサイル"),
    ("バレルスピナー", "Heavy Splatling", "スピナー", "スプリンクラー", "ホップソナー"),
    ("バレルスピナーデコ", "Heavy Splatling Deco", "スピナー", "ポイントセンサー", "テイオウイカ"),
    ("ハイドラント", "Hydra Splatling", "スピナー", "ロボボム", "メガホンレーザー5.1ch"),
    ("ハイドラントカスタム", "Custom Hydra Splatling", "スピナー", "インクマイン", "エナジースタンド"),
    ("クーゲルシュライバー", "Ballpoint Splatling", "スピナー", "タンサンボム", "テイオウイカ"),
    ("クーゲルシュライバー・ヒュー", "Ballpoint Splatling Nouveau", "スピナー", "インクマイン", "アメフラシ"),
    ("ノーチラス47", "Nautilus 47", "スピナー", "ポイントセンサー", "ウルトラショット"),
    ("ノーチラス79", "Nautilus 79", "スピナー", "キューバンボム", "デコイチラシ"),
    ("イグザミナー", "Heavy Edit Splatling", "スピナー", "カーリングボム", "ナイスダマ"),
    ("イグザミナー・ヒュー", "Heavy Edit Splatling Nouveau", "スピナー", "ロボボム", "マルチミサイル"),

    # マニューバー
    ("スパッタリー", "Dapple Dualies", "マニューバー", "キューバンボム", "ウルトラショット"),
    ("スパッタリー・ヒュー", "Dapple Dualies Nouveau", "マニューバー", "トーピード", "サメライド"),
    ("スプラマニューバー", "Splat Dualies", "マニューバー", "キューバンボム", "カニタンク"),
    ("スプラマニューバーコラボ", "Enperry Splat Dualies", "マニューバー", "スプラッシュボム", "カニタンク"),
    ("ケルビン525", "Glooga Dualies", "マニューバー", "スプラッシュシールド", "ショクワンダー"),
    ("ケルビン525デコ", "Glooga Dualies Deco", "マニューバー", "スプラッシュボム", "グレートバリア"),
    ("デュアルスイーパー", "Dualie Squelchers", "マニューバー", "スプラッシュボム", "デコイチラシ"),
    ("デュアルスイーパーカスタム", "Custom Dualie Squelchers", "マニューバー", "キューバンボム", "メガホンレーザー5.1ch"),
    ("クアッドホッパーブラック", "Dark Tetra Dualies", "マニューバー", "スプラッシュボム", "マルチミサイル"),
    ("クアッドホッパーホワイト", "Light Tetra Dualies", "マニューバー", "スプリンクラー", "ウルトラショット"),
    ("ガエンFF", "Douser Dualies FF", "マニューバー", "スプラッシュボム", "メガホンレーザー5.1ch"),
    ("ガエンFFカスタム", "Custom Douser Dualies FF", "マニューバー", "スプリンクラー", "ナイスダマ"),

    # シェルター
    ("パラシェルター", "Splat Brella", "シェルター", "スプリンクラー", "トリプルトルネード"),
    ("パラシェルターソレーラ", "Sorella Brella", "シェルター", "ロボボム", "メガホンレーザー5.1ch"),
    ("キャンピングシェルター", "Tenta Brella", "シェルター", "スプラッシュシールド", "マルチミサイル"),
    ("キャンピングシェルターソレーラ", "Tenta Sorella Brella", "シェルター", "タンサンボム", "カニタンク"),
    ("スパイガジェット", "Undercover Brella", "シェルター", "インクマイン", "エナジースタンド"),
    ("スパイガジェットソレーラ", "Undercover Sorella Brella", "シェルター", "トーピード", "ウルトラショット"),
    ("24式張替傘・甲", "Recycled Brella 24 Mk I", "シェルター", "タンサンボム", "ウルトラショット"),
    ("24式張替傘・乙", "Recycled Brella 24 Mk II", "シェルター", "スプラッシュシールド", "アメフラシ"),

    # ストリンガー
    ("トライストリンガー", "Tri-Stringer", "ストリンガー", "ポイズンミスト", "メガホンレーザー5.1ch"),
    ("トライストリンガーコラボ", "Inkline Tri-Stringer", "ストリンガー", "スプリンクラー", "ウルトラショット"),
    ("LACT-450", "Snipewriter 5H", "ストリンガー", "カーリングボム", "マルチミサイル"),

    # ワイパー
    ("ドライブワイパー", "Splatana Stamper", "ワイパー", "スプラッシュボム", "カニタンク"),
    ("ドライブワイパーデコ", "Splatana Stamper Nouveau", "ワイパー", "ポイズンミスト", "エナジースタンド"),
    ("ジムワイパー", "Splatana Wiper", "ワイパー", "クイックボム", "ショクワンダー"),
    ("ジムワイパーデコ", "Splatana Wiper Deco", "ワイパー", "ポイントセンサー", "テイオウイカ"),
]

# サブウェポン (日本語名, 英語ファイル名)
SUB_WEAPONS = [
    ("スプラッシュボム", "Splat_Bomb"),
    ("キューバンボム", "Suction_Bomb"),
    ("クイックボム", "Burst_Bomb"),
    ("カーリングボム", "Curling_Bomb"),
    ("ロボボム", "Autobomb"),
    ("インクマイン", "Ink_Mine"),
    ("ポイズンミスト", "Toxic_Mist"),
    ("ポイントセンサー", "Point_Sensor"),
    ("スプラッシュシールド", "Splash_Wall"),
    ("スプリンクラー", "Sprinkler"),
    ("ジャンプビーコン", "Squid_Beakon"),
    ("タンサンボム", "Fizzy_Bomb"),
    ("トーピード", "Torpedo"),
    ("アングルシューター", "Angle_Shooter"),
]

# スペシャルウェポン (日本語名, 英語ファイル名)
SPECIAL_WEAPONS = [
    ("グレートバリア", "Big_Bubbler"),
    ("ナイスダマ", "Booyah_Bomb"),
    ("カニタンク", "Crab_Tank"),
    ("ジェットパック", "Inkjet"),
    ("アメフラシ", "Ink_Storm"),
    ("インクアーマー", "Ink_Vac"),
    ("メガホンレーザー5.1ch", "Killer_Wail_5.1"),
    ("テイオウイカ", "Kraken_Royale"),
    ("サメライド", "Reefslider"),
    ("デコイチラシ", "Super_Chump"),
    ("エナジースタンド", "Tacticooler"),
    ("マルチミサイル", "Tenta_Missiles"),
    ("トリプルトルネード", "Triple_Inkstrike"),
    ("ウルトラショット", "Trizooka"),
    ("ウルトラハンコ", "Ultra_Stamp"),
    ("ホップソナー", "Wave_Breaker"),
    ("ショクワンダー", "Zipcaster"),
]


def get_image_url(filename):
    """Inkipedia APIで画像の実URLを取得"""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    })
    url = f"{API_URL}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Gamers-For/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                info = page.get("imageinfo", [])
                if info:
                    return info[0]["url"]
    except Exception as e:
        print(f"  API error for {filename}: {e}")
    return None


def download_image(url, filepath):
    """画像をダウンロード"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Gamers-For/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  Download error: {e}")
        return False


def sanitize_filename(name):
    """ファイル名をサニタイズ"""
    return name.replace(" ", "_").replace("'", "%27").replace(".", ".")


def main():
    os.makedirs(ICON_DIR, exist_ok=True)
    os.makedirs(SUB_ICON_DIR, exist_ok=True)
    os.makedirs(SP_ICON_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    results = {"weapons": [], "subs": [], "specials": []}
    failed = []

    # メイン武器アイコン取得
    print("=== メイン武器アイコン取得 ===")
    seen_en = set()
    for ja_name, en_name, weapon_class, sub, special in WEAPONS:
        # 同じ英語名は一度だけ（バリアント別のアイコンは基本同じ）
        base_en = en_name.split(" ")[0] if " " not in en_name else en_name
        slug = ja_name.replace("・", "-").replace("　", "-")
        safe_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in slug)

        filepath = os.path.join(ICON_DIR, f"{safe_slug}.png")

        if os.path.exists(filepath):
            print(f"  [SKIP] {ja_name} (already exists)")
            results["weapons"].append({
                "ja": ja_name, "en": en_name, "class": weapon_class,
                "sub": sub, "special": special,
                "icon": f"/images/games/splatoon3/weapons/{safe_slug}.png"
            })
            continue

        # APIで画像URL取得
        wiki_filename = f"S3 Weapon Main {en_name}.png"
        print(f"  [{len(results['weapons'])+1}] {ja_name} ({en_name})...", end=" ", flush=True)
        image_url = get_image_url(wiki_filename)

        if image_url:
            if download_image(image_url, filepath):
                print("OK")
                results["weapons"].append({
                    "ja": ja_name, "en": en_name, "class": weapon_class,
                    "sub": sub, "special": special,
                    "icon": f"/images/games/splatoon3/weapons/{safe_slug}.png"
                })
            else:
                print("DOWNLOAD FAILED")
                failed.append(ja_name)
                results["weapons"].append({
                    "ja": ja_name, "en": en_name, "class": weapon_class,
                    "sub": sub, "special": special, "icon": ""
                })
        else:
            print("NOT FOUND")
            failed.append(ja_name)
            results["weapons"].append({
                "ja": ja_name, "en": en_name, "class": weapon_class,
                "sub": sub, "special": special, "icon": ""
            })

        time.sleep(0.3)

    # サブウェポンアイコン取得
    print("\n=== サブウェポンアイコン取得 ===")
    for ja_name, en_file in SUB_WEAPONS:
        slug = ja_name.replace("・", "-")
        safe_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in slug)
        filepath = os.path.join(SUB_ICON_DIR, f"{safe_slug}.png")

        if os.path.exists(filepath):
            print(f"  [SKIP] {ja_name}")
            results["subs"].append({"ja": ja_name, "icon": f"/images/games/splatoon3/subs/{safe_slug}.png"})
            continue

        wiki_filename = f"S3 Weapon Sub {en_file}.png"
        print(f"  {ja_name}...", end=" ", flush=True)
        image_url = get_image_url(wiki_filename)

        if image_url and download_image(image_url, filepath):
            print("OK")
            results["subs"].append({"ja": ja_name, "icon": f"/images/games/splatoon3/subs/{safe_slug}.png"})
        else:
            print("FAILED")
            results["subs"].append({"ja": ja_name, "icon": ""})

        time.sleep(0.3)

    # スペシャルウェポンアイコン取得
    print("\n=== スペシャルウェポンアイコン取得 ===")
    for ja_name, en_file in SPECIAL_WEAPONS:
        slug = ja_name.replace("・", "-")
        safe_slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in slug)
        filepath = os.path.join(SP_ICON_DIR, f"{safe_slug}.png")

        if os.path.exists(filepath):
            print(f"  [SKIP] {ja_name}")
            results["specials"].append({"ja": ja_name, "icon": f"/images/games/splatoon3/specials/{safe_slug}.png"})
            continue

        wiki_filename = f"S3 Weapon Special {en_file}.png"
        print(f"  {ja_name}...", end=" ", flush=True)
        image_url = get_image_url(wiki_filename)

        if image_url and download_image(image_url, filepath):
            print("OK")
            results["specials"].append({"ja": ja_name, "icon": f"/images/games/splatoon3/specials/{safe_slug}.png"})
        else:
            print("FAILED")
            results["specials"].append({"ja": ja_name, "icon": ""})

        time.sleep(0.3)

    # データをJSONで保存
    json_path = os.path.join(DATA_DIR, "splatoon3_weapons.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"武器: {len(results['weapons'])}件")
    print(f"サブ: {len(results['subs'])}件")
    print(f"スペシャル: {len(results['specials'])}件")
    print(f"失敗: {len(failed)}件")
    if failed:
        print(f"失敗リスト: {', '.join(failed)}")
    print(f"データ保存: {json_path}")


if __name__ == "__main__":
    main()
