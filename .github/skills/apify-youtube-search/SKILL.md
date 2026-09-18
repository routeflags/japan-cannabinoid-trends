---
name: apify-youtube-search
description: |
  Apify YouTube 検索スキル(API課金)で動画をキーワード検索するスキル。「YouTube検索」「CBXリキッドの動画」などで使う。
---

# Apify YouTube 検索スキル (API課金)

`https://console.apify.com/actors/gJvjeCYNraSfhIaNd` = `danek/youtube-search` を **API課金** で実行し、YouTube 検索結果をキーワードで取得するスキル。YouTubeアカウント・APIキー不要で、タイトル/チャンネル/再生数/公開日/長さ/サムネ/バッジ/チャプター等の構造化データを JSON/CSV で取得する。

- Actor: `gJvjeCYNraSfhIaNd` / `danek/youtube-search` — Youtube Search Scraper (軽量, 最小128MBで動作)
- 上流: https://console.apify.com/actors/gJvjeCYNraSfhIaNd / https://apify.com/danek/youtube-search
- 課金: **PAY_PER_EVENT** — `Actor Start $0.00005` + `result $0.0005/件` (FREE) → GOLD以上 `$0.0002/件`。旧定額 $10/月は終了, 現行は従量課金のみ
- 認証: `.env.d/apify.env` の `APIFY_TOKEN` (https://console.apify.com/settings/integrations で発行, `chmod 600`)

## トリガー

「YouTube 検索して」「YouTube 調べて」「CBXリキッド の動画見て」「gJvjeCYNraSfhIaNd で検索」「ApifyでYouTube検索」などで使う。

## 前提

- Apifyアカウントに **支払い方法登録済み** (無料 $5 付与後, 従量課金。YouTubeは $0.50/1000件と Instagram $2.50/1000件 の1/5)
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在 (`apify-mcp` スキルで管理)
- Node.js v18+ (本環境 v24.13.1) または Python + `curl`
- MCPは `apify-mcp` スキル参照。API直叩きでも可（MCP不調時のフォールバック）

## 料金モデル (2026-07-16改定, build 1.1.20)

| イベント | 説明 | 単価 (FREE) | GOLD+ |
|---------|------|------------|-------|
| `apify-actor-start` | 起動1回あたり (1GBごとに1イベント, 最低1。128MB指定でも1) | **$0.00005** | $0.00005 |
| `apify-default-dataset-item` | 取得1件あたり (primary) | **$0.0005** | **$0.0002** |

計算例: `max_videos=10` で10件取得 → `0.00005 + 10×0.0005 = $0.00505` (FREE) / GOLDなら `0.00205`。旧 $10/月定額は不要。

> Instagram `TxU0ZBQIHdR20dr9C` ($0.0025/件) の 1/5 の単価。1000件で $0.50 (Instagramは $2.50)。

## Input Schema

Build `lcBfQ1sbz5bx58c1X` (2026-07-02) 時点:

```json
{
  "title": "Scrape data from a web page",
  "type": "object",
  "required": ["search_term", "max_videos"],
  "properties": {
    "search_term": {
      "type": "string",
      "description": "",
      "prefill": "apify",
      "title": "search term"
    },
    "max_videos": {
      "type": "integer",
      "description": "Max number of videos to scrape. Upper limit is 100. Contact us for higher limits.",
      "prefill": 10,
      "title": "max videos"
    }
  }
}
```

| フィールド | 必須 | 例 | 備考 |
|-----------|------|---|------|
| `search_term` | ✅ | `"CBXリキッド"` / `"CBD oil"` / `"apify"` | YouTube検索クエリ (日本語可) |
| `max_videos` | ✅ | `10` (default 10, 1-100) | 取得上限。100超は要相談 (support@) |

> Instagram とは命名が異なる: `query` → `search_term`, `maxPages` → `max_videos`。`max_videos` は **件数** (ページ数ではない) で課金も件数比例。

## Output Schema (主要フィールド)

全件 `youtube#searchResult`, null-safe。CSV/Excel 出力も可。

| フィールド | 説明 |
|-----------|------|
| `id.videoId` | 動画ID (`https://youtube.com/watch?v={videoId}`) |
| `snippet.title` | 動画タイトル |
| `snippet.channelId` / `snippet.channelTitle` / `snippet.channelHandle` | チャンネルID / 表示名 / ハンドル (`@...`) |
| `snippet.timestamp` | 相対公開日 (`"1 year ago"` / `"7 years ago"`) — 絶対日付ではない |
| `snippet.duration` | 長さ (秒, integer) |
| `snippet.views` | 再生数 (integer) |
| `snippet.badges` | バッジ配列 (`["CC"]` 等) |
| `snippet.channelApproval` | `"Verified"` 等 |
| `snippet.thumbnails[]` / `snippet.channelThumbnails[]` | サムネ配列 `{url, width, height}` |
| `snippet.detailedMetadataSnippet[]` | 検索スニペットのハイライト `{text, bold}` |
| `snippet.chapters[]` | チャプター `{title, time, thumbnails[]}` |

サンプル (1件抜粋, `sid1ONbELIAFGNrUJ` より):

```json
{
  "kind": "youtube#searchResult",
  "id": { "kind": "youtube#video", "videoId": "MSzIYGWRXbE" },
  "snippet": {
    "channelId": "UCP6HGa63sBC7-KHtkme-p-g",
    "title": "What's all the buzz about CBD oil? | Just The FAQs",
    "channelTitle": "USA TODAY",
    "channelHandle": "@USATODAY",
    "timestamp": "7 years ago",
    "duration": 95,
    "views": 1040971,
    "badges": ["CC"],
    "channelApproval": "Verified",
    "thumbnails": [{"url": "https://i.ytimg.com/vi/MSzIYGWRXbE/hq720.jpg", "width": 360, "height": 202}],
    "detailedMetadataSnippet": [{"text": "CBD", "bold": true}, {"text": ", or "}, {"text": "cannabidiol", "bold": true}],
    "chapters": []
  }
}
```

詳細: https://console.apify.com/actors/gJvjeCYNraSfhIaNd/input の Output タブ + `https://docs.google.com/spreadsheets/d/1L_k-LZwhilb5pRnW0D6IDjlUY_VfdXANIUzyB13NqwM/edit?gid=0` 類似

## 実行方法

### 方法A — MCP経由 (推奨, `apify-mcp` 管理)

```bash
# 1. 実行 (CBXリキッド例, API課金, 5件)
# tools/call call-actor {"actor":"gJvjeCYNraSfhIaNd","input":{"search_term":"CBXリキッド","max_videos":5},"waitSecs":45}
# → { runId:"...", defaultDatasetId:"...", itemCount:5, usageTotalUsd:0.00255 }

# 2. 結果取得
# tools/call get-dataset-items {"datasetId":"<datasetId>","limit":5,"clean":true}
# → 5件 JSON (前述サンプル形式)

# 3. 課金確認
# tools/call get-actor-run {"runId":"<runId>"}
# → { usageTotalUsd: 0.00255, usageUsd: {"ACTOR_COMPUTE_UNITS": ...} }
```

本ワークスペースの `.mcp.json` `apify` はデフォルトで広く有効。`apify-hosted` (`mcp-remote https://mcp.apify.com`) でも可。

### 方法B — API直叩き (MCP不調時のフォールバック, API課金)

```bash
source .env.d/apify.env

# 1. 非同期実行 (run, waitForFinish=60で同期待ち)
curl -s -X POST "https://api.apify.com/v2/acts/gJvjeCYNraSfhIaNd/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"search_term":"CBXリキッド","max_videos":5}' | jq '{id, status, defaultDatasetId}'

# → {"id":"xxxxx","status":"SUCCEEDED","defaultDatasetId":"yyyyy"}

# 2. データセット取得 (JSON)
curl -s "https://api.apify.com/v2/datasets/yyyyy/items?clean=true&format=json&limit=5" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq '.[0] | {videoId: .id.videoId, title: .snippet.title, views: .snippet.views}'

# 3. CSVで保存
curl -s "https://api.apify.com/v2/datasets/yyyyy/items?clean=true&format=csv" \
  -H "Authorization: Bearer $APIFY_TOKEN" -o /tmp/youtube_search_CBX.csv

# 4. 課金確認
curl -s "https://api.apify.com/v2/actor-runs/xxxxx" -H "Authorization: Bearer $APIFY_TOKEN" \
  | jq '{status, usageTotalUsd, usageUsd}'
```

### 方法C — Node.js MCP stdio (VS Codeで直接MCPツールが呼べない場合)

`gmail-search` スキルと同様、MCP stdioを子プロセスで起動:

```javascript
// /tmp/youtube_search.js
const { spawn } = require('child_process');
const server = spawn('/Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx',
  ['-y','@apify/actors-mcp-server'], { stdio:['pipe','pipe','pipe'], env:{...process.env, APIFY_TOKEN: process.env.APIFY_TOKEN}});
let buf='', id=1;
function call(name, args){ server.stdin.write(JSON.stringify({jsonrpc:'2.0',id:id++,method:'tools/call',params:{name,arguments:args}})+'\n'); }
server.stdout.on('data', d=>{ buf+=d.toString(); let lines=buf.split('\n'); buf=lines.pop()||''; for(const l of lines) console.log(l); });
setTimeout(()=>call('call-actor', {actor:'gJvjeCYNraSfhIaNd', input:{search_term:'CBXリキッド', max_videos:5}, waitSecs:45}), 3000);
setTimeout(()=>process.exit(0), 25000);
```
```bash
source .env.d/apify.env && node /tmp/youtube_search.js 2>&1 | jq .
```

## 検証実績 (2026-09-01)

- Actor `gJvjeCYNraSfhIaNd` (danek/youtube-search, 1.1.20, 1.5万runs, 258 users)
- 既存 dataset `sid1ONbELIAFGNrUJ` (別ユーザ, run `i8ZEfSq0ti1d0oym6` 2026-09-01) → 2件取得成功, `CBD oil` で `USA TODAY` 等の高view動画を正常パース
- Cost (本Actor): `max_videos=5` なら FREEで `$0.00005 + 5×$0.0005 = $0.00255` (Instagramの約1/7)
- 試行 `search_term="CBXリキッド" max_videos=5` は要実費検証 (本スキル作成時は未実行, 上記は他クエリの参考値)

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `max_videos` を5-20に制限。100が上限, 1回で100件→ $0.05 (FREE) 程度。Instagramより1桁安いが、100回実行で$5消費 |
| 課金確認 | `get-actor-run` / `GET /v2/actor-runs/{runId}` の `usageTotalUsd` で都度確認。`https://console.apify.com/actors/runs` でも確認可 |
| レート | 連続実行は `waitSecs` 45秒 + 1秒間隔。YouTube側のレート制限は特になし (APIキー不要のため) |
| メモリ | 128MBでも可 (Actor推奨最小)。本ワークスペースの default 4096MB でも課金は `apify-actor-start` $0.00005 のまま (1GB刻みだが128MBは切り上げ1イベント) |

## 制約・注意

- 公開動画のみ。限定公開/非公開は対象外
- `timestamp` は相対表記 (`"3 days ago"`)。絶対日付が必要なら `yt-dlp` や YouTube Data API v3 で `videoId` から再取得
- 1実行1キーワード。複数キーワードは複数回実行 (並列可, 課金も件数倍)
- 日本語クエリ可 (`CBXリキッド` / `THCH 副作用` 等) — YouTube検索と同様にヒット
- `search_term` は YouTube検索演算子可 (`site:`, `"exact phrase"`, `-exclude` 等はYouTube側仕様に依存)

## 出力先

| 種別 | パス/URL |
|------|----------|
| MCP生JSON | `tools/call` の `content[0].text` (標準出力) |
| Dataset JSON | `https://api.apify.com/v2/datasets/{datasetId}/items?clean=true&format=json` |
| Dataset CSV | `.../items?clean=true&format=csv` |
| ローカル保存例 | `/tmp/youtube_search_{query}.json` / `/tmp/youtube_search_{query}.csv` |
| コンソール | `https://console.apify.com/actors/gJvjeCYNraSfhIaNd/runs/{runId}` |

## Instagram との比較

| 項目 | YouTube `gJvjeCYNraSfhIaNd` | Instagram `TxU0ZBQIHdR20dr9C` |
|------|---------------------------|------------------------------|
| 入力 | `search_term` + `max_videos` (件数) | `query` + `maxPages` (ページ数) |
| 単価 (FREE) | $0.0005/件 | $0.0025/件 |
| 1000件コスト | $0.50 | $2.50 |
| Login | 不要 | 不要 (cookieless) |
| 言語 | 日本語OK, 演算子可 | 日本語OKだがシャドウバンあり |
| 出力 | `videoId/title/views/duration` | `id/code/caption/ig_play_count/like_count` |

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `401 Unauthorized` / `Invalid token` | `APIFY_TOKEN` 未設定・誤り・失効 | `https://console.apify.com/settings/integrations` で再発行 → `echo 'APIFY_TOKEN=apify_api_...' > .env.d/apify.env && chmod 600 .env.d/apify.env` |
| `402 Payment required` / `Not enough usage credits` | 無料枠枯渇・支払い方法未登録 | Console → Billing で支払い方法登録。`max_videos=5` で再試行 |
| 0件 / 少ない | クエリがニッチ / YouTube検索で0件 | YouTube本家で `search_term` を手動検索して件数確認。`max_videos` を20-50に増やす |
| `timestamp` が相対表記で使いにくい | YouTube検索ページの仕様 | `videoId` を `https://api.apify.com/v2/datasets/...` で得た後, `yt-dlp --dump-json` や YouTube Data API v3 の `videos.list` で `publishedAt` を補完 |
| `Tool not found` | `.mcp.json` の `TOOLS` 制限 | `apify-hosted` (`mcp-remote https://mcp.apify.com`) を使用, またはAPI直叩き (方法B) |
| `MCP closed connection` | npxキャッシュ破損 | `rm -rf ~/.npm/_npx && /Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx -y @apify/actors-mcp-server --help` |
| Tokenがログに平文出力された | `cat .env.d/apify.env` を実行 | 直ちに `Rotate Token` (Console → Integrations → Rotate) |

## 関連

- 管理スキル: `apify-mcp` (MCP起動・認証・ツール一覧)
- 姉妹スキル: `apify-instagram-search` (`TxU0ZBQIHdR20dr9C` Instagram, $2.50/1000件) — 同様に **キーワード検索** だが YouTubeは 1/5 のコスト
- 代替: `apify/rag-web-browser` (汎用Web検索)
- 参照MCP: `serpbear` (順位取得), `ga4` / `google-search-console`
