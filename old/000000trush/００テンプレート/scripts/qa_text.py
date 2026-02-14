#!/usr/bin/env python3
"""
QA Text: Claude API による文章品質チェック（スタブ）

生成されたMarkdownコンテンツの文章品質を評価する。

チェック項目:
  1. テンプレ感（機械的な文章になっていないか）
  2. 具体性（具体的なデータや数値が含まれているか）
  3. 正確性（矛盾や明らかな誤りがないか）
  4. 読みやすさ（文章の長さ、構造、接続詞の使い方）
  5. SEO（キーワード密度、メタ情報の充実度）

使い方:
  python qa_text.py /path/to/game_config.json [--api-key KEY]

必要:
  pip install anthropic
"""

import json
import os
import sys
import glob


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_generated_content(hugo_dir, game_slug):
    """生成済みコンテンツを読み込み"""
    content_dir = os.path.join(hugo_dir, "content", "games", game_slug)
    pages = {}

    if not os.path.exists(content_dir):
        return pages

    for md_file in glob.glob(os.path.join(content_dir, "*.md")):
        name = os.path.basename(md_file)
        with open(md_file, "r", encoding="utf-8") as f:
            pages[name] = f.read()

    return pages


def check_template_feel(content):
    """テンプレ感チェック"""
    # TODO: Claude API で評価
    return {"name": "テンプレ感", "score": 0, "comment": "未実装"}


def check_specificity(content):
    """具体性チェック"""
    return {"name": "具体性", "score": 0, "comment": "未実装"}


def check_accuracy(content):
    """正確性チェック"""
    return {"name": "正確性", "score": 0, "comment": "未実装"}


def check_readability(content):
    """読みやすさチェック"""
    return {"name": "読みやすさ", "score": 0, "comment": "未実装"}


def check_seo(content, keywords):
    """SEOチェック"""
    return {"name": "SEO", "score": 0, "comment": "未実装"}


def main():
    if len(sys.argv) < 2:
        print("Usage: python qa_text.py /path/to/game_config.json [--api-key KEY]")
        sys.exit(1)

    config_path = os.path.abspath(sys.argv[1])
    config = load_config(config_path)

    config_dir = os.path.dirname(config_path)
    hugo_dir = os.path.join(config_dir, config.get("hugo_site_dir", "../gamers-for"))
    game_slug = config["game_slug"]

    print(f"=== QA Text: {config['game_name']} 文章品質チェック ===")

    pages = read_generated_content(hugo_dir, game_slug)
    print(f"対象ページ数: {len(pages)}")

    if not pages:
        print("チェック対象のページが見つかりません")
        return

    all_results = []
    for page_name, content in pages.items():
        print(f"\n--- {page_name} ---")
        results = [
            check_template_feel(content),
            check_specificity(content),
            check_accuracy(content),
            check_readability(content),
            check_seo(content, config.get("seo", {}).get("target_keywords", [])),
        ]
        for r in results:
            print(f"  {r['name']}: {r['score']}/10 - {r['comment']}")
        all_results.extend(results)

    if all_results:
        avg = sum(r["score"] for r in all_results) / len(all_results)
        print(f"\n総合スコア: {avg:.1f}/10")


if __name__ == "__main__":
    main()
