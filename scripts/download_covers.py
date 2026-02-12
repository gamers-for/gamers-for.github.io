#!/usr/bin/env python3
"""Download game cover images from Wikipedia API.
Saves to static/images/games/{slug}/thumb.jpg
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TSV_PATH = BASE_DIR / 'titles' / 'game_titles_500.tsv'
IMAGES_DIR = BASE_DIR / 'static' / 'images' / 'games'
THUMB_SIZE = 400  # px width

# Wikipedia API endpoints
EN_WIKI_API = 'https://en.wikipedia.org/w/api.php'
JA_WIKI_API = 'https://ja.wikipedia.org/w/api.php'

# Manual mappings for games that don't match well with Wikipedia search
MANUAL_TITLES = {
    'splatoon3': 'Splatoon 3',
    'splatoon-3': 'Splatoon 3',
    'dark-souls': 'Dark Souls',
    'dark-souls-ii': 'Dark Souls II',
    'dark-souls-iii': 'Dark Souls III',
    'elden-ring': 'Elden Ring',
    'elden-ring-nightreign': 'Elden Ring Nightreign',
    'gta-v': 'Grand Theft Auto V',
    'gta-online': 'Grand Theft Auto Online',
    'gta-vi': 'Grand Theft Auto VI',
    'ff-xiv': 'Final Fantasy XIV',
    'pubg': 'PlayerUnknown\'s Battlegrounds',
    'pubg-mobile': 'PUBG Mobile',
    'cod-mw3': 'Call of Duty: Modern Warfare III (2023 video game)',
    'yu-gi-oh-master-duel': 'Yu-Gi-Oh! Master Duel',
    'pso2-new-genesis': 'Phantasy Star Online 2: New Genesis',
    'pokemon-go': 'Pokémon Go',
    'pokemon-scarlet-violet': 'Pokémon Scarlet and Violet',
    'pokemon-legends-za': 'Pokémon Legends: Z-A',
    'pokemon-tcg-pocket': 'Pokémon Trading Card Game Pocket',
    'pokemon-unite': 'Pokémon Unite',
    'pokemon-sleep': 'Pokémon Sleep',
    'pokemon-masters-ex': 'Pokémon Masters EX',
    'pokemon-legends-arceus': 'Pokémon Legends: Arceus',
    'pokemon-sword-shield': 'Pokémon Sword and Shield',
    'pokemon-diamond-pearl-remake': 'Pokémon Brilliant Diamond and Shining Pearl',
    'fate-grand-order': 'Fate/Grand Order',
    'nikke': 'Goddess of Victory: Nikke',
    'nikke-goddess-of-victory': 'Goddess of Victory: Nikke',
    'proseka': 'Project Sekai: Colorful Stage! feat. Hatsune Miku',
    'project-sekai': 'Project Sekai: Colorful Stage! feat. Hatsune Miku',
    'monster-strike': 'Monster Strike',
    'puzzle-and-dragons': 'Puzzle & Dragons',
    'uma-musume': 'Uma Musume Pretty Derby',
    'apex-legends': 'Apex Legends',
    'valorant': 'Valorant',
    'fortnite': 'Fortnite',
    'minecraft': 'Minecraft',
    'league-of-legends': 'League of Legends',
    'dead-by-daylight': 'Dead by Daylight',
    'identity-v': 'Identity V',
    'identity-v-5th': 'Identity V',
    'touhou-project': 'Touhou Project',
    'counter-strike-2': 'Counter-Strike 2',
    'counter-strike-2-console': 'Counter-Strike 2',
    'knives-out': 'Knives Out (video game)',
    'free-fire': 'Garena Free Fire',
    'roblox': 'Roblox',
    'cod-warzone': 'Call of Duty: Warzone',
    'baldurs-gate-3': "Baldur's Gate 3",
    'overwatch-2': 'Overwatch 2',
    'fifa-fc-25': 'EA Sports FC 25',
    'eafc-mobile': 'EA Sports FC Mobile',
    'efootball': 'EFootball',
    'suika-game': 'Suika Game',
    'stardew-valley': 'Stardew Valley',
    'cyberpunk-2077': 'Cyberpunk 2077',
    'skyrim': 'The Elder Scrolls V: Skyrim',
    'persona-5-royal': 'Persona 5 Royal',
    'persona-3-reload': 'Persona 3 Reload',
    'street-fighter-6': 'Street Fighter 6',
    'tekken-8': 'Tekken 8',
    'monster-hunter-wilds': 'Monster Hunter Wilds',
    'zelda-tears-of-the-kingdom': 'The Legend of Zelda: Tears of the Kingdom',
    'zelda-breath-of-the-wild': 'The Legend of Zelda: Breath of the Wild',
    'zelda-echoes-of-wisdom': 'The Legend of Zelda: Echoes of Wisdom',
    'dragon-quest-iii-hd2d': 'Dragon Quest III HD-2D Remake',
    'mario-kart-8-deluxe': 'Mario Kart 8 Deluxe',
    'super-mario-bros-wonder': 'Super Mario Bros. Wonder',
    'super-smash-bros-ultimate': 'Super Smash Bros. Ultimate',
    'animal-crossing-new-horizons': 'Animal Crossing: New Horizons',
    'hollow-knight-silksong': 'Hollow Knight: Silksong',
    'helldivers-2': 'Helldivers 2',
    'black-myth-wukong': 'Black Myth: Wukong',
    'hades-2': 'Hades II',
    'palworld': 'Palworld',
    'metaphor-refantazio': 'Metaphor: ReFantazio',
}


def wiki_search_image(title, api_url=EN_WIKI_API):
    """Search Wikipedia for a game and get its page image."""
    # First try exact title
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
    except Exception as e:
        pass

    # Try search if exact match fails
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': f'{title} video game',
        'srnamespace': '0',
        'srlimit': '3',
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
                # Get image for this page
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
    except Exception as e:
        pass

    return None


def download_image(url, filepath):
    """Download image from URL to filepath."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GamersFor/1.0 (game guide site)'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 500:  # Too small, probably an error
                return False
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        return False


def main():
    # Read TSV
    games = []
    with open(TSV_PATH, 'r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                slug = parts[0]
                name_ja = parts[1]
                name_en = parts[2]
                games.append((slug, name_ja, name_en))

    # Add splatoon3 (directory name differs from TSV slug)
    # The directory is 'splatoon3' but TSV has 'splatoon-3'

    success = 0
    failed = 0
    skipped = 0
    failed_list = []

    total = len(games)
    for i, (slug, name_ja, name_en) in enumerate(games):
        # Check both possible directory names
        dir_slug = slug
        if slug == 'splatoon-3':
            dir_slug = 'splatoon3'

        img_dir = IMAGES_DIR / dir_slug
        img_path = img_dir / 'thumb.jpg'

        # Skip if already exists
        if img_path.exists() and img_path.stat().st_size > 1000:
            skipped += 1
            continue

        # Determine search title
        search_title = MANUAL_TITLES.get(slug, name_en)

        print(f"[{i+1}/{total}] {slug}: Searching for '{search_title}'...", end=' ', flush=True)

        # Try English Wikipedia first
        img_url = wiki_search_image(search_title, EN_WIKI_API)

        # If not found, try Japanese Wikipedia with Japanese name
        if not img_url:
            img_url = wiki_search_image(name_ja, JA_WIKI_API)

        # If still not found, try with "(video game)" suffix
        if not img_url:
            img_url = wiki_search_image(f"{search_title} (video game)", EN_WIKI_API)

        if img_url:
            img_dir.mkdir(parents=True, exist_ok=True)
            if download_image(img_url, img_path):
                success += 1
                print(f"OK ({img_path.stat().st_size} bytes)")
            else:
                failed += 1
                failed_list.append(slug)
                print("DOWNLOAD FAILED")
        else:
            failed += 1
            failed_list.append(slug)
            print("NOT FOUND")

        # Rate limiting - be nice to Wikipedia
        time.sleep(0.3)

    print(f"\n=== Results ===")
    print(f"Success: {success}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Failed: {failed}")
    if failed_list:
        print(f"\nFailed games:")
        for s in failed_list:
            print(f"  - {s}")


if __name__ == '__main__':
    main()
