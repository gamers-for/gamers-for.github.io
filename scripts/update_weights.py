#!/usr/bin/env python3
"""Update weight in all game _index.md files for ordering.
Top priority: Splatoon 3, Dark Souls 1/2/3, Elden Ring
Then: by priority S > A > B, keeping TSV order within each priority.
"""
import os
import re

CONTENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'content', 'games')
TSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'titles', 'game_titles_500.tsv')

# Top pinned games (slug -> weight)
PINNED = {
    'splatoon3': 1,      # directory name is splatoon3
    'splatoon-3': 1,     # TSV slug
    'dark-souls': 2,
    'dark-souls-ii': 3,
    'dark-souls-iii': 4,
    'elden-ring': 5,
    'elden-ring-nightreign': 6,
}

def read_tsv_order():
    """Read TSV and return ordered list of (slug, priority)."""
    entries = []
    with open(TSV_PATH, 'r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 6:
                slug = parts[0]
                priority = parts[5]
                entries.append((slug, priority))
    return entries

def compute_weights():
    """Compute weight for each slug."""
    entries = read_tsv_order()
    weights = {}

    # Pinned games get fixed weights
    for slug, w in PINNED.items():
        weights[slug] = w

    # Remaining games: S priority first, then A, then B
    # Within each priority, maintain TSV order
    priority_order = {'S': 0, 'A': 1, 'B': 2}
    remaining = [(slug, p) for slug, p in entries if slug not in PINNED]
    remaining.sort(key=lambda x: priority_order.get(x[1], 3))

    w = 10  # Start after pinned games
    for slug, _ in remaining:
        if slug not in weights:
            weights[slug] = w
            w += 1

    return weights

def update_md_weight(filepath, new_weight):
    """Update the weight field in a markdown front matter."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace weight line in front matter
    new_content = re.sub(
        r'^(weight:\s*)\d+',
        f'weight: {new_weight}',
        content,
        count=1,
        flags=re.MULTILINE
    )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    weights = compute_weights()
    updated = 0
    skipped = 0

    # Iterate over all game directories
    for dirname in os.listdir(CONTENT_DIR):
        md_path = os.path.join(CONTENT_DIR, dirname, '_index.md')
        if not os.path.isfile(md_path):
            continue

        # Map directory name to weight
        w = weights.get(dirname)
        if w is None:
            # Try without trailing characters
            skipped += 1
            continue

        if update_md_weight(md_path, w):
            updated += 1

    print(f"Updated: {updated}, Skipped: {skipped}")
    print("Pinned weights:", {k: v for k, v in sorted(weights.items(), key=lambda x: x[1]) if v <= 10})

if __name__ == '__main__':
    main()
