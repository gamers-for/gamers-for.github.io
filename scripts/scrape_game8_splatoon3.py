#!/usr/bin/env python3
"""
Game8のスプラトゥーン3攻略ページをスクレイプするスクリプト
保存先: ００００１スプラトゥーン３/raw_html/
"""

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "００００１スプラトゥーン３", "raw_html")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}

# リクエスト間隔（秒）
DELAY = 1.5

# ========== URLリスト ==========

# メインページ
MAIN_PAGES = {
    "top": "https://game8.jp/splatoon3",
    "tier_list": "https://game8.jp/splatoon3/477903",
    "tier_nawabari": "https://game8.jp/splatoon3/480285",
    "tier_area": "https://game8.jp/splatoon3/480159",
    "tier_yagura": "https://game8.jp/splatoon3/480157",
    "tier_hoko": "https://game8.jp/splatoon3/480158",
    "tier_asari": "https://game8.jp/splatoon3/480156",
    "stage_list": "https://game8.jp/splatoon3/477902",
    "gear_power_ranking": "https://game8.jp/splatoon3/480277",
    "gear_power_list": "https://game8.jp/splatoon3/477901",
    "gear_list": "https://game8.jp/splatoon3/477900",
    "salmon_run": "https://game8.jp/splatoon3/480290",
    "bankara_match": "https://game8.jp/splatoon3/477905",
    "beginner_guide": "https://game8.jp/splatoon3/478654",
    "beginner_weapons": "https://game8.jp/splatoon3/480302",
}

# 武器種一覧ページ
WEAPON_CLASS_PAGES = {
    "shooter": "https://game8.jp/splatoon3/478524",
    "blaster": "https://game8.jp/splatoon3/478542",
    "roller": "https://game8.jp/splatoon3/478548",
    "charger": "https://game8.jp/splatoon3/478547",
    "slosher": "https://game8.jp/splatoon3/478546",
    "spinner": "https://game8.jp/splatoon3/478545",
    "maneuver": "https://game8.jp/splatoon3/478544",
    "shelter": "https://game8.jp/splatoon3/478543",
    # フデ・ストリンガー・ワイパーはトップから自動取得
}

# ステージ個別ページ
STAGE_PAGES = {
    "ユノハナ大渓谷": "https://game8.jp/splatoon3/479885",
    "ゴンズイ地区": "https://game8.jp/splatoon3/479884",
    "ヤガラ市場": "https://game8.jp/splatoon3/479883",
    "マテガイ放水路": "https://game8.jp/splatoon3/479882",
    "ナメロウ金属": "https://game8.jp/splatoon3/479881",
    "マサバ海峡大橋": "https://game8.jp/splatoon3/479880",
    "キンメダイ美術館": "https://game8.jp/splatoon3/480321",
    "マヒマヒリゾート": "https://game8.jp/splatoon3/480320",
    "海女美術大学": "https://game8.jp/splatoon3/479879",
    "チョウザメ造船": "https://game8.jp/splatoon3/480319",
    "ザトウマーケット": "https://game8.jp/splatoon3/480318",
    "スメーシーワールド": "https://game8.jp/splatoon3/479878",
    "クサヤ温泉": "https://game8.jp/splatoon3/495231",
    "ヒラメが丘団地": "https://game8.jp/splatoon3/494954",
    "ナンプラー遺跡": "https://game8.jp/splatoon3/513004",
    "マンタマリア号": "https://game8.jp/splatoon3/512954",
    "タラポートショッピングパーク": "https://game8.jp/splatoon3/528154",
    "コンブトラック": "https://game8.jp/splatoon3/528179",
    "タカアシ経済特区": "https://game8.jp/splatoon3/546890",
    "オヒョウ海運": "https://game8.jp/splatoon3/546907",
    "バイガイ亭": "https://game8.jp/splatoon3/579105",
    "ネギトロ炭鉱": "https://game8.jp/splatoon3/579110",
    "カジキ空港": "https://game8.jp/splatoon3/594641",
    "リュウグウターミナル": "https://game8.jp/splatoon3/610305",
    "デカライン高架下": "https://game8.jp/splatoon3/697757",
}

# サーモンランステージ
SR_STAGE_PAGES = {
    "アラマキ砦": "https://game8.jp/splatoon3/481306",
    "ムニ・エール海洋発電所": "https://game8.jp/splatoon3/481314",
    "シェケナダム": "https://game8.jp/splatoon3/481312",
    "難破船ドン・ブラコ": "https://game8.jp/splatoon3/500815",
    "すじこジャンクション跡": "https://game8.jp/splatoon3/528390",
}

# 既知の武器個別ページURL（WebFetchで確認済み）
KNOWN_WEAPON_PAGES = {
    # シューター
    "わかばシューター": "478553", "スプラシューター": "478552", "プロモデラーMG": "478557",
    "N-ZAP85": "478558", "もみじシューター": "500143", "スペースシューター": "494975",
    "ボールドマーカー": "480118", "プライムシューター": "478556",
    "スプラシューターコラボ": "497691", "52ガロン": "478555",
    "N-ZAP89": "512887", "ボールドマーカーネオ": "512890",
    "52ガロンデコ": "594482", "ジェットスイーパー": "480104",
    "シャープマーカー": "480105", "96ガロン": "480117",
    "プロモデラーRG": "499242", "ボトルガイザー": "480115",
    "L3リールガンD": "512886", "L3リールガン": "480109",
    "96ガロンデコ": "512873", "プライムシューターコラボ": "498918",
    "シャープマーカーネオ": "512888", "ボトルガイザーフォイル": "576999",
    "H3リールガン": "480113", "H3リールガンD": "529151",
    "ジェットスイーパーカスタム": "512896",
    "オーダーシューターレプリカ": "595554", "オクタシューターレプリカ": "595569",
    "ヒーローシューターレプリカ": "480411",
    # ブラスター
    "ホットブラスター": "478575", "ラピッドブラスター": "480100",
    "ホットブラスターカスタム": "577060", "ラピッドブラスターデコ": "512895",
    "ロングブラスター": "480107", "ノヴァブラスター": "478574",
    "ロングブラスターカスタム": "609978", "S-BLAST92": "528247",
    "クラッシュブラスター": "480099", "ノヴァブラスターネオ": "499130",
    "クラッシュブラスターネオ": "512891", "Rブラスターエリート": "480102",
    "S-BLAST91": "577059", "Rブラスターエリートデコ": "529153",
    "オーダーブラスターレプリカ": "595564",
    # ローラー
    "スプラローラー": "478576", "カーボンローラー": "480111",
    "スプラローラーコラボ": "512871", "ダイナモローラー": "478565",
    "ワイドローラー": "497116", "ダイナモローラーテスラ": "546820",
    "ワイドローラーコラボ": "529816", "ヴァリアブルローラー": "480123",
    "カーボンローラーデコ": "500259", "ヴァリアブルローラーフォイル": "594559",
    "オーダーローラーレプリカ": "595555",
    # チャージャー
    "スプラチャージャー": "478572", "スクイックリンα": "480106",
    "スプラチャージャーコラボ": "512892", "スプラスコープ": "478573",
    "スクイックリンβ": "594553", "R-PEN/5H": "497089",
    "スプラスコープコラボ": "512894", "リッター4K": "478559",
    "R-PEN/5B": "577259", "リッター4Kカスタム": "594566",
    "14式竹筒銃・甲": "480112", "ソイチューバー": "480110",
    "14式竹筒銃・乙": "610072", "4Kスコープ": "478560",
    "ソイチューバーカスタム": "546706", "4Kスコープカスタム": "594576",
    "オーダーチャージャーレプリカ": "595557",
    # スロッシャー
    "バケットスロッシャー": "478571", "ヒッセン": "478570",
    "バケットスロッシャーデコ": "499248", "スクリュースロッシャー": "480103",
    "モップリン": "546627", "ヒッセンヒュー": "512885",
    "モップリンD": "594556", "オーバーフロッシャー": "480098",
    "スクリュースロッシャーネオ": "546843", "オーバーフロッシャーデコ": "546840",
    "エクスプロッシャー": "480119", "エクスプロッシャーカスタム": "594492",
    "オーダースロッシャーレプリカ": "595563",
    # スピナー
    "バレルスピナー": "478569", "スプラスピナー": "480101",
    "イグザミナー": "546628", "バレルスピナーデコ": "529815",
    "イグザミナーヒュー": "609973", "ハイドラント": "478568",
    "ハイドラントカスタム": "610071", "スプラスピナーコラボ": "497797",
    "ノーチラス47": "480108", "ノーチラス79": "595105",
    "クーゲルシュライバー": "480114", "クーゲルシュライバーヒュー": "546842",
    "オーダースピナーレプリカ": "595567",
    # マニューバー
    "スプラマニューバー": "478563", "デュアルスイーパー": "480122",
    "スプラマニューバーコラボ": "576984", "スパッタリー": "480120",
    "ケルビン525": "480121", "クアッドホッパーブラック": "478564",
    "クアッドホッパーホワイト": "529277", "デュアルスイーパーカスタム": "529813",
    "スパッタリーヒュー": "499219", "ケルビン525デコ": "595106",
    "ガエンFF": "594466", "ガエンFFカスタム": "609974",
    "オーダーマニューバーレプリカ": "595547",
    # シェルター
    "パラシェルター": "478549", "24式張替傘・甲": "594463",
    "キャンピングシェルター": "478550", "スパイガジェット": "480116",
    "パラシェルターソレーラ": "546822", "24式張替傘・乙": "609975",
    "キャンピングシェルターソレーラ": "529279", "スパイガジェットソレーラ": "577064",
    "オーダーシェルターレプリカ": "595553",
    # ストリンガー
    "トライストリンガー": "478566", "LACT-450": "480097",
    "トライストリンガーコラボ": "512870", "LACT-450デコ": "595107",
    "フルイドV": "594462", "フルイドVカスタム": "609972",
    "オーダーストリンガーレプリカ": "595558",
    # ワイパー
    "ジムワイパー": "480124", "ドライブワイパー": "478567",
    "ジムワイパーヒュー": "577014", "ドライブワイパーデコ": "499122",
    "デンタルワイパーミント": "609971", "デンタルワイパースミ": "529152",
    "オーダーワイパーレプリカ": "595565",
    # フデ
    "パブロ": "478561", "ホクサイ": "478562",
    "パブロ・ヒュー": "512889", "ホクサイ・ヒュー": "529278",
    "フィンセント": "594458", "フィンセントヒュー": "609976",
    "オーダーフデレプリカ": "595566",
}


def fetch_page(url, name=""):
    """ページ取得 → HTML保存"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ✗ エラー ({name}): {e}")
        return None


def save_html(html, filename):
    """HTMLをファイルに保存"""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def extract_weapon_links(html):
    """ページ内から武器個別ページのリンクを抽出"""
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.match(r"^/splatoon3/\d+$", href) or re.match(r"^https://game8\.jp/splatoon3/\d+$", href):
            full_url = urljoin("https://game8.jp", href)
            links.add(full_url)
    return links


def main():
    fetched = 0
    total_pages = (
        len(MAIN_PAGES)
        + len(WEAPON_CLASS_PAGES)
        + len(STAGE_PAGES)
        + len(SR_STAGE_PAGES)
        + len(KNOWN_WEAPON_PAGES)
    )
    print(f"=== Game8 スプラ3 スクレイプ開始 ===")
    print(f"予定ページ数: ~{total_pages}")

    # 1. メインページ
    print("\n--- メインページ ---")
    for name, url in MAIN_PAGES.items():
        print(f"  取得中: {name} ({url})")
        html = fetch_page(url, name)
        if html:
            save_html(html, f"main_{name}.html")
            fetched += 1
        time.sleep(DELAY)

    # 2. 武器種一覧ページ
    print("\n--- 武器種一覧ページ ---")
    for name, url in WEAPON_CLASS_PAGES.items():
        print(f"  取得中: {name} ({url})")
        html = fetch_page(url, name)
        if html:
            save_html(html, f"weapon_class_{name}.html")
            fetched += 1
        time.sleep(DELAY)

    # 3. 武器個別ページ
    print(f"\n--- 武器個別ページ ({len(KNOWN_WEAPON_PAGES)}件) ---")
    for weapon_name, page_id in KNOWN_WEAPON_PAGES.items():
        url = f"https://game8.jp/splatoon3/{page_id}"
        safe_name = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー・]', '_', weapon_name)
        print(f"  取得中: {weapon_name} ({url})")
        html = fetch_page(url, weapon_name)
        if html:
            save_html(html, f"weapon_{safe_name}_{page_id}.html")
            fetched += 1
        time.sleep(DELAY)

    # 4. ステージ個別ページ
    print(f"\n--- ステージ個別ページ ({len(STAGE_PAGES)}件) ---")
    for stage_name, url in STAGE_PAGES.items():
        safe_name = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー・]', '_', stage_name)
        print(f"  取得中: {stage_name} ({url})")
        html = fetch_page(url, stage_name)
        if html:
            save_html(html, f"stage_{safe_name}.html")
            fetched += 1
        time.sleep(DELAY)

    # 5. サーモンランステージ
    print(f"\n--- サーモンランステージ ({len(SR_STAGE_PAGES)}件) ---")
    for stage_name, url in SR_STAGE_PAGES.items():
        safe_name = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー・]', '_', stage_name)
        print(f"  取得中: {stage_name} ({url})")
        html = fetch_page(url, stage_name)
        if html:
            save_html(html, f"sr_stage_{safe_name}.html")
            fetched += 1
        time.sleep(DELAY)

    # 結果サマリ
    print(f"\n=== スクレイプ完了 ===")
    print(f"取得: {fetched}ページ")
    print(f"保存先: {OUTPUT_DIR}")

    # URL一覧をJSONで保存
    url_map = {}
    url_map["main"] = MAIN_PAGES
    url_map["weapon_class"] = WEAPON_CLASS_PAGES
    url_map["stages"] = STAGE_PAGES
    url_map["sr_stages"] = SR_STAGE_PAGES
    url_map["weapons"] = {
        name: f"https://game8.jp/splatoon3/{pid}"
        for name, pid in KNOWN_WEAPON_PAGES.items()
    }

    with open(os.path.join(OUTPUT_DIR, "_url_map.json"), "w", encoding="utf-8") as f:
        json.dump(url_map, f, ensure_ascii=False, indent=2)
    print(f"URLマップ保存: _url_map.json")


if __name__ == "__main__":
    main()
