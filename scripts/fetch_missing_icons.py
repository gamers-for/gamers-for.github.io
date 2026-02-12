#!/usr/bin/env python3
"""
不足アイコンをInkipediaからダウンロード
- 新サブウェポン: トラップ、ラインマーカー、ロボットボム
- 新スペシャル: ウルトラチャクチ、キューインキ、スミナガシート
- 新メイン武器: バリアント含む53武器
"""

import requests
import os
import time
import json
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEAPONS_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "weapons")
SUBS_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "subs")
SPECIALS_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3", "specials")
API_URL = "https://splatoonwiki.org/w/api.php"


def download_from_inkipedia(wiki_filename, save_path):
    """InkipediaのAPIからアイコンをダウンロード"""
    if os.path.exists(save_path) and os.path.getsize(save_path) > 100:
        print(f"  [skip] {os.path.basename(save_path)} already exists")
        return True

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
        print(f"  [FAIL] {wiki_filename} not found on Inkipedia")
        return False
    except Exception as e:
        print(f"  [ERROR] {wiki_filename}: {e}")
        return False


def copy_variant_icon(base_slug, variant_slug, target_dir):
    """バリアント武器: ベース武器のアイコンをコピー"""
    src = os.path.join(target_dir, f"{base_slug}.png")
    dst = os.path.join(target_dir, f"{variant_slug}.png")
    if os.path.exists(dst) and os.path.getsize(dst) > 100:
        print(f"  [skip] {variant_slug}.png already exists")
        return True
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  [copy] {variant_slug}.png <- {base_slug}.png")
        return True
    else:
        print(f"  [FAIL] base icon {base_slug}.png not found")
        return False


def main():
    os.makedirs(WEAPONS_DIR, exist_ok=True)
    os.makedirs(SUBS_DIR, exist_ok=True)
    os.makedirs(SPECIALS_DIR, exist_ok=True)

    # ============================================
    # 1. 不足サブウェポン (3個)
    # ============================================
    print("=== サブウェポンアイコン ===")
    missing_subs = [
        ("Ink Mine", "ink-mine", "S3 Weapon Sub Ink Mine Flat.png"),
        ("Angle Shooter", "line-marker", "S3 Weapon Sub Angle Shooter Flat.png"),
        ("Autobomb", "autobomb", "S3 Weapon Sub Autobomb Flat.png"),
    ]
    for en_name, slug, wiki_file in missing_subs:
        save_path = os.path.join(SUBS_DIR, f"{slug}.png")
        download_from_inkipedia(wiki_file, save_path)
        time.sleep(0.5)

    # ============================================
    # 2. 不足スペシャル (3個)
    # ============================================
    print("\n=== スペシャルウェポンアイコン ===")
    missing_specials = [
        ("Ultra Stamp", "ultra-stamp", "S3 Weapon Special Ultra Stamp.png"),
        ("Ink Vac", "ink-vac", "S3 Weapon Special Ink Vac.png"),
        ("Splattercolor Screen", "splattercolor-screen", "S3 Weapon Special Splattercolor Screen.png"),
    ]
    for en_name, slug, wiki_file in missing_specials:
        save_path = os.path.join(SPECIALS_DIR, f"{slug}.png")
        download_from_inkipedia(wiki_file, save_path)
        time.sleep(0.5)

    # ============================================
    # 3. 新武器のメインアイコン (Inkipediaからダウンロード)
    # ============================================
    print("\n=== 新武器メインアイコン ===")
    new_weapons = [
        # Blasters
        ("Range Blaster", "range-blaster", "S3 Weapon Main Range Blaster.png"),
        ("Custom Range Blaster", "custom-range-blaster", "S3 Weapon Main Custom Range Blaster.png"),
        ("S-BLAST '91", "s-blast-91", "S3 Weapon Main S-BLAST '91.png"),
        ("S-BLAST '92", "s-blast-92", "S3 Weapon Main S-BLAST '92.png"),
        # Brushes
        ("Painbrush", "painbrush", "S3 Weapon Main Painbrush.png"),
        ("Inkbrush Nouveau", "inkbrush-nouveau", "S3 Weapon Main Inkbrush Nouveau.png"),
        ("Octobrush Nouveau", "octobrush-nouveau", "S3 Weapon Main Octobrush Nouveau.png"),
        ("Painbrush Nouveau", "painbrush-nouveau", "S3 Weapon Main Painbrush Nouveau.png"),
        # Chargers
        ("Custom E-liter 4K", "custom-e-liter-4k", "S3 Weapon Main Custom E-liter 4K.png"),
        ("Custom E-liter 4K Scope", "custom-e-liter-4k-scope", "S3 Weapon Main Custom E-liter 4K Scope.png"),
        # Sloshers
        ("Tri-Slosher Nouveau", "tri-slosher-nouveau", "S3 Weapon Main Tri-Slosher Nouveau.png"),
        # Spinners
        ("Ballpoint Splatling Nouveau", "ballpoint-splatling-nouveau", "S3 Weapon Main Ballpoint Splatling Nouveau.png"),
        ("Heavy Edit Splatling Nouveau", "heavy-edit-splatling-nouveau", "S3 Weapon Main Heavy Edit Splatling Nouveau.png"),
        # Dualies
        ("Dapple Dualies Nouveau", "dapple-dualies-nouveau", "S3 Weapon Main Dapple Dualies Nouveau.png"),
        # Stringers
        ("REEF-LUX 450", "reef-lux-450", "S3 Weapon Main REEF-LUX 450.png"),
        ("REEF-LUX 450 Deco", "reef-lux-450-deco", "S3 Weapon Main REEF-LUX 450 Deco.png"),
        # Wipers
        ("Splatana Wiper Deco", "splatana-wiper-deco", "S3 Weapon Main Splatana Wiper Deco.png"),
        ("Mint Decavitator", "mint-decavitator", "S3 Weapon Main Mint Decavitator.png"),
        ("Charcoal Decavitator", "charcoal-decavitator", "S3 Weapon Main Charcoal Decavitator.png"),
        # Shooters
        ("Douser Dualies FF", "douser-dualies-ff", "S3 Weapon Main Douser Dualies FF.png"),
        ("Custom Douser Dualies FF", "custom-douser-dualies-ff", "S3 Weapon Main Custom Douser Dualies FF.png"),
    ]
    for en_name, slug, wiki_file in new_weapons:
        save_path = os.path.join(WEAPONS_DIR, f"{slug}.png")
        download_from_inkipedia(wiki_file, save_path)
        time.sleep(0.5)

    # ============================================
    # 4. バリアント武器 (ベース武器のアイコンをコピー)
    # バンカラコレクション等のバリアントは見た目はベース武器と同じ
    # ============================================
    print("\n=== バリアント武器アイコン (コピー) ===")
    variants = [
        # (base_slug, variant_slug)
        # コレクション武器（漢字・英字サフィックス）
        ("splattershot", "splattershot-kira"),          # スプラシューター煌
        ("blaster", "blaster-tsuya"),                    # ホットブラスター艶
        ("aerospray-mg", "aerospray-iro"),               # プロモデラー彩
        ("96-gal", "96-gal-tsume"),                      # .96ガロン爪
        ("sloshing-machine", "sloshing-machine-kaku"),   # モップリン角
        ("dualie-squelchers", "dualie-squelchers-hizume"),  # デュアルスイーパー蹄
        ("splatana-wiper", "splatana-wiper-fu"),          # ジムワイパー封
        ("hydra-splatling", "hydra-splatling-atsu"),      # ハイドラント圧
        ("undercover-brella", "undercover-brella-ryou"),  # スパイガジェット繚
        ("splat-dualies", "splat-dualies-you"),           # スプラマニューバー耀
        ("big-swig-roller", "big-swig-roller-waku"),      # ワイドローラー惑
        ("l-3-nozzlenose", "l-3-nozzlenose-haku"),        # L3リールガン箔
        ("octobrush", "octobrush-sui"),                   # ホクサイ彗
        ("tri-stringer", "tri-stringer-tou"),             # トライストリンガー燈
        ("dynamo-roller", "dynamo-roller-mei"),            # ダイナモローラー冥
        ("splat-brella", "splat-brella-maku"),            # パラシェルター幕
        # ヒュー/GECK/OWL等のバリアント
        ("splash-o-matic", "splash-o-matic-geck"),       # シャープマーカーGECK
        ("carbon-roller", "carbon-roller-angl"),          # カーボンローラーANGL
        ("dapple-dualies", "dapple-dualies-owl"),        # スパッタリーOWL
        ("tri-slosher", "tri-slosher-ash"),               # ヒッセンASH
        ("splatana-stamper", "splatana-stamper-rust"),    # ドライブワイパーRUST
        ("splattershot-pro", "splattershot-pro-frzn"),    # プライムシューターFRZN
        ("splat-charger", "splat-charger-frst"),          # スプラチャージャーFRST
        ("splatterscope", "splatterscope-frst"),          # スプラスコープFRST
        ("range-blaster", "range-blaster-wntr"),          # RブラスターエリートWNTR
        ("jet-squelcher", "jet-squelcher-cobr"),          # ジェットスイーパーCOBR
        ("mini-splatling", "mini-splatling-pytn"),        # スプラスピナーPYTN
        ("h-3-nozzlenose", "h-3-nozzlenose-snak"),       # H3リールガンSNAK
        ("tri-stringer", "tri-stringer-milk"),            # LACT-450MILK → ストリンガー系
        ("tenta-brella", "tenta-brella-crem"),            # キャンピングシェルターCREM
        ("heavy-splatling", "heavy-splatling-rose"),      # バレルスピナーROSE
        ("painbrush", "painbrush-brnz"),                  # フィンセントBRNZ
    ]
    for base_slug, variant_slug in variants:
        copy_variant_icon(base_slug, variant_slug, WEAPONS_DIR)

    # ============================================
    # 統計
    # ============================================
    print("\n=== 統計 ===")
    weapon_count = len([f for f in os.listdir(WEAPONS_DIR) if f.endswith('.png') and os.path.getsize(os.path.join(WEAPONS_DIR, f)) > 100])
    sub_count = len([f for f in os.listdir(SUBS_DIR) if f.endswith('.png') and os.path.getsize(os.path.join(SUBS_DIR, f)) > 100])
    sp_count = len([f for f in os.listdir(SPECIALS_DIR) if f.endswith('.png') and os.path.getsize(os.path.join(SPECIALS_DIR, f)) > 100])
    print(f"メイン武器アイコン: {weapon_count}")
    print(f"サブウェポンアイコン: {sub_count}")
    print(f"スペシャルアイコン: {sp_count}")

    # マスターJSONのicon情報を更新
    update_master_json()


def update_master_json():
    """マスターJSONのアイコンパスを更新"""
    master_path = os.path.join(BASE_DIR, "data", "splatoon3_master.json")
    with open(master_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 新しいサブ/SPアイコンマッピング
    new_sub_map = {
        "トラップ": "/images/games/splatoon3/subs/ink-mine.png",
        "ラインマーカー": "/images/games/splatoon3/subs/line-marker.png",
        "ロボットボム": "/images/games/splatoon3/subs/autobomb.png",
    }
    new_sp_map = {
        "ウルトラチャクチ": "/images/games/splatoon3/specials/ultra-stamp.png",
        "キューインキ": "/images/games/splatoon3/specials/ink-vac.png",
        "スミナガシート": "/images/games/splatoon3/specials/splattercolor-screen.png",
    }

    # 新武器のアイコンマッピング (日本語名→slugファイル名)
    new_weapon_map = {
        "Rブラスターエリート": "range-blaster",
        "Rブラスターエリートデコ": "custom-range-blaster",
        "S-BLAST91": "s-blast-91",
        "S-BLAST92": "s-blast-92",
        "フィンセント": "painbrush",
        "パブロヒュー": "inkbrush-nouveau",
        "ホクサイヒュー": "octobrush-nouveau",
        "フィンセントヒュー": "painbrush-nouveau",
        "リッター4Kカスタム": "custom-e-liter-4k",
        "4Kスコープカスタム": "custom-e-liter-4k-scope",
        "ヒッセンヒュー": "tri-slosher-nouveau",
        "クーゲルシュライバーヒュー": "ballpoint-splatling-nouveau",
        "イグザミナーヒュー": "heavy-edit-splatling-nouveau",
        "スパッタリーヒュー": "dapple-dualies-nouveau",
        "フルイドV": "reef-lux-450",
        "フルイドVカスタム": "reef-lux-450-deco",
        "ジムワイパーヒュー": "splatana-wiper-deco",
        "デンタルワイパーミント": "mint-decavitator",
        "デンタルワイパースミ": "charcoal-decavitator",
        "R-PEN/5H": "douser-dualies-ff",
        "R-PEN/5B": "custom-douser-dualies-ff",
        # バリアント
        "シャープマーカーGECK": "splash-o-matic-geck",
        "カーボンローラーANGL": "carbon-roller-angl",
        "スパッタリーOWL": "dapple-dualies-owl",
        "フィンセントBRNZ": "painbrush-brnz",
        "ヒッセンASH": "tri-slosher-ash",
        "ドライブワイパーRUST": "splatana-stamper-rust",
        "プライムシューターFRZN": "splattershot-pro-frzn",
        "スプラチャージャーFRST": "splat-charger-frst",
        "スプラスコープFRST": "splatterscope-frst",
        "RブラスターエリートWNTR": "range-blaster-wntr",
        "ジェットスイーパーCOBR": "jet-squelcher-cobr",
        "スプラスピナーPYTN": "mini-splatling-pytn",
        "H3リールガンSNAK": "h-3-nozzlenose-snak",
        "LACT-450MILK": "tri-stringer-milk",
        "キャンピングシェルターCREM": "tenta-brella-crem",
        "バレルスピナーROSE": "heavy-splatling-rose",
        "スプラシューター煌": "splattershot-kira",
        "ホットブラスター艶": "blaster-tsuya",
        "プロモデラー彩": "aerospray-iro",
        ".96ガロン爪": "96-gal-tsume",
        "モップリン角": "sloshing-machine-kaku",
        "デュアルスイーパー蹄": "dualie-squelchers-hizume",
        "ジムワイパー封": "splatana-wiper-fu",
        "ハイドラント圧": "hydra-splatling-atsu",
        "スパイガジェット繚": "undercover-brella-ryou",
        "スプラマニューバー耀": "splat-dualies-you",
        "ワイドローラー惑": "big-swig-roller-waku",
        "L3リールガン箔": "l-3-nozzlenose-haku",
        "ホクサイ彗": "octobrush-sui",
        "トライストリンガー燈": "tri-stringer-tou",
        "ダイナモローラー冥": "dynamo-roller-mei",
        "パラシェルター幕": "splat-brella-maku",
    }

    updated = 0
    for w in data["weapons"]:
        # サブアイコン更新
        if not w.get("sub_icon") and w["sub"] in new_sub_map:
            w["sub_icon"] = new_sub_map[w["sub"]]
            updated += 1
        # SPアイコン更新
        if not w.get("special_icon") and w["special"] in new_sp_map:
            w["special_icon"] = new_sp_map[w["special"]]
            updated += 1
        # メインアイコン更新
        if not w.get("icon") and w["name"] in new_weapon_map:
            slug = new_weapon_map[w["name"]]
            icon_path = f"/images/games/splatoon3/weapons/{slug}.png"
            w["icon"] = icon_path
            updated += 1

    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nマスターJSON更新: {updated}箇所")


if __name__ == "__main__":
    main()
