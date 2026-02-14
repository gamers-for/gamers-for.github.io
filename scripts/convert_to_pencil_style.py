#!/usr/bin/env python3
"""
static/{game_slug}/内の全HTMLを色鉛筆風に変換
- 広告・スクリプト・トラッキング除去
- 元CSSはそのまま残す（レイアウト維持）
- 色味だけ上書きするオーバーレイCSSを追加注入
- 禁止名称除去
"""
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, Comment

GAME_SLUG = sys.argv[1] if len(sys.argv) > 1 else "splatoon3"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = PROJECT_ROOT / "static" / GAME_SLUG

FORBIDDEN = [
    "Game8", "game8", "GameWith", "gamewith", "Altema", "altema",
    "ゲームエイト", "ゲーム8", "ゲームウィズ", "アルテマ", "攻略班",
    "Game8（ゲームエイト）- 日本最大級のゲーム攻略wikiサイト",
]


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # ─── 0. HTMLコメント除去 ───
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
    for el in soup.find_all("div", id=re.compile(r"g8-ad")):
        el.decompose()
    for el in soup.find_all("div", id=re.compile(r"ad-placement")):
        el.decompose()

    # ─── 3. トラッキング要素除去 ───
    for el in soup.find_all(class_="track_mario"):
        el.decompose()
    for el in soup.find_all(class_="premium-plan-link"):
        el.decompose()
    for el in soup.find_all(True):
        for attr in list(el.attrs):
            if attr.startswith("data-track"):
                del el[attr]

    # ─── 4. インラインイベントハンドラ除去 ───
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.startswith("on"):
                del tag[attr]

    # ─── 5. 元CSSをローカル参照に差し替え ───
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href", "")
        if "application-2a375ea" in href or "pc/new/application" in href:
            link["href"] = "/css/base1.css"
        elif "application-BEEMSW8" in href or "vite/assets/application" in href:
            link["href"] = "/css/base2.css"

    # ─── 6. 色オーバーレイCSS追加（headの末尾に） ───
    head = soup.find("head")
    if head:
        overlay_css = soup.new_tag("link", rel="stylesheet", href="/css/pencil-overlay.css")
        head.append(overlay_css)

    # ─── 7. og:site_name 差し替え ───
    og_site = soup.find("meta", property="og:site_name")
    if og_site:
        og_site["content"] = "Gamers-For | ゲーム攻略"

    # ─── 8. title タグからサイト名除去 ───
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        t = title_tag.string
        t = re.sub(r'[｜|]\s*ゲームエイト.*$', '', t)
        title_tag.string = t

    # ─── 文字列化 ───
    result = str(soup)

    # ─── 9. 禁止名称・URL除去 ───
    result = re.sub(r'https?://[a-z.]*game8\.jp[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://img\.game8\.jp[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://[a-z.]*gamewith[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://[a-z.]*altema[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://tracking\.game8\.jp[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://flux-cdn\.com[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://securepubads[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://html-load\.com[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://error-report\.com[^\s"\'<>]*', '', result)
    result = re.sub(r'https?://report\.error-report\.com[^\s"\'<>]*', '', result)
    for w in FORBIDDEN:
        result = result.replace(w, "")

    # ─── 10. author メタタグ除去 ───
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
