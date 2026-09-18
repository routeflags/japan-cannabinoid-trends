---
name: apify-instagram-search
description: |
  Apify Instagram 検索スキル(API課金)でReelsをキーワード検索するスキル。「Instagram検索」「リール調べて」「CBXリキッド」などで使う。
---

# Apify Instagram 検索スキル (API課金)

`https://console.apify.com/actors/TxU0ZBQIHdR20dr9C` = `patient_discovery/instagram-search-reels` を **API課金** で実行し、Instagram Reels をキーワード検索するスキル。ログイン不要・クッキー不要で、プレイ数/いいね/コメント/共有/音声/ハッシュタグ等の構造化データを JSON/CSV で取得する。

- Actor: `TxU0ZBQIHdR20dr9C` / `patient_discovery/instagram-search-reels` — Instagram Reels Keyword Scraper (No Login, No Cookie)
- 上流: https://console.apify.com/actors/TxU0ZBQIHdR20dr9C / https://apify.com/patient_discovery/instagram-search-reels
- 課金: **PAY_PER_EVENT** — `Actor Start $0.002` + `result $0.0025/件` (FREE) → GOLD以上 `$0.0015/件`。Apify無料枠の残高から差引、超過はクレカ請求
- 認証: `.env.d/apify.env` の `APIFY_TOKEN` (https://console.apify.com/settings/integrations で発行, `chmod 600`)

## トリガー

「Instagram 検索して」「リール調べて」「CBXリキッド のReels見て」「TxU0ZBQIHdR20dr9C で検索」「Apifyでインスタ検索」などで使う。

## 前提

- Apifyアカウントに **支払い方法登録済み** (無料 $5 付与後、従量課金)
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在 (`apify-mcp` スキルで管理)
- Node.js v18+ (本環境 v24.13.1) または Python + `curl`
- MCPは `apify-mcp` スキル参照。API直叩きでも可（MCP不調時のフォールバック）

## 料金モデル (2026-09-01確認, build 1.0.14)

| イベント | 説明 | 単価 (FREE) | GOLD+ |
|---------|------|------------|-------|
| `apify-actor-start` | 起動1回あたり (1GBごとに1イベント, 最低1) | **$0.002** | $0.002 |
| `apify-default-dataset-item` | 取得1件あたり (primary) | **$0.0025** | **$0.0015** |

計算例: `maxPages=1` で6件取得 → `0.002 + 6×0.0025 = $0.017` (2026-09-01実績 `CBXリキッド` run `whiuCNcuRxmDVWjLF` dataset `gN4fgq80j5H58dA8C`)

> 表示は $2.50/1,000件。これは `1000×0.0025` と一致。

## Input Schema

Build `CSX02NO8ZROJ67jQO` (2026-08-20) 時点:

```json
{
  "title": "Instagram Search Reels Input",
  "type": "object",
  "required": ["query"],
  "properties": {
    "query":    { "type": "string",  "description": "Search term or keyword", "default": "trending" },
    "maxPages": { "type": "integer", "description": "Maximum number of pages to fetch (pagination handled automatically)", "default": 1, "minimum": 1, "maximum": 100 }
  }
}
```

| フィールド | 必須 | 例 |
|-----------|------|---|
| `query` | ✅ | `"CBXリキッド"` / `"skincare"` / `"trending"` |
| `maxPages` | — | `1` (デフォルト1, 費用はページ数ではなく取得件数で決まる) |

## Output Schema (主要フィールド)

全件 JSON, null-safe。CSV/Excel 出力も可。

| フィールド | 説明 |
|-----------|------|
| `id` / `code` | Reel ID / ショートコード (`https://instagram.com/reel/{code}`) |
| `caption.text` | キャプション全文 (hashtag/mention含む) |
| `caption.hashtags` / `caption.mentions` | ハッシュタグ / メンション配列 |
| `user.username` / `user.full_name` / `user.is_verified` / `user.profile_pic_url` | 投稿者情報 |
| `ig_play_count` / `like_count` / `comment_count` / `share_count` | 再生/いいね/コメント/共有数 |
| `video_url` / `thumbnail_url` / `video_duration` | 動画直リンク / サムネ / 秒数 |
| `taken_at` / `taken_at_date` | Unix timestamp / ISO8601 |
| `clips_metadata.audio_type` / `clips_metadata.original_sound_info.audio_id` / `original_audio_title` | 音声種別 / 音声ID / タイトル |
| `has_audio` / `is_video` | フラグ |

サンプル (1件抜粋):

```json
{
  "id": "3575393669538547061", "code": "DGeWZllBoV1",
  "caption": { "text": "For more tips... #instagrammarketingtips", "hashtags": ["#instagrammarketingtips"], "mentions": ["@iamishachopra"] },
  "user": { "username": "iamishachopra", "full_name": "Isha Chopra: Social Media Marketer", "is_verified": true },
  "ig_play_count": 7169443, "like_count": 39008, "comment_count": 284, "share_count": 95428,
  "video_duration": 24.3, "taken_at_date": "2025-02-24T23:37:12+00:00",
  "clips_metadata": { "audio_type": "original_sounds", "original_sound_info": { "audio_id": 939635911650210, "original_audio_title": "Original audio" } }
}
```

完全なCSVサンプル: https://docs.google.com/spreadsheets/d/1L_k-LZwhilb5pRnW0D6IDjlUY_VfdXANIUzyB13NqwM/edit?gid=0#gid=0

## 実行方法

### 方法A — MCP経由 (推奨, `apify-mcp` 管理)

```bash
# 1. Actor詳細確認 (inputSchema)
# tools/call fetch-actor-details {"actor":"TxU0ZBQIHdR20dr9C"}  # 本Actorは apify-mcp の TOOLS 制限で未公開のため、API直叩きか wide MCP (https://mcp.apify.com) を使用

# 2. 実行 (CBXリキッド例, API課金)
# tools/call call-actor {"actor":"TxU0ZBQIHdR20dr9C","input":{"query":"CBXリキッド","maxPages":1},"waitSecs":45}
# → { runId:"whiuCNcuRxmDVWjLF", defaultDatasetId:"gN4fgq80j5H58dA8C", itemCount:6, usageTotalUsd:0.017 }

# 3. 結果取得
# tools/call get-dataset-items {"datasetId":"gN4fgq80j5H58dA8C","limit":6,"clean":true}
# → 6件 JSON (前述サンプル形式)
```

本ワークスペースの `.mcp.json` `apify` は `TOOLS` 制限で `fetch-actor-details` が無効な場合、`apify-hosted` (`mcp-remote https://mcp.apify.com`) か `https://mcp.apify.com?tools=search-actors,fetch-actor-details` で wide MCP を使う。または方法BのAPI直叩き。

### 方法B — API直叩き (MCP不調時のフォールバック, API課金)

```bash
source .env.d/apify.env

# 1. 非同期実行 (run)
curl -s -X POST "https://api.apify.com/v2/acts/TxU0ZBQIHdR20dr9C/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBXリキッド","maxPages":1}' | jq '{id, status, defaultDatasetId}'

# → {"id":"whiuCNcuRxmDVWjLF","status":"SUCCEEDED","defaultDatasetId":"gN4fgq80j5H58dA8C"}

# 2. データセット取得
curl -s "https://api.apify.com/v2/datasets/gN4fgq80j5H58dA8C/items?clean=true&format=json&limit=6" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq '.[0] | {code, caption: .caption.text, ig_play_count, like_count}'

# 3. 課金確認
curl -s "https://api.apify.com/v2/actor-runs/whiuCNcuRxmDVWjLF" -H "Authorization: Bearer $APIFY_TOKEN" \
  | jq '{status, usageTotalUsd, usageUsd}'

# CSVで保存
curl -s "https://api.apify.com/v2/datasets/gN4fgq80j5H58dA8C/items?clean=true&format=csv" \
  -H "Authorization: Bearer $APIFY_TOKEN" -o /tmp/instagram_reels_CBX.csv
```

### 方法C — Node.js MCP stdio (VS Codeで直接MCPツールが呼べない場合)

`gmail-search` スキルと同様、MCP stdioを子プロセスで起動:

```javascript
// /tmp/instagram_search.js
const { spawn } = require('child_process');
const server = spawn('/Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx',
  ['-y','@apify/actors-mcp-server'], { stdio:['pipe','pipe','pipe'], env:{...process.env, APIFY_TOKEN: process.env.APIFY_TOKEN}});
let buf='', id=1;
function call(name, args){ server.stdin.write(JSON.stringify({jsonrpc:'2.0',id:id++,method:'tools/call',params:{name,arguments:args}})+'\n'); }
server.stdout.on('data', d=>{ buf+=d.toString(); let lines=buf.split('\n'); buf=lines.pop()||''; for(const l of lines) console.log(l); });
setTimeout(()=>call('call-actor', {actor:'TxU0ZBQIHdR20dr9C', input:{query:'CBXリキッド', maxPages:1}, waitSecs:45}), 3000);
setTimeout(()=>process.exit(0), 25000);
```
```bash
source .env.d/apify.env && node /tmp/instagram_search.js 2>&1 | jq .
```

## 検証実績 (2026-09-01)

- Actor `TxU0ZBQIHdR20dr9C` (patient_discovery/instagram-search-reels, 1.0.14, 13.7万runs, 2,618 users, ★4.75/4件)
- Input `query="CBXリキッド"` `maxPages=1` → 6件全取得, 全て `CBX400F` バイク関連 (リキッド該当0件, Instagram規制/shadowbanでリキッド系はヒットしない)
- Cost: `apify-actor-start $0.002 + 6×$0.0025 = $0.017` (FREE tier)
- Run `whiuCNcuRxmDVWjLF` / Dataset `gN4fgq80j5H58dA8C` / 保存先 `/tmp/cbx_dataset.json`

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `maxPages` を1-3に制限, 1実行あたりの想定件数を確認してから `maxPages` を上げる。`maxPages=100` は100ページ分ではなく100×ページサイズ件数になるため高額注意 |
| 課金確認 | `get-actor-run` / `GET /v2/actor-runs/{runId}` の `usageTotalUsd` で都度確認。`https://console.apify.com/actors/runs` でも確認可 |
| 無料枠 | Apify新規は $5 無料クレジット。FREE tierは $0.0025/件, BRONZE以降は $0.00217→$0.0015 と逓減 |
| 中断 | 実行中に `POST /v2/actor-runs/{runId}/abort` で中断可だが起動料 $0.002 は請求 |

## 制約・注意

- 公開Reelsのみ。非公開アカウントは取得不可。ログイン不要 (cookieless)
- 1実行1キーワード。複数キーワードは複数回実行 (並列可だが課金も倍)
- Instagram規制: `CBXリキッド` 等のセンシティブ商材はシャドウバンで一般語 (`CBX400F`) に引っ張られる。`apify/rag-web-browser` でのWeb検索を併用推奨
- レート: 連続実行は `waitSecs` 45秒 + 1秒間隔を空ける。大量取得時は `maxPages` を分割

## 出力先

| 種別 | パス/URL |
|------|----------|
| MCP生JSON | `tools/call` の `content[0].text` (標準出力) |
| Dataset JSON | `https://api.apify.com/v2/datasets/{datasetId}/items?clean=true&format=json` |
| Dataset CSV | `.../items?clean=true&format=csv` |
| ローカル保存例 | `/tmp/cbx_dataset.json` / `/tmp/instagram_reels_{query}.csv` |
| コンソール | `https://console.apify.com/actors/TxU0ZBQIHdR20dr9C/runs/{runId}` |

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `401 Unauthorized` / `Invalid token` | `APIFY_TOKEN` 未設定・誤り・失効 | `https://console.apify.com/settings/integrations` で再発行 → `echo 'APIFY_TOKEN=apify_api_...' > .env.d/apify.env && chmod 600 .env.d/apify.env` + `cat .env.d/apify.env` がログに残ったら即Rotate |
| `402 Payment required` / `Not enough usage credits` | 無料枠枯渇・支払い方法未登録 | Console → Billing で支払い方法登録 or プランUP。`apify-default-dataset-item` の単価を確認 |
| `CBXリキッド`で6件中0件が本命 | Instagram規制・キーワード曖昧 | `query: "CBX リキッド"` `maxPages:3` で再試行, ダメなら `apify/rag-web-browser` でWeb検索に切替 |
| `fetch-actor-details` が `Tool not found` | `.mcp.json` の `apify` が `TOOLS` 制限 | `apify-hosted` (`mcp-remote https://mcp.apify.com`) を使用, またはAPI直叩き (方法B) |
| `MCP closed connection` / `mcp-remote not found` | npxキャッシュ破損 | `rm -rf ~/.npm/_npx && /Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx -y @apify/actors-mcp-server --help` |
| Tokenがログに平文出力された | `cat .env.d/apify.env` を実行 | 直ちに `Rotate Token` (Console → Integrations → Rotate) |
| `maxPages=100` で想定外の高額請求 | `maxPages` はページ数、上限100で大量件数 | 事前に `maxPages=1` で件数確認, 必要件数から逆算して `maxPages` 設定 |

## 関連

- 管理スキル: `apify-mcp` (MCP起動・認証・ツール一覧) — 本スキルは `TxU0ZBQIHdR20dr9C` 専用のAPI課金実行スキル
- 代替: `apify/rag-web-browser` (Web検索, 規制回避用)
- 参照MCP: `serpbear` (順位取得), `ga4` / `google-search-console`

