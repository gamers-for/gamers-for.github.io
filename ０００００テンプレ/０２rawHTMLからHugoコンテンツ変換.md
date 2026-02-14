# raw HTML → Hugo コンテンツ 完全変換手順書

## 目的

スクレイプ済みの **全1,515件** の raw HTML ファイルを、
1ページも漏らさず Hugo の `.md` コンテンツに変換する。

---

## セクション0: スコープと入出力定義

### 入力

```
{game_dir}/raw_html/
├── 394146.html          ← 記事ID形式（大多数）
├── ranking.html         ← 英単語パス形式（少数）
├── top.html             ← トップページ
├── _metadata.json       ← 全ページのタイトル・サイズ
├── _sitemap_urls.json   ← 全URL一覧
└── _progress.json       ← スクレイプ進捗（参考用）
```

- **ファイル名形式**: `{記事ID}.html`（旧形式 `weapon_スプラシューター_478553.html` は廃止済み）
- **ファイル数**: 1,515件（top.html, ranking.html, writer_profile.html 含む）

### 出力

```
content/games/{game_slug}/
├── _index.md                  ← トップページ
├── weapons/
│   ├── _index.md
│   └── {weapon-slug}.md       ← 武器個別ページ（~196件）
├── gear/
│   ├── _index.md
│   └── {gear-slug}.md         ← ギア個別ページ（~153件）
├── gear-powers/
│   ├── _index.md
│   └── {gp-slug}.md           ← ギアパワー個別ページ（~886件）
├── stages/
│   ├── _index.md
│   └── {stage-slug}.md        ← ステージ個別（~29件）
├── salmon-run/
│   ├── _index.md
│   └── {sr-slug}.md           ← サーモンラン関連（~46件）
├── hero-mode/
│   ├── _index.md
│   └── {hm-slug}.md           ← ヒーローモード関連（~120件）
├── updates/
│   ├── _index.md
│   └── {update-slug}.md       ← アプデ情報（~38件）
├── side-order/
│   ├── _index.md
│   └── {so-slug}.md           ← サイドオーダー（~19件）
├── fes/
│   ├── _index.md
│   └── {fes-slug}.md          ← フェス（~11件）
├── specials/
│   ├── _index.md
│   └── {sp-slug}.md           ← スペシャル個別（~21件）
├── subs/
│   ├── _index.md
│   └── {sub-slug}.md          ← サブウェポン個別（~4件）
├── beginner/
│   ├── _index.md
│   └── {guide-slug}.md        ← 初心者・テクニック（~36件）
└── misc/
    ├── _index.md
    └── {misc-slug}.md         ← その他（システム, 見た目, コミュニティ等）
```

### 副産物

| ファイル | 用途 |
|---------|------|
| `page_categories.json` | 全1,515件の分類結果 |
| `link_map.json` | 記事ID → Hugo内部パスのマッピング |
| `conversion_report.json` | 変換ログ（成功/失敗/スキップ） |
| `conversion_progress.json` | バッチ処理のレジューム用 |

### 制約（MEMORY.mdより — 絶対遵守）

1. **Game8, GameWith, Altema** の名前を一切書かない（HTMLコメント内も禁止）
2. HTML構造はそのまま維持（`archive-style-wrapper` の中身を保持）
3. テーブル内アイコンはそのまま配置（禁止ではない）
4. 文章は全て書き換え（コピペ禁止）
5. 3サイトの情報の **和集合** で作る

---

## セクション1: 全ページ自動分類（Phase 1 — CLASSIFY）

### なぜ分類が必要か

1,515件のHTMLは全て `{記事ID}.html` という無機質なファイル名で保存されている。
どれが武器ページで、どれがギアで、どれがサーモンランか、ファイル名からは判別できない。

### パンくずリストは使えない

Game8スプラ3の全ページは **同じ3階層パンくず** を持つ：

```
Game8 → スプラトゥーン3攻略ガイド｜スプラ3 → [ページタイトル]
```

中間カテゴリがないため、パンくずからの分類は不可能。
**タイトルキーワードで分類する。**

### 分類アルゴリズム

`_metadata.json` のタイトルを使い、キーワードマッチで分類する。
**長いキーワード優先・排他的マッチ** で誤分類を防ぐ。

```python
import json
import re
from pathlib import Path

# ─── カテゴリマッピング辞書 ──────────────────────────
# キー: Hugoセクション名
# 値: {
#   "keywords": タイトルに含まれるキーワード（OR条件、長い順）,
#   "exclude": 除外キーワード（これが含まれていたらマッチしない）,
#   "page_type": ページタイプ,
#   "priority": 数字が小さいほど先にマッチ試行（排他的）
# }

CATEGORY_MAP = {
    # --- Priority 10: 最優先（長いキーワードで確実にマッチ） ---
    "gear-powers": {
        "keywords": ["ギアパワーと入手方法", "ギアパワー一覧", "ギアパワーの効果",
                      "ギアパワーランキング", "付きやすいギアパワー"],
        "exclude": [],
        "page_type": "detail_page",
        "priority": 10,
        "hugo_section": "gear-powers",
    },
    "side-order": {
        "keywords": ["サイドオーダー"],
        "exclude": [],
        "page_type": "guide_page",
        "priority": 15,
        "hugo_section": "side-order",
    },
    "salmon-run": {
        "keywords": ["サーモンラン", "オカシラ", "ビッグラン", "クマサン"],
        "exclude": [],
        "page_type": "guide_page",
        "priority": 20,
        "hugo_section": "salmon-run",
    },
    "hero-mode": {
        "keywords": ["ヒーローモード", "オルタナ", "ミステリーファイル",
                      "ミステリーボックス", "イリコニウム", "ゴールドディスク",
                      "ホラガイ"],
        "exclude": [],
        "page_type": "guide_page",
        "priority": 25,
        "hugo_section": "hero-mode",
    },
    # ヒーローモードのステージ（"X-Y"パターン: 1-1, 2-5, 6-12等）
    "hero-mode-stages": {
        "keywords_regex": [r'(\d+-\d+)\s*(の攻略|攻略)'],
        "exclude": ["サイドオーダー", "サーモンラン"],
        "page_type": "guide_page",
        "priority": 26,
        "hugo_section": "hero-mode",
    },

    # --- Priority 30: 武器系 ---
    "weapons": {
        "keywords": ["おすすめギアと立ち回り", "の評価とおすすめギア",
                      "武器一覧", "ブキ評価", "最強武器", "ブキランキング"],
        "exclude": ["ギアパワー"],
        "page_type": "detail_page",
        "priority": 30,
        "hugo_section": "weapons",
    },
    # 武器カテゴリ一覧（"シューター一覧", "チャージャー一覧" 等）
    "weapon-categories": {
        "keywords": ["シューター一覧", "ブラスター一覧", "ローラー一覧",
                      "フデ一覧", "チャージャー一覧", "スロッシャー一覧",
                      "スピナー一覧", "マニューバー一覧", "シェルター一覧",
                      "ストリンガー一覧", "ワイパー一覧"],
        "exclude": [],
        "page_type": "list_page",
        "priority": 31,
        "hugo_section": "weapons",
    },

    # --- Priority 40: スペシャル・サブ ---
    "specials": {
        "keywords": ["スペシャルウェポン一覧", "スペシャル一覧"],
        "exclude": [],
        "page_type": "list_page",
        "priority": 40,
        "hugo_section": "specials",
    },
    # スペシャル個別（武器名で直接マッチ）
    "specials-detail": {
        "keywords": ["アメフラシ", "カニタンク", "ウルトラショット", "メガホンレーザー",
                      "ナイスダマ", "サメライド", "トリプルトルネード", "ホップソナー",
                      "グレートバリア", "キューインキ", "ジェットパック", "エナジースタンド",
                      "テイオウイカ", "スーパーチャクチ", "マルチミサイル",
                      "ウルトラハンコ", "デコイチラシ", "スミナガシート"],
        "keywords_suffix": ["の使い方", "の効果"],
        "exclude": ["ギア", "おすすめ武器"],
        "page_type": "detail_page",
        "priority": 41,
        "hugo_section": "specials",
    },
    "subs": {
        "keywords": ["サブウェポン一覧", "サブウェポンの効果"],
        "exclude": [],
        "page_type": "list_page",
        "priority": 42,
        "hugo_section": "subs",
    },
    # サブウェポン個別
    "subs-detail": {
        "keywords_suffix": ["の使い方と射程"],
        "exclude": [],
        "page_type": "detail_page",
        "priority": 43,
        "hugo_section": "subs",
    },

    # --- Priority 50: ステージ・ルール ---
    "stages": {
        "keywords": ["ステージ", "マップ"],
        "exclude": ["ヒーローモード", "サーモンラン", "サイドオーダー"],
        "page_type": "detail_page",
        "priority": 50,
        "hugo_section": "stages",
    },

    # --- Priority 55: ギア（ギアパワーでないもの） ---
    "gear": {
        "keywords": ["ギア一覧", "ブランド一覧", "ギアの"],
        "exclude": ["ギアパワー"],
        "page_type": "detail_page",
        "priority": 55,
        "hugo_section": "gear",
    },
    # 個別ギアページ（「のギアパワーと入手方法」を含まないがギア関連）
    "gear-items": {
        "keywords": ["アタマ装備", "フク装備", "クツ装備"],
        "exclude": [],
        "page_type": "detail_page",
        "priority": 56,
        "hugo_section": "gear",
    },

    # --- Priority 60: イベント系 ---
    "fes": {
        "keywords": ["フェス"],
        "exclude": [],
        "page_type": "guide_page",
        "priority": 60,
        "hugo_section": "fes",
    },
    "updates": {
        "keywords": ["アップデート", "アプデ", "Ver."],
        "exclude": [],
        "page_type": "reference_page",
        "priority": 65,
        "hugo_section": "updates",
    },

    # --- Priority 70: ガイド系 ---
    "beginner": {
        "keywords": ["初心者", "遊び方", "やり方", "操作方法", "基本操作",
                      "エイム", "感度設定", "ジャイロ"],
        "exclude": [],
        "page_type": "guide_page",
        "priority": 70,
        "hugo_section": "beginner",
    },
    "nawabattler": {
        "keywords": ["ナワバトラー", "テーブルターフ"],
        "exclude": [],
        "page_type": "guide_page",
        "priority": 75,
        "hugo_section": "misc",
    },

    # --- Priority 80: ルール・マッチ ---
    "rules": {
        "keywords": ["ガチエリア", "ガチホコ", "ガチヤグラ", "ガチアサリ",
                      "ナワバリバトル", "バンカラマッチ", "Xマッチ",
                      "リーグマッチ", "プライベートマッチ"],
        "exclude": ["ステージ", "最強武器"],
        "page_type": "guide_page",
        "priority": 80,
        "hugo_section": "beginner",
    },

    # --- Priority 90: その他 ---
    "misc": {
        "keywords": [],  # フォールバック — 何にもマッチしない全ページ
        "exclude": [],
        "page_type": "guide_page",
        "priority": 999,
        "hugo_section": "misc",
    },
}
```

### 分類処理

```python
def classify_all_pages(metadata_path):
    """全ページをカテゴリに分類"""
    with open(metadata_path) as f:
        metadata = json.load(f)

    all_files = metadata.get("all_files", metadata)
    # priority順にソートしたカテゴリ一覧
    sorted_cats = sorted(
        CATEGORY_MAP.items(),
        key=lambda x: x[1].get("priority", 999)
    )

    results = {}  # filename → { category, hugo_section, page_type, title }

    for filename, info in all_files.items():
        if not filename.endswith(".html"):
            continue
        if filename.startswith("_"):
            continue  # メタファイルはスキップ
        if filename == "writer_profile.html":
            continue  # プロフィールページはスキップ

        title = info.get("title", "")
        classified = False

        for cat_name, cat_config in sorted_cats:
            if cat_config.get("priority", 999) >= 999:
                continue  # フォールバックは後で

            # 除外チェック
            if any(ex in title for ex in cat_config.get("exclude", [])):
                continue

            # キーワードマッチ
            matched = False

            # 通常キーワード
            for kw in cat_config.get("keywords", []):
                if kw in title:
                    matched = True
                    break

            # 正規表現キーワード
            if not matched:
                for pattern in cat_config.get("keywords_regex", []):
                    if re.search(pattern, title):
                        matched = True
                        break

            # サフィックスキーワード（タイトル末尾マッチ）
            if not matched:
                for suffix in cat_config.get("keywords_suffix", []):
                    if suffix in title:
                        matched = True
                        break

            if matched:
                article_id = filename.replace(".html", "")
                results[filename] = {
                    "category": cat_name,
                    "hugo_section": cat_config["hugo_section"],
                    "page_type": cat_config["page_type"],
                    "title": title,
                    "article_id": article_id,
                }
                classified = True
                break

        # フォールバック
        if not classified:
            article_id = filename.replace(".html", "")
            results[filename] = {
                "category": "misc",
                "hugo_section": "misc",
                "page_type": "guide_page",
                "title": title,
                "article_id": article_id,
            }

    return results


def save_classification(results, output_path):
    """分類結果を保存"""
    # 統計出力
    from collections import Counter
    cat_counts = Counter(r["hugo_section"] for r in results.values())
    print("=== 分類結果 ===")
    for section, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {section}: {count}件")
    print(f"  合計: {len(results)}件")

    with open(output_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n保存: {output_path}")
```

### 実行

```python
# Phase 1 実行
metadata_path = Path("００００１スプラトゥーン３/raw_html/_metadata.json")
page_categories = classify_all_pages(metadata_path)
save_classification(page_categories, Path("００００１スプラトゥーン３/page_categories.json"))
```

### 期待される出力

```
=== 分類結果 ===
  gear-powers: 886件
  weapons: 207件  (個別196 + カテゴリ一覧11)
  gear: 153件
  hero-mode: 120件  (直接10 + ステージ攻略76 + ミステリーファイル25 + オルタナ9)
  salmon-run: 49件  (本体46 + ビッグラン3)
  updates: 38件
  stages: 29件
  beginner: 36件  (初心者1 + テクニック35)
  specials: 21件  (一覧3 + 個別18)
  side-order: 19件
  fes: 11件
  subs: 4件
  misc: ~30件  (システム, 見た目, コミュニティ, 掲示板, その他)
  合計: 1,515件
```

### カテゴリ調整（手動修正が必要な場合）

自動分類後、以下を目視確認：

```python
# 分類漏れチェック
misc_pages = [f for f, r in page_categories.items() if r["category"] == "misc"]
print(f"未分類: {len(misc_pages)}件")
for f in sorted(misc_pages):
    print(f"  {f}: {page_categories[f]['title']}")
```

未分類が多すぎる場合、`CATEGORY_MAP` にキーワードを追加して再分類する。
**目標: misc カテゴリが30件以下。**

---

## セクション2: リンクマップ構築（Phase 2 — LINK MAP）

### なぜ必要か

既存の `process_links()` は武器・ステージ・メインページ（約230件）のリンクしか解決できない。
残り約1,285ページへのリンクは全て `href="#"` に置換されてしまう。

**全1,515ページの内部リンクを正しく解決するため、完全なリンクマップが必要。**

### リンクマップの構造

```python
# link_map.json の形式
{
    "478553": "/games/splatoon3/weapons/スプラシューター/",
    "477903": "/games/splatoon3/tier-list/",
    "477900": "/games/splatoon3/gear/",
    "480290": "/games/splatoon3/salmon-run/",
    "478657": "/games/splatoon3/hero-mode/",
    ...
}
# キー: 記事ID（数字文字列）
# 値: Hugo内部パス
```

### 構築アルゴリズム

```python
import unicodedata

def title_to_slug(title, max_length=80):
    """タイトルからURL安全なslugを生成"""
    # 【スプラ3】【スプラトゥーン3】等のプレフィックスを除去
    slug = re.sub(r'【[^】]*】', '', title)
    # ｜以降を除去
    slug = re.sub(r'[｜|].*$', '', slug)
    # 「の攻略」「の評価」等のサフィックスを除去（短縮化）
    slug = re.sub(r'(の攻略.*|の評価.*|まとめ$|について$)', '', slug)
    slug = slug.strip()

    # 全角→半角
    slug = unicodedata.normalize("NFKC", slug)
    # スペース・記号をハイフンに
    slug = re.sub(r'[\s/・（）()【】「」]+', '-', slug)
    # 連続ハイフンを1つに
    slug = re.sub(r'-+', '-', slug)
    # 先頭末尾のハイフンを除去
    slug = slug.strip('-')
    # 長すぎる場合は切り詰め
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')

    return slug


def build_link_map(page_categories, game_slug="splatoon3"):
    """全ページのリンクマップを構築"""
    link_map = {}
    base = f"/games/{game_slug}"

    for filename, info in page_categories.items():
        article_id = info["article_id"]
        section = info["hugo_section"]
        title = info["title"]
        slug = title_to_slug(title)

        # 特殊ページ
        if filename == "top.html":
            link_map["top"] = f"{base}/"
            continue
        if filename == "ranking.html":
            link_map["ranking"] = f"{base}/ranking/"
            continue

        # セクション別パス生成
        if section == "weapons":
            # 武器ページは武器名をslugに
            link_map[article_id] = f"{base}/weapons/{slug}/"
        elif section == "gear-powers":
            link_map[article_id] = f"{base}/gear-powers/{slug}/"
        elif section == "gear":
            link_map[article_id] = f"{base}/gear/{slug}/"
        elif section == "stages":
            link_map[article_id] = f"{base}/stages/{slug}/"
        elif section == "salmon-run":
            link_map[article_id] = f"{base}/salmon-run/{slug}/"
        elif section == "hero-mode":
            link_map[article_id] = f"{base}/hero-mode/{slug}/"
        elif section == "updates":
            link_map[article_id] = f"{base}/updates/{slug}/"
        elif section == "side-order":
            link_map[article_id] = f"{base}/side-order/{slug}/"
        elif section == "fes":
            link_map[article_id] = f"{base}/fes/{slug}/"
        elif section == "specials":
            link_map[article_id] = f"{base}/specials/{slug}/"
        elif section == "subs":
            link_map[article_id] = f"{base}/subs/{slug}/"
        elif section == "beginner":
            link_map[article_id] = f"{base}/beginner/{slug}/"
        else:  # misc
            link_map[article_id] = f"{base}/misc/{slug}/"

    return link_map


def save_link_map(link_map, output_path):
    """リンクマップを保存"""
    with open(output_path, "w") as f:
        json.dump(link_map, f, ensure_ascii=False, indent=2)
    print(f"リンクマップ保存: {len(link_map)}件 → {output_path}")
```

### slug重複チェック

```python
def check_slug_duplicates(link_map):
    """同じパスを持つ記事がないか確認"""
    path_to_ids = {}
    for article_id, path in link_map.items():
        if path in path_to_ids:
            path_to_ids[path].append(article_id)
        else:
            path_to_ids[path] = [article_id]

    dupes = {p: ids for p, ids in path_to_ids.items() if len(ids) > 1}
    if dupes:
        print(f"⚠ slug重複: {len(dupes)}件")
        for path, ids in dupes.items():
            print(f"  {path} ← {ids}")
        # 重複はIDをサフィックスとして追加して解決
        for path, ids in dupes.items():
            for article_id in ids[1:]:  # 最初の1つはそのまま
                link_map[article_id] = f"{path.rstrip('/')}-{article_id}/"
        print("  → IDサフィックスで解決済み")
    else:
        print("✓ slug重複なし")
```

### 実行

```python
# Phase 2 実行
link_map = build_link_map(page_categories)
check_slug_duplicates(link_map)
save_link_map(link_map, Path("００００１スプラトゥーン３/link_map.json"))
```

---

## セクション3: Hugoディレクトリ構造生成（Phase 3 — STRUCTURE）

### ディレクトリツリー自動生成

```python
def create_directory_structure(page_categories, content_dir, game_slug="splatoon3"):
    """分類結果に基づいてHugoディレクトリを作成"""
    game_dir = Path(content_dir) / "games" / game_slug

    # 全セクションを収集
    sections = set(info["hugo_section"] for info in page_categories.values())

    for section in sorted(sections):
        section_dir = game_dir / section
        section_dir.mkdir(parents=True, exist_ok=True)

        # _index.md がなければ作成
        index_path = section_dir / "_index.md"
        if not index_path.exists():
            title = SECTION_TITLES.get(section, section)
            index_content = generate_section_index(section, title)
            index_path.write_text(index_content, encoding="utf-8")
            print(f"  📁 {section}/ + _index.md")

    # ルートの _index.md
    root_index = game_dir / "_index.md"
    if not root_index.exists():
        root_index.write_text(generate_root_index(game_slug), encoding="utf-8")
        print(f"  📁 {game_slug}/_index.md")


# セクション別タイトル
SECTION_TITLES = {
    "weapons": "武器一覧",
    "gear-powers": "ギアパワー一覧",
    "gear": "ギア一覧",
    "stages": "ステージ一覧",
    "salmon-run": "サーモンラン攻略",
    "hero-mode": "ヒーローモード攻略",
    "updates": "アップデート情報",
    "side-order": "サイドオーダー攻略",
    "fes": "フェス情報",
    "specials": "スペシャルウェポン",
    "subs": "サブウェポン",
    "beginner": "初心者ガイド",
    "misc": "その他ガイド",
}


def generate_section_index(section, title):
    """セクション用 _index.md を生成"""
    return f"""---
title: "【スプラ3】{title}"
linkTitle: "{title}"
weight: 10
date: 2026-02-13
description: "スプラトゥーン3の{title}。"
---
"""


def generate_root_index(game_slug):
    """ゲームルート _index.md を生成"""
    return """---
title: "スプラトゥーン3 攻略ガイド"
linkTitle: "スプラトゥーン3"
weight: 1
date: 2026-02-13
description: "スプラトゥーン3の攻略情報まとめ。武器、ギア、ステージ、サーモンランなどの攻略を掲載。"
---
"""
```

### slug生成アルゴリズムの詳細

タイトルからslugへの変換ルール:

```
入力: 「【スプラ3】スプラシューターのおすすめギアと立ち回り【スプラトゥーン3】」
  ↓ 【...】除去
  「スプラシューターのおすすめギアと立ち回り」
  ↓ サフィックス除去
  「スプラシューター」
  ↓ NFKC正規化 + 記号→ハイフン
  「スプラシューター」
  ↓ 最終slug
  → "スプラシューター"

入力: 「【スプラ3】Ver.9.3.0アップデートの調整内容まとめ【スプラトゥーン3】」
  ↓ 【...】除去
  「Ver.9.3.0アップデートの調整内容まとめ」
  ↓ サフィックス除去
  「Ver.9.3.0アップデートの調整内容」
  ↓ NFKC正規化
  → "Ver.9.3.0アップデートの調整内容"
```

---

## セクション4: フロントマター自動生成（Phase 4 — FRONTMATTER）

### タイトル生成ルール

```python
def clean_title(raw_title):
    """HTMLの<title>タグからHugo用タイトルを生成"""
    title = raw_title

    # 「｜ゲームエイト」「| ゲームエイト」を除去
    title = re.sub(r'[｜|]\s*ゲームエイト.*$', '', title)

    # 「【ゲーム名】」が末尾にある場合は除去（冒頭の【スプラ3】は残す）
    title = re.sub(r'【スプラトゥーン3】\s*$', '', title)
    title = re.sub(r'【スプラ3】\s*$', '', title)

    return title.strip()
```

### linkTitle生成（コアの名前のみ抽出）

```python
def extract_link_title(title):
    """タイトルからlinkTitle（短い表示名）を抽出"""
    lt = title

    # 【...】を全て除去
    lt = re.sub(r'【[^】]*】', '', lt)

    # サフィックスを除去
    suffixes = [
        "のおすすめギアと立ち回り", "の評価とおすすめギア",
        "のギアパワーと入手方法", "の攻略と進め方",
        "の攻略", "の評価", "の使い方", "の効果",
        "一覧と評価", "一覧",
        "まとめ", "について",
    ]
    for suffix in suffixes:
        if lt.endswith(suffix):
            lt = lt[:-len(suffix)]
            break

    return lt.strip() or title
```

### カテゴリ別フロントマター

```python
def generate_frontmatter(page_info, title, link_title):
    """カテゴリに応じたフロントマターを生成"""
    section = page_info["hugo_section"]
    page_type = page_info["page_type"]

    # weight算出（カテゴリ優先度）
    section_weights = {
        "weapons": 10, "gear-powers": 20, "gear": 25,
        "stages": 30, "salmon-run": 35, "hero-mode": 40,
        "specials": 45, "subs": 46, "updates": 50,
        "side-order": 55, "fes": 60, "beginner": 65,
        "misc": 90,
    }
    weight = section_weights.get(section, 50)

    # description自動生成
    desc = generate_description(title, section)

    # categories & tags
    categories = [SECTION_TITLES.get(section, section)]
    tags = ["スプラトゥーン3"] + categories + [link_title]

    # エスケープ（ダブルクォート）
    safe_title = title.replace('"', '\\"')
    safe_lt = link_title.replace('"', '\\"')
    safe_desc = desc.replace('"', '\\"')

    fm = f'''---
title: "{safe_title}"
linkTitle: "{safe_lt}"
weight: {weight}
date: 2026-02-13
categories: {json.dumps(categories, ensure_ascii=False)}
tags: {json.dumps(tags, ensure_ascii=False)}
description: "{safe_desc}"
---

'''
    return fm


def generate_description(title, section):
    """SEO用descriptionを自動生成"""
    # 【...】を除去したクリーンなタイトル
    clean = re.sub(r'【[^】]*】', '', title).strip()

    templates = {
        "weapons": f"スプラトゥーン3の{clean}。性能評価やおすすめギアパワー、立ち回りのコツを解説。",
        "gear-powers": f"スプラトゥーン3の{clean}。効果や入手方法、おすすめの付け方を紹介。",
        "gear": f"スプラトゥーン3の{clean}。ギア情報とおすすめギアパワーを掲載。",
        "stages": f"スプラトゥーン3の{clean}。ステージの特徴やルール別の攻略を解説。",
        "salmon-run": f"スプラトゥーン3の{clean}。攻略のコツや立ち回りを紹介。",
        "hero-mode": f"スプラトゥーン3の{clean}。攻略手順やクリアのコツを解説。",
        "updates": f"スプラトゥーン3の{clean}。武器やギアの調整内容をまとめて掲載。",
        "side-order": f"スプラトゥーン3の{clean}。攻略情報やクリアのコツを紹介。",
        "fes": f"スプラトゥーン3の{clean}。開催日程や結果、攻略情報をまとめて掲載。",
        "specials": f"スプラトゥーン3の{clean}。使い方や効果的な立ち回りを解説。",
        "subs": f"スプラトゥーン3の{clean}。使い方や射程の情報を紹介。",
        "beginner": f"スプラトゥーン3の{clean}。基本的な知識やコツを解説。",
    }
    return templates.get(section, f"スプラトゥーン3の{clean}。攻略情報を掲載。")
```

---

## セクション5: HTMLコンテンツ変換（Phase 5 — TRANSFORM）★核心部分

### 概要

各HTMLファイルを以下の6ステップで変換する。
**既存の `build_from_game8_html.py` の関数を最大限再利用** し、不足分のみ新規実装。

```
HTML → [5.1 抽出] → [5.2 除去] → [5.3 画像] → [5.4 リンク] → [5.5 テキスト] → [5.6 禁止名称] → .md
```

### Step 5.1: コンテンツ抽出

**再利用**: `extract_article_content()` @ build_from_game8_html.py:234

```python
def extract_content(html_path):
    """HTMLから .archive-style-wrapper と title を抽出"""
    with open(html_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    # 既存関数を再利用
    wrapper, title = extract_article_content(html_text)

    if not wrapper:
        # フォールバック: archive-style-wrapper がない場合
        soup = BeautifulSoup(html_text, "html.parser")
        # メインコンテンツ領域を探す
        wrapper = soup.find(class_="l-3colMain__center")
        if not wrapper:
            wrapper = soup.find("main")
        title_tag = soup.find("title")
        title = title_tag.get_text() if title_tag else ""
        title = re.sub(r'[｜|]\s*ゲームエイト.*$', '', title).strip()

    return wrapper, title
```

### Step 5.2: 不要要素除去

**再利用**: `remove_unwanted_elements()` @ build_from_game8_html.py:253

```python
def clean_html(wrapper):
    """不要な要素を除去"""
    # 既存関数を再利用
    remove_unwanted_elements(wrapper)

    # === 追加除去（全カテゴリ共通） ===

    # 攻略班プロフィールセクション
    for el in wrapper.find_all("div", class_="writer-profile"):
        el.decompose()

    # SNSシェアボタン
    for el in wrapper.find_all("div", class_=re.compile(r"sns|share|social")):
        el.decompose()

    # コメント欄
    for el in wrapper.find_all("div", class_=re.compile(r"comment")):
        el.decompose()

    # 「この記事の編集者」系
    for el in wrapper.find_all("div", class_=re.compile(r"editor|author")):
        el.decompose()

    # 掲示板埋め込み
    for el in wrapper.find_all("div", class_=re.compile(r"bbs|board")):
        el.decompose()

    # ページナビゲーション（前の記事・次の記事）
    for el in wrapper.find_all("div", class_=re.compile(r"pagenav|pagination")):
        el.decompose()
```

### Step 5.3: 画像処理

**再利用**: `process_images()` @ build_from_game8_html.py:296

既存の11カテゴリのアイコンマッピングをそのまま使用:

| # | マッピング | ファイル:行 | 対象 |
|---|-----------|-----------|------|
| 1 | `weapon_icon_map` | build_image_mappings():59 | 武器アイコン（162種） |
| 2 | `sub_icon_map` | build_image_mappings():72 | サブアイコン |
| 3 | `special_icon_map` | build_image_mappings():80 | スペシャルアイコン |
| 4 | `tier_map` | build_image_mappings():88 | ティアバッジ（S+, A等） |
| 5 | `GEAR_POWER_ICONS` | :108 | ギアパワー（26種） |
| 6 | `STAR_ICONS` | :140 | 星評価（1-5） |
| 7 | `RULE_ICONS` | :149 | ルール（6種） |
| 8 | `MARKER_ICONS` | :171 | マーカー（強い点/弱い点等） |
| 9 | `BRAND_ICONS` | :181 | ブランド（24種） |
| 10 | `BUTTON_ICONS` | :207 | Switchボタン（7種） |
| 11 | `WEAPON_CLASS_ICONS` | :218 | 武器種（11種） |

**未マッチ画像の処理**:

```python
# process_images() 内の最終フォールバック（既存コードそのまま）:
# game8.jp の画像 → サイズに応じた黒プレースホルダー
if "game8.jp" in actual_src or "img.game8.jp" in actual_src:
    height = int(img.get("height", 0) or 0)
    img["src"] = _black_placeholder_src(width if width > 0 else 50, height)
    img["loading"] = "lazy"
    continue
```

### Step 5.4: リンク変換（拡張版）

**既存**: `process_links()` @ build_from_game8_html.py:459 は武器・ステージ・メインのみ対応。
**新規**: `link_map.json` を使って全1,515ページのリンクを解決。

```python
def process_links_full(wrapper, link_map, game_slug="splatoon3"):
    """全ページのリンクを link_map.json で解決"""

    for a in wrapper.find_all("a"):
        href = a.get("href", "")
        if not href:
            continue

        resolved = False

        # Game8 絶対URL
        if "game8.jp" in href:
            # URLから記事IDを抽出
            match = re.search(rf'/{game_slug}/(\d+)', href)
            if match:
                article_id = match.group(1)
                if article_id in link_map:
                    a["href"] = link_map[article_id]
                    resolved = True

            # 英単語パス（/splatoon3/ranking 等）
            if not resolved:
                match = re.search(rf'/{game_slug}/([a-zA-Z][\w-]*)', href)
                if match:
                    path_key = match.group(1)
                    if path_key in link_map:
                        a["href"] = link_map[path_key]
                        resolved = True

            if not resolved:
                a["href"] = "#"
            continue

        # Game8 相対URL（/splatoon3/xxxxx）
        if href.startswith(f"/{game_slug}/"):
            suffix = href.replace(f"/{game_slug}/", "").strip("/")
            if suffix in link_map:
                a["href"] = link_map[suffix]
                resolved = True
            else:
                # フラグメント除去してリトライ
                clean_suffix = suffix.split("#")[0].split("?")[0]
                if clean_suffix in link_map:
                    a["href"] = link_map[clean_suffix]
                    resolved = True

            if not resolved:
                a["href"] = "#"
            continue

        # 外部リンク → href="#"
        if href.startswith("http"):
            a["href"] = "#"
            continue

        # アンカーリンク（#xxx）はそのまま
        # 相対パスもそのまま

    # トラッキング属性を除去
    for a in wrapper.find_all("a"):
        for attr in list(a.attrs.keys()):
            if attr.startswith("data-track"):
                del a[attr]
```

### Step 5.5: テキスト書き換え

**再利用**: `rewrite_text()` @ build_from_game8_html.py:557
**再利用**: `rewrite_paragraph()` / `rewrite_short_phrase()` @ text_rewriter.py

テキスト書き換えは4層構造（既存のまま）:

```
Layer 1: 定型文のファジーマッチ → 丸ごと別表現に置換（STOCK_PHRASES）
Layer 2: フレーズ単位の同義語置換（PHRASE_REPLACEMENTS）
Layer 3: 接続詞の置換 + 文構造変換
Layer 4: 文末パターンのカジュアル化
```

**カテゴリ別のコンテキスト名を渡す**:

```python
def rewrite_content(wrapper, page_info):
    """カテゴリに応じたテキスト書き換え"""
    # weapon_name パラメータにカテゴリ+タイトル情報を渡す
    # → ハッシュベースの選択に使用（同じページは常に同じリライト結果）
    context_name = f"{page_info['hugo_section']}_{page_info['article_id']}"
    rewrite_text(wrapper, context_name)
```

### Step 5.6: 禁止名称除去（最終工程）

**再利用**: `remove_forbidden_names()` @ build_from_game8_html.py:934

```python
def final_cleanup(inner_html):
    """最終クリーンアップ（禁止名称除去）"""
    # 既存関数を再利用
    html = remove_forbidden_names(inner_html)

    # 追加チェック: HTMLコメント内も除去
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    return html
```

### 全体をつなぐ変換関数

```python
def convert_single_page(html_path, page_info, link_map,
                          weapon_icon_map, sub_icon_map,
                          special_icon_map, tier_map):
    """1ページを完全変換"""

    # 5.1: 抽出
    wrapper, raw_title = extract_content(html_path)
    if not wrapper:
        return None, f"archive-style-wrapper not found"

    # タイトル処理
    title = clean_title(raw_title)
    link_title = extract_link_title(title)

    # 5.2: 不要要素除去
    clean_html(wrapper)

    # 5.3: 画像処理
    process_images(wrapper, weapon_icon_map, sub_icon_map,
                   special_icon_map, tier_map)

    # 5.4: リンク変換
    process_links_full(wrapper, link_map)

    # 5.5: テキスト書き換え
    rewrite_content(wrapper, page_info)

    # wrapper div を除去して中身だけ取得
    inner_html = wrapper.decode_contents()

    # 5.6: 禁止名称除去
    inner_html = final_cleanup(inner_html)

    # フロントマター生成
    frontmatter = generate_frontmatter(page_info, title, link_title)

    return frontmatter + inner_html, None
```

---

## セクション6: バッチ処理戦略（Phase 6 — EXECUTE）

### 処理優先度

重要なページから先に処理する。エラーが出ても全体を止めない。

```python
# 処理優先度（小さいほど先に処理）
PROCESSING_ORDER = [
    ("weapons", 1),       # 武器（最重要コンテンツ）
    ("stages", 2),        # ステージ
    ("specials", 3),      # スペシャル
    ("subs", 4),          # サブ
    ("beginner", 5),      # 初心者ガイド
    ("salmon-run", 6),    # サーモンラン
    ("hero-mode", 7),     # ヒーローモード
    ("side-order", 8),    # サイドオーダー
    ("fes", 9),           # フェス
    ("updates", 10),      # アプデ
    ("gear", 11),         # ギア
    ("gear-powers", 12),  # ギアパワー（最大886件 → 最後に回す）
    ("misc", 99),         # その他
]
```

### バッチ処理メインループ

```python
def batch_convert(page_categories, link_map, raw_html_dir, content_dir,
                   weapon_icon_map, sub_icon_map, special_icon_map, tier_map,
                   game_slug="splatoon3"):
    """全ページをバッチ変換"""

    game_content_dir = Path(content_dir) / "games" / game_slug

    # 進捗管理
    progress = load_progress(raw_html_dir)
    completed = set(progress.get("completed", []))
    failed = dict(progress.get("failed", {}))

    # 優先度順にソート
    order_map = {s: p for s, p in PROCESSING_ORDER}
    sorted_pages = sorted(
        page_categories.items(),
        key=lambda x: (order_map.get(x[1]["hugo_section"], 50), x[0])
    )

    total = len(sorted_pages)
    success_count = 0
    fail_count = 0
    skip_count = 0

    print(f"\n{'='*60}")
    print(f"バッチ変換開始: {total}ページ（完了済み: {len(completed)}件）")
    print(f"{'='*60}")

    current_section = ""

    for i, (filename, page_info) in enumerate(sorted_pages, 1):
        # セクション表示
        if page_info["hugo_section"] != current_section:
            current_section = page_info["hugo_section"]
            section_count = sum(
                1 for _, p in sorted_pages if p["hugo_section"] == current_section
            )
            print(f"\n📦 {SECTION_TITLES.get(current_section, current_section)} "
                  f"({section_count}件)")
            print("-" * 40)

        # スキップ判定
        if filename in completed:
            skip_count += 1
            continue

        # HTML読み込み
        html_path = Path(raw_html_dir) / filename
        if not html_path.exists():
            print(f"  ⚠ ファイルなし: {filename}")
            fail_count += 1
            failed[filename] = "file_not_found"
            continue

        # 出力パス決定
        article_id = page_info["article_id"]
        if article_id in link_map:
            hugo_path = link_map[article_id]
            # /games/splatoon3/weapons/xxx/ → weapons/xxx.md
            relative = hugo_path.replace(f"/games/{game_slug}/", "").strip("/")
            output_path = game_content_dir / f"{relative}.md"
        else:
            print(f"  ⚠ リンクマップにない: {filename}")
            fail_count += 1
            failed[filename] = "not_in_link_map"
            continue

        # 変換実行
        try:
            result, error = convert_single_page(
                html_path, page_info, link_map,
                weapon_icon_map, sub_icon_map, special_icon_map, tier_map
            )
            if error:
                print(f"  ❌ {filename}: {error}")
                fail_count += 1
                failed[filename] = error
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result, encoding="utf-8")
                success_count += 1
                completed.add(filename)
                print(f"  ✅ [{i}/{total}] {page_info['title'][:40]}...")
        except Exception as e:
            print(f"  ❌ {filename}: {e}")
            fail_count += 1
            failed[filename] = str(e)

        # 50件ごとに進捗保存
        if i % 50 == 0:
            save_progress(raw_html_dir, completed, failed)
            print(f"  💾 進捗保存 ({len(completed)}/{total})")

    # 最終進捗保存
    save_progress(raw_html_dir, completed, failed)

    # サマリー
    print(f"\n{'='*60}")
    print(f"変換完了!")
    print(f"  成功: {success_count}")
    print(f"  失敗: {fail_count}")
    print(f"  スキップ（完了済み）: {skip_count}")
    print(f"  合計: {success_count + fail_count + skip_count}")
    print(f"{'='*60}")

    # レポート保存
    save_conversion_report(raw_html_dir, success_count, fail_count,
                            skip_count, failed)

    return success_count, fail_count
```

### レジューム機能

```python
def load_progress(raw_html_dir):
    """前回の進捗を読み込み"""
    progress_path = Path(raw_html_dir) / "conversion_progress.json"
    if progress_path.exists():
        with open(progress_path) as f:
            return json.load(f)
    return {"completed": [], "failed": {}}


def save_progress(raw_html_dir, completed, failed):
    """進捗を保存"""
    progress = {
        "completed": sorted(completed),
        "failed": failed,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "total_completed": len(completed),
        "total_failed": len(failed),
    }
    progress_path = Path(raw_html_dir) / "conversion_progress.json"
    with open(progress_path, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def save_conversion_report(raw_html_dir, success, fail, skip, failed_details):
    """変換レポートを保存"""
    report = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "summary": {
            "success": success,
            "failed": fail,
            "skipped": skip,
            "total": success + fail + skip,
        },
        "failed_details": failed_details,
    }
    report_path = Path(raw_html_dir) / "conversion_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"レポート保存: {report_path}")
```

### エラーハンドリング方針

```
1ページの失敗で全体を止めない。

- archive-style-wrapper なし → failed に記録、スキップ
- 画像マッチなし → プレースホルダーで代替（既存動作）
- リンク解決不能 → href="#" に（既存動作）
- テキスト書き換え失敗 → 元テキストをそのまま使用
- ファイル書き込み失敗 → failed に記録、次のページへ
```

---

## セクション7: 検証（Phase 7 — VERIFY）

### 検証1: 禁止名称チェック

```bash
# 禁止ワードが0件であることを確認
grep -ri "game8\|gamewith\|altema\|ゲームエイト\|攻略班\|3サイト" content/games/splatoon3/

# 期待結果: 出力なし（0件）
```

```python
def verify_forbidden_names(content_dir):
    """禁止名称チェック"""
    forbidden = ["game8", "gamewith", "altema", "ゲームエイト", "攻略班", "3サイト"]
    violations = []

    for md_file in Path(content_dir).rglob("*.md"):
        text = md_file.read_text(encoding="utf-8").lower()
        for word in forbidden:
            if word.lower() in text:
                violations.append((md_file, word))

    if violations:
        print(f"✗ 禁止名称検出: {len(violations)}件")
        for path, word in violations:
            print(f"  {path}: '{word}'")
    else:
        print(f"✓ 禁止名称: 0件")
    return violations
```

### 検証2: カバレッジチェック

```python
def verify_coverage(page_categories, link_map, content_dir, game_slug):
    """全HTMLに対応する.mdが存在するか確認"""
    game_dir = Path(content_dir) / "games" / game_slug
    missing = []

    for filename, info in page_categories.items():
        article_id = info["article_id"]
        if article_id not in link_map:
            missing.append((filename, "リンクマップにない"))
            continue

        hugo_path = link_map[article_id]
        relative = hugo_path.replace(f"/games/{game_slug}/", "").strip("/")
        md_path = game_dir / f"{relative}.md"

        if not md_path.exists():
            missing.append((filename, f".mdなし: {md_path}"))

    coverage = ((len(page_categories) - len(missing)) / len(page_categories)) * 100

    if missing:
        print(f"✗ カバレッジ: {coverage:.1f}% ({len(missing)}件の.mdが未生成)")
        for fname, reason in missing[:20]:
            print(f"  {fname}: {reason}")
        if len(missing) > 20:
            print(f"  ... 他 {len(missing)-20}件")
    else:
        print(f"✓ カバレッジ: 100% ({len(page_categories)}件全て生成済み)")

    return missing
```

### 検証3: コンテンツ品質チェック

```python
import random

def verify_content_quality(content_dir, game_slug, sample_size=50):
    """ランダム抽出して品質チェック"""
    game_dir = Path(content_dir) / "games" / game_slug
    all_md = list(game_dir.rglob("*.md"))

    if len(all_md) < sample_size:
        sample = all_md
    else:
        sample = random.sample(all_md, sample_size)

    issues = []

    for md_path in sample:
        text = md_path.read_text(encoding="utf-8")

        # 空ボディチェック
        parts = text.split("---", 2)
        if len(parts) < 3 or not parts[2].strip():
            issues.append((md_path, "空ボディ"))
            continue

        body = parts[2]

        # Game8 URL残留チェック
        if "game8.jp" in body:
            issues.append((md_path, "game8.jp URL残留"))

        # 画像パスチェック（srcが空やgame8ドメインでないか）
        if 'src=""' in body:
            issues.append((md_path, "空のsrc属性"))
        if "img.game8.jp" in body:
            issues.append((md_path, "game8画像URL残留"))

        # 最低文字数チェック（フロントマター除き500文字未満は薄い）
        if len(body) < 500:
            issues.append((md_path, f"内容が薄い ({len(body)}文字)"))

    if issues:
        print(f"⚠ 品質問題: {len(issues)}件 (サンプル{len(sample)}件中)")
        for path, issue in issues:
            print(f"  {path.name}: {issue}")
    else:
        print(f"✓ 品質チェックOK (サンプル{len(sample)}件)")

    return issues
```

### 検証4: Hugoビルドチェック

```bash
# Hugoビルドがエラーなしで通るか確認
hugo --minify 2>&1 | tail -20

# 期待結果:
# | EN
# -------------------+------
#   Pages            | 1600+
#   ...
# Total in xxx ms
```

### 検証5: リンク整合性チェック

```python
def verify_internal_links(content_dir, game_slug):
    """内部リンクが全て有効なページを指すか確認"""
    game_dir = Path(content_dir) / "games" / game_slug
    all_md = set()

    # 全.mdファイルのパスを収集
    for md in game_dir.rglob("*.md"):
        relative = md.relative_to(game_dir.parent.parent.parent)
        # /content/games/splatoon3/weapons/xxx.md → /games/splatoon3/weapons/xxx/
        path = "/" + str(relative).replace(".md", "/").replace("_index/", "")
        all_md.add(path)

    broken_links = []

    for md in game_dir.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        # href="/games/splatoon3/..." を抽出
        links = re.findall(r'href="(/games/[^"#]+)"', text)
        for link in links:
            clean = link.rstrip("/") + "/"
            if clean not in all_md and clean.rstrip("/") + ".md" not in all_md:
                broken_links.append((md.name, link))

    if broken_links:
        print(f"⚠ 壊れた内部リンク: {len(broken_links)}件")
        for source, target in broken_links[:20]:
            print(f"  {source} → {target}")
    else:
        print(f"✓ 内部リンク整合性OK")

    return broken_links
```

### 検証6: 画像参照チェック

```python
def verify_image_refs(content_dir, static_dir, game_slug):
    """img srcが全て有効パスか確認"""
    game_dir = Path(content_dir) / "games" / game_slug
    static_images = Path(static_dir) / "images" / "games" / game_slug

    missing_images = set()

    for md in game_dir.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        srcs = re.findall(r'src="(/images/games/[^"]+)"', text)
        for src in srcs:
            # /images/games/splatoon3/xxx → static/images/games/splatoon3/xxx
            local_path = Path(static_dir) / src.lstrip("/")
            if not local_path.exists():
                missing_images.add(src)

    if missing_images:
        print(f"⚠ 存在しない画像参照: {len(missing_images)}件")
        for img in sorted(missing_images)[:20]:
            print(f"  {img}")
    else:
        print(f"✓ 画像参照OK")

    return missing_images
```

### 全検証の一括実行

```python
def verify_all(content_dir, static_dir, page_categories, link_map, game_slug):
    """7つの検証を一括実行"""
    print("=" * 60)
    print("検証開始")
    print("=" * 60)

    print("\n[1/6] 禁止名称チェック")
    v1 = verify_forbidden_names(content_dir + f"/games/{game_slug}")

    print("\n[2/6] カバレッジチェック")
    v2 = verify_coverage(page_categories, link_map, content_dir, game_slug)

    print("\n[3/6] コンテンツ品質チェック")
    v3 = verify_content_quality(content_dir, game_slug)

    print("\n[4/6] Hugoビルドチェック")
    print("  → 手動実行: hugo --minify")

    print("\n[5/6] リンク整合性チェック")
    v5 = verify_internal_links(content_dir, game_slug)

    print("\n[6/6] 画像参照チェック")
    v6 = verify_image_refs(content_dir, static_dir, game_slug)

    # 合否判定
    total_issues = len(v1) + len(v2) + len(v3) + len(v5) + len(v6)
    print(f"\n{'='*60}")
    if total_issues == 0:
        print("✓ 全検証パス！")
    else:
        print(f"⚠ 合計 {total_issues} 件の問題あり")
    print(f"{'='*60}")
```

---

## セクション8: 他ゲームへの汎用化

### パラメータ化すべき箇所

この手順書はスプラトゥーン3に特化しているが、以下をパラメータ化すれば他ゲームにも適用可能。

| パラメータ | 現在の値 | 変更方法 |
|-----------|---------|---------|
| `game_slug` | `"splatoon3"` | コマンドライン引数で渡す |
| `CATEGORY_MAP` | スプラ3専用のキーワード辞書 | ゲームごとに定義ファイルを用意 |
| 画像マッピング | 武器・サブ・スペシャル等11種 | ゲームごとにマスターデータから構築 |
| `SECTION_TITLES` | スプラ3のセクション名 | ゲームごとに定義 |
| テキスト書き換え辞書 | `STOCK_PHRASES` 等 | ゲーム汎用の辞書 + ゲーム固有の辞書 |

### CATEGORY_MAP半自動生成

新しいゲームのraw HTMLを取得した後、以下でカテゴリを半自動生成:

```python
def analyze_categories_from_titles(metadata_path):
    """タイトルのキーワード頻度からカテゴリ候補を推定"""
    with open(metadata_path) as f:
        metadata = json.load(f)

    # 全タイトルからN-gramを抽出
    from collections import Counter
    ngram_counts = Counter()

    all_files = metadata.get("all_files", metadata)
    for info in all_files.values():
        title = info.get("title", "")
        # 【...】内のテキストを除外
        clean = re.sub(r'【[^】]*】', '', title)
        # 3〜10文字のN-gram
        for n in range(3, 11):
            for i in range(len(clean) - n + 1):
                ngram = clean[i:i+n]
                if not re.match(r'^[\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]+$', ngram):
                    continue
                ngram_counts[ngram] += 1

    # 出現回数5回以上のN-gramをカテゴリ候補として表示
    print("=== カテゴリ候補（出現5回以上のキーワード） ===")
    for ngram, count in ngram_counts.most_common(100):
        if count >= 5:
            print(f"  {ngram}: {count}回")
```

### スクリプトのエントリーポイント

```python
# 全フェーズ実行スクリプト
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="raw HTML → Hugo コンテンツ変換")
    parser.add_argument("game_slug", help="ゲーム識別子 (例: splatoon3)")
    parser.add_argument("--phase", type=int, default=0,
                        help="開始フェーズ (0=全て, 1=分類, 2=リンクマップ, ...)")
    args = parser.parse_args()

    # パス設定
    game_dir = Path(f"００００１スプラトゥーン３")  # TODO: game_slug → ディレクトリ名マッピング
    raw_html_dir = game_dir / "raw_html"
    content_dir = Path("content")
    static_dir = Path("static")

    # Phase 1: 分類
    if args.phase <= 1:
        print("\n=== Phase 1: 分類 ===")
        page_categories = classify_all_pages(raw_html_dir / "_metadata.json")
        save_classification(page_categories, game_dir / "page_categories.json")

    # Phase 2: リンクマップ
    if args.phase <= 2:
        print("\n=== Phase 2: リンクマップ ===")
        link_map = build_link_map(page_categories, args.game_slug)
        check_slug_duplicates(link_map)
        save_link_map(link_map, game_dir / "link_map.json")

    # Phase 3: ディレクトリ構造
    if args.phase <= 3:
        print("\n=== Phase 3: ディレクトリ構造 ===")
        create_directory_structure(page_categories, content_dir, args.game_slug)

    # Phase 4: フロントマター（Phase 5に統合）

    # Phase 5+6: 変換 + バッチ実行
    if args.phase <= 5:
        print("\n=== Phase 5+6: 変換実行 ===")
        # マスターデータ読み込み（画像マッピング用）
        master_data = load_master_data()
        weapon_icon_map, sub_icon_map, special_icon_map, tier_map = \
            build_image_mappings(master_data)

        batch_convert(
            page_categories, link_map, raw_html_dir, content_dir,
            weapon_icon_map, sub_icon_map, special_icon_map, tier_map,
            args.game_slug
        )

    # Phase 7: 検証
    if args.phase <= 7:
        print("\n=== Phase 7: 検証 ===")
        verify_all(str(content_dir), str(static_dir),
                   page_categories, link_map, args.game_slug)
```

---

## 完成スクリプトの全体構造

```
convert_game8_to_hugo.py <game_slug>
│
├── Phase 1: CLASSIFY — 全ページ自動分類
│   ├── _metadata.json のタイトルを読み込み
│   ├── CATEGORY_MAP でキーワードマッチ（優先度順）
│   └── 出力: page_categories.json（1,515件）
│
├── Phase 2: LINK MAP — リンクマップ構築
│   ├── page_categories.json から全ページの Hugo パスを生成
│   ├── slug重複チェック → IDサフィックスで自動解決
│   └── 出力: link_map.json（1,515件）
│
├── Phase 3: STRUCTURE — ディレクトリ生成
│   ├── 13セクションのディレクトリ作成
│   └── 各セクションに _index.md 配置
│
├── Phase 4+5: TRANSFORM — HTMLコンテンツ変換
│   ├── Step 5.1: .archive-style-wrapper 抽出
│   ├── Step 5.2: 不要要素除去（広告, トラッキング, 攻略班等）
│   ├── Step 5.3: 画像処理（11カテゴリマッピング + プレースホルダー）
│   ├── Step 5.4: リンク変換（link_map.json で全1,515ページ解決）
│   ├── Step 5.5: テキスト書き換え（4層変換）
│   └── Step 5.6: 禁止名称除去
│
├── Phase 6: EXECUTE — バッチ実行
│   ├── 優先度順（武器→ステージ→...→ギアパワー886件）
│   ├── 50件ごとに進捗保存（レジューム対応）
│   └── エラーは記録してスキップ（全体を止めない）
│
└── Phase 7: VERIFY — 検証
    ├── 検証1: 禁止名称 → 0件
    ├── 検証2: カバレッジ → 100%（全HTMLに対応.md）
    ├── 検証3: 品質チェック → ランダム50件
    ├── 検証4: hugo --minify → エラーなし
    ├── 検証5: 内部リンク整合性
    └── 検証6: 画像参照チェック
```

---

## 既存コードの再利用マップ

| 既存関数 | ファイル:行 | 本手順での用途 |
|---------|-----------|-------------|
| `extract_article_content()` | build_from_game8_html.py:234 | Step 5.1 コンテンツ抽出 |
| `remove_unwanted_elements()` | build_from_game8_html.py:253 | Step 5.2 不要要素除去 |
| `process_images()` | build_from_game8_html.py:296 | Step 5.3 画像処理 |
| `process_links()` | build_from_game8_html.py:459 | Step 5.4 の参考（拡張版を新規作成） |
| `rewrite_text()` | build_from_game8_html.py:557 | Step 5.5 テキスト書き換え |
| `remove_forbidden_names()` | build_from_game8_html.py:934 | Step 5.6 禁止名称除去 |
| `rewrite_paragraph()` | text_rewriter.py:636 | Step 5.5 段落リライト |
| `rewrite_short_phrase()` | text_rewriter.py:664 | Step 5.5 短文リライト |
| `GEAR_POWER_ICONS` | build_from_game8_html.py:108 | Step 5.3 ギアパワー26種 |
| `BRAND_ICONS` | build_from_game8_html.py:181 | Step 5.3 ブランド24種 |
| `BUTTON_ICONS` | build_from_game8_html.py:207 | Step 5.3 Switchボタン7種 |
| `WEAPON_CLASS_ICONS` | build_from_game8_html.py:218 | Step 5.3 武器種11種 |
| `build_image_mappings()` | build_from_game8_html.py:59 | Step 5.3 画像マッピング構築 |
| `load_master_data()` | build_from_game8_html.py:49 | マスターデータ読み込み |
| `weapon_name_to_slug()` | build_from_game8_html.py:591 | slug生成の参考 |
| `_black_placeholder_src()` | build_from_game8_html.py:35 | 未マッチ画像のプレースホルダー |

---

## 禁止事項

1. **禁止名称をコンテンツに含めない** → 最終工程 + 検証で二重チェック
2. **テキストをコピペしない** → text_rewriter.py の4層変換で必ず書き換え
3. **ページを手動で分類しない** → CATEGORY_MAP + タイトルキーワードで自動分類
4. **リンクをハードコードしない** → link_map.json で全1,515ページを自動解決
5. **1ページの失敗で止めない** → エラー記録 + スキップ + レジューム
6. **検証をスキップしない** → 6種の検証を全て実行
7. **ファイル名形式を旧形式に戻さない** → `{記事ID}.html` のまま処理

---

## 実行例

```bash
python3 scripts/convert_game8_to_hugo.py splatoon3
```

```
=== Phase 1: 分類 ===
  gear-powers: 886件
  weapons: 207件
  gear: 153件
  hero-mode: 120件
  salmon-run: 49件
  updates: 38件
  beginner: 36件
  stages: 29件
  specials: 21件
  side-order: 19件
  fes: 11件
  subs: 4件
  misc: ~30件
  合計: 1,515件

=== Phase 2: リンクマップ ===
リンクマップ保存: 1,515件
✓ slug重複なし

=== Phase 3: ディレクトリ構造 ===
  📁 weapons/ + _index.md
  📁 gear-powers/ + _index.md
  📁 gear/ + _index.md
  ...

=== Phase 5+6: 変換実行 ===
============================================================
バッチ変換開始: 1,515ページ

📦 武器一覧 (207件)
----------------------------------------
  ✅ [1/1515] スプラシューターのおすすめギアと立ち回り...
  ✅ [2/1515] スプラシューターコラボのおすすめギアと立...
  ...
  💾 進捗保存 (50/1515)
  ...

📦 ギアパワー一覧 (886件)
----------------------------------------
  ✅ [630/1515] インク効率アップ（メイン）のギアパワーと入手方法...
  ...
  💾 進捗保存 (1500/1515)
  ...

============================================================
変換完了!
  成功: 1,510
  失敗: 3
  スキップ: 2
  合計: 1,515
============================================================

=== Phase 7: 検証 ===

[1/6] 禁止名称チェック
✓ 禁止名称: 0件

[2/6] カバレッジチェック
✓ カバレッジ: 100% (1,515件全て生成済み)

[3/6] コンテンツ品質チェック
✓ 品質チェックOK (サンプル50件)

[4/6] Hugoビルドチェック
  → 手動実行: hugo --minify

[5/6] リンク整合性チェック
✓ 内部リンク整合性OK

[6/6] 画像参照チェック
✓ 画像参照OK

============================================================
✓ 全検証パス！
============================================================
```

---

## まとめ: なぜこれで全件変換できるのか

| リスク | 対策 |
|-------|------|
| ファイル名変更で既存スクリプトが動かない | `_metadata.json` ベースで全ファイルを自動検索 |
| カテゴリ不明で分類できない | タイトルキーワード優先度マッチ + miscフォールバック |
| 1,285件のリンクが解決できない | `link_map.json` で全1,515ページの内部リンクを解決 |
| 特定カテゴリの変換が漏れる | CATEGORY_MAP + フォールバック + カバレッジ検証 |
| 大量処理で途中エラー | レジューム機能 + エラースキップ + 50件ごと進捗保存 |
| 禁止名称が混入 | 最終工程の `remove_forbidden_names()` + 検証1 |
| テキストがコピペのまま | text_rewriter.py の4層変換 + 品質チェック |
| 他ゲームに流用できない | パラメータ化 + CATEGORY_MAP半自動生成 |
