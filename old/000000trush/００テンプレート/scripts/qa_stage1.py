#!/usr/bin/env python3
"""
QA Stage 1: Playwright による機械的チェック（スタブ）

チェック項目:
  1. リンク切れ（内部リンク）
  2. 画像表示（imgタグのsrcが存在）
  3. レスポンシブ（viewport 375px / 1280px）
  4. 目次（TOCの存在と正しいアンカー）
  5. パンくずリスト（breadcrumb構造）
  6. メタタグ（title, description, og:*）
  7. 見出し構造（h2/h3の階層が正しい）
  8. コンテンツ量（本文が最低300文字）
  9. 内部リンク（各ページに最低2つ）
 10. 表示速度（DOMContentLoaded < 3秒）

使い方:
  python qa_stage1.py /path/to/game_config.json [--hugo-port 1313]

必要:
  pip install playwright
  playwright install chromium
"""

import json
import os
import sys


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_links(page, base_url):
    """内部リンク切れチェック"""
    # TODO: Playwright実装
    return {"name": "リンク切れ", "status": "stub", "details": "未実装"}


def check_images(page):
    """画像表示チェック"""
    return {"name": "画像表示", "status": "stub", "details": "未実装"}


def check_responsive(page):
    """レスポンシブチェック"""
    return {"name": "レスポンシブ", "status": "stub", "details": "未実装"}


def check_toc(page):
    """目次チェック"""
    return {"name": "目次", "status": "stub", "details": "未実装"}


def check_breadcrumb(page):
    """パンくずリストチェック"""
    return {"name": "パンくずリスト", "status": "stub", "details": "未実装"}


def check_meta_tags(page):
    """メタタグチェック"""
    return {"name": "メタタグ", "status": "stub", "details": "未実装"}


def check_heading_structure(page):
    """見出し構造チェック"""
    return {"name": "見出し構造", "status": "stub", "details": "未実装"}


def check_content_length(page):
    """コンテンツ量チェック"""
    return {"name": "コンテンツ量", "status": "stub", "details": "未実装"}


def check_internal_links(page):
    """内部リンク数チェック"""
    return {"name": "内部リンク", "status": "stub", "details": "未実装"}


def check_load_speed(page):
    """表示速度チェック"""
    return {"name": "表示速度", "status": "stub", "details": "未実装"}


ALL_CHECKS = [
    check_links, check_images, check_responsive, check_toc,
    check_breadcrumb, check_meta_tags, check_heading_structure,
    check_content_length, check_internal_links, check_load_speed,
]


def run_checks(config, hugo_port=1313):
    """全チェックを実行"""
    game_slug = config["game_slug"]
    base_url = f"http://localhost:{hugo_port}/gamers-for/games/{game_slug}/"

    print(f"=== QA Stage 1: {config['game_name']} ===")
    print(f"対象: {base_url}")
    print(f"チェック項目: {len(ALL_CHECKS)}個\n")

    results = []
    for check_fn in ALL_CHECKS:
        result = check_fn(None)  # page=None (stub)
        status_icon = {"pass": "✓", "fail": "✗", "stub": "○"}.get(result["status"], "?")
        print(f"  {status_icon} {result['name']}: {result['details']}")
        results.append(result)

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    stubs = sum(1 for r in results if r["status"] == "stub")

    print(f"\n結果: {passed}パス / {failed}失敗 / {stubs}未実装")
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python qa_stage1.py /path/to/game_config.json [--hugo-port 1313]")
        sys.exit(1)

    config_path = os.path.abspath(sys.argv[1])
    config = load_config(config_path)

    hugo_port = 1313
    if "--hugo-port" in sys.argv:
        idx = sys.argv.index("--hugo-port")
        if idx + 1 < len(sys.argv):
            hugo_port = int(sys.argv[idx + 1])

    run_checks(config, hugo_port)


if __name__ == "__main__":
    main()
