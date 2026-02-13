#!/usr/bin/env python3
"""
Gemini APIを使って画像を3色の色鉛筆風に書き直すスクリプト
"""

import os
import sys
import json
import base64
import time
import requests
from pathlib import Path

API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDFhJk5yZk1BI8_JZFRPVvfRQLA-IkoQnM")
# 画像生成対応モデル
MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT = "この画像を3色の色鉛筆で書き直してください。手描き風の温かみのあるイラストにしてください。"


def encode_image(image_path: str) -> tuple:
    """画像をbase64エンコード"""
    with open(image_path, "rb") as f:
        data = f.read()

    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime_type = mime_map.get(ext, "image/png")
    return base64.b64encode(data).decode("utf-8"), mime_type


def generate_pencil_image(image_path: str, output_path: str) -> bool:
    """Gemini APIで色鉛筆風画像を生成"""
    print(f"  処理中: {Path(image_path).name} ...", flush=True)

    b64_data, mime_type = encode_image(image_path)

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64_data
                        }
                    },
                    {
                        "text": PROMPT
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 1.0,
        }
    }

    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}

    try:
        resp = requests.post(ENDPOINT, headers=headers, params=params, json=payload, timeout=120)

        if resp.status_code != 200:
            print(f"  エラー (HTTP {resp.status_code}): {resp.text[:500]}")
            return False

        result = resp.json()

        # レスポンスから画像データを抽出
        candidates = result.get("candidates", [])
        if not candidates:
            print(f"  エラー: candidatesが空です")
            print(f"  レスポンス: {json.dumps(result, ensure_ascii=False)[:500]}")
            return False

        parts = candidates[0].get("content", {}).get("parts", [])

        image_saved = False
        for part in parts:
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                img_mime = part["inlineData"].get("mimeType", "image/png")

                # MIMEタイプに応じて拡張子を決定
                ext_map = {
                    "image/png": ".png",
                    "image/jpeg": ".jpg",
                    "image/webp": ".webp",
                }
                ext = ext_map.get(img_mime, ".png")

                # 出力パスの拡張子を調整
                out = Path(output_path).with_suffix(ext)
                with open(out, "wb") as f:
                    f.write(img_data)
                print(f"  保存完了: {out} ({len(img_data)} bytes)")
                image_saved = True
                break
            elif "text" in part:
                print(f"  テキスト応答: {part['text'][:200]}")

        if not image_saved:
            print(f"  エラー: 画像が生成されませんでした")
            return False

        return True

    except requests.exceptions.Timeout:
        print(f"  タイムアウト")
        return False
    except Exception as e:
        print(f"  例外: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 gemini_pencil_redraw.py <画像ディレクトリ>")
        sys.exit(1)

    img_dir = Path(sys.argv[1])
    if not img_dir.is_dir():
        print(f"エラー: ディレクトリが見つかりません: {img_dir}")
        sys.exit(1)

    # 出力ディレクトリ
    out_dir = img_dir / "gemini_pencil"
    out_dir.mkdir(exist_ok=True)

    # 対象画像（test_で始まるものとgemini_pencilディレクトリを除外）
    image_files = sorted([
        f for f in img_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        and not f.name.startswith("test_")
    ])

    if not image_files:
        print("対象画像が見つかりません")
        sys.exit(1)

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
        if output_path.exists() or output_path.with_suffix(".jpg").exists() or output_path.with_suffix(".webp").exists():
            print(f"  スキップ（生成済み）")
            success += 1
            continue

        if generate_pencil_image(str(img_file), str(output_path)):
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
