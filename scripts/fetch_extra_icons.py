#!/usr/bin/env python3
"""
ステージ/ギアパワー/サーモンランボスのアイコンをInkipediaからダウンロード
"""

import requests
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_BASE = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3")
STAGES_DIR = os.path.join(IMG_BASE, "stages")
GEAR_DIR = os.path.join(IMG_BASE, "gear-powers")
BOSSES_DIR = os.path.join(IMG_BASE, "bosses")
API_URL = "https://splatoonwiki.org/w/api.php"

INTERVAL = 1.0  # Inkipedia API rate limit


def download_from_inkipedia(wiki_filenames, save_path):
    """InkipediaのAPIからアイコンをダウンロード（複数候補名に対応）"""
    if os.path.exists(save_path) and os.path.getsize(save_path) > 100:
        print(f"  [skip] {os.path.basename(save_path)} already exists")
        return True

    if isinstance(wiki_filenames, str):
        wiki_filenames = [wiki_filenames]

    for wiki_filename in wiki_filenames:
        params = {
            "action": "query",
            "titles": f"File:{wiki_filename}",
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json"
        }
        try:
            resp = requests.get(API_URL, params=params, timeout=15)
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "imageinfo" in page_data:
                    url = page_data["imageinfo"][0]["url"]
                    img_resp = requests.get(url, timeout=15)
                    if img_resp.status_code == 200 and len(img_resp.content) > 100:
                        with open(save_path, "wb") as f:
                            f.write(img_resp.content)
                        print(f"  [ok] {os.path.basename(save_path)} ({len(img_resp.content)} bytes)")
                        return True
            time.sleep(INTERVAL)
        except Exception as e:
            print(f"  [ERROR] {wiki_filename}: {e}")
            time.sleep(INTERVAL)

    print(f"  [FAIL] {os.path.basename(save_path)} - tried: {wiki_filenames}")
    return False


def fetch_stages():
    """ステージ画像を取得"""
    print("=" * 50)
    print("=== ステージ画像 (25) ===")
    print("=" * 50)
    os.makedirs(STAGES_DIR, exist_ok=True)

    # (日本語名, slug, Inkipedia候補ファイル名リスト)
    stages = [
        ("ユノハナ大渓谷", "scorch-gorge", [
            "S3 Stage Scorch Gorge.png",
            "S3 stage previews Scorch Gorge.png",
        ]),
        ("ゴンズイ地区", "eeltail-alley", [
            "S3 Stage Eeltail Alley.png",
            "S3 stage previews Eeltail Alley.png",
        ]),
        ("ヤガラ市場", "hagglefish-market", [
            "S3 Stage Hagglefish Market.png",
            "S3 stage previews Hagglefish Market.png",
        ]),
        ("マテガイ放水路", "undertow-spillway", [
            "S3 Stage Undertow Spillway.png",
            "S3 stage previews Undertow Spillway.png",
        ]),
        ("ナメロウ金属", "mincemeat-metalworks", [
            "S3 Stage Mincemeat Metalworks.png",
            "S3 stage previews Mincemeat Metalworks.png",
        ]),
        ("マサバ海峡大橋", "hammerhead-bridge", [
            "S3 Stage Hammerhead Bridge.png",
            "S3 stage previews Hammerhead Bridge.png",
        ]),
        ("キンメダイ美術館", "museum-d-alfonsino", [
            "S3 Stage Museum d'Alfonsino.png",
            "S3 stage previews Museum d'Alfonsino.png",
        ]),
        ("マヒマヒリゾート＆スパ", "mahi-mahi-resort", [
            "S3 Stage Mahi-Mahi Resort.png",
            "S3 stage previews Mahi-Mahi Resort.png",
        ]),
        ("海女美術大学", "inkblot-art-academy", [
            "S3 Stage Inkblot Art Academy.png",
            "S3 stage previews Inkblot Art Academy.png",
        ]),
        ("チョウザメ造船", "sturgeon-shipyard", [
            "S3 Stage Sturgeon Shipyard.png",
            "S3 stage previews Sturgeon Shipyard.png",
        ]),
        ("ザトウマーケット", "makomart", [
            "S3 Stage MakoMart.png",
            "S3 stage previews MakoMart.png",
        ]),
        ("スメーシーワールド", "wahoo-world", [
            "S3 Stage Wahoo World.png",
            "S3 stage previews Wahoo World.png",
        ]),
        ("クサヤ温泉", "brinewater-springs", [
            "S3 Stage Brinewater Springs.png",
            "S3 stage previews Brinewater Springs.png",
        ]),
        ("ヒラメが丘団地", "flounder-heights", [
            "S3 Stage Flounder Heights.png",
            "S3 stage previews Flounder Heights.png",
        ]),
        ("ナンプラー遺跡", "umami-ruins", [
            "S3 Stage Um'ami Ruins.png",
            "S3 stage previews Um'ami Ruins.png",
        ]),
        ("マンタマリア号", "manta-maria", [
            "S3 Stage Manta Maria.png",
            "S3 stage previews Manta Maria.png",
        ]),
        ("タラポートショッピングパーク", "barnacle-and-dime", [
            "S3 Stage Barnacle & Dime.png",
            "S3 stage previews Barnacle & Dime.png",
        ]),
        ("コンブトラック", "crableg-capital", [
            "S3 Stage Crableg Capital.png",
            "S3 stage previews Crableg Capital.png",
        ]),
        ("タカアシ経済特区", "shipshape-cargo-co", [
            "S3 Stage Shipshape Cargo Co..png",
            "S3 Stage Shipshape Cargo Co.png",
            "S3 stage previews Shipshape Cargo Co..png",
        ]),
        ("オヒョウ海運", "robo-rom-en", [
            "S3 Stage Robo ROM-en.png",
            "S3 stage previews Robo ROM-en.png",
        ]),
        ("バイガイ亭", "bluefin-depot", [
            "S3 Stage Bluefin Depot.png",
            "S3 stage previews Bluefin Depot.png",
        ]),
        ("ネギトロ炭鉱", "lemuria-hub", [
            "S3 Stage Lemuria Hub.png",
            "S3 stage previews Lemuria Hub.png",
        ]),
        ("カジキ空港", "marlin-airport", [
            "S3 Stage Marlin Airport.png",
            "S3 stage previews Marlin Airport.png",
        ]),
        ("リュウグウターミナル", "humpback-pump-track", [
            "S3 Stage Humpback Pump Track.png",
            "S3 stage previews Humpback Pump Track.png",
        ]),
        ("デカライン高架下", "urchin-underpass", [
            "S3 Stage Urchin Underpass.png",
            "S3 stage previews Urchin Underpass.png",
        ]),
    ]

    ok = 0
    for jp_name, slug, wiki_files in stages:
        save_path = os.path.join(STAGES_DIR, f"{slug}.png")
        if download_from_inkipedia(wiki_files, save_path):
            ok += 1
        time.sleep(INTERVAL)
    print(f"\nステージ: {ok}/{len(stages)}")
    return ok


def fetch_gear_powers():
    """ギアパワーアイコンを取得"""
    print("\n" + "=" * 50)
    print("=== ギアパワーアイコン (26) ===")
    print("=" * 50)
    os.makedirs(GEAR_DIR, exist_ok=True)

    # (日本語名, slug, Inkipedia候補ファイル名リスト)
    gear_powers = [
        # === 基本ギアパワー (14) ===
        ("インク効率アップ（メイン）", "ink-saver-main", [
            "S3 Ability Ink Saver (Main).png",
            "S3 Ability Ink Saver Main.png",
        ]),
        ("インク効率アップ（サブ）", "ink-saver-sub", [
            "S3 Ability Ink Saver (Sub).png",
            "S3 Ability Ink Saver Sub.png",
        ]),
        ("インク回復力アップ", "ink-recovery-up", [
            "S3 Ability Ink Recovery Up.png",
        ]),
        ("ヒト移動速度アップ", "run-speed-up", [
            "S3 Ability Run Speed Up.png",
        ]),
        ("イカダッシュ速度アップ", "swim-speed-up", [
            "S3 Ability Swim Speed Up.png",
        ]),
        ("スペシャル増加量アップ", "special-charge-up", [
            "S3 Ability Special Charge Up.png",
        ]),
        ("スペシャル減少量ダウン", "special-saver", [
            "S3 Ability Special Saver.png",
        ]),
        ("スペシャル性能アップ", "special-power-up", [
            "S3 Ability Special Power Up.png",
        ]),
        ("復活時間短縮", "quick-respawn", [
            "S3 Ability Quick Respawn.png",
        ]),
        ("スーパージャンプ時間短縮", "quick-super-jump", [
            "S3 Ability Quick Super Jump.png",
        ]),
        ("サブ性能アップ", "sub-power-up", [
            "S3 Ability Sub Power Up.png",
        ]),
        ("相手インク影響軽減", "ink-resistance-up", [
            "S3 Ability Ink Resistance Up.png",
        ]),
        ("サブ影響軽減", "sub-resistance-up", [
            "S3 Ability Sub Resistance Up.png",
        ]),
        ("アクション強化", "intensify-action", [
            "S3 Ability Intensify Action.png",
        ]),
        # === メイン専用ギアパワー (12) ===
        ("スタートダッシュ", "opening-gambit", [
            "S3 Ability Opening Gambit.png",
        ]),
        ("ラストスパート", "last-ditch-effort", [
            "S3 Ability Last-Ditch Effort.png",
        ]),
        ("逆境強化", "tenacity", [
            "S3 Ability Tenacity.png",
        ]),
        ("カムバック", "comeback", [
            "S3 Ability Comeback.png",
        ]),
        ("イカニンジャ", "ninja-squid", [
            "S3 Ability Ninja Squid.png",
        ]),
        ("リベンジ", "haunt", [
            "S3 Ability Haunt.png",
        ]),
        ("サーマルインク", "thermal-ink", [
            "S3 Ability Thermal Ink.png",
        ]),
        ("復活ペナルティアップ", "respawn-punisher", [
            "S3 Ability Respawn Punisher.png",
        ]),
        ("追加ギアパワー倍化", "ability-doubler", [
            "S3 Ability Ability Doubler.png",
        ]),
        ("ステルスジャンプ", "stealth-jump", [
            "S3 Ability Stealth Jump.png",
        ]),
        ("対物攻撃力アップ", "object-shredder", [
            "S3 Ability Object Shredder.png",
        ]),
        ("受け身術", "drop-roller", [
            "S3 Ability Drop Roller.png",
        ]),
    ]

    ok = 0
    for jp_name, slug, wiki_files in gear_powers:
        save_path = os.path.join(GEAR_DIR, f"{slug}.png")
        if download_from_inkipedia(wiki_files, save_path):
            ok += 1
        time.sleep(INTERVAL)
    print(f"\nギアパワー: {ok}/{len(gear_powers)}")
    return ok


def fetch_bosses():
    """サーモンランボスアイコンを取得"""
    print("\n" + "=" * 50)
    print("=== サーモンランボス (14) ===")
    print("=" * 50)
    os.makedirs(BOSSES_DIR, exist_ok=True)

    # (日本語名, slug, Inkipedia候補ファイル名リスト)
    bosses = [
        # === オオモノシャケ (11) ===
        ("テッキュウ", "big-shot", [
            "S3 icon Big Shot.png",
            "S3 Salmon Run icon Big Shot.png",
            "S3 Boss Salmonid Big Shot icon.png",
        ]),
        ("カタパッド", "flyfish", [
            "S3 icon Flyfish.png",
            "S3 Salmon Run icon Flyfish.png",
            "S3 Boss Salmonid Flyfish icon.png",
        ]),
        ("タワー", "stinger", [
            "S3 icon Stinger.png",
            "S3 Salmon Run icon Stinger.png",
            "S3 Boss Salmonid Stinger icon.png",
        ]),
        ("ヘビ", "steel-eel", [
            "S3 icon Steel Eel.png",
            "S3 Salmon Run icon Steel Eel.png",
            "S3 Boss Salmonid Steel Eel icon.png",
        ]),
        ("コウモリ", "drizzler", [
            "S3 icon Drizzler.png",
            "S3 Salmon Run icon Drizzler.png",
            "S3 Boss Salmonid Drizzler icon.png",
        ]),
        ("ハシラ", "fish-stick", [
            "S3 icon Fish Stick.png",
            "S3 Salmon Run icon Fish Stick.png",
            "S3 Boss Salmonid Fish Stick icon.png",
        ]),
        ("バクダン", "steelhead", [
            "S3 icon Steelhead.png",
            "S3 Salmon Run icon Steelhead.png",
            "S3 Boss Salmonid Steelhead icon.png",
        ]),
        ("テッパン", "scrapper", [
            "S3 icon Scrapper.png",
            "S3 Salmon Run icon Scrapper.png",
            "S3 Boss Salmonid Scrapper icon.png",
        ]),
        ("モグラ", "maws", [
            "S3 icon Maws.png",
            "S3 Salmon Run icon Maws.png",
            "S3 Boss Salmonid Maws icon.png",
        ]),
        ("ダイバー", "flipper-flopper", [
            "S3 icon Flipper-Flopper.png",
            "S3 Salmon Run icon Flipper-Flopper.png",
            "S3 Boss Salmonid Flipper-Flopper icon.png",
        ]),
        ("ナベブタ", "slammin-lid", [
            "S3 icon Slammin' Lid.png",
            "S3 Salmon Run icon Slammin' Lid.png",
            "S3 Boss Salmonid Slammin' Lid icon.png",
        ]),
        # === オカシラシャケ (3) ===
        ("ヨコヅナ", "cohozuna", [
            "S3 icon Cohozuna.png",
            "S3 Salmon Run icon Cohozuna.png",
            "S3 King Salmonid Cohozuna icon.png",
        ]),
        ("タツ", "horrorboros", [
            "S3 icon Horrorboros.png",
            "S3 Salmon Run icon Horrorboros.png",
            "S3 King Salmonid Horrorboros icon.png",
        ]),
        ("ジョー", "megalodontia", [
            "S3 icon Megalodontia.png",
            "S3 Salmon Run icon Megalodontia.png",
            "S3 King Salmonid Megalodontia icon.png",
        ]),
    ]

    ok = 0
    for jp_name, slug, wiki_files in bosses:
        save_path = os.path.join(BOSSES_DIR, f"{slug}.png")
        if download_from_inkipedia(wiki_files, save_path):
            ok += 1
        time.sleep(INTERVAL)
    print(f"\nボス: {ok}/{len(bosses)}")
    return ok


def main():
    print("Inkipediaからアイコンを取得します")
    print(f"保存先: {IMG_BASE}")
    print(f"リクエスト間隔: {INTERVAL}秒\n")

    s_ok = fetch_stages()
    g_ok = fetch_gear_powers()
    b_ok = fetch_bosses()

    print("\n" + "=" * 50)
    print("=== 最終結果 ===")
    print("=" * 50)
    print(f"ステージ: {s_ok}/25")
    print(f"ギアパワー: {g_ok}/26")
    print(f"ボス: {b_ok}/14")
    total = s_ok + g_ok + b_ok
    print(f"合計: {total}/65")

    if total < 65:
        print("\n[!] 取得できなかったアイコンがあります。")
        print("    Inkipediaのファイル名を確認して、スクリプトを調整してください。")
        print("    検索: https://splatoonwiki.org/wiki/Special:Search")


if __name__ == "__main__":
    main()
