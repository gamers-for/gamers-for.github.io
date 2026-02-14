#!/usr/bin/env python3
"""
QA Stage 2: Claude API による画像評価（スタブ）

テンプレート変更時のみ実行。ページのスクリーンショットを撮影し、
Claude APIで視覚的品質を評価する。

評価項目:
  1. レイアウト（Game8風のUI配置か）
  2. 色使い（ダークネイビー+赤アクセントの統一感）
  3. タイポグラフィ（フォントサイズ・行間・可読性）
  4. インタラクション（ホバー・アクティブ状態の視認性）
  5. 情報密度（適切な余白・密度のバランス）

使い方:
  python qa_stage2.py /path/to/game_config.json [--api-key KEY]

必要:
  pip install anthropic playwright
"""

import json
import os
import sys


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def capture_screenshots(config, hugo_port=1313):
    """主要ページのスクリーンショットを撮影"""
    # TODO: Playwright でスクリーンショット撮影
    print("  [stub] スクリーンショット撮影: 未実装")
    return []


def evaluate_with_claude(screenshots, api_key=None):
    """Claude APIで画像評価"""
    # TODO: anthropic SDK で画像評価
    print("  [stub] Claude API画像評価: 未実装")
    return {
        "layout": {"score": 0, "comment": "未実装"},
        "color": {"score": 0, "comment": "未実装"},
        "typography": {"score": 0, "comment": "未実装"},
        "interaction": {"score": 0, "comment": "未実装"},
        "density": {"score": 0, "comment": "未実装"},
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python qa_stage2.py /path/to/game_config.json [--api-key KEY]")
        sys.exit(1)

    config_path = os.path.abspath(sys.argv[1])
    config = load_config(config_path)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if "--api-key" in sys.argv:
        idx = sys.argv.index("--api-key")
        if idx + 1 < len(sys.argv):
            api_key = sys.argv[idx + 1]

    print(f"=== QA Stage 2: {config['game_name']} 画像評価 ===")

    screenshots = capture_screenshots(config)
    results = evaluate_with_claude(screenshots, api_key)

    print("\n評価結果:")
    for item, result in results.items():
        print(f"  {item}: {result['score']}/10 - {result['comment']}")

    avg = sum(r["score"] for r in results.values()) / max(len(results), 1)
    print(f"\n総合スコア: {avg:.1f}/10")


if __name__ == "__main__":
    main()
