じゃあ、一からまたHTMLを取得し直してみましょう。元の、まずはraw_htmlのフォルダーを一旦バックアップにしましょう。raw_htmlをraw_html_backupにリネームしてください。
#!/usr/bin/env python3
import json, base64, sys, urllib.request

API_KEY = "AIzaSyDZQV79qMJh4hZSMFzbm3Mhy56oa5w1tKs"
INPUT_PATH = "/mnt/ubuntu22-home/robot/work_space/project_blog/gamers-for/００００１スプラトゥーン３/images/test_game8_img.png"
OUTPUT_PATH = "/mnt/ubuntu22-home/robot/work_space/project_blog/gamers-for/０００００テンプレ/colored_pencil_output.png"

PROMPT = (
    "この画像に描かれている武器（ブキ）を参考にして、三色の色鉛筆だけで描いたイラストとして描き直してください。"
    "条件："
    "使用する色鉛筆は「黄緑」「紫」「灰色」の3色のみ。"
    "色鉛筆で紙に描いたような手描き感のあるタッチにする。"
    "白い画用紙の上に描かれている構図にする。"
    "色鉛筆の筆跡（ストローク）がはっきり見えるようにする。"
    "塗り残しや紙の白地が適度に残るリアルな色鉛筆画にする。"
    "武器の形状やディテール（溝、丸い部分、上部のパーツ）は元画像を忠実に再現する。"
    "背景は描かず、白い紙のままにする。"
)

# 試行するモデルリスト
MODELS = [
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-exp-image-generation",
    "gemini-3-pro-image-preview",
]

# 入力画像をbase64エンコード
with open(INPUT_PATH, "rb") as f:
    b64_data = base64.b64encode(f.read()).decode("utf-8")

print(f"入力画像サイズ: {len(b64_data)} chars (base64)")

payload = {
    "contents": [{
        "parts": [
            {"inlineData": {"mimeType": "image/png", "data": b64_data}},
            {"text": PROMPT}
        ]
    }],
    "generationConfig": {
        "responseModalities": ["TEXT", "IMAGE"]
    }
}

body = json.dumps(payload).encode("utf-8")
print(f"リクエストサイズ: {len(body) / 1024 / 1024:.1f} MB")

for model in MODELS:
    print(f"\n--- モデル: {model} を試行中 ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  HTTPエラー {e.code}: {error_body[:300]}")
        continue
    except Exception as e:
        print(f"  エラー: {e}")
        continue

    if "error" in data:
        print(f"  APIエラー: {data['error']['message'][:200]}")
        continue

    # 成功 - レスポンス処理
    print(f"  成功! モデル: {model}")
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            img_bytes = base64.b64decode(part["inlineData"]["data"])
            with open(OUTPUT_PATH, "wb") as out:
                out.write(img_bytes)
            print(f"  画像保存完了: {OUTPUT_PATH} ({len(img_bytes)} bytes)")
        elif "text" in part:
            print(f"  Gemini応答: {part['text']}")
    print("完了!")
    sys.exit(0)

print("\n全モデルで失敗しました。")
sys.exit(1)
