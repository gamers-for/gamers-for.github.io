#!/usr/bin/env python3
"""
汎用アイコン取得スクリプト
game_config.json の icon_source 設定に従い、アイコンをダウンロードする。

対応ソース:
  - wiki_api: MediaWiki API（Inkipedia等）
  - direct_url: 直接URL指定
  - manual: 手動配置（何もしない）

使い方:
  python fetch_icons.py /path/to/０１ゲーム名/game_config.json
"""

import json
import os
import shutil
import sys
import time

try:
    import requests
except ImportError:
    print("Warning: requests not installed. Install with: pip install requests")
    requests = None


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def download_from_wiki_api(api_url, wiki_filename, save_path, interval_sec=2):
    """MediaWiki APIからファイルをダウンロード"""
    if requests is None:
        print("  [ERROR] requests module not available")
        return False

    if os.path.exists(save_path) and os.path.getsize(save_path) > 100:
        print(f"  [skip] {os.path.basename(save_path)} already exists")
        return True

    params = {
        "action": "query",
        "titles": f"File:{wiki_filename}",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
    }

    try:
        resp = requests.get(api_url, params=params, timeout=15)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            if "imageinfo" in page_data:
                url = page_data["imageinfo"][0]["url"]
                img_resp = requests.get(url, timeout=15)
                if img_resp.status_code == 200 and len(img_resp.content) > 100:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(img_resp.content)
                    print(f"  [ok] {os.path.basename(save_path)} ({len(img_resp.content)} bytes)")
                    time.sleep(interval_sec)
                    return True

        print(f"  [FAIL] {wiki_filename} not found")
        return False

    except Exception as e:
        print(f"  [ERROR] {wiki_filename}: {e}")
        return False


def download_direct(url, save_path, interval_sec=2):
    """直接URLからダウンロード"""
    if requests is None:
        print("  [ERROR] requests module not available")
        return False

    if os.path.exists(save_path) and os.path.getsize(save_path) > 100:
        print(f"  [skip] {os.path.basename(save_path)} already exists")
        return True

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 100:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            print(f"  [ok] {os.path.basename(save_path)} ({len(resp.content)} bytes)")
            time.sleep(interval_sec)
            return True
        else:
            print(f"  [FAIL] {url}: status={resp.status_code}")
            return False

    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return False


def copy_variant_icon(base_slug, variant_slug, target_dir):
    """バリアント: ベースのアイコンをコピー"""
    src = os.path.join(target_dir, f"{base_slug}.png")
    dst = os.path.join(target_dir, f"{variant_slug}.png")
    if os.path.exists(dst) and os.path.getsize(dst) > 100:
        return True
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  [copy] {variant_slug}.png <- {base_slug}.png")
        return True
    else:
        print(f"  [FAIL] base icon {base_slug}.png not found")
        return False


def fetch_icons(config, hugo_dir):
    """config の icon_source と icons_to_fetch に従いアイコン取得"""
    icon_source = config.get("icon_source", {})
    source_type = icon_source.get("type", "manual")
    api_endpoint = icon_source.get("api_endpoint", "")
    interval = icon_source.get("request_interval_sec", 2)
    game_slug = config["game_slug"]

    output_tmpl = icon_source.get(
        "output_dir_template",
        "static/images/games/{game_slug}/{category}/",
    )

    icons_conf = config.get("icons_to_fetch", [])
    variants_conf = config.get("icon_variants", [])

    ok_count = 0
    fail_count = 0

    for item in icons_conf:
        category = item.get("category", "main")
        output_dir = os.path.join(
            hugo_dir,
            output_tmpl.format(game_slug=game_slug, category=category),
        )
        os.makedirs(output_dir, exist_ok=True)

        slug = item.get("slug", "")
        save_path = os.path.join(output_dir, f"{slug}.png")

        if source_type == "wiki_api":
            wiki_file = item.get("wiki_filename", "")
            if wiki_file:
                ok = download_from_wiki_api(api_endpoint, wiki_file, save_path, interval)
            else:
                ok = False
        elif source_type == "direct_url":
            url = item.get("url", "")
            if url:
                ok = download_direct(url, save_path, interval)
            else:
                ok = False
        else:
            # manual: skip
            ok = True

        if ok:
            ok_count += 1
        else:
            fail_count += 1

    # バリアントコピー
    for var in variants_conf:
        category = var.get("category", "main")
        output_dir = os.path.join(
            hugo_dir,
            output_tmpl.format(game_slug=game_slug, category=category),
        )
        copy_variant_icon(var["base_slug"], var["variant_slug"], output_dir)

    return ok_count, fail_count


def update_master_json(config, hugo_dir):
    """マスターJSONのアイコンパスを更新"""
    game_slug = config["game_slug"]
    master_path = os.path.join(hugo_dir, "data", f"{game_slug}_master.json")
    if not os.path.exists(master_path):
        return

    with open(master_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    icon_updates = config.get("icon_updates", {})
    slug_prefix = config["entity_type"]["slug_prefix"]
    entities = data.get(slug_prefix, [])

    updated = 0
    for e in entities:
        name = e.get("name", "")
        # name→iconパスのマッピングがあれば適用
        if name in icon_updates:
            for field, path in icon_updates[name].items():
                if not e.get(field):
                    e[field] = path
                    updated += 1

    if updated > 0:
        with open(master_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nマスターJSON更新: {updated}箇所")


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_icons.py /path/to/game_config.json")
        sys.exit(1)

    config_path = os.path.abspath(sys.argv[1])
    config = load_config(config_path)
    config["_config_path"] = config_path

    config_dir = os.path.dirname(config_path)
    hugo_dir = os.path.join(config_dir, config.get("hugo_site_dir", "../gamers-for"))

    print(f"=== {config['game_name']} アイコン取得 ===")
    print(f"ソース: {config.get('icon_source', {}).get('type', 'manual')}")
    print(f"interval: {config.get('icon_source', {}).get('request_interval_sec', 2)}s\n")

    ok, fail = fetch_icons(config, hugo_dir)

    print(f"\n=== 結果 ===")
    print(f"成功: {ok}, 失敗: {fail}")

    # 統計
    game_slug = config["game_slug"]
    icon_tmpl = config.get("icon_source", {}).get(
        "output_dir_template",
        "static/images/games/{game_slug}/{category}/",
    )
    for category in ["weapons", "subs", "specials"]:
        dir_path = os.path.join(
            hugo_dir,
            icon_tmpl.format(game_slug=game_slug, category=category),
        )
        if os.path.exists(dir_path):
            count = len([f for f in os.listdir(dir_path) if f.endswith(".png")])
            print(f"{category}: {count}ファイル")

    # マスターJSON更新
    update_master_json(config, hugo_dir)


if __name__ == "__main__":
    main()
