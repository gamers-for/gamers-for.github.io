#!/usr/bin/env python3
"""Retry downloading cover images for games that failed in the first pass.
Uses alternative search terms and Japanese Wikipedia as fallback.
"""
import os
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / 'static' / 'images' / 'games'
THUMB_SIZE = 400

EN_WIKI_API = 'https://en.wikipedia.org/w/api.php'
JA_WIKI_API = 'https://ja.wikipedia.org/w/api.php'

# Failed games with alternative search terms
RETRY_MAP = {
    'pokemon-scarlet-violet': ['Pokémon Scarlet and Violet', 'Pokemon Scarlet Violet'],
    'pokemon-unite': ['Pokémon Unite', 'Pokemon Unite (video game)'],
    'pokemon-diamond-pearl-remake': ['Pokémon Brilliant Diamond and Shining Pearl', 'Pokemon BDSP'],
    'pokemon-sword-shield': ['Pokémon Sword and Shield', 'Pokemon Sword Shield'],
    'new-pokemon-snap': ['New Pokémon Snap', 'New Pokemon Snap (video game)'],
    'dragon-quest-walk': ['Dragon Quest Walk', 'ドラゴンクエストウォーク'],
    'dragon-quest-monsters-3': ['Dragon Quest Monsters: The Dark Prince', 'ドラゴンクエストモンスターズ3'],
    'blue-archive': ['Blue Archive', 'ブルーアーカイブ'],
    'project-sekai': ['Project Sekai', 'プロジェクトセカイ カラフルステージ！'],
    'proseka': ['Project Sekai Colorful Stage', 'プロジェクトセカイ'],
    'dragon-ball-z-dokkan-battle': ['Dragon Ball Z Dokkan Battle', 'ドラゴンボールZ ドッカンバトル'],
    'valheim': ['Valheim (video game)', 'Valheim game'],
    'throne-and-liberty': ['Throne and Liberty (video game)', 'Throne and Liberty MMORPG'],
    'multiversus': ['MultiVersus (video game)', 'MultiVersus game'],
    'phasmophobia': ['Phasmophobia (video game)', 'Phasmophobia game'],
    'pro-baseball-spirits-2024': ['プロ野球スピリッツ2024', 'Pro Yakyu Spirits'],
    'pro-baseball-spirits-a': ['プロ野球スピリッツA', 'Pro Yakyu Spirits A'],
    'eafc-mobile': ['EA Sports FC Mobile', 'FIFA Mobile'],
    'nba-2k-mobile': ['NBA 2K Mobile Basketball', 'NBA 2K Mobile'],
    'winning-post-10': ['ウイニングポスト10', 'Winning Post 10'],
    'soccer-spirits': ['Soccer Spirits (video game)', 'サッカースピリッツ'],
    'azur-lane': ['Azur Lane', 'アズールレーン'],
    'alchemy-stars': ['Alchemy Stars (video game)', '白夜極光'],
    'guardian-tales': ['Guardian Tales (video game)', 'ガーディアンテイルズ'],
    'summoners-war': ['Summoners War: Sky Arena', 'サマナーズウォー'],
    'brown-dust-2': ['Brown Dust II', 'ブラウンダスト2'],
    'brave-frontier': ['Brave Frontier (video game)', 'ブレイブフロンティア'],
    'afk-journey': ['AFK Journey (video game)', 'AFKジャーニー'],
    'afk-arena': ['AFK Arena (video game)', 'AFKアリーナ'],
    'idle-heroes': ['Idle Heroes (video game)', 'アイドルヒーローズ'],
    'survivor-io': ['Survivor.io (video game)', 'Survivor io game'],
    'slay-the-spire-2': ['Slay the Spire 2', 'Slay the Spire II'],
    'slay-the-spire': ['Slay the Spire (video game)', 'Slay the Spire game'],
    'sinoalice': ['SINoALICE', 'シノアリス'],
    'honkai-impact-3rd': ['Honkai Impact 3rd', '崩壊3rd'],
    'tower-of-fantasy': ['Tower of Fantasy (video game)', '幻塔'],
    'torchlight-infinite': ['Torchlight Infinite', 'トーチライトインフィニティ'],
    'star-wars-galaxy-of-heroes': ['Star Wars: Galaxy of Heroes', 'SWGoH'],
    'romancing-saga-minstrel-song-remastered': ['Romancing SaGa', 'ロマンシング サガ ミンストレルソング'],
    'yo-kai-watch-punipuni': ['Yo-kai Watch Wibble Wobble', '妖怪ウォッチ ぷにぷに'],
    'monster-hunter-now': ['Monster Hunter Now', 'モンスターハンターNow'],
    'total-war-warhammer-iii': ['Total War: Warhammer III', 'Total War Warhammer 3'],
    'triangle-strategy': ['Triangle Strategy (video game)', 'トライアングルストラテジー'],
    'mario-plus-rabbids-sparks-of-hope': ['Mario + Rabbids Sparks of Hope', 'マリオ＋ラビッツ'],
    'astral-chain': ['Astral Chain (video game)', 'アストラルチェイン'],
    'dave-the-diver': ['Dave the Diver (video game)', 'Dave the Diver game'],
    'indivisible': ['Indivisible (video game)', 'Indivisible game'],
    'sea-of-stars': ['Sea of Stars (video game)', 'Sea of Stars RPG'],
    'chained-echoes': ['Chained Echoes (video game)', 'Chained Echoes RPG'],
    'cosmic-star-heroine': ['Cosmic Star Heroine (video game)', 'Cosmic Star Heroine RPG'],
    'world-of-tanks-blitz': ['World of Tanks Blitz', 'WoT Blitz'],
    'marvel-future-fight': ['Marvel Future Fight', 'MARVEL Future Fight'],
    'marvel-strike-force': ['Marvel Strike Force', 'MARVEL Strike Force'],
    'marvel-contest-of-champions': ['Marvel Contest of Champions', 'MCOC'],
    'dc-heroes-villains': ['DC Heroes & Villains', 'DC Heroes Villains game'],
    'lotr-heroes-of-middle-earth': ['Heroes of Middle-earth', 'LotR Heroes'],
    'maplestory': ['MapleStory (video game)', 'メイプルストーリー'],
    'love-nikki': ['Love Nikki-Dress UP Queen', 'ミラクルニキ'],
    'taiko-no-tatsujin': ['Taiko no Tatsujin (video game)', '太鼓の達人'],
    'rhythm-game-arcaea': ['Arcaea (video game)', 'Arcaea rhythm game'],
    'cytus-ii': ['Cytus II (video game)', 'Cytus 2'],
    'bloons-td-6': ['Bloons TD 6 (video game)', 'Bloons Tower Defense 6'],
    'coin-master': ['Coin Master (video game)', 'Coin Master game'],
    'life-after': ['LifeAfter (video game)', 'ライフアフター'],
    'digimon-story-cyber-sleuth': ['Digimon Story Cyber Sleuth', 'デジモンストーリー サイバースルゥース'],
    'snack-world': ['The Snack World (video game)', 'スナックワールド'],
    'professor-layton-new-world': ['Professor Layton and the New World of Steam', 'レイトン教授'],
    'danganronpa-s': ['Danganronpa S: Ultimate Summer Camp', 'ダンガンロンパS'],
    'visual-novel-clannad': ['Clannad (visual novel)', 'CLANNAD'],
    'melty-blood-type-lumina': ['Melty Blood: Type Lumina', 'メルティブラッド タイプルミナ'],
    'touhou-project': ['Touhou Project', '東方Project'],
    'world-flipper': ['World Flipper (video game)', 'ワールドフリッパー'],
    'mir4': ['MIR4 (video game)', 'MIR4 MMORPG'],
    'squad': ['Squad (video game)', 'Squad game FPS'],
    'luigi-mansion-3': ["Luigi's Mansion 3", 'ルイージマンション3'],
    'naruto-storm-connections': ['Naruto x Boruto Ultimate Ninja Storm Connections', 'ナルティメットストームコネクションズ'],
    'atelier-resleriana': ['Atelier Resleriana', 'レスレリアーナのアトリエ'],
    'romancing-saga-2-remake': ['Romancing SaGa 2', 'ロマンシング サガ2'],
    'suika-game': ['Suika Game', 'スイカゲーム'],
    'donkey-kong-country-tropical-freeze': ['Donkey Kong Country: Tropical Freeze', 'ドンキーコング トロピカルフリーズ'],
    'balatro': ['Balatro (video game)', 'Balatro card game'],
    'ender-magnolia': ['Ender Magnolia: Bloom in the Mist', 'ENDER MAGNOLIA'],
    'dwarf-fortress': ['Dwarf Fortress (video game)', 'Dwarf Fortress game'],
    'crusader-kings-3': ['Crusader Kings III', 'Crusader Kings 3 game'],
}


def wiki_search_image(title, api_url=EN_WIKI_API):
    """Search Wikipedia for a game and get its page image."""
    params = {
        'action': 'query',
        'titles': title,
        'prop': 'pageimages',
        'format': 'json',
        'pithumbsize': THUMB_SIZE,
        'pilicense': 'any',
    }
    url = f"{api_url}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamersFor/1.0 (game guide site)'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            pages = data.get('query', {}).get('pages', {})
            for pid, page in pages.items():
                if pid == '-1':
                    continue
                thumb = page.get('thumbnail', {}).get('source')
                if thumb:
                    return thumb
    except:
        pass

    # Search
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': title,
        'srnamespace': '0',
        'srlimit': '5',
        'format': 'json',
    }
    url = f"{api_url}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamersFor/1.0 (game guide site)'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            results = data.get('query', {}).get('search', [])
            for result in results:
                page_title = result.get('title', '')
                img_params = {
                    'action': 'query',
                    'titles': page_title,
                    'prop': 'pageimages',
                    'format': 'json',
                    'pithumbsize': THUMB_SIZE,
                    'pilicense': 'any',
                }
                img_url = f"{api_url}?{urllib.parse.urlencode(img_params)}"
                req2 = urllib.request.Request(img_url, headers={'User-Agent': 'GamersFor/1.0 (game guide site)'})
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    img_data = json.loads(resp2.read())
                    pages = img_data.get('query', {}).get('pages', {})
                    for pid, page in pages.items():
                        if pid == '-1':
                            continue
                        thumb = page.get('thumbnail', {}).get('source')
                        if thumb:
                            return thumb
    except:
        pass
    return None


def download_image(url, filepath):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamersFor/1.0 (game guide site)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 500:
                return False
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except:
        return False


def main():
    success = 0
    still_failed = []

    total = len(RETRY_MAP)
    for i, (slug, search_terms) in enumerate(RETRY_MAP.items()):
        img_dir = IMAGES_DIR / slug
        img_path = img_dir / 'thumb.jpg'

        if img_path.exists() and img_path.stat().st_size > 1000:
            print(f"[{i+1}/{total}] {slug}: Already exists, skipping")
            continue

        print(f"[{i+1}/{total}] {slug}:", end=' ', flush=True)

        found = False
        for term in search_terms:
            # Try EN Wikipedia
            img_url = wiki_search_image(term, EN_WIKI_API)
            if not img_url:
                # Try JA Wikipedia
                img_url = wiki_search_image(term, JA_WIKI_API)

            if img_url:
                img_dir.mkdir(parents=True, exist_ok=True)
                if download_image(img_url, img_path):
                    success += 1
                    found = True
                    print(f"OK with '{term}' ({img_path.stat().st_size} bytes)")
                    break

            time.sleep(0.2)

        if not found:
            still_failed.append(slug)
            print("STILL FAILED")

        time.sleep(0.3)

    print(f"\n=== Retry Results ===")
    print(f"Success: {success}")
    print(f"Still failed: {len(still_failed)}")
    if still_failed:
        print(f"\nStill failed games:")
        for s in still_failed:
            print(f"  - {s}")


if __name__ == '__main__':
    main()
