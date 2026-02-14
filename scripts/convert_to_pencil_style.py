#!/usr/bin/env python3
"""
static/{game_slug}/内の全HTMLを色鉛筆風に変換
- 広告・スクリプト・トラッキング除去
- CSS差し替え（独自の色鉛筆風CSS）
- 禁止名称除去
"""
import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

GAME_SLUG = sys.argv[1] if len(sys.argv) > 1 else "splatoon3"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = PROJECT_ROOT / "static" / GAME_SLUG

FORBIDDEN = [
    "Game8", "game8", "GameWith", "gamewith", "Altema", "altema",
    "ゲームエイト", "ゲーム8", "ゲームウィズ", "アルテマ", "攻略班",
    "Game8（ゲームエイト）- 日本最大級のゲーム攻略wikiサイト",
]

# 除去するリンク rel タイプ
REMOVE_LINK_RELS = {"stylesheet", "preload", "preconnect", "dns-prefetch"}

# 除去するメタタグ name/property
REMOVE_META = {
    "csrf-param", "csrf-token",
    "fb:app_id", "twitter:site",
}


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # ─── 0. HTMLコメント除去 ───
    from bs4 import Comment
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # ─── 1. script / noscript 全除去 ───
    for tag in soup.find_all(["script", "noscript"]):
        tag.decompose()

    # ─── 2. 広告系要素除去 ───
    for el in soup.find_all(class_="ad-wrapper"):
        el.decompose()
    for el in soup.find_all("div", class_=re.compile(r"ad[-_]")):
        el.decompose()
    for el in soup.find_all("div", id=re.compile(r"^div-gpt")):
        el.decompose()
    # g8-ad-placement系
    for el in soup.find_all("div", id=re.compile(r"g8-ad")):
        el.decompose()
    for el in soup.find_all("div", id=re.compile(r"ad-placement")):
        el.decompose()

    # ─── 3. トラッキング要素除去（a, div 両方）───
    for el in soup.find_all(class_="track_mario"):
        el.decompose()
    for el in soup.find_all(class_="premium-plan-link"):
        el.decompose()
    # data-track属性を持つ要素のdata-track属性を除去
    for el in soup.find_all(True):
        for attr in list(el.attrs):
            if attr.startswith("data-track"):
                del el[attr]

    # ─── 4. インラインイベントハンドラ除去 ───
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.startswith("on"):
                del tag[attr]

    # ─── 5. 元CSS除去 ───
    for link in soup.find_all("link", rel="stylesheet"):
        link.decompose()
    for link in soup.find_all("link"):
        rel = link.get("rel", [])
        if isinstance(rel, list):
            rel_str = " ".join(rel).lower()
        else:
            rel_str = str(rel).lower()
        if any(r in rel_str for r in ("preload", "preconnect", "dns-prefetch")):
            link.decompose()
    for style in soup.find_all("style"):
        style.decompose()

    # ─── 6. 不要なメタタグ除去 ───
    for meta in soup.find_all("meta"):
        name = meta.get("name", "")
        prop = meta.get("property", "")
        if name in REMOVE_META or prop in REMOVE_META:
            meta.decompose()

    # ─── 7. favicon（元サイト）除去 ───
    for link in soup.find_all("link"):
        href = link.get("href", "")
        if "game8.jp" in href or "assets.game8" in href:
            link.decompose()

    # ─── 8. 独自CSS注入 ───
    head = soup.find("head")
    if head:
        # Google Fonts
        preconnect = soup.new_tag("link", rel="preconnect", href="https://fonts.googleapis.com")
        head.append(preconnect)
        font_tag = soup.new_tag("link", rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Klee+One:wght@400;600&display=swap")
        head.append(font_tag)
        # 独自CSS
        css_tag = soup.new_tag("link", rel="stylesheet", href="/css/style.css")
        head.append(css_tag)

    # ─── 9. og:site_name を差し替え ───
    og_site = soup.find("meta", property="og:site_name")
    if og_site:
        og_site["content"] = "Gamers-For | ゲーム攻略"

    # ─── 10. title タグからサイト名除去 ───
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        t = title_tag.string
        t = re.sub(r'[｜|]\s*ゲームエイト.*$', '', t)
        title_tag.string = t

    # ─── 文字列化 ───
    result = str(soup)

    # ─── 11. 禁止名称・URL除去 ───
    result = re.sub(r'https?://[a-z.]*game8\.jp[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://img\.game8\.jp[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://[a-z.]*gamewith[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://[a-z.]*altema[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://tracking\.game8\.jp[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://assets\.game8\.jp[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://flux-cdn\.com[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://securepubads[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://html-load\.com[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://error-report\.com[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://report\.error-report\.com[^\s"\'<>]*', '', result)
    for w in FORBIDDEN:
        result = result.replace(w, "")

    # ─── 12. author メタタグのクリーンアップ ───
    result = re.sub(r'<meta\s+content="スプラトゥーン3[^"]*"\s+name="author"\s*/?\s*>', '', result)
    result = re.sub(r'<meta\s+name="author"\s+content="[^"]*攻略[^"]*"\s*/?\s*>', '', result)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result)


def main():
    if not HTML_DIR.exists():
        print(f"エラー: {HTML_DIR} が存在しません")
        sys.exit(1)

    files = sorted(HTML_DIR.glob("*.html"))
    total = len(files)
    print(f"対象: {total}件 ({HTML_DIR})")
    print("=" * 60)

    for i, fp in enumerate(files, 1):
        try:
            process_file(fp)
        except Exception as e:
            print(f"  ✗ エラー: {fp.name}: {e}")

        if i % 100 == 0 or i == total:
            print(f"  {i}/{total} 完了")

    print("=" * 60)
    print(f"全{total}件の変換完了")


if __name__ == "__main__":
    main()
