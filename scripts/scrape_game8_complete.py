#!/usr/bin/env python3
"""
Game8 完全スクレイピングスクリプト
手順書: ０００００テンプレ/０１もれなくスクレイピング.md に準拠

Phase 0: sitemap.xml.gz → 対象ゲームのURL抽出
Phase 1: BFSクロール + ダウンロード（sitemap URLs を初期キューに）
Phase 2: 4種の完了検証
Phase 3: 補完（漏れがあれば追加取得）
Phase 4: メタデータ保存
"""

import os
import re
import sys
import gzip
import json
import time
import random
import hashlib
from collections import deque
from datetime import datetime
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# ========== 設定 ==========

GAME_SLUG = sys.argv[1] if len(sys.argv) > 1 else "splatoon3"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "００００１スプラトゥーン３", "raw_html")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://game8.jp/",
})
TIMEOUT = 30

# ========== ユーティリティ ==========

def normalize_url(url, base_url="https://game8.jp"):
    """URLを正規化（フラグメント・クエリ除去、相対→絶対変換）"""
    url = urljoin(base_url, url)
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return normalized.rstrip("/")


def is_target_url(url):
    """対象URLかどうか判定"""
    url = normalize_url(url)

    # パターン1: トップページ
    if url == f"https://game8.jp/{GAME_SLUG}":
        return True

    # パターン2: 記事ページ（数字ID）
    if re.match(rf"^https://game8\.jp/{GAME_SLUG}/\d+$", url):
        return True

    # パターン3: 英単語パスのページ（例: /ranking）
    if re.match(rf"^https://game8\.jp/{GAME_SLUG}/[a-zA-Z][\w\-/]*$", url):
        exclude = ["/user/", "/search/", "/preview/", "/edit/", "/draft/",
                   "/forum/", "/comment/", "/favorite/"]
        if not any(ex in url for ex in exclude):
            return True

    return False


def url_to_filename(url):
    """URLからファイル名を生成"""
    path = urlparse(normalize_url(url)).path
    suffix = path.replace(f"/{GAME_SLUG}", "").strip("/")
    if not suffix:
        return "top.html"
    safe = suffix.replace("/", "_")
    return f"{safe}.html"


def get_already_saved():
    """保存済みファイル名セットを返す"""
    saved = set()
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith(".html"):
                saved.add(f)
    return saved


def wait():
    """リクエスト間の待機。5〜10秒のランダム"""
    delay = random.uniform(5.0, 10.0)
    print(f"  待機 {delay:.1f}秒...", flush=True)
    time.sleep(delay)


def fetch_with_retry(url, max_retries=3):
    """リトライ付きGET。指数バックオフ。"""
    for attempt in range(max_retries + 1):
        if attempt > 0:
            backoff = 30 * (2 ** (attempt - 1))
            print(f"  リトライ {attempt}/{max_retries} - {backoff}秒待機...", flush=True)
            time.sleep(backoff)

        try:
            resp = SESSION.get(url, timeout=TIMEOUT)

            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                print(f"  レート制限検出 (429) - 120秒待機", flush=True)
                time.sleep(120)
                continue
            elif resp.status_code == 403:
                print(f"  アクセス拒否 (403) - 180秒待機", flush=True)
                time.sleep(180)
                continue
            elif resp.status_code >= 500:
                print(f"  サーバーエラー ({resp.status_code})", flush=True)
                continue
            else:
                print(f"  HTTP {resp.status_code}: {url}", flush=True)
                return None

        except requests.exceptions.Timeout:
            print(f"  タイムアウト", flush=True)
            continue
        except requests.exceptions.ConnectionError:
            print(f"  接続エラー - 60秒待機", flush=True)
            time.sleep(60)
            continue

    print(f"  ✗ 最終失敗: {url}", flush=True)
    return None


def save_html(html, url):
    """HTMLをファイルに保存"""
    filename = url_to_filename(url)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filename


def extract_links(html):
    """HTML内のsplatoon3対象リンクを全て抽出"""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        normalized = normalize_url(href)
        if is_target_url(normalized):
            links.add(normalized)
    return links


def extract_title(html):
    """HTMLからページタイトルを抽出"""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title = soup.find("title")
    if title:
        return title.get_text(strip=True)
    return ""


def save_progress(discovered, processed, failed, sitemap_urls, bfs_extra):
    """進捗をJSONに保存"""
    progress = {
        "timestamp": datetime.now().isoformat(),
        "discovered_count": len(discovered),
        "processed_count": len(processed),
        "failed_count": len(failed),
        "sitemap_count": len(sitemap_urls),
        "bfs_extra_count": len(bfs_extra),
        "failed": sorted(failed),
    }
    with open(os.path.join(OUTPUT_DIR, "_progress.json"), "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ========== Phase 0: sitemap ==========

def phase0_sitemap():
    """sitemapから対象ゲームの全URLを抽出"""
    print("\n=== Phase 0: sitemap解析 ===", flush=True)

    sitemap_index_url = "https://game8.jp/sitemaps/sitemap.xml.gz"
    print(f"  sitemap.xml.gzダウンロード中...", flush=True)

    try:
        resp = SESSION.get(sitemap_index_url, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ⚠ sitemapダウンロード失敗: {e}", flush=True)
        print(f"  → sitemapなしでBFSクロールのみで続行", flush=True)
        return set()

    try:
        xml_data = gzip.decompress(resp.content)
    except:
        xml_data = resp.content

    print(f"  サイズ: {len(xml_data):,} bytes", flush=True)

    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_data)

    # namespace検出
    ns_match = re.match(r'\{(.+?)\}', root.tag)
    ns = {"sm": ns_match.group(1)} if ns_match else {}

    # sitemapインデックスかチェック
    if ns:
        child_sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
        url_locs = root.findall(".//sm:url/sm:loc", ns)
    else:
        child_sitemaps = root.findall(".//sitemap/loc")
        url_locs = root.findall(".//url/loc")

    target_urls = set()

    if child_sitemaps:
        print(f"  sitemapインデックス検出: 子sitemap {len(child_sitemaps)}件", flush=True)
        for i, child in enumerate(child_sitemaps):
            child_url = child.text.strip()
            # game_slugが含まれるsitemapだけ処理（効率化）
            # ただし汎用sitemapの場合は全て見る
            print(f"  [{i+1}/{len(child_sitemaps)}] {child_url}", flush=True)
            try:
                child_resp = SESSION.get(child_url, timeout=60)
                if child_url.endswith(".gz"):
                    try:
                        child_xml = gzip.decompress(child_resp.content)
                    except:
                        child_xml = child_resp.content
                else:
                    child_xml = child_resp.content

                child_root = ET.fromstring(child_xml)
                if ns:
                    locs = child_root.findall(".//sm:url/sm:loc", ns)
                else:
                    locs = child_root.findall(".//url/loc")

                count = 0
                for loc in locs:
                    url = loc.text.strip()
                    if is_target_url(url):
                        target_urls.add(normalize_url(url))
                        count += 1
                if count > 0:
                    print(f"    → {GAME_SLUG}対象: {count}件", flush=True)

            except Exception as e:
                print(f"    ⚠ 失敗: {e}", flush=True)

            time.sleep(1)  # sitemap取得間は1秒待機（HTMLではないので短めでOK）

    elif url_locs:
        print(f"  単一sitemap: {len(url_locs)} URL", flush=True)
        for loc in url_locs:
            url = loc.text.strip()
            if is_target_url(url):
                target_urls.add(normalize_url(url))

    print(f"\n  sitemap発見URL: {len(target_urls)}件", flush=True)

    # 保存
    with open(os.path.join(OUTPUT_DIR, "_sitemap_urls.json"), "w") as f:
        json.dump(sorted(target_urls), f, ensure_ascii=False, indent=2)
    print(f"  _sitemap_urls.json 保存完了", flush=True)

    return target_urls


# ========== Phase 1: BFSクロール + ダウンロード ==========

def phase1_bfs_crawl(sitemap_urls):
    """BFSクロール + ダウンロード"""
    print(f"\n=== Phase 1: BFSクロール + ダウンロード ===", flush=True)

    top_url = f"https://game8.jp/{GAME_SLUG}"

    # 初期キュー: トップページ + sitemap URLs
    queue = deque()
    queue.append(top_url)
    for url in sorted(sitemap_urls):
        if url != top_url:
            queue.append(url)

    discovered = set(sitemap_urls)
    discovered.add(top_url)
    processed = set()
    failed = set()
    bfs_extra = set()  # BFSで追加発見したURL
    title_map = {}

    already_saved = get_already_saved()
    total_initial = len(queue)
    download_count = 0

    print(f"  初期キュー: {total_initial}件（sitemap {len(sitemap_urls)} + トップ 1）", flush=True)

    while queue:
        url = queue.popleft()
        normalized = normalize_url(url)

        if normalized in processed:
            continue
        processed.add(normalized)

        filename = url_to_filename(normalized)
        current_num = len(processed)

        # 保存済みチェック
        if filename in already_saved:
            # リンク抽出のためにファイル読込
            filepath = os.path.join(OUTPUT_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    html = f.read()
                print(f"  [{current_num}] スキップ（保存済み）: {filename}", flush=True)
                # リンク抽出
                new_links = extract_links(html)
                for link in new_links:
                    if link not in discovered:
                        discovered.add(link)
                        bfs_extra.add(link)
                        queue.append(link)
                # タイトル抽出
                title_map[filename] = extract_title(html)
            except Exception as e:
                print(f"  [{current_num}] ⚠ 読込失敗: {filename}: {e}", flush=True)
            continue

        # ダウンロード
        wait()
        html = fetch_with_retry(normalized)

        if html is None:
            failed.add(normalized)
            print(f"  [{current_num}] ✗ 失敗: {normalized}", flush=True)
        else:
            saved_name = save_html(html, normalized)
            already_saved.add(saved_name)
            download_count += 1
            lines = html.count('\n') + 1
            title = extract_title(html)
            title_map[saved_name] = title
            title_short = title[:40] + "..." if len(title) > 40 else title
            print(f"  [{current_num}] ✓ {saved_name} ({lines:,}行) {title_short}", flush=True)

            # リンク抽出
            new_links = extract_links(html)
            new_count = 0
            for link in new_links:
                if link not in discovered:
                    discovered.add(link)
                    bfs_extra.add(link)
                    queue.append(link)
                    new_count += 1
            if new_count > 0:
                print(f"    → 新規URL {new_count}件発見", flush=True)

        # 50件ごとに進捗保存
        if len(processed) % 50 == 0:
            save_progress(discovered, processed, failed, sitemap_urls, bfs_extra)
            print(f"  --- 進捗保存 (処理済み: {len(processed)}, 発見: {len(discovered)}, 失敗: {len(failed)}) ---", flush=True)

    print(f"\n  クロール完了:", flush=True)
    print(f"    処理済み: {len(processed)}件", flush=True)
    print(f"    ダウンロード: {download_count}件", flush=True)
    print(f"    BFS追加発見: {len(bfs_extra)}件", flush=True)
    print(f"    失敗: {len(failed)}件", flush=True)

    return discovered, processed, failed, bfs_extra, title_map


# ========== Phase 2: 検証 ==========

def phase2_verify(sitemap_urls, discovered, bfs_extra, failed):
    """4種の完了検証"""
    print(f"\n=== Phase 2: 検証 ===", flush=True)

    saved = get_already_saved()
    issues = []

    # 検証1: 発見URL vs 保存ファイル
    print(f"\n  検証1: 発見URL vs 保存ファイル", flush=True)
    missing_files = []
    for url in discovered:
        fn = url_to_filename(url)
        if fn not in saved:
            missing_files.append(url)
    if missing_files:
        print(f"    ✗ 未取得: {len(missing_files)}件", flush=True)
        for url in missing_files[:20]:
            print(f"      - {url}", flush=True)
        if len(missing_files) > 20:
            print(f"      ... 他 {len(missing_files)-20}件", flush=True)
        issues.extend(missing_files)
    else:
        print(f"    ✓ 全{len(discovered)}URL取得済み", flush=True)

    # 検証2: ファイルサイズ
    print(f"\n  検証2: ファイルサイズチェック", flush=True)
    suspicious = []
    for f in saved:
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        if size < 10000:
            suspicious.append((f, size))
    if suspicious:
        print(f"    ⚠ 異常に小さいファイル: {len(suspicious)}件", flush=True)
        for fn, size in suspicious:
            print(f"      - {fn}: {size:,} bytes", flush=True)
    else:
        print(f"    ✓ 全ファイル10KB以上", flush=True)

    # 検証3: リンク網羅性
    print(f"\n  検証3: リンク網羅性チェック", flush=True)
    all_linked = set()
    for f in saved:
        try:
            with open(os.path.join(OUTPUT_DIR, f), "r", encoding="utf-8") as fh:
                html = fh.read()
            links = extract_links(html)
            for link in links:
                all_linked.add(url_to_filename(link))
        except:
            pass
    missing_linked = all_linked - saved
    if missing_linked:
        print(f"    ✗ HTML内リンク先で未取得: {len(missing_linked)}件", flush=True)
        for fn in sorted(missing_linked)[:20]:
            print(f"      - {fn}", flush=True)
    else:
        print(f"    ✓ 全リンク先が取得済み", flush=True)

    # 検証4: sitemap vs BFS クロスチェック
    print(f"\n  検証4: sitemap vs BFS クロスチェック", flush=True)
    sitemap_set = set(normalize_url(u) for u in sitemap_urls)
    bfs_set = discovered.copy()
    only_sitemap = sitemap_set - bfs_set
    only_bfs = bfs_extra
    both = sitemap_set & bfs_set

    print(f"    両方で発見: {len(both)}件", flush=True)
    if only_sitemap:
        print(f"    ⚠ sitemapのみ: {len(only_sitemap)}件", flush=True)
    if only_bfs:
        print(f"    ⚠ BFSのみ: {len(only_bfs)}件", flush=True)
    if not only_sitemap and not only_bfs:
        print(f"    ✓ 完全一致", flush=True)

    all_missing = set(missing_files)
    # missing_linkedからURL復元
    for fn in missing_linked:
        # filenameからURLを推定
        name = fn.replace(".html", "")
        if name == "top":
            all_missing.add(f"https://game8.jp/{GAME_SLUG}")
        else:
            all_missing.add(f"https://game8.jp/{GAME_SLUG}/{name.replace('_', '/')}")

    return all_missing, suspicious


# ========== Phase 3: 補完 ==========

def phase3_补完(missing_urls):
    """漏れたURLを追加取得"""
    if not missing_urls:
        print(f"\n=== Phase 3: 補完不要 ===", flush=True)
        return set()

    print(f"\n=== Phase 3: 補完 ({len(missing_urls)}件) ===", flush=True)
    still_failed = set()

    for i, url in enumerate(sorted(missing_urls), 1):
        filename = url_to_filename(url)
        print(f"  [{i}/{len(missing_urls)}] {url}", flush=True)
        wait()
        html = fetch_with_retry(url)
        if html:
            save_html(html, url)
            lines = html.count('\n') + 1
            print(f"    ✓ {filename} ({lines:,}行)", flush=True)
        else:
            still_failed.add(url)
            print(f"    ✗ 失敗", flush=True)

    print(f"\n  補完結果: 成功 {len(missing_urls)-len(still_failed)}, 失敗 {len(still_failed)}", flush=True)
    return still_failed


# ========== Phase 4: メタデータ保存 ==========

def phase4_metadata(sitemap_urls, discovered, bfs_extra, failed, title_map):
    """メタデータ保存"""
    print(f"\n=== Phase 4: メタデータ保存 ===", flush=True)

    saved = get_already_saved()

    metadata = {
        "game_slug": GAME_SLUG,
        "scrape_date": datetime.now().isoformat(),
        "total_pages": len(saved),
        "url_sources": {
            "sitemap": len(sitemap_urls),
            "bfs_crawl_total": len(discovered),
            "bfs_extra": len(bfs_extra),
            "union": len(discovered),
        },
        "top_url": f"https://game8.jp/{GAME_SLUG}",
        "all_files": {
            fn: {
                "title": title_map.get(fn, ""),
                "size": os.path.getsize(os.path.join(OUTPUT_DIR, fn)),
            }
            for fn in sorted(saved)
        },
        "failed_urls": sorted(failed),
    }

    path = os.path.join(OUTPUT_DIR, "_metadata.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"  _metadata.json 保存完了 ({len(saved)}ページ)", flush=True)


# ========== メイン ==========

def main():
    start_time = time.time()
    print(f"=== Game8 完全スクレイピング: {GAME_SLUG} ===", flush=True)
    print(f"  出力先: {OUTPUT_DIR}", flush=True)
    print(f"  開始: {datetime.now().isoformat()}", flush=True)

    # Phase 0
    sitemap_urls = phase0_sitemap()

    # Phase 1
    discovered, processed, failed, bfs_extra, title_map = phase1_bfs_crawl(sitemap_urls)

    # Phase 2
    missing_urls, suspicious = phase2_verify(sitemap_urls, discovered, bfs_extra, failed)

    # Phase 3 (最大3回ループ)
    for round_num in range(3):
        if not missing_urls:
            break
        print(f"\n  --- 補完ラウンド {round_num+1} ---", flush=True)
        still_failed = phase3_补完(missing_urls)
        # 再検証
        missing_urls = still_failed
        if missing_urls:
            print(f"  まだ {len(missing_urls)}件未取得", flush=True)

    # Phase 4
    phase4_metadata(sitemap_urls, discovered, bfs_extra, failed | (missing_urls or set()), title_map)

    elapsed = time.time() - start_time
    saved = get_already_saved()
    print(f"\n=== 完了: {len(saved)}ページ取得（所要時間: {elapsed/60:.1f}分） ===", flush=True)


if __name__ == "__main__":
    main()
