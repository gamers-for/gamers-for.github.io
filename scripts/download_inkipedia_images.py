#!/usr/bin/env python3
"""
Inkipedia (splatoonwiki.org) からステージ・武器・ルール画像をダウンロード
プレースホルダー黒画像を実画像に置き換える
"""
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_IMG = PROJECT_ROOT / "static" / "images" / "games" / "splatoon3"
CONTENT_DIR = PROJECT_ROOT / "content" / "games" / "splatoon3"

USER_AGENT = "GamersFor/1.0 (game guide site; contact@gamers-for.github.io)"
DOWNLOAD_DELAY = 0.3  # 秒

# ─── 日本語 → 英語 ステージ名マッピング ──────────
STAGE_NAME_MAP = {
    "ユノハナ大渓谷": "Scorch_Gorge",
    "ゴンズイ地区": "Eeltail_Alley",
    "ヤガラ市場": "Hagglefish_Market",
    "マテガイ放水路": "Undertow_Spillway",
    "ナメロウ金属": "Mincemeat_Metalworks",
    "マサバ海峡大橋": "Hammerhead_Bridge",
    "キンメダイ美術館": "Museum_d%27Alfonsino",
    "マヒマヒリゾート＆スパ": "Mahi-Mahi_Resort",
    "マヒマヒリゾート&スパ": "Mahi-Mahi_Resort",
    "海女美術大学": "Inkblot_Art_Academy",
    "チョウザメ造船": "Sturgeon_Shipyard",
    "ザトウマーケット": "MakoMart",
    "スメーシーワールド": "Wahoo_World",
    "コンブトラック": "Humpback_Pump_Track",
    "ヒラメが丘団地": "Flounder_Heights",
    "マンタマリア号": "Manta_Maria",
    "タカアシ経済特区": "Crableg_Capital",
    "オヒョウ海運": "Shipshape_Cargo_Co.",
    "デカライン高架下": "Urchin_Underpass",
    "タラポートショッピングパーク": "Grand_Splatlands_Bowl",
    "クサヤ温泉": "Brinewater_Springs",
    "ナンプラー遺跡": "Um%27ami_Ruins",
    "バイガイ亭": "Barnacle_%26_Dime",
    "ネギトロ炭鉱": "Bluefin_Depot",
    "カジキ空港": "Marlin_Airport",
    "リュウグウターミナル": "Lemuria_Hub",
}

# ─── 日本語 → 英語 武器名マッピング ──────────
WEAPON_NAME_MAP = {
    "わかばシューター": "Splattershot_Jr.",
    "もみじシューター": "Custom_Splattershot_Jr.",
    "おちばシューター": "Splash-o-matic_7",
    "スプラシューター": "Splattershot",
    "スプラシューターコラボ": "Tentatek_Splattershot",
    "スプラシューター煌": "Annaki_Splattershot",
    "ヒーローシューターレプリカ": "Hero_Shot_Replica",
    "オクタシューターレプリカ": "Octo_Shot_Replica",
    "オーダーシューターレプリカ": "Order_Shot_Replica",
    "ボールドマーカー": "Sploosh-o-matic",
    "ボールドマーカーネオ": "Neo_Sploosh-o-matic",
    "ボールドマーカー7": "Sploosh-o-matic_7",
    "シャープマーカー": "Splash-o-matic",
    "シャープマーカーネオ": "Neo_Splash-o-matic",
    "プロモデラーMG": "Aerospray_MG",
    "プロモデラーRG": "Aerospray_RG",
    "プロモデラーPG": "Aerospray_PG",
    "N-ZAP85": "N-ZAP_%2785",
    "N-ZAP89": "N-ZAP_%2789",
    "N-ZAP83": "N-ZAP_%2783",
    "52ガロン": ".52_Gal",
    "52ガロンデコ": ".52_Gal_Deco",
    "52ガロン爪": ".52_Gal_Kensa",
    "96ガロン": ".96_Gal",
    "96ガロンデコ": ".96_Gal_Deco",
    "96ガロン爪": ".96_Gal_Kensa",
    "プライムシューター": "Splattershot_Pro",
    "プライムシューターコラボ": "Forge_Splattershot_Pro",
    "プライムシューターベッチュー": "Kensa_Splattershot_Pro",
    "ジェットスイーパー": "Jet_Squelcher",
    "ジェットスイーパーカスタム": "Custom_Jet_Squelcher",
    "L3リールガン": "L-3_Nozzlenose",
    "L3リールガンD": "L-3_Nozzlenose_D",
    "H3リールガン": "H-3_Nozzlenose",
    "H3リールガンD": "H-3_Nozzlenose_D",
    "ボトルガイザー": "Squeezer",
    "ボトルガイザーフォイル": "Foil_Squeezer",
    "スペースシューター": "Splattershot_Nova",
    "スペースシューターコラボ": "Annaki_Splattershot_Nova",
    "スペースシューターベッチュー": "Kensa_Splattershot_Nova",
    "デュアルスイーパー": "Dualie_Squelchers",
    "デュアルスイーパーカスタム": "Custom_Dualie_Squelchers",
    "スプラマニューバー": "Splat_Dualies",
    "スプラマニューバーコラボ": "Enperry_Splat_Dualies",
    "スプラマニューバーベッチュー": "Kensa_Splat_Dualies",
    "ケルビン525": "Glooga_Dualies",
    "ケルビン525デコ": "Glooga_Dualies_Deco",
    "ケルビン525ベッチュー": "Kensa_Glooga_Dualies",
    "スパッタリー": "Dapple_Dualies",
    "スパッタリーヒュー": "Dapple_Dualies_Nouveau",
    "スパッタリーowl": "Dapple_Dualies_Owl",
    "クアッドホッパーブラック": "Dark_Tetra_Dualies",
    "クアッドホッパーホワイト": "Light_Tetra_Dualies",
    "ガエンFF": "Douser_Dualies_FF",
    "ガエンFFカスタム": "Custom_Douser_Dualies_FF",
    "スプラローラー": "Splat_Roller",
    "スプラローラーコラボ": "Krak-On_Splat_Roller",
    "スプラローラーベッチュー": "Kensa_Splat_Roller",
    "ダイナモローラー": "Dynamo_Roller",
    "ダイナモローラーテスラ": "Gold_Dynamo_Roller",
    "ダイナモローラーバーンド": "Kensa_Dynamo_Roller",
    "カーボンローラー": "Carbon_Roller",
    "カーボンローラーデコ": "Carbon_Roller_Deco",
    "ヴァリアブルローラー": "Flingza_Roller",
    "ヴァリアブルローラーフォイル": "Foil_Flingza_Roller",
    "ワイドローラー": "Big_Swig_Roller",
    "ワイドローラーコラボ": "Big_Swig_Roller_Express",
    "ワイドローラーデジタル": "Digital_Big_Swig_Roller",
    "パブロ": "Inkbrush",
    "パブロ・ヒュー": "Inkbrush_Nouveau",
    "ホクサイ": "Octobrush",
    "ホクサイ・ヒュー": "Octobrush_Nouveau",
    "フィンセント": "Painbrush",
    "フィンセント・ヒュー": "Painbrush_Nouveau",
    "オーダーブラシレプリカ": "Order_Brush_Replica",
    "ノヴァブラスター": "Luna_Blaster",
    "ノヴァブラスターネオ": "Luna_Blaster_Neo",
    "ノヴァブラスターベッチュー": "Kensa_Luna_Blaster",
    "ホットブラスター": "Blaster",
    "ホットブラスターカスタム": "Custom_Blaster",
    "ロングブラスター": "Range_Blaster",
    "ロングブラスターカスタム": "Custom_Range_Blaster",
    "ラピッドブラスター": "Rapid_Blaster",
    "ラピッドブラスターデコ": "Rapid_Blaster_Deco",
    "ラピッドブラスターベッチュー": "Kensa_Rapid_Blaster",
    "Rブラスターエリート": "Rapid_Blaster_Pro",
    "Rブラスターエリートデコ": "Rapid_Blaster_Pro_Deco",
    "クラッシュブラスター": "Clash_Blaster",
    "クラッシュブラスターネオ": "Clash_Blaster_Neo",
    "S-BLAST92": "S-BLAST_%2792",
    "S-BLAST91": "S-BLAST_%2791",
    "スプラチャージャー": "Splat_Charger",
    "スプラチャージャーコラボ": "Firefin_Splat_Charger",
    "スプラチャージャーベッチュー": "Kensa_Charger",
    "スプラスコープ": "Splatterscope",
    "スプラスコープコラボ": "Firefin_Splatterscope",
    "スプラスコープベッチュー": "Kensa_Splatterscope",
    "リッター4K": "E-liter_4K",
    "リッター4Kカスタム": "Custom_E-liter_4K",
    "4Kスコープ": "E-liter_4K_Scope",
    "4Kスコープカスタム": "Custom_E-liter_4K_Scope",
    "14式竹筒銃・甲": "Bamboozler_14_Mk_I",
    "14式竹筒銃・乙": "Bamboozler_14_Mk_II",
    "ソイチューバー": "Goo_Tuber",
    "ソイチューバーカスタム": "Custom_Goo_Tuber",
    "スクイックリンα": "Classic_Squiffer",
    "スクイックリンβ": "New_Squiffer",
    "スクイックリンγ": "Fresh_Squiffer",
    "R-PEN/5H": "Snipewriter_5H",
    "R-PEN/5B": "Snipewriter_5B",
    "LACT-450": "REEF-LUX_450",
    "LACT-450デコ": "REEF-LUX_450_Deco",
    "LACT-450ベッチュー": "Kensa_REEF-LUX_450",
    "トライストリンガー": "Tri-Stringer",
    "トライストリンガーコラボ": "Inkline_Tri-Stringer",
    "トライストリンガーベッチュー": "Kensa_Tri-Stringer",
    "オーダーストリンガーレプリカ": "Order_Stringer_Replica",
    "バケットスロッシャー": "Slosher",
    "バケットスロッシャーデコ": "Slosher_Deco",
    "バケットスロッシャーソーダ": "Soda_Slosher",
    "ヒッセン": "Tri-Slosher",
    "ヒッセン・ヒュー": "Tri-Slosher_Nouveau",
    "スクリュースロッシャー": "Sloshing_Machine",
    "スクリュースロッシャーネオ": "Sloshing_Machine_Neo",
    "スクリュースロッシャーベッチュー": "Kensa_Sloshing_Machine",
    "オーバーフロッシャー": "Bloblobber",
    "オーバーフロッシャーデコ": "Bloblobber_Deco",
    "エクスプロッシャー": "Explosher",
    "エクスプロッシャーカスタム": "Custom_Explosher",
    "モップリン": "Dread_Wringer",
    "モップリンD": "Dread_Wringer_D",
    "オーダースロッシャーレプリカ": "Order_Slosher_Replica",
    "スプラスピナー": "Mini_Splatling",
    "スプラスピナーコラボ": "Zink_Mini_Splatling",
    "スプラスピナーベッチュー": "Kensa_Mini_Splatling",
    "バレルスピナー": "Heavy_Splatling",
    "バレルスピナーデコ": "Heavy_Splatling_Deco",
    "バレルスピナーリミックス": "Heavy_Splatling_Remix",
    "ハイドラント": "Hydra_Splatling",
    "ハイドラントカスタム": "Custom_Hydra_Splatling",
    "クーゲルシュライバー": "Ballpoint_Splatling",
    "クーゲルシュライバー・ヒュー": "Ballpoint_Splatling_Nouveau",
    "ノーチラス47": "Nautilus_47",
    "ノーチラス79": "Nautilus_79",
    "イグザミナー": "Heavy_Edit_Splatling",
    "イグザミナーヒュー": "Heavy_Edit_Splatling_Nouveau",
    "オーダースピナーレプリカ": "Order_Splatling_Replica",
    "パラシェルター": "Splat_Brella",
    "パラシェルターソレーラ": "Sorella_Brella",
    "スパイガジェット": "Undercover_Brella",
    "スパイガジェットソレーラ": "Undercover_Sorella_Brella",
    "キャンピングシェルター": "Tenta_Brella",
    "キャンピングシェルターソレーラ": "Tenta_Sorella_Brella",
    "キャンピングシェルターカーモ": "Tenta_Camo_Brella",
    "24式張替傘・甲": "Recycled_Brella_24_Mk_I",
    "24式張替傘・乙": "Recycled_Brella_24_Mk_II",
    "オーダーシェルターレプリカ": "Order_Brella_Replica",
    "ドライブワイパー": "Splatana_Wiper",
    "ドライブワイパーデコ": "Splatana_Wiper_Deco",
    "ジムワイパー": "Splatana_Stamper",
    "ジムワイパー・ヒュー": "Splatana_Stamper_Nouveau",
    "ジムワイパーベッチュー": "Kensa_Splatana_Stamper",
    "デンタルワイパーミント": "Mint_Decavitator",
    "デンタルワイパースミ": "Charcoal_Decavitator",
    "オーダーワイパーレプリカ": "Order_Wiper_Replica",
    "オーダーマニューバーレプリカ": "Order_Dualie_Replica",
    "フルイドV": "Reef-Lux_450",
    "フルイドVカスタム": "Reef-Lux_450_Deco",
}

# ─── ルール名マッピング ──────────
RULE_ICON_MAP = {
    "ナワバリバトル": ("Mode_Icon_Turf_War.png", "turf-war"),
    "ガチエリア": ("S3_icon_Splat_Zones.png", "splat-zones"),
    "ガチヤグラ": ("S3_icon_Tower_Control.png", "tower-control"),
    "ガチホコバトル": ("S3_icon_Rainmaker.png", "rainmaker"),
    "ガチホコ": ("S3_icon_Rainmaker.png", "rainmaker"),
    "ガチアサリ": ("S3_icon_Clam_Blitz.png", "clam-blitz"),
}


def api_get_image_urls(prefix):
    """Inkipedia APIで画像URLを取得"""
    results = {}
    cont = ""
    while True:
        url = f"https://splatoonwiki.org/w/api.php?action=query&list=allimages&aiprefix={prefix}&ailimit=500&format=json"
        if cont:
            url += f"&aicontinue={cont}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read())
        for img in data.get("query", {}).get("allimages", []):
            results[img["name"]] = img["url"]
        if "continue" in data:
            cont = data["continue"]["aicontinue"]
        else:
            break
    return results


def download_image(url, save_path, resize=None):
    """画像をダウンロードして保存。resizeが指定されていればリサイズ"""
    if save_path.exists() and save_path.stat().st_size > 100:
        return False  # 既にダウンロード済み

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        data = urllib.request.urlopen(req, timeout=30).read()

        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(data)

        if resize:
            img = Image.open(save_path)
            img = img.resize(resize, Image.LANCZOS)
            img.save(save_path)

        time.sleep(DOWNLOAD_DELAY)
        return True
    except Exception as e:
        print(f"  ✗ DLエラー: {url[:60]} → {e}")
        return False


def download_stages(api_images):
    """ステージ画像をダウンロード"""
    print("\n=== ステージ画像 ===")
    stage_dir = STATIC_IMG / "stages"
    stage_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for ja_name, en_name in STAGE_NAME_MAP.items():
        # .png を優先、なければ .jpg
        fname_png = f"S3_Stage_{en_name}.png"
        fname_jpg = f"S3_Stage_{en_name}.jpg"

        url = api_images.get(fname_png) or api_images.get(fname_jpg)
        if not url:
            # URL エンコード版で検索
            for k, v in api_images.items():
                if en_name.replace("%27", "'").replace("%26", "&") in k and k.startswith("S3_Stage_"):
                    if "Map" not in k:
                        url = v
                        break

        if not url:
            print(f"  ✗ 見つからない: {ja_name} ({en_name})")
            continue

        # ローカルファイル名（既存のslug形式に合わせる）
        local_name = en_name.replace("%27", "").replace("%26", "and").replace(".", "").replace("'", "").lower().replace("_", "-") + ".png"
        save_path = stage_dir / local_name

        if download_image(url, save_path):
            print(f"  ✓ {ja_name} → {local_name}")
            count += 1
        else:
            if save_path.exists():
                print(f"  - {ja_name} (既存)")
            else:
                print(f"  ✗ {ja_name} DL失敗")

    print(f"  ステージ: {count}件ダウンロード")
    return count


def download_weapons(api_images):
    """武器ヒーロー画像をダウンロード"""
    print("\n=== 武器ヒーロー画像 ===")
    weapon_dir = STATIC_IMG / "weapons"
    weapon_dir.mkdir(parents=True, exist_ok=True)

    # マスターデータから全武器名を取得
    parsed_dir = PROJECT_ROOT / "０００１スプラトゥーン３" / "parsed_data"
    if not parsed_dir.exists():
        parsed_dir = PROJECT_ROOT / "００００１スプラトゥーン３" / "parsed_data"

    count = 0
    not_found = []

    for ja_name, en_name in WEAPON_NAME_MAP.items():
        # 3D版を探す
        clean_en = en_name.replace("%27", "'").replace("%2C", ",")
        fname = f"S3_Weapon_Main_{clean_en}.png"

        url = api_images.get(fname)
        if not url:
            # URLエンコード版で試行
            for k, v in api_images.items():
                k_clean = k.replace("S3_Weapon_Main_", "").replace(".png", "")
                if k_clean == clean_en and "2D" not in k:
                    url = v
                    break

        if not url:
            not_found.append(ja_name)
            continue

        # hero画像として保存（大きいサイズ）
        local_name = en_name.replace("%27", "").replace("%2C", "").replace(".", "").replace("'", "").lower().replace("_", "-") + "-hero.png"
        save_path = weapon_dir / local_name

        if download_image(url, save_path):
            print(f"  ✓ {ja_name} → {local_name}")
            count += 1
        else:
            if save_path.exists():
                pass  # 既存、ログ不要

    if not_found:
        print(f"  見つからない武器: {len(not_found)}件")
        for n in not_found[:10]:
            print(f"    - {n}")

    print(f"  武器ヒーロー: {count}件ダウンロード")
    return count


def download_rules(api_images):
    """ルールアイコン（大サイズ版）をダウンロード"""
    print("\n=== ルール画像（ナビ用大サイズ） ===")
    rule_dir = STATIC_IMG / "rules"
    rule_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for ja_name, (ink_fname, local_base) in RULE_ICON_MAP.items():
        url = api_images.get(ink_fname)
        if not url:
            print(f"  ✗ 見つからない: {ja_name} ({ink_fname})")
            continue

        # ナビ用大サイズ版として保存
        save_path = rule_dir / f"{local_base}-large.png"

        if download_image(url, save_path):
            print(f"  ✓ {ja_name} → {local_base}-large.png")
            count += 1
        else:
            if save_path.exists():
                print(f"  - {ja_name} (既存)")

    print(f"  ルール大サイズ: {count}件ダウンロード")
    return count


def main():
    print("=== Inkipedia画像ダウンロード開始 ===")

    # API から全画像URLを取得
    print("\nAPI問い合わせ中...")
    stage_imgs = api_get_image_urls("S3_Stage_")
    print(f"  ステージ画像: {len(stage_imgs)}件")

    weapon_imgs = api_get_image_urls("S3_Weapon_Main_")
    print(f"  武器画像: {len(weapon_imgs)}件")

    rule_imgs = {}
    for prefix in ["S3_icon_", "Mode_Icon_"]:
        rule_imgs.update(api_get_image_urls(prefix))
    print(f"  ルール/モードアイコン: {len(rule_imgs)}件")

    all_imgs = {**stage_imgs, **weapon_imgs, **rule_imgs}

    # ダウンロード実行
    total = 0
    total += download_stages(all_imgs)
    total += download_weapons(all_imgs)
    total += download_rules(all_imgs)

    print(f"\n=== 完了: 合計 {total}件ダウンロード ===")


if __name__ == "__main__":
    main()
