# raw HTML → Hugo 公開手順書

## 目的

`０１もれなくスクレイピング.md` で取得した raw HTML を、
そのまま GitHub Pages で公開する。

---

## 前提

- スクレイピング済みの raw HTML が `{game_dir}/raw_html/` に入っている
- ファイル名形式: `{記事ID}.html`（例: `478553.html`）
- トップページ: `top.html`
- メタデータ: `_metadata.json`, `_sitemap_urls.json`

---

## ステップ1: static ディレクトリにコピー

raw HTML をそのまま `static/{game_slug}/` にコピーする。
Hugo の `static/` 配下のファイルはビルド時にそのまま `public/` に出力される。

```bash
# 例: splatoon3
mkdir -p static/splatoon3
cp ００００１スプラトゥーン３/raw_html/*.html static/splatoon3/
```

### トップページ用の index.html を作る

`/{game_slug}/` でアクセスしたときに表示されるように、
`top.html` を `index.html` としてもコピーする。

```bash
cp static/splatoon3/top.html static/splatoon3/index.html
```

### メタファイルは不要

`_metadata.json` 等はコピーしない。`*.html` のみ。

---

## ステップ2: サイズ確認

GitHub Pages の artifact アップロード上限は **1GB**。
`public/` 全体のサイズが 1GB を超えるとデプロイが不完全になる。

```bash
# Hugoビルド
hugo --minify

# サイズ確認
du -sh public/
```

**1GB を超える場合の対処:**

1. Hugo で生成している他コンテンツ（`.md` ファイル）が不要なら削除する
2. `static/images/` の画像が大きければ圧縮する
3. raw HTML 自体は手を付けない（そのまま配信が目的）

### スプラ3の実績

| 項目 | サイズ |
|------|--------|
| raw HTML 1,515件 | 644 MB |
| 他ゲーム + 画像 + CSS等 | ~170 MB |
| **合計** | **~813 MB** (1GB以内) |

※ スプラ3の Hugo 生成コンテンツ（`.md` → `.html`）715MB は削除して収めた。

---

## ステップ3: コミット & プッシュ

```bash
git add static/splatoon3/
git commit -m "splatoon3: raw HTMLをそのまま配信"
git push origin main
```

GitHub Actions が自動で Hugo ビルド → GitHub Pages デプロイを実行する。

---

## ステップ4: 動作確認

デプロイ完了後（約2分）、以下の URL でアクセスできることを確認。

```
https://{your-domain}/{game_slug}/           ← トップページ
https://{your-domain}/{game_slug}/478553.html ← 個別ページ（記事ID）
https://{your-domain}/{game_slug}/top.html    ← トップページ（別名）
```

### 確認ポイント

- ページが表示されるか（404 でないか）
- 元サイトと同じ見た目になっているか
- 画像は元サイトの CDN から読み込まれるので表示される

---

## ディレクトリ構成

```
gamers-for/
├── static/
│   └── splatoon3/          ← raw HTML をここに置く
│       ├── index.html      ← top.html のコピー
│       ├── top.html
│       ├── 478553.html
│       ├── 477903.html
│       └── ... (1,515件)
├── ００００１スプラトゥーン３/
│   └── raw_html/           ← スクレイプ元（マスターコピー）
│       ├── _metadata.json
│       ├── _sitemap_urls.json
│       └── *.html
├── hugo.toml
└── .github/workflows/hugo.yml
```

**`static/splatoon3/`** = 公開用（Hugo がそのまま配信）
**`raw_html/`** = マスターコピー（変更せず保管）

---

## 他ゲームへの展開

同じ手順を繰り返すだけ。

```bash
# 1. スクレイピング（０１の手順）
python3 scrape_game8_complete.py genshin

# 2. static にコピー
mkdir -p static/genshin
cp ００００２原神/raw_html/*.html static/genshin/
cp static/genshin/top.html static/genshin/index.html

# 3. サイズ確認
hugo --minify && du -sh public/

# 4. プッシュ
git add static/genshin/ && git commit -m "genshin: raw HTML配信" && git push
```

### サイズ制限に注意

複数ゲームを追加すると 1GB を超える可能性がある。
その場合は古いゲームを `static/` から外すか、リポジトリを分割する。

---

## 注意事項

1. **raw HTML は一切変更しない** — スクレイプしたままの状態で配信する
2. **`_metadata.json` 等のメタファイルは公開しない** — `*.html` のみコピー
3. **`index.html` を忘れない** — ないと `/{game_slug}/` で 404 になる
4. **`public/` が 1GB を超えないようにする** — GitHub Pages の制限
