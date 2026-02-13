#!/usr/bin/env python3
"""
Gemini APIを使って画像をネオンサイン風に書き直すスクリプト
引数: ファイルパスのリスト
"""

import os
import sys
import json
import base64
import time
import requests
from pathlib import Path

API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDFhJk5yZk1BI8_JZFRPVvfRQLA-IkoQnM")
MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT = "Redraw this image in watercolor painting style. Use soft, flowing watercolor techniques with gentle color bleeding and paper texture."


def encode_image(image_path: str) -> tuple:
    with open(image_path, "rb") as f:
        data = f.read()
    ext = Path(image_path).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    return base64.b64encode(data).decode("utf-8"), mime_map.get(ext, "image/png")


def generate_image(image_path: str, output_path: str) -> bool:
    print(f"  処理中: {Path(image_path).name} ...", flush=True)
    b64_data, mime_type = encode_image(image_path)

    payload = {
        "contents": [{
            "parts": [
                {"inlineData": {"mimeType": mime_type, "data": b64_data}},
                {"text": PROMPT}
            ]
        }],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 1.0,
        }
    }

    try:
        resp = requests.post(ENDPOINT, headers={"Content-Type": "application/json"},
                             params={"key": API_KEY}, json=payload, timeout=120)
        if resp.status_code != 200:
            print(f"  エラー (HTTP {resp.status_code}): {resp.text[:500]}")
            return False

        result = resp.json()
        candidates = result.get("candidates", [])
        if not candidates:
            print(f"  エラー: candidatesが空")
            return False

        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                img_mime = part["inlineData"].get("mimeType", "image/png")
                ext = {
                    "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"
                }.get(img_mime, ".png")
                out = Path(output_path).with_suffix(ext)
                with open(out, "wb") as f:
                    f.write(img_data)
                print(f"  保存完了: {out} ({len(img_data)} bytes)")
                return True
            elif "text" in part:
                print(f"  テキスト応答: {part['text'][:200]}")

        print(f"  エラー: 画像が生成されませんでした")
        return False

    except requests.exceptions.Timeout:
        print(f"  タイムアウト")
        return False
    except Exception as e:
        print(f"  例外: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 gemini_neon_redraw.py <画像パス1> [画像パス2] ...")
        print("  または: python3 gemini_neon_redraw.py --dir <ディレクトリ>")
        sys.exit(1)

    image_files = [Path(f) for f in sys.argv[1:]]

    # 存在確認
    for f in image_files:
        if not f.exists():
            print(f"エラー: ファイルが見つかりません: {f}")
            sys.exit(1)

    # 出力ディレクトリ（最初のファイルの親ディレクトリ/gemini_neon/）
    out_dir = image_files[0].parent / "gemini_watercolor"
    out_dir.mkdir(exist_ok=True)

    print(f"対象画像: {len(image_files)}枚")
    print(f"出力先: {out_dir}")
    print(f"モデル: {MODEL}")
    print(f"プロンプト: {PROMPT}")
    print("=" * 60)

    success = 0
    fail = 0

    for i, img_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] {img_file.name}")
        output_path = out_dir / img_file.name

        # 既に生成済みならスキップ
        if any((out_dir / (img_file.stem + ext)).exists() for ext in [".png", ".jpg", ".webp"]):
            print(f"  スキップ（生成済み）")
            success += 1
            continue

        if generate_image(str(img_file), str(output_path)):
            success += 1
        else:
            fail += 1

        # API レートリミット対策
        if i < len(image_files):
            print("  待機中 (5秒)...")
            time.sleep(5)

    print("\n" + "=" * 60)
    print(f"完了: 成功 {success}/{len(image_files)}, 失敗 {fail}")


if __name__ == "__main__":
    main()
