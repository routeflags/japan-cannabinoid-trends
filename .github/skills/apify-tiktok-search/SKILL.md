---
name: apify-tiktok-search
description: |
  Apify TikTok 検索スキル(API課金)で動画をキーワード検索するスキル。「TikTok検索」「バズってるTikTok」などで使う。
---

# Apify TikTok 検索スキル (API課金)

`https://console.apify.com/actors/jQfZ1h9FrcWcliKZX` = `novi/tiktok-search-api` を **API課金** で実行し、TikTok 動画をキーワードで検索するスキル。透かし無し動画URL/音楽/作者/エンゲージメント等の構造化データを JSON で取得する。

- Actor: `jQfZ1h9FrcWcliKZX` / `novi/tiktok-search-api` — TikTok Search Scraper (Unofficial API, free-watermark, 128MBで100件/30秒)
- 上流: https://console.apify.com/actors/jQfZ1h9FrcWcliKZX / https://apify.com/novi/tiktok-search-api
- 課金: **PAY_PER_EVENT** — `start $0.00023` + `result-item $0.0004/件` + `query-level1 (<30件時) $0.0025` (FREE) → GOLD以上 `result $0.0003` / `query $0.002`
- 認証: `.env.d/apify.env` の `APIFY_TOKEN` (https://console.apify.com/settings/integrations で発行, `chmod 600`)

## トリガー

「TikTok 検索して」「TikTok 調べて」「バズってるTikTok見て」「jQfZ1h9FrcWcliKZX で検索」「ApifyでTikTok検索」などで使う。

## 前提

- Apifyアカウントに **支払い方法登録済み** (無料 $5 付与後, 従量課金)
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在 (`apify-mcp` スキルで管理)
- Node.js v18+ (本環境 v24.13.1) または Python + `curl`
- MCPは `apify-mcp` スキル参照。API直叩きでも可（MCP不調時のフォールバック）

## 料金モデル (2026-08-29改定, build 0.5.35)

| イベント | 説明 | 単価 (FREE) | GOLD+ |
|---------|------|------------|-------|
| `start` (apify-actor-start) | 起動1回あたり (1GBごとに1イベント, 最小1。2048MBでも2イベント) | **$0.00023** | $0.0002 |
| `result-item` | 取得1件あたり (primary) | **$0.0004** | **$0.0003** |
| `query-level1` | 検索結果が **30件未満** のクエリに追加課金 (疎なキーワードのペナルティ) | **$0.0025** | $0.002 |

計算例:
- 100件取得 → `0.00046 (2GB start) + 100×0.0004 = $0.04046` (FREE)
- 10件取得 (30件未満) → `0.00046 + 10×0.0004 + 0.0025 = $0.00696` (小クエリは割高)
- 旧定額 $35/月プランは `FLAT_PRICE_PER_MONTH` として残存だが現行は従量課金がデフォルト

> 比較: Instagram `TxU0ZBQIHdR20dr9C` $0.0025/件、YouTube `gJvjeCYNraSfhIaNd` $0.0005/件、TikTokは **$0.0004/件** で最安クラス (1000件で $0.40)。

## Input Schema

Build `EmBKwxaWuxZ3SgTb6` (2026-09-01) 時点:

```json
{
  "title": "TikTok Search API input",
  "type": "object",
  "properties": {
    "keyword":      { "type": "string",  "description": "Keyword, can contain space. Ex: viral", "default": "viral" },
    "sortType":     { "type": "integer", "description": "Sort Type. 0: Relevance. 1: Most liked. 2: Most recent", "minimum": 0, "maximum": 2, "prefill": 0 },
    "publishTime":  { "type": "string",  "enum": ["ALL_TIME","YESTERDAY","WEEK","MONTH","THREE_MONTH","SIX_MONTH"], "prefill": "ALL_TIME" },
    "region":       { "type": "string",  "description": "Country target (2-char code)", "default": "GB", "enum": ["","GB","JP","US","...240件"] },
    "limit":        { "type": "integer", "description": "Number of videos to scrape", "minimum": 1, "maximum": 10000, "prefill": 20, "default": 1 }
  }
}
```

| フィールド | 必須 | 例 | 備考 |
|-----------|------|---|------|
| `keyword` | 推奨 | `"CBXリキッド"` / `"viral"` / `"skincare"` | スペース可。空でも可だが結果はランダム |
| `limit` | 推奨 | `20` (1-10000) | 取得上限。**課金は件数比例** + 30件未満は `query-level1` 追加 |
| `sortType` | — | `0` Relevance / `1` Most liked / `2` Most recent | デフォ `0` |
| `publishTime` | — | `"ALL_TIME"` / `"WEEK"` / `"MONTH"` | デフォ `ALL_TIME`。新着を絞るなら `WEEK` |
| `region` | — | `"JP"` / `"US"` / `"GB"` (デフォ) / `""` (None) | 240カ国。日本向けは `JP` 推奨。`GB` は英国 |

> `limit` は **件数**。YouTube `max_videos` と同義。Instagram `maxPages` はページ数ではない点に注意。

## Output Schema (主要フィールド)

1件は `aweme_info` (動画) + `author` + `added_sound_music_info` のネスト。全件 JSON, null-safe。

| フィールド | 説明 |
|-----------|------|
| `aweme_info.aweme_id` / `aweme_info.desc` | 動画ID (`https://tiktok.com/@{unique_id}/video/{aweme_id}`) / キャプション |
| `aweme_info.statistics.*` | `digg_count` (いいね) / `comment_count` / `share_count` / `play_count` / `collect_count` |
| `aweme_info.video.*` / `aweme_info.downloadAddr` | 動画URL (透かし無し) / `cover` / `duration` / `width/height` |
| `author.unique_id` / `author.nickname` / `author.sec_uid` / `author.signature` | 作者ID / 表示名 / 内部UID / 自己紹介 |
| `author.follower_count` / `following_count` / `avatar_medium.url_list[]` | フォロワー等のプロフィール。`author` は詳細版 |
| `added_sound_music_info.title` / `author` / `play_url.url_list[]` / `duration` | BGM情報。`is_original_sound` でオリジナル判定 |
| `aweme_info.createTime` / `aweme_info.create_time` | Unix timestamp (秒) |

> 旧版では `isDownloadVideoCover` / `isDownloadVideo` が存在したが build 0.5.35 では **削除**。カバー/動画URLは常に `url_list` で取得可能。

サンプル (1件抜粋, `ny4ftVfzqoWfqxMe2` より):

```json
{
  "aweme_info": {
    "aweme_id": "7493907421532310289",
    "desc": "オリジナル楽曲 - dinh huy",
    "createTime": 1744811290,
    "statistics": { "digg_count": 1234, "comment_count": 56, "share_count": 78, "play_count": 98765 },
    "video": { "downloadAddr": "https://.../video.mp4", "cover": "https://...", "duration": 15 },
    "music": { "title": "original sound - vtvgiaitriofficial", "author": "VTV Giai Tri" }
  },
  "author": {
    "unique_id": "vtvgiaitriofficial",
    "nickname": "VTV Giai Tri Official",
    "follower_count": 123456,
    "signature": "..."
  },
  "added_sound_music_info": {
    "title": "original sound - vtvgiaitriofficial",
    "author": "VTV Giai Tri Official",
    "duration": 15,
    "play_url": { "url_list": ["https://sf16-ies-music-sg.tiktokcdn.com/...mp3"] }
  }
}
```

実際は `ny4ftVfzqoWfqxMe2` の生JSONは上記より深いネスト（`avatar_medium.url_list[]` 等に複数CDN URL）。CSV/Excel 出力も可。

## 実行方法

### 方法A — MCP経由 (推奨, `apify-mcp` 管理)

```bash
# 1. 実行 (CBXリキッド例, JP, 最新順, 20件)
# tools/call call-actor {"actor":"jQfZ1h9FrcWcliKZX","input":{"keyword":"CBXリキッド","limit":20,"sortType":0,"publishTime":"ALL_TIME","region":"JP"},"waitSecs":45}
# → { runId:"c4OjvVx4G8M3QNyT9", defaultDatasetId:"ny4ftVfzqoWfqxMe2", itemCount:20, usageTotalUsd:0.008 }

# 2. 結果取得
# tools/call get-dataset-items {"datasetId":"ny4ftVfzqoWfqxMe2","limit":20,"clean":true}

# 3. 課金確認
# tools/call get-actor-run {"runId":"c4OjvVx4G8M3QNyT9"}
# → { usageTotalUsd: 0.00846, usageUsd: {"result-item": ..., "start": ...} }
```

### 方法B — API直叩き (MCP不調時のフォールバック, API課金)

```bash
source .env.d/apify.env

# 1. 実行 (日本, 20件)
curl -s -X POST "https://api.apify.com/v2/acts/jQfZ1h9FrcWcliKZX/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"keyword":"CBXリキッド","limit":20,"sortType":0,"publishTime":"ALL_TIME","region":"JP"}' \
  | jq '{id, status, defaultDatasetId}'

# → {"id":"xxxxx","status":"SUCCEEDED","defaultDatasetId":"yyyyy"}

# 2. データセット取得 (JSON)
curl -s "https://api.apify.com/v2/datasets/yyyyy/items?clean=true&format=json&limit=20" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq '.[0] | {aweme_id: .aweme_info.aweme_id, desc: .aweme_info.desc, author: .author.unique_id}'

# 3. CSVで保存
curl -s "https://api.apify.com/v2/datasets/yyyyy/items?clean=true&format=csv" \
  -H "Authorization: Bearer $APIFY_TOKEN" -o /tmp/tiktok_search_CBX.csv

# 4. 課金確認
curl -s "https://api.apify.com/v2/actor-runs/xxxxx" -H "Authorization: Bearer $APIFY_TOKEN" \
  | jq '{status, usageTotalUsd, usageUsd}'

# 5. フィルタ例 (直近1週間, 人気順, US)
curl -s -X POST "https://api.apify.com/v2/acts/jQfZ1h9FrcWcliKZX/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"keyword":"skincare","limit":50,"sortType":1,"publishTime":"WEEK","region":"US"}' | jq .
```

### 方法C — Node.js MCP stdio (VS Codeで直接MCPツールが呼べない場合)

```javascript
// /tmp/tiktok_search.js
const { spawn } = require('child_process');
const server = spawn('/Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx',
  ['-y','@apify/actors-mcp-server'], { stdio:['pipe','pipe','pipe'], env:{...process.env, APIFY_TOKEN: process.env.APIFY_TOKEN}});
let buf='', id=1;
function call(name, args){ server.stdin.write(JSON.stringify({jsonrpc:'2.0',id:id++,method:'tools/call',params:{name,arguments:args}})+'\n'); }
server.stdout.on('data', d=>{ buf+=d.toString(); let lines=buf.split('\n'); buf=lines.pop()||''; for(const l of lines) console.log(l); });
setTimeout(()=>call('call-actor', {actor:'jQfZ1h9FrcWcliKZX', input:{keyword:'CBXリキッド', limit:20, region:'JP'}, waitSecs:45}), 3000);
setTimeout(()=>process.exit(0), 25000);
```
```bash
source .env.d/apify.env && node /tmp/tiktok_search.js 2>&1 | jq .
```

## 検証実績 (2026-09-01)

- Actor `jQfZ1h9FrcWcliKZX` (novi/tiktok-search-api, 0.5.35, 72万runs, 522 users, ★5.0/2件)
- 既存 dataset `ny4ftVfzqoWfqxMe2` (run `c4OjvVx4G8M3QNyT9` 2026-09-01) → 取得成功, `usageTotalUsd 0.01383` (約34件相当) — 日本クエリでも正常パース
- 本スキル作成時は未実行 (参考値は他クエリ)。`limit=20` なら FREEで `0.00046 + 20×0.0004 = $0.00846` (30件未満なら +$0.0025)

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `limit` を20-50に制限。`10000` が上限だが 1000件→ $0.40 + start $0.00046。大量取得は `limit` を分割 |
| 小クエリ割高回避 | 結果が30件未満で `query-level1 $0.0025` が追加。ニッチKWで10件しか無い場合は `0.0025` が支配的 → 広めのKW (`cannabis` より `weed`) で試す |
| 課金確認 | `get-actor-run` / `GET /v2/actor-runs/{runId}` の `usageTotalUsd` で都度確認。`usageUsd` に `result-item` / `query-level1` が分けて表示 |
| レート | 連続実行は `waitSecs` 45秒 + 1秒間隔。TikTok側のレート制限は特になし (非公式API) |
| メモリ | 2048MBデフォでも課金は `start` $0.00023×2GB=$0.00046。128MBに下げても $0.00023 だが速度低下 |

## 制約・注意

- 非公開/削除済み動画は取得不可。地域制限あり (`region` でフィルタ)
- 透かし無しURL (`downloadAddr` / `play_url`) は TikTok CDN の一時URL ( `x-expires` 付き, 数時間で失効)。保存時は即時DL
- 1実行1キーワード。複数キーワードは複数回実行 (並列可だが課金も件数倍)
- 日本語クエリ可 (`CBXリキッド` / `CBD オイル` 等) — TikTok検索と同様にヒットするが、ニッチだと30件未満で `query-level1` 割増
- `region=""` は国フィルタ無し。日本向け分析では `JP` を明示
- レート: 短時間に同一KWで連打すると TikTok側で一時BANの可能性。1秒間隔を空ける

## 出力先

| 種別 | パス/URL |
|------|----------|
| MCP生JSON | `tools/call` の `content[0].text` (標準出力) |
| Dataset JSON | `https://api.apify.com/v2/datasets/{datasetId}/items?clean=true&format=json` |
| Dataset CSV | `.../items?clean=true&format=csv` |
| ローカル保存例 | `/tmp/tiktok_search_{keyword}.json` / `/tmp/tiktok_search_{keyword}.csv` |
| コンソール | `https://console.apify.com/actors/jQfZ1h9FrcWcliKZX/runs/{runId}` |

## 他SNSとの比較

| 項目 | TikTok `jQfZ1h9FrcWcliKZX` | YouTube `gJvjeCYNraSfhIaNd` | Instagram `TxU0ZBQIHdR20dr9C` |
|------|--------------------------|---------------------------|------------------------------|
| 入力 | `keyword` + `limit` (件数) | `search_term` + `max_videos` (件数) | `query` + `maxPages` (ページ数) |
| 単価 (FREE) | $0.0004/件 + $0.0025/小クエリ | $0.0005/件 | $0.0025/件 |
| 1000件コスト | $0.40 (+小クエリ時$2.50) | $0.50 | $2.50 |
| フィルタ | `region` / `publishTime` / `sortType` | なし | なし |
| 透かし | 無しURL取得可 | N/A | N/A |
| 出力 | `aweme_info/author/music` | `videoId/title/views` | `id/caption/ig_play_count` |

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `401 Unauthorized` / `Invalid token` | `APIFY_TOKEN` 未設定・誤り・失効 | `https://console.apify.com/settings/integrations` で再発行 → `echo 'APIFY_TOKEN=apify_api_...' > .env.d/apify.env && chmod 600 .env.d/apify.env` |
| `402 Payment required` | 無料枠枯渇・支払い方法未登録 | Console → Billing で支払い方法登録。`limit=20` で再試行 |
| 0件 / 少ない (かつ `query-level1` 課金) | ニッチKWで30件未満 | 広めのKWで再試行 (`CBX` → `cannabis` / `CBD`)。`publishTime=ALL_TIME` `region=""` で緩和 |
| `region` で0件 | 国フィルタが強すぎ | `region=""` で全世界に。日本向けなら `JP` + `limit 50` で再試行 |
| `limit=10000` で高額請求 | 上限10000で大量件数 | 事前に `limit=20` で件数確認, 必要件数から逆算 |
| `downloadAddr` が 403/期限切れ | CDN URLの `x-expires` 失効 | 取得後すぐに `curl -o video.mp4 "$downloadAddr"` でDL。失効後は再実行 |
| `Tool not found` | `.mcp.json` の `TOOLS` 制限 | `apify-hosted` (`mcp-remote https://mcp.apify.com`) を使用, またはAPI直叩き |
| Tokenがログに平文出力された | `cat .env.d/apify.env` を実行 | 直ちに `Rotate Token` (Console → Integrations → Rotate) |

## 関連

- 管理スキル: `apify-mcp` (MCP起動・認証・ツール一覧)
- 姉妹スキル: `apify-instagram-search` (`TxU0ZBQIHdR20dr9C` Instagram, $2.50/1000件) / `apify-youtube-search` (`gJvjeCYNraSfhIaNd` YouTube, $0.50/1000件) — TikTokは最安クラス
- 代替: `apify/rag-web-browser` (汎用Web検索)
- 参照MCP: `serpbear` (順位取得), `ga4` / `google-search-console`
