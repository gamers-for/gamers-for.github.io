#!/usr/bin/env python3
"""
汎用ページ生成スクリプト
game_config.json を読み込み、マスターJSONから Hugo コンテンツページを自動生成。

5種の汎用ページ:
  1. _index.md    - ゲームTOPページ
  2. tier-list.md - 最強ランキング
  3. all-list.md  - 全エンティティ一覧
  4. beginner.md  - 初心者攻略ガイド
  5. individual/  - 個別ページ（武器/キャラごと）

+ custom plugin で追加ページ生成

使い方:
  python generate_pages.py /path/to/０１ゲーム名/game_config.json
"""

import json
import os
import re
import sys
import textwrap
import importlib.util


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_master(hugo_dir, game_slug):
    master_path = os.path.join(hugo_dir, "data", f"{game_slug}_master.json")
    with open(master_path, "r", encoding="utf-8") as f:
        return json.load(f)


def tier_to_num(t, tiers):
    """ティア→ソート順"""
    for i, tier in enumerate(tiers):
        if tier == t:
            return i
    return 99


def tier_to_rating(tier, tiers):
    """ティア→数値評価（10段階）"""
    n = len(tiers)
    if n == 0:
        return "7"
    for i, t in enumerate(tiers):
        if t == tier:
            rating = 10.0 - (i * 4.0 / max(n - 1, 1))
            return f"{rating:.1f}".rstrip("0").rstrip(".")
    return "7"


def entity_slug(name):
    """エンティティ名からURLスラッグを生成"""
    slug = name.lower()
    slug = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug if slug else "item"


def img_path(icon, game_slug, base_url):
    """アイコンパスをサイトURL付きに変換"""
    if not icon:
        return ""
    return f"{base_url}/images/games/{game_slug}{icon.replace(f'/images/games/{game_slug}', '')}"


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    lines = content.count("\n")
    size_kb = len(content.encode("utf-8")) / 1024
    print(f"  -> {os.path.basename(path)}: {lines}行 ({size_kb:.1f}KB)")


# =============================================
# 1. _index.md - ゲームTOP
# =============================================
def generate_index(config, master, content_dir, img_fn):
    page_conf = config["pages"].get("index", {})
    if not page_conf.get("generate", True):
        return

    game_name = config["game_name"]
    entity_name = config["entity_type"]["name"]
    slug_prefix = config["entity_type"]["slug_prefix"]
    entities = master.get(slug_prefix, [])

    # クラス集計
    classes = {}
    for e in entities:
        cls = e.get("class", "その他")
        classes[cls] = classes.get(cls, 0) + 1

    class_list = config.get("classes", [])

    content = f"""---
title: "{game_name} 攻略"
linkTitle: "{config.get('game_name_short', game_name)}"
description: "{config['description']}"
weight: {page_conf.get('weight', 1)}
---

{{{{< update-info date="2026-02-12" >}}}}

## {game_name} 攻略TOP

{config['description']}

### 人気記事

- [最強{entity_name}ランキング](tier-list/) - 全{entity_name}のティアランク
- [全{entity_name}一覧]({slug_prefix}/) - {len(entities)}{entity_name}の性能比較
- [初心者攻略ガイド](beginner/) - はじめての{game_name}
- [最新イベント](events/) - イベント情報

"""

    if class_list:
        content += f"### {entity_name}種別一覧\n\n"
        content += f"| {entity_name}種 | {entity_name}数 | 特徴 |\n"
        content += "|--------|--------|------|\n"
        for cls in class_list:
            count = classes.get(cls["name"], 0)
            content += f"| **{cls['name']}** | {count} | {cls.get('description', '')} |\n"
        content += "\n"

    write_file(os.path.join(content_dir, "_index.md"), content)


# =============================================
# 2. tier-list.md - 最強ランキング
# =============================================
def generate_tier_list(config, master, content_dir, img_fn):
    page_conf = config["pages"].get("tier_list", {})
    if not page_conf.get("generate", True):
        return

    game_name = config["game_name"]
    entity_name = config["entity_type"]["name"]
    slug_prefix = config["entity_type"]["slug_prefix"]
    entities = master.get(slug_prefix, [])
    tiers = config["tier_definition"]["tiers"]

    tiered = [e for e in entities if e.get("tier")]
    tiered.sort(key=lambda e: (tier_to_num(e["tier"], tiers), e.get("name", "")))

    title = page_conf.get("title_template", "【{game_name}】最強{entity_name}ランキング").format(
        game_name=game_name, entity_name=entity_name
    )

    content = f"""---
title: "{title}"
linkTitle: "最強{entity_name}"
weight: {page_conf.get('weight', 2)}
date: 2026-02-11
categories: ["最強ランキング"]
tags: ["{game_name}", "{entity_name}"]
description: "{game_name}の最強{entity_name}ランキング。全{entity_name}を徹底評価。"
---

{{{{< update-info date="2026-02-12" >}}}}

{game_name}で**最も強い{entity_name}**をランキング形式で紹介します。

## 最強{entity_name}ランキング早見表

"""

    # ティア別グループ化
    tier_groups = {}
    for e in tiered:
        t = e["tier"]
        tier_groups.setdefault(t, []).append(e)

    # tier-grid 早見表
    for tier in tiers:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f'{{{{< tier-grid tier="{tier}" >}}}}\n'
        for e in group:
            icon = img_fn(e.get("icon", ""))
            content += f'{{{{< weapon-icon name="{e["name"]}" img="{icon}" >}}}}\n'
        content += f'{{{{< /tier-grid >}}}}\n\n'

    content += "\n---\n\n"

    # 各ティアの詳細
    for tier in tiers:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f"## {tier}ランク\n\n"

        for e in group:
            rating = tier_to_rating(tier, tiers)
            img_attr = f' img="{img_fn(e.get("icon", ""))}"' if e.get("icon") else ""
            role = e.get("class", "")

            content += f"### {e['name']}\n\n"
            content += f'{{{{< character-card name="{e["name"]}" role="{role}" rating="{rating}"{img_attr} >}}}}\n\n'

            # サブ/スペシャル情報
            if e.get("sub"):
                content += f"- **サブ**: {e['sub']}\n"
            if e.get("special"):
                content += f"- **スペシャル**: {e['special']}\n"

            content += f'\n{{{{< /character-card >}}}}\n\n'

        content += "---\n\n"

    write_file(os.path.join(content_dir, "tier-list.md"), content)


# =============================================
# 3. all-list.md (weapons.md) - 全一覧
# =============================================
def generate_all_list(config, master, content_dir, img_fn):
    page_conf = config["pages"].get("all_list", {})
    if not page_conf.get("generate", True):
        return

    game_name = config["game_name"]
    entity_name = config["entity_type"]["name"]
    slug_prefix = config["entity_type"]["slug_prefix"]
    entities = master.get(slug_prefix, [])
    tiers = config["tier_definition"]["tiers"]
    class_list = config.get("classes", [])

    title = page_conf.get("title_template", "【{game_name}】全{entity_name}一覧").format(
        game_name=game_name, entity_name=entity_name
    )

    content = f"""---
title: "{title}"
linkTitle: "全{entity_name}一覧"
weight: {page_conf.get('weight', 3)}
date: 2026-02-11
categories: ["{entity_name}"]
tags: ["{game_name}", "{entity_name}"]
description: "{game_name}の全{len(entities)}{entity_name}を一覧。サブ・スペシャル・評価を完全網羅。"
---

{{{{< update-info date="2026-02-12" >}}}}

{game_name}の**全{len(entities)}{entity_name}**を種別ごとに一覧でまとめています。

"""

    # クラスごとにグループ化
    by_class = {}
    for e in entities:
        cls = e.get("class", "その他")
        by_class.setdefault(cls, []).append(e)

    class_order = [c["name"] for c in class_list] if class_list else list(by_class.keys())

    for cls in class_order:
        if cls not in by_class:
            continue
        group = by_class[cls]
        group.sort(key=lambda e: (tier_to_num(e.get("tier", ""), tiers), e.get("name", "")))

        content += f"## {cls}（{len(group)}種）\n\n"
        content += f"| {entity_name} | {entity_name}名 | サブ | スペシャル | 評価 |\n"
        content += "|------|--------|------|-----------|------|\n"

        for e in group:
            icon = f"![{e['name']}]({img_fn(e.get('icon', ''))})" if e.get("icon") else ""
            tier = e.get("tier", "-")
            content += f"| {icon} | {e['name']} | {e.get('sub', '-')} | {e.get('special', '-')} | **{tier}** |\n"

        content += "\n---\n\n"

    # ファイル名は slug_prefix.md
    write_file(os.path.join(content_dir, f"{slug_prefix}.md"), content)


# =============================================
# 4. beginner.md - 初心者攻略
# =============================================
def generate_beginner(config, master, content_dir, img_fn):
    page_conf = config["pages"].get("beginner", {})
    if not page_conf.get("generate", True):
        return

    game_name = config["game_name"]
    entity_name = config["entity_type"]["name"]

    title = page_conf.get("title_template", "【{game_name}】初心者攻略ガイド").format(
        game_name=game_name, entity_name=entity_name
    )

    beginner_conf = config.get("beginner_guide", {})
    steps = beginner_conf.get("steps", [])

    content = f"""---
title: "{title}"
linkTitle: "初心者攻略"
weight: {page_conf.get('weight', 4)}
date: 2026-02-11
categories: ["初心者攻略"]
tags: ["{game_name}", "初心者"]
description: "{game_name}の初心者向け攻略ガイド。序盤の進め方とやるべきことを解説。"
---

{{{{< update-info date="2026-02-12" >}}}}

{game_name}をこれから始める方・始めたばかりの方向けの攻略ガイドです。

## 序盤の進め方

"""

    for i, step in enumerate(steps, 1):
        content += f"### STEP {i}: {step.get('title', '')}\n\n"
        content += f"{step.get('content', '')}\n\n"

    # おすすめTOP5
    slug_prefix = config["entity_type"]["slug_prefix"]
    entities = master.get(slug_prefix, [])
    tiers = config["tier_definition"]["tiers"]
    top_n = beginner_conf.get("top_picks", 5)

    top_entities = sorted(
        [e for e in entities if e.get("tier")],
        key=lambda e: tier_to_num(e["tier"], tiers)
    )[:top_n]

    if top_entities:
        content += f"---\n\n## 初心者おすすめ{entity_name}TOP{top_n}\n\n"
        content += f"| 順位 | {entity_name}名 | おすすめ理由 |\n"
        content += "|------|--------|-------------|\n"
        for i, e in enumerate(top_entities, 1):
            reason = f"{e.get('class', '')}。{e.get('sub', '')}と{e.get('special', '')}が扱いやすい"
            content += f"| {i} | **{e['name']}** | {reason} |\n"

    content += "\n"

    write_file(os.path.join(content_dir, "beginner.md"), content)


# =============================================
# 5. events.md - イベント情報
# =============================================
def generate_events(config, master, content_dir, img_fn):
    page_conf = config["pages"].get("events", {})
    if not page_conf.get("generate", True):
        return

    game_name = config["game_name"]

    title = page_conf.get("title_template", "【{game_name}】最新イベントまとめ").format(
        game_name=game_name, entity_name=config["entity_type"]["name"]
    )

    content = f"""---
title: "{title}"
linkTitle: "イベント"
weight: {page_conf.get('weight', 5)}
date: 2026-02-11
categories: ["イベント"]
tags: ["{game_name}", "イベント"]
description: "{game_name}の最新イベント情報まとめ。"
---

{{{{< update-info date="2026-02-12" >}}}}

{game_name}の最新イベント情報をまとめています。

## 開催中のイベント

*最新情報が入り次第更新します。*

## 過去のイベント

| イベント名 | 期間 | 主な報酬 |
|-----------|------|---------|
| - | - | - |
"""

    write_file(os.path.join(content_dir, "events.md"), content)


# =============================================
# 6. 個別ページ
# =============================================
def generate_individual_pages(config, master, content_dir, img_fn):
    page_conf = config["pages"].get("individual_pages", {})
    if not page_conf.get("generate", True):
        return 0

    game_name = config["game_name"]
    entity_name = config["entity_type"]["name"]
    slug_prefix = config["entity_type"]["slug_prefix"]
    entities = master.get(slug_prefix, [])
    tiers = config["tier_definition"]["tiers"]
    ind_dir_name = page_conf.get("dir", slug_prefix)

    ind_dir = os.path.join(content_dir, ind_dir_name)
    os.makedirs(ind_dir, exist_ok=True)

    # _index.md
    idx_content = f"""---
title: "{game_name} 全{entity_name}一覧"
linkTitle: "全{entity_name}"
weight: 2
date: 2026-02-11
description: "{game_name}の全{entity_name}データベース。"
---

全{entity_name}の個別ページです。

"""
    # クラスごとにリスト
    class_entities = {}
    for e in entities:
        cls = e.get("class", "その他")
        class_entities.setdefault(cls, []).append(e)

    class_order = [c["name"] for c in config.get("classes", [])]
    if not class_order:
        class_order = list(class_entities.keys())

    for cls in class_order:
        if cls not in class_entities:
            continue
        idx_content += f"## {cls}\n\n"
        for e in class_entities[cls]:
            slug = entity_slug(e["name"])
            tier_badge = f" ({e['tier']})" if e.get("tier") else ""
            idx_content += f"- [{e['name']}{tier_badge}]({slug}/)\n"
        idx_content += "\n"

    write_file(os.path.join(ind_dir, "_index.md"), idx_content)

    # 個別ページ
    count = 0
    title_tmpl = page_conf.get("title_template", "【{game_name}】{entity_name}の性能と評価")
    for e in entities:
        slug = entity_slug(e["name"])
        rating = tier_to_rating(e.get("tier", ""), tiers)
        img_attr = f' img="{img_fn(e.get("icon", ""))}"' if e.get("icon") else ""
        role = e.get("class", "")

        title = title_tmpl.format(
            game_name=game_name, entity_name=e["name"]
        )

        content = f"""---
title: "{title}"
linkTitle: "{e['name']}"
weight: 50
date: 2026-02-11
categories: ["{role}"]
tags: ["{game_name}", "{role}", "{e['name']}"]
description: "{game_name}の{e['name']}の性能評価。"
---

{{{{< update-info date="2026-02-12" >}}}}

{{{{< character-card name="{e['name']}" role="{role}" rating="{rating}"{img_attr} >}}}}

"""
        if e.get("sub"):
            content += f"- **サブ**: {e['sub']}\n"
        if e.get("special"):
            content += f"- **スペシャル**: {e['special']}\n"

        content += f"""
{{{{< /character-card >}}}}

## 基本性能

| 項目 | 値 |
|------|-----|
| **{entity_name}種** | {role} |
"""
        if e.get("sub"):
            content += f"| **サブ** | {e['sub']} |\n"
        if e.get("special"):
            content += f"| **スペシャル** | {e['special']} |\n"
        if e.get("tier"):
            content += f"| **ランク** | {e['tier']} |\n"
        if e.get("damage"):
            content += f"| **ダメージ** | {e['damage']} |\n"
        if e.get("range"):
            content += f"| **射程** | {e['range']} |\n"

        content += f"""
## 関連記事

- [最強{entity_name}ランキング](../../tier-list/)
- [全{entity_name}一覧](../)
- [初心者攻略ガイド](../../beginner/)
"""

        write_file(os.path.join(ind_dir, f"{slug}.md"), content)
        count += 1

    return count


# =============================================
# カスタムプラグイン
# =============================================
def run_custom_generators(config, master, content_dir, img_fn):
    """custom/generators.py があればロードして実行"""
    plugin_dir = config.get("custom_plugin_dir", "./custom")
    config_dir = os.path.dirname(os.path.abspath(config.get("_config_path", ".")))
    plugin_path = os.path.join(config_dir, plugin_dir, "generators.py")

    if not os.path.exists(plugin_path):
        return

    spec = importlib.util.spec_from_file_location("generators", plugin_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if hasattr(mod, "generate_custom_pages"):
        count = mod.generate_custom_pages(config, master, content_dir, img_fn, write_file)
        print(f"  [plugin] generators.py: {count} custom pages generated")


# =============================================
# メイン
# =============================================
def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_pages.py /path/to/game_config.json")
        sys.exit(1)

    config_path = os.path.abspath(sys.argv[1])
    config = load_config(config_path)
    config["_config_path"] = config_path

    config_dir = os.path.dirname(config_path)
    hugo_dir = os.path.join(config_dir, config.get("hugo_site_dir", "../gamers-for"))
    game_slug = config["game_slug"]

    content_dir = os.path.join(hugo_dir, "content", "games", game_slug)
    os.makedirs(content_dir, exist_ok=True)

    master = load_master(hugo_dir, game_slug)

    # 画像パス関数
    base_url = config.get("_base_url", "")
    if not base_url:
        # hugo.toml から推定
        toml_path = os.path.join(hugo_dir, "hugo.toml")
        if os.path.exists(toml_path):
            with open(toml_path, "r") as f:
                for line in f:
                    if line.strip().startswith("baseURL"):
                        base_url = line.split("=")[1].strip().strip("'\"").rstrip("/")
                        break

    def img_fn(icon):
        return img_path(icon, game_slug, base_url)

    print(f"=== {config['game_name']} ページ生成 ===")
    print(f"出力先: {content_dir}")
    print(f"baseURL: {base_url}\n")

    # 汎用ページ生成
    generate_index(config, master, content_dir, img_fn)
    generate_tier_list(config, master, content_dir, img_fn)
    generate_all_list(config, master, content_dir, img_fn)
    generate_beginner(config, master, content_dir, img_fn)
    generate_events(config, master, content_dir, img_fn)

    # 個別ページ
    ind_count = generate_individual_pages(config, master, content_dir, img_fn)
    if ind_count:
        print(f"  -> 個別ページ: {ind_count}件")

    # カスタムプラグイン
    run_custom_generators(config, master, content_dir, img_fn)

    print(f"\n生成完了！")


if __name__ == "__main__":
    main()
