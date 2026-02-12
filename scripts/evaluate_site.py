#!/usr/bin/env python3
"""
サイト品質の自動スコア測定ツール
Game8レベルの100点満点で評価し、不足項目をリスト出力
"""

import os
import re
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, "content")
LAYOUT_DIR = os.path.join(BASE_DIR, "layouts")
CSS_PATH = os.path.join(BASE_DIR, "static", "css", "style.css")
SPLATOON_DIR = os.path.join(CONTENT_DIR, "games", "splatoon3")


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def count_files(pattern):
    return len(glob.glob(pattern))


def evaluate():
    scores = {}
    issues = []
    css = read_file(CSS_PATH)

    # ==============================
    # ビジュアル (30点満点)
    # ==============================

    # 1. ティアリスト表示 (10点)
    tier_list = read_file(os.path.join(SPLATOON_DIR, "tier-list.md"))
    tier_score = 0
    if "tier-grid" in tier_list:
        tier_score += 5
    else:
        issues.append("[ビジュアル] ティアリストがtier-gridショートコードを使っていない")
    if "weapon-icon" in tier_list or "weapon-grid-item" in tier_list:
        tier_score += 3
    else:
        issues.append("[ビジュアル] ティアリストにweapon-iconグリッドがない")
    if tier_list.count("character-card") >= 20:
        tier_score += 2
    else:
        issues.append("[ビジュアル] 武器詳細カードが少ない（20件未満）")
    scores["ティアリスト表示"] = (tier_score, 10)

    # 2. 武器カードデザイン (8点)
    card_score = 0
    if ".character-card" in css:
        card_score += 2
    if "character-card-img" in css:
        card_score += 2
    if "hover" in css and "character-card" in css:
        card_score += 2
    else:
        issues.append("[ビジュアル] character-cardにホバーエフェクトがない")
    if "rating-badge" in css or "rating-value" in css:
        card_score += 2
    else:
        issues.append("[ビジュアル] 評価バッジのCSSが不十分")
    scores["武器カードデザイン"] = (card_score, 8)

    # 3. トップページ (6点)
    index_html = read_file(os.path.join(LAYOUT_DIR, "index.html"))
    splatoon_index = read_file(os.path.join(SPLATOON_DIR, "_index.md"))
    top_score = 0
    if "game-card-thumb" in index_html or "game-card" in index_html:
        top_score += 2
    if "stats-" in splatoon_index or "数字" in splatoon_index or "162" in splatoon_index:
        top_score += 2
    else:
        issues.append("[ビジュアル] トップページに数字インパクトがない")
    if "hero" in index_html or "banner" in index_html:
        top_score += 2
    scores["トップページ"] = (top_score, 6)

    # 4. 色分け・バッジ (6点)
    color_score = 0
    if "tier-grid-label" in css or "tier-grid" in css:
        color_score += 3
    else:
        issues.append("[ビジュアル] ティアグリッドのCSSがない")
    if "#d4af37" in css or "gold" in css.lower() or "gradient" in css:
        color_score += 1
    if "weapon-grid" in css:
        color_score += 2
    else:
        issues.append("[ビジュアル] weapon-gridのCSSがない")
    scores["色分け・バッジ"] = (color_score, 6)

    # ==============================
    # コンテンツ深度 (30点満点)
    # ==============================

    # 5. ルール別ランキング (8点)
    rule_pages = ["tier-area.md", "tier-yagura.md", "tier-hoko.md", "tier-asari.md", "tier-nawabari.md"]
    rule_count = sum(1 for p in rule_pages if os.path.exists(os.path.join(SPLATOON_DIR, p)))
    rule_score = min(8, rule_count * 2)  # 各2点、最大8点
    if rule_count < 5:
        issues.append(f"[コンテンツ] ルール別ランキングが{rule_count}/5ページしかない")
    scores["ルール別ランキング"] = (rule_score, 8)

    # 6. 武器個別ページ (10点)
    weapons_dir = os.path.join(SPLATOON_DIR, "weapons")
    weapon_pages = count_files(os.path.join(weapons_dir, "*.md")) if os.path.isdir(weapons_dir) else 0
    # _index.mdを除く
    if os.path.exists(os.path.join(weapons_dir, "_index.md")):
        weapon_pages -= 1
    weapon_score = min(10, weapon_pages // 16)  # 160件で10点
    if weapon_pages < 100:
        issues.append(f"[コンテンツ] 武器個別ページが{weapon_pages}/162件しかない")
    scores["武器個別ページ"] = (weapon_score, 10)

    # 7. 立ち回り解説 (6点)
    content_depth = 0
    for md_file in glob.glob(os.path.join(SPLATOON_DIR, "*.md")):
        content = read_file(md_file)
        lines = content.count("\n")
        if lines >= 50:
            content_depth += 1
    content_score = min(6, content_depth)
    if content_depth < 6:
        issues.append(f"[コンテンツ] 50行以上のページが{content_depth}ページしかない")
    scores["立ち回り解説"] = (content_score, 6)

    # 8. 執筆者の権威 (3点)
    auth_score = 0
    all_content = ""
    for md_file in glob.glob(os.path.join(SPLATOON_DIR, "*.md")):
        all_content += read_file(md_file)
    if "評価基準" in all_content:
        auth_score += 1
    if "Game8" in all_content or "GameWith" in all_content:
        auth_score += 1
    if "執筆" in all_content or "監修" in all_content or "ウデマエ" in all_content:
        auth_score += 1
    else:
        issues.append("[コンテンツ] 執筆者/権威情報がない")
    scores["執筆者の権威"] = (auth_score, 3)

    # 9. 関連記事リンク (3点)
    link_count = all_content.count("](")
    link_score = min(3, link_count // 30)  # 90リンクで3点
    if link_count < 60:
        issues.append(f"[コンテンツ] 関連リンクが{link_count}個しかない（目標90+）")
    scores["関連記事リンク"] = (link_score, 3)

    # ==============================
    # UX/機能 (20点満点)
    # ==============================

    # 10. 検索機能 (5点)
    search_score = 0
    header = read_file(os.path.join(LAYOUT_DIR, "partials", "header.html"))
    if "search" in header.lower():
        search_score += 3
    if os.path.exists(os.path.join(BASE_DIR, "static", "js", "search.js")):
        search_score += 2
    if search_score == 0:
        issues.append("[UX] 検索機能がない")
    scores["検索機能"] = (search_score, 5)

    # 11. SNSシェア (3点)
    share_score = 0
    share_partial = read_file(os.path.join(LAYOUT_DIR, "partials", "share-buttons.html"))
    single = read_file(os.path.join(LAYOUT_DIR, "_default", "single.html"))
    if share_partial:
        share_score += 1
    if "share-buttons" in single:
        share_score += 1
    if "share-btn" in css:
        share_score += 1
    else:
        issues.append("[UX] シェアボタンのCSSがない")
    scores["SNSシェア"] = (share_score, 3)

    # 12. コメント機能 (4点)
    comment_score = 0
    if "utterances" in single or "comment" in single.lower() or "disqus" in single.lower():
        comment_score += 4
    else:
        issues.append("[UX] コメント機能がない")
    scores["コメント機能"] = (comment_score, 4)

    # 13. 目次 (3点)
    toc_score = 0
    if "TableOfContents" in single:
        toc_score += 1
    if "collapsed" in single or "toggle" in single:
        toc_score += 1
    if "toc-toggle" in css or "toc.collapsed" in css:
        toc_score += 1
    else:
        issues.append("[UX] 目次の折り畳みCSSがない")
    scores["目次"] = (toc_score, 3)

    # 14. 画像遅延読み込み (2点)
    lazy_score = 0
    if 'loading="lazy"' in all_content or "loading=lazy" in all_content:
        lazy_score += 1
    shortcodes_dir = os.path.join(LAYOUT_DIR, "shortcodes")
    all_shortcodes = ""
    for sc in glob.glob(os.path.join(shortcodes_dir, "*.html")):
        all_shortcodes += read_file(sc)
    if 'loading="lazy"' in all_shortcodes:
        lazy_score += 1
    if lazy_score == 0:
        issues.append("[UX] 画像にloading=lazyが設定されていない")
    scores["画像遅延読み込み"] = (lazy_score, 2)

    # 15. お気に入り (2点)
    fav_score = 0
    # 静的サイトでは難しいので、localStorageベースでOK
    if "favorite" in css or "bookmark" in css:
        fav_score += 2
    scores["お気に入り"] = (fav_score, 2)

    # 16. パフォーマンス (1点)
    perf_score = 1  # Hugo静的サイトなので基本的にOK
    scores["パフォーマンス"] = (perf_score, 1)

    # ==============================
    # SEO/構造 (10点満点)
    # ==============================

    # 17. メタタグ (4点)
    baseof = read_file(os.path.join(LAYOUT_DIR, "_default", "baseof.html"))
    meta_score = 0
    if "og:title" in baseof:
        meta_score += 1
    if "og:description" in baseof:
        meta_score += 1
    if "twitter:card" in baseof:
        meta_score += 1
    if "canonical" in baseof:
        meta_score += 1
    scores["メタタグ"] = (meta_score, 4)

    # 18. 構造化データ (3点)
    json_ld_score = 0
    if "application/ld+json" in baseof or "application/ld+json" in single:
        json_ld_score += 3
    else:
        issues.append("[SEO] JSON-LD構造化データがない")
    scores["構造化データ"] = (json_ld_score, 3)

    # 19. 内部リンク設計 (3点)
    internal_score = min(3, link_count // 40)
    if link_count < 80:
        issues.append(f"[SEO] 内部リンクが少ない（{link_count}個）")
    scores["内部リンク設計"] = (internal_score, 3)

    # ==============================
    # レスポンシブ (10点満点)
    # ==============================

    # 20. モバイル表示 (5点)
    mobile_score = 0
    if "@media" in css:
        mobile_score += 2
    if "max-width: 640px" in css or "max-width: 768px" in css:
        mobile_score += 2
    if "mobile-menu" in css:
        mobile_score += 1
    scores["モバイル表示"] = (mobile_score, 5)

    # 21. テーブルスクロール (3点)
    table_score = 0
    if "overflow-x" in css:
        table_score += 2
    if "webkit-overflow-scrolling" in css:
        table_score += 1
    scores["テーブルスクロール"] = (table_score, 3)

    # 22. タッチ操作 (2点)
    touch_score = 0
    if "touch-action" in css or "-webkit-tap" in css:
        touch_score += 1
    if "min-height: 44px" in css or "min-height: 48px" in css:
        touch_score += 1
    else:
        issues.append("[レスポンシブ] タッチターゲットサイズ（44px+）が未設定")
    scores["タッチ操作"] = (touch_score, 2)

    # ==============================
    # 結果出力
    # ==============================
    total = sum(s[0] for s in scores.values())
    max_total = sum(s[1] for s in scores.values())

    print("=" * 60)
    print(f"  Gamers-For サイト品質スコア: {total}/{max_total}点")
    print("=" * 60)
    print()

    categories = {
        "ビジュアル (30点)": ["ティアリスト表示", "武器カードデザイン", "トップページ", "色分け・バッジ"],
        "コンテンツ深度 (30点)": ["ルール別ランキング", "武器個別ページ", "立ち回り解説", "執筆者の権威", "関連記事リンク"],
        "UX/機能 (20点)": ["検索機能", "SNSシェア", "コメント機能", "目次", "画像遅延読み込み", "お気に入り", "パフォーマンス"],
        "SEO/構造 (10点)": ["メタタグ", "構造化データ", "内部リンク設計"],
        "レスポンシブ (10点)": ["モバイル表示", "テーブルスクロール", "タッチ操作"],
    }

    for cat_name, items in categories.items():
        cat_total = sum(scores[i][0] for i in items)
        cat_max = sum(scores[i][1] for i in items)
        print(f"### {cat_name}: {cat_total}/{cat_max}")
        for item in items:
            s, m = scores[item]
            bar = "█" * s + "░" * (m - s)
            status = "✓" if s == m else "△" if s > 0 else "✗"
            print(f"  {status} {item}: {s}/{m} [{bar}]")
        print()

    if issues:
        print(f"### 不足項目 ({len(issues)}件)")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    print()
    print(f">>> 次に改善すべき: 最もインパクトの大きい不足項目から対応")

    return total, max_total, issues


if __name__ == "__main__":
    evaluate()
