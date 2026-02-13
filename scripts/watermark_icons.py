#!/usr/bin/env python3
"""
既存アイコンに「GF」透かしを追加しWebPで保存するスクリプト
対象: static/images/games/splatoon3/weapons/, subs/, specials/
元PNGはバックアップとして残す
"""

import os
import glob
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "static", "images", "games", "splatoon3")

# 処理対象ディレクトリ
TARGET_DIRS = [
    os.path.join(IMG_DIR, "weapons"),
    os.path.join(IMG_DIR, "subs"),
    os.path.join(IMG_DIR, "specials"),
]

# バックアップ先
BACKUP_DIR = os.path.join(IMG_DIR, "backup_originals")

# WebP品質
WEBP_QUALITY = 85

# 透かし設定
WATERMARK_TEXT = "GF"
WATERMARK_OPACITY = 80  # 0-255, 80 = 約31%透明


def get_font(size):
    """フォントを取得（システムフォントから探す）"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    # フォールバック
    return ImageFont.load_default()


def add_watermark(img):
    """画像に「GF」透かしを左下に追加"""
    # RGBA変換
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    w, h = img.size

    # フォントサイズ: 画像の高さの15%程度
    font_size = max(10, int(h * 0.15))
    font = get_font(font_size)

    # 透かし用レイヤー作成
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # テキストサイズ計測
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 左下に配置（マージン: 画像サイズの3%）
    margin = max(2, int(min(w, h) * 0.03))
    x = margin
    y = h - text_h - margin - bbox[1]

    # 白い文字 + 半透明
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, WATERMARK_OPACITY))

    # 合成
    return Image.alpha_composite(img, overlay)


def process_directory(dir_path):
    """ディレクトリ内の全PNG画像を処理"""
    if not os.path.exists(dir_path):
        print(f"  スキップ（存在しない）: {dir_path}")
        return 0

    png_files = glob.glob(os.path.join(dir_path, "*.png"))
    if not png_files:
        print(f"  スキップ（PNGなし）: {dir_path}")
        return 0

    # バックアップディレクトリ
    dir_name = os.path.basename(dir_path)
    backup_subdir = os.path.join(BACKUP_DIR, dir_name)
    os.makedirs(backup_subdir, exist_ok=True)

    count = 0
    for png_path in sorted(png_files):
        filename = os.path.basename(png_path)
        webp_name = os.path.splitext(filename)[0] + ".webp"

        try:
            # 元ファイルをバックアップ
            backup_path = os.path.join(backup_subdir, filename)
            if not os.path.exists(backup_path):
                img_orig = Image.open(png_path)
                img_orig.save(backup_path)

            # 透かし追加
            img = Image.open(png_path)
            img_wm = add_watermark(img)

            # WebP保存（同じディレクトリ）
            webp_path = os.path.join(dir_path, webp_name)
            # アルファチャンネル付きで保存
            img_wm.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=4)

            count += 1
        except Exception as e:
            print(f"  ✗ エラー: {filename}: {e}")

    return count


def main():
    print("=== アイコン透かし処理開始 ===\n")

    total = 0
    for dir_path in TARGET_DIRS:
        dir_name = os.path.basename(dir_path)
        print(f"処理中: {dir_name}/")
        count = process_directory(dir_path)
        print(f"  完了: {count}件")
        total += count

    print(f"\n=== 完了 ===")
    print(f"合計: {total}件のWebPファイル生成")
    print(f"バックアップ: {BACKUP_DIR}")
    print(f"\n元PNGは残しています。WebPに切り替える場合は以下を実行:")
    print(f"  Hugoテンプレートの画像パスを .png → .webp に変更")


if __name__ == "__main__":
    main()
