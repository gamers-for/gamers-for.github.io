#!/usr/bin/env python3
"""
サブウェポン・スペシャルウェポンのアイコンを再取得
英語ベースのファイル名を使用
"""

import json
import os
import time
import urllib.request
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUB_ICON_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "subs")
SP_ICON_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "specials")
DATA_PATH = os.path.join(BASE_DIR, "data", "splatoon3_weapons.json")

API_URL = "https://splatoonwiki.org/w/api.php"

# サブウェポン (日本語名, Inkipedia英語名, ファイル用スラッグ)
SUB_WEAPONS = [
    ("スプラッシュボム", "Splat Bomb", "splat-bomb"),
    ("キューバンボム", "Suction Bomb", "suction-bomb"),
    ("クイックボム", "Burst Bomb", "burst-bomb"),
    ("カーリングボム", "Curling Bomb", "curling-bomb"),
    ("ロボボム", "Autobomb", "autobomb"),
    ("インクマイン", "Ink Mine", "ink-mine"),
    ("ポイズンミスト", "Toxic Mist", "toxic-mist"),
    ("ポイントセンサー", "Point Sensor", "point-sensor"),
    ("スプラッシュシールド", "Splash Wall", "splash-wall"),
    ("スプリンクラー", "Sprinkler", "sprinkler"),
    ("ジャンプビーコン", "Squid Beakon", "squid-beakon"),
    ("タンサンボム", "Fizzy Bomb", "fizzy-bomb"),
    ("トーピード", "Torpedo", "torpedo"),
    ("アングルシューター", "Angle Shooter", "angle-shooter"),
]

# スペシャルウェポン (日本語名, Inkipedia英語名, ファイル用スラッグ)
SPECIAL_WEAPONS = [
    ("グレートバリア", "Big Bubbler", "big-bubbler"),
    ("ナイスダマ", "Booyah Bomb", "booyah-bomb"),
    ("カニタンク", "Crab Tank", "crab-tank"),
    ("ジェットパック", "Inkjet", "inkjet"),
    ("アメフラシ", "Ink Storm", "ink-storm"),
    ("インクアーマー", "Ink Vac", "ink-vac"),
    ("メガホンレーザー5.1ch", "Killer Wail 5.1", "killer-wail-5-1"),
    ("テイオウイカ", "Kraken Royale", "kraken-royale"),
    ("サメライド", "Reefslider", "reefslider"),
    ("デコイチラシ", "Super Chump", "super-chump"),
    ("エナジースタンド", "Tacticooler", "tacticooler"),
    ("マルチミサイル", "Tenta Missiles", "tenta-missiles"),
    ("トリプルトルネード", "Triple Inkstrike", "triple-inkstrike"),
    ("ウルトラショット", "Trizooka", "trizooka"),
    ("ウルトラハンコ", "Ultra Stamp", "ultra-stamp"),
    ("ホップソナー", "Wave Breaker", "wave-breaker"),
    ("ショクワンダー", "Zipcaster", "zipcaster"),
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


def main():
    os.makedirs(SUB_ICON_DIR, exist_ok=True)
    os.makedirs(SP_ICON_DIR, exist_ok=True)

    # 既存の壊れたファイルを削除
    for d in [SUB_ICON_DIR, SP_ICON_DIR]:
        for f in os.listdir(d):
            fp = os.path.join(d, f)
            if os.path.isfile(fp):
                os.remove(fp)
                print(f"  Removed broken file: {fp}")

    sub_results = []
    sp_results = []

    # サブウェポンアイコン取得
    print("=== サブウェポンアイコン取得 ===")
    for ja_name, en_name, slug in SUB_WEAPONS:
        filepath = os.path.join(SUB_ICON_DIR, f"{slug}.png")

        # Inkipediaファイル名パターン: "S3 Weapon Sub <English Name> Flat.png"
        wiki_filenames = [
            f"S3 Weapon Sub {en_name} Flat.png",
            f"S3 Weapon Sub {en_name}.png",
        ]

        print(f"  {ja_name} ({en_name})...", end=" ", flush=True)
        downloaded = False
        for wiki_filename in wiki_filenames:
            image_url = get_image_url(wiki_filename)
            if image_url:
                if download_image(image_url, filepath):
                    print(f"OK ({wiki_filename})")
                    sub_results.append({
                        "ja": ja_name,
                        "en": en_name,
                        "icon": f"/images/games/splatoon3/subs/{slug}.png"
                    })
                    downloaded = True
                    break
            time.sleep(0.2)

        if not downloaded:
            print("FAILED")
            sub_results.append({"ja": ja_name, "en": en_name, "icon": ""})

        time.sleep(0.3)

    # スペシャルウェポンアイコン取得
    print("\n=== スペシャルウェポンアイコン取得 ===")
    for ja_name, en_name, slug in SPECIAL_WEAPONS:
        filepath = os.path.join(SP_ICON_DIR, f"{slug}.png")

        # Inkipediaファイル名パターン
        wiki_filenames = [
            f"S3 Weapon Special {en_name} Flat.png",
            f"S3 Weapon Special {en_name}.png",
        ]

        print(f"  {ja_name} ({en_name})...", end=" ", flush=True)
        downloaded = False
        for wiki_filename in wiki_filenames:
            image_url = get_image_url(wiki_filename)
            if image_url:
                if download_image(image_url, filepath):
                    print(f"OK ({wiki_filename})")
                    sp_results.append({
                        "ja": ja_name,
                        "en": en_name,
                        "icon": f"/images/games/splatoon3/specials/{slug}.png"
                    })
                    downloaded = True
                    break
            time.sleep(0.2)

        if not downloaded:
            print("FAILED")
            sp_results.append({"ja": ja_name, "en": en_name, "icon": ""})

        time.sleep(0.3)

    # 既存JSONを更新
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["subs"] = sub_results
    data["specials"] = sp_results

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 結果サマリー
    sub_ok = sum(1 for s in sub_results if s["icon"])
    sp_ok = sum(1 for s in sp_results if s["icon"])
    print(f"\n=== 完了 ===")
    print(f"サブウェポン: {sub_ok}/{len(sub_results)} 成功")
    print(f"スペシャル: {sp_ok}/{len(sp_results)} 成功")
    print(f"データ更新: {DATA_PATH}")


if __name__ == "__main__":
    main()
