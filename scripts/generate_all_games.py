#!/usr/bin/env python3
"""
567ゲームタイトル分のHugo用Markdownページを一括生成する。
各ページ500文字以上のSEO対策済みコンテンツを生成。
"""

import csv
import os
from datetime import datetime

TSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'titles', 'game_titles_500.tsv')
CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content', 'games')
TODAY = datetime.now().strftime('%Y-%m-%d')

# カテゴリの日本語マッピング
CATEGORY_JA = {
    'rpg': 'RPG',
    'action': 'アクション',
    'shooter': 'シューター',
    'strategy': 'ストラテジー',
    'mmorpg': 'MMORPG',
    'moba': 'MOBA',
    'fighting': '格闘ゲーム',
    'card': 'カードゲーム',
    'horror': 'ホラー',
    'sports': 'スポーツ',
    'racing': 'レース',
    'puzzle': 'パズル',
    'rhythm': 'リズムゲーム',
    'simulation': 'シミュレーション',
    'sandbox': 'サンドボックス',
    'survival': 'サバイバル',
    'adventure': 'アドベンチャー',
    'srpg': 'シミュレーションRPG',
    'party': 'パーティーゲーム',
    'board': 'ボードゲーム',
    'tower-defense': 'タワーディフェンス',
    'fitness': 'フィットネス',
    'dress-up': '着せ替え',
    'casual': 'カジュアル',
    'other': 'その他',
}

# プラットフォームの表示名
PLATFORM_JA = {
    'ps5': 'PS5',
    'ps4': 'PS4',
    'xbox': 'Xbox',
    'pc': 'PC（Steam）',
    'switch': 'Nintendo Switch',
    'ios': 'iOS',
    'android': 'Android',
}

# カテゴリ別の攻略ポイントテンプレート
TIPS_BY_CATEGORY = {
    'rpg': [
        'キャラクター育成の効率的な進め方',
        'おすすめのパーティ編成とビルド',
        '序盤の効率的な攻略ルート',
        'レベル上げにおすすめの場所',
        'ボス戦の攻略法とコツ',
    ],
    'action': [
        '操作の基本とコンボテクニック',
        'ボス攻略のコツと立ち回り',
        '武器・装備のおすすめ構成',
        '難所の攻略法とショートカット',
        '周回効率を上げるテクニック',
    ],
    'shooter': [
        'エイム力を上げる練習方法',
        'マップごとの立ち回りとポジション',
        'おすすめの武器セッティング',
        'チーム戦での役割と連携',
        'ランクマッチで勝率を上げるコツ',
    ],
    'strategy': [
        '序盤の効率的な進め方',
        'リソース管理の基本戦略',
        '最強ユニット・兵種のランキング',
        '初心者が避けるべきミス',
        '中盤以降の戦略転換ポイント',
    ],
    'mmorpg': [
        '職業（クラス）選びのポイント',
        '効率的なレベリング方法',
        'エンドコンテンツの攻略ガイド',
        '金策・素材集めのおすすめ方法',
        'ギルド・パーティ募集のコツ',
    ],
    'moba': [
        'ロール別の立ち回り解説',
        '最強キャラクターランキング',
        'レーン戦の基本テクニック',
        'チームファイトでの立ち位置',
        '初心者おすすめキャラクター',
    ],
    'fighting': [
        'キャラクター別の基本コンボ',
        'フレームデータの読み方',
        '対戦で勝つための基本戦術',
        'ランクマッチでの立ち回り',
        '初心者おすすめキャラクター',
    ],
    'card': [
        '最強デッキレシピ・構築ガイド',
        '環境トップのデッキランキング',
        'カード資産の効率的な集め方',
        '初心者おすすめのスターターデッキ',
        'メタゲームの読み方と対策',
    ],
    'horror': [
        '序盤の生き残り方と基本操作',
        'マップ別の攻略ポイント',
        '敵キャラクターの対策法',
        'マルチプレイでの立ち回り',
        '隠し要素・エンディング条件',
    ],
    'sports': [
        '基本操作とテクニック解説',
        '試合で勝つための戦術ガイド',
        'おすすめの選手・チーム編成',
        'オンライン対戦のコツ',
        'シーズンモードの効率的な進め方',
    ],
    'racing': [
        'ドライビングテクニックの基本',
        'コース別の攻略ポイント',
        'おすすめの車種セッティング',
        'オンラインレースでの戦略',
        'タイムアタックのコツ',
    ],
    'puzzle': [
        'パズルの基本テクニック',
        '高スコアを狙うコツ',
        '難ステージの攻略法',
        '効率的なアイテムの使い方',
        '上級者向けの連鎖テクニック',
    ],
    'rhythm': [
        '楽曲別の攻略ポイント',
        '高難度譜面のクリアのコツ',
        'フルコンボを狙うテクニック',
        'おすすめの設定・オプション',
        'イベント効率的な周回方法',
    ],
    'simulation': [
        '序盤の効率的な進め方',
        'リソース管理のコツ',
        'おすすめの施設配置・レイアウト',
        '中盤以降の発展戦略',
        '隠し要素・やり込みポイント',
    ],
    'sandbox': [
        '序盤の生活基盤の作り方',
        '建築テクニックとアイデア',
        '素材の効率的な集め方',
        '冒険・探索のおすすめルート',
        'マルチプレイの楽しみ方',
    ],
    'survival': [
        '最初の夜を生き延びる方法',
        '拠点づくりの基本ガイド',
        '食料・水の確保テクニック',
        '危険な敵への対処法',
        'クラフトの優先順位',
    ],
    'adventure': [
        'ストーリー攻略の進め方',
        '謎解き・パズルのヒント',
        '収集要素のコンプリートガイド',
        'エンディング分岐条件',
        '見逃しやすい隠し要素',
    ],
    'srpg': [
        'ユニット育成の優先順位',
        'マップ攻略のコツと配置',
        'おすすめのクラスチェンジ',
        '難マップの攻略法',
        'キャラクター評価ランキング',
    ],
    'party': [
        'ミニゲーム別の攻略テクニック',
        'マルチプレイの楽しみ方',
        '隠し要素の解放条件',
        'CPU戦で勝つコツ',
        'おすすめのルール設定',
    ],
}

# デフォルトの攻略ポイント
DEFAULT_TIPS = [
    '序盤の効率的な進め方',
    'おすすめの攻略ルート',
    '初心者向けの基本ガイド',
    'やり込み要素の解説',
    '最新アップデート情報',
]


def format_platforms(platform_str):
    """プラットフォーム文字列を整形"""
    platforms = [p.strip() for p in platform_str.split(',')]
    return [PLATFORM_JA.get(p, p) for p in platforms]


def get_platform_tags(platform_str):
    """プラットフォームからタグ用リストを生成"""
    platforms = [p.strip() for p in platform_str.split(',')]
    tags = []
    for p in platforms:
        if p in ('ios', 'android'):
            if 'スマホゲーム' not in tags:
                tags.append('スマホゲーム')
        elif p == 'switch':
            tags.append('Switch')
        elif p == 'ps5':
            tags.append('PS5')
        elif p == 'pc':
            tags.append('PC')
        elif p == 'xbox':
            tags.append('Xbox')
    return tags


def generate_content(game):
    """ゲームごとのMarkdownコンテンツを生成（500文字以上）"""
    slug = game['slug']
    name_ja = game['name_ja']
    name_en = game['name_en']
    platform_str = game['platform']
    category = game['category']
    priority = game['priority']

    cat_ja = CATEGORY_JA.get(category, category)
    platforms = format_platforms(platform_str)
    platform_display = '・'.join(platforms)
    tips = TIPS_BY_CATEGORY.get(category, DEFAULT_TIPS)
    platform_tags = get_platform_tags(platform_str)

    # タグ生成
    tags = [cat_ja] + platform_tags
    tags_str = '\n'.join(f'  - "{t}"' for t in tags)

    # モバイルかどうか
    is_mobile = 'ios' in platform_str or 'android' in platform_str
    is_console = any(p in platform_str for p in ['switch', 'ps5', 'xbox'])
    is_pc = 'pc' in platform_str

    # プラットフォーム説明文
    platform_sections = []
    if is_console:
        console_names = []
        if 'switch' in platform_str:
            console_names.append('Nintendo Switch')
        if 'ps5' in platform_str:
            console_names.append('PlayStation 5')
        if 'xbox' in platform_str:
            console_names.append('Xbox Series X|S')
        platform_sections.append(f"コンシューマー版は{'、'.join(console_names)}に対応しています。")
    if is_pc:
        platform_sections.append("PC版はSteamなどのプラットフォームでプレイできます。")
    if is_mobile:
        platform_sections.append("スマートフォン版はiOS・Androidの両方に対応しており、無料でダウンロードできます。")

    platform_detail = ''.join(platform_sections)

    # 優先度に応じた表現
    if priority == 'S':
        popularity = f'「{name_ja}」は現在最も注目されている{cat_ja}タイトルの一つです。世界中で多くのプレイヤーに遊ばれており、攻略情報への需要も非常に高いゲームです。'
    elif priority == 'A':
        popularity = f'「{name_ja}」は安定した人気を誇る{cat_ja}タイトルです。熱心なファンコミュニティがあり、攻略情報を求めるプレイヤーも多くいます。'
    else:
        popularity = f'「{name_ja}」は根強いファン層を持つ{cat_ja}タイトルです。独自の魅力があり、コアなプレイヤーから支持されています。'

    # weight: S=1, A=50, B=100
    weight_map = {'S': 1, 'A': 50, 'B': 100}
    weight = weight_map.get(priority, 100)

    # 攻略ポイントリスト
    tips_md = '\n'.join(f'- **{t}**' for t in tips)

    # Front matter
    front_matter = f"""---
title: "{name_ja} 攻略"
linkTitle: "{name_ja}"
description: "{name_ja}（{name_en}）の攻略情報まとめ。初心者ガイド、おすすめ攻略法、最新情報を掲載。対応機種：{platform_display}。"
date: {TODAY}
lastmod: {TODAY}
weight: {weight}
categories:
  - "{cat_ja}"
tags:
{tags_str}
---"""

    # 本文
    body = f"""
## {name_ja}（{name_en}）攻略ガイド

{popularity}

当サイト「Gamers-For」では、{name_ja}の最新攻略情報をお届けしています。初心者から上級者まで、すべてのプレイヤーに役立つ情報を掲載していきます。

## ゲーム基本情報

| 項目 | 内容 |
|------|------|
| **タイトル** | {name_ja} |
| **英語名** | {name_en} |
| **ジャンル** | {cat_ja} |
| **対応機種** | {platform_display} |

{platform_detail}

## 攻略情報

{name_ja}の攻略で押さえておきたいポイントをまとめています。

{tips_md}

各攻略記事は随時更新していきます。最新のアップデートやバランス調整にも対応した情報をお届けします。

## 初心者向けガイド

{name_ja}をこれから始める方に向けた基本ガイドです。ゲームの基本システムや序盤の進め方、知っておくと便利なテクニックを解説しています。まずはゲームの世界観とシステムを理解してから、本格的な攻略に取り組みましょう。

## 最新情報・アップデート

{name_ja}の最新アップデート情報やイベント情報をまとめています。新コンテンツの追加やバランス調整、キャンペーン情報などをいち早くお届けします。

---

*この記事は随時更新しています。ブックマークして最新情報をチェックしてください。*
"""

    return front_matter + body


def main():
    # TSVファイルを読み込み
    games = []
    with open(TSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['slug'].startswith('#'):
                continue
            games.append(row)

    print(f"読み込み完了: {len(games)} タイトル")

    # 既存のsplatoon3ディレクトリはスキップ
    skip_slugs = {'splatoon3'}  # 既に詳細な攻略ページがある

    created = 0
    skipped = 0
    for game in games:
        slug = game['slug']

        # splatoon-3 → splatoon3 のような変換チェック
        # 既存のsplatoon3はスキップ
        if slug.replace('-', '') in skip_slugs or slug in skip_slugs:
            skipped += 1
            continue

        game_dir = os.path.join(CONTENT_DIR, slug)
        os.makedirs(game_dir, exist_ok=True)

        index_path = os.path.join(game_dir, '_index.md')

        content = generate_content(game)

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)

        created += 1

    print(f"生成完了: {created} ページ作成, {skipped} スキップ")

    # コンテンツの文字数をサンプルチェック
    sample_path = os.path.join(CONTENT_DIR, games[0]['slug'], '_index.md')
    if os.path.exists(sample_path):
        with open(sample_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"サンプルページ文字数: {len(content)} 文字 ({games[0]['slug']})")


if __name__ == '__main__':
    main()
