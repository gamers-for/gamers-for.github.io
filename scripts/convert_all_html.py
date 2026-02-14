#!/usr/bin/env python3
"""
全1,515件のraw HTMLをHugoコンテンツに一括変換
"""
import json
import os
import re
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "００００１スプラトゥーン３"
RAW_HTML_DIR = DATA_DIR / "raw_html"
CONTENT_DIR = PROJECT_ROOT / "content" / "games" / "splatoon3"

# ─── タイトルからカテゴリを判定 ──────────────────
CATEGORY_RULES = [
    ("gear-powers", ["ギアパワーと入手方法", "ギアパワー一覧", "ギアパワーの効果", "ギアパワーランキング"]),
    ("side-order", ["サイドオーダー"]),
    ("salmon-run", ["サーモンラン", "オカシラ", "ビッグラン", "クマサン"]),
    ("hero-mode", ["ヒーローモード", "オルタナ", "ミステリーファイル", "ミステリーボックス"]),
    ("weapons", ["おすすめギアと立ち回り", "評価とおすすめギア", "武器一覧", "ブキ評価",
                  "最強武器", "ブキランキング", "シューター一覧", "ブラスター一覧",
                  "ローラー一覧", "フデ一覧", "チャージャー一覧", "スロッシャー一覧",
                  "スピナー一覧", "マニューバー一覧", "シェルター一覧", "ストリンガー一覧", "ワイパー一覧"]),
    ("specials", ["スペシャルウェポン", "スペシャル一覧", "の使い方と効果"]),
    ("subs", ["サブウェポン"]),
    ("stages", ["ステージ", "マップ"]),
    ("gear", ["ギア一覧", "ブランド一覧"]),
    ("fes", ["フェス"]),
    ("updates", ["アップデート", "アプデ", "Ver."]),
    ("beginner", ["初心者", "遊び方", "やり方", "操作方法"]),
]

def classify(title):
    for section, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in title:
                return section
    return "guides"

# ─── タイトルクリーニング ──────────────────────
def clean_title(raw):
    t = re.sub(r'[｜|]\s*ゲームエイト.*$', '', raw)
    t = re.sub(r'【スプラトゥーン3】\s*$', '', t)
    t = re.sub(r'【スプラ3】\s*$', '', t)
    return t.strip()

def title_to_slug(title):
    s = re.sub(r'【[^】]*】', '', title)
    s = re.sub(r'[｜|].*$', '', s)
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r'[\s/・（）()「」\[\]]+', '-', s)
    s = re.sub(r'[^\w\-ぁ-んァ-ヶー一-龥々]', '', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s[:80] if s else "page"

# ─── 禁止名称除去 ──────────────────────────
FORBIDDEN = ["Game8", "game8", "GameWith", "gamewith", "Altema", "altema",
             "ゲームエイト", "ゲーム8", "ゲームウィズ", "アルテマ", "3サイト", "攻略班"]

def remove_forbidden(html):
    html = re.sub(r'https?://[a-z.]*game8\.jp[^\s"\'<>]*', '', html)
    html = re.sub(r'https?://img\.game8\.jp[^\s"\'<>]*', '', html)
    html = re.sub(r'https?://[a-z.]*gamewith[^\s"\'<>]*', '', html)
    html = re.sub(r'https?://[a-z.]*altema[^\s"\'<>]*', '', html)
    for w in FORBIDDEN:
        html = html.replace(w, "")
    return html

# ─── メイン変換 ──────────────────────────────
def convert_one(html_path, title, section):
    with open(html_path, "r", encoding="utf-8") as f:
        raw = f.read()

    soup = BeautifulSoup(raw, "html.parser")
    wrapper = soup.find(class_="archive-style-wrapper")
    if not wrapper:
        return None

    # 不要要素を最低限除去
    for tag in wrapper.find_all(["script", "noscript"]):
        tag.decompose()
    for el in wrapper.find_all(class_="ad-wrapper"):
        el.decompose()
    for el in wrapper.find_all("div", class_=re.compile(r"ad[-_]")):
        el.decompose()
    for el in wrapper.find_all("div", id=re.compile(r"^div-gpt")):
        el.decompose()

    content = wrapper.decode_contents()
    content = remove_forbidden(content)

    clean = clean_title(title)
    safe = clean.replace('"', '\\"')

    fm = f'''---
title: "{safe}"
date: 2026-02-13
description: "スプラトゥーン3の攻略情報"
---

'''
    return fm + content


def main():
    # メタデータ読み込み
    with open(RAW_HTML_DIR / "_metadata.json") as f:
        meta = json.load(f)

    all_files = meta.get("all_files", meta)
    total = 0
    success = 0
    fail = 0
    skip_files = {"_metadata.json", "_sitemap_urls.json", "_progress.json", "writer_profile.html"}

    for filename, info in sorted(all_files.items()):
        if filename in skip_files or not filename.endswith(".html"):
            continue

        total += 1
        title = info.get("title", filename.replace(".html", ""))
        section = classify(title)
        slug = title_to_slug(title)
        html_path = RAW_HTML_DIR / filename

        if not html_path.exists():
            print(f"  ✗ {filename} (ファイルなし)")
            fail += 1
            continue

        result = convert_one(html_path, title, section)
        if not result:
            print(f"  ✗ {filename} (wrapper なし)")
            fail += 1
            continue

        out_dir = CONTENT_DIR / section
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slug}.md"

        # 重複回避
        if out_path.exists():
            article_id = filename.replace(".html", "")
            out_path = out_dir / f"{slug}-{article_id}.md"

        out_path.write_text(result, encoding="utf-8")
        success += 1

        if success % 100 == 0:
            print(f"  ... {success}/{total}")

    # セクション _index.md
    for section_dir in CONTENT_DIR.iterdir():
        if section_dir.is_dir():
            idx = section_dir / "_index.md"
            if not idx.exists():
                name = section_dir.name
                idx.write_text(f'---\ntitle: "{name}"\n---\n', encoding="utf-8")

    print(f"\n完了: {success} 成功 / {fail} 失敗 / {total} 合計")


if __name__ == "__main__":
    main()
