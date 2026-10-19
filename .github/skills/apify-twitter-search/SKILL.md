---
name: apify-twitter-search
description: |
  Apify X(Twitter)検索スキル(API課金)でツイートをキーワード検索するスキル。「X検索」「Twitter調べて」「ハッシュタグ調べて」などで使う。
---

# Apify X (Twitter) 検索スキル (API課金)

`https://console.apify.com/actors/cPYLH3QT9GyzKhB4S` = `patient_discovery/twitter-search` を **API課金** で実行し、X (旧Twitter) の検索結果をキーワードで取得するスキル。ログイン不要・クッキー不要で、ツイート本文/エンゲージメント/メディア/ハッシュタグ/ユーザプロフィールを JSON/CSV で取得する。Xの高度な検索演算子にも対応。

- Actor: `cPYLH3QT9GyzKhB4S` / `patient_discovery/twitter-search` — Twitter (X.com) Search Results Scraper (No Login, Cookieless)
- 上流: https://console.apify.com/actors/cPYLH3QT9GyzKhB4S / https://apify.com/patient_discovery/twitter-search
- 課金: **PAY_PER_EVENT** — `Actor Start $0.002` + `result $0.0025/件` (FREE) → GOLD以上 `$0.0015/件`。旧 $2.50/1,000件と同額
- 認証: `.env.d/apify.env` の `APIFY_TOKEN` (https://console.apify.com/settings/integrations で発行, `chmod 600`)

## トリガー

「X 検索して」「Twitter 調べて」「ツイート検索して」「cPYLH3QT9GyzKhB4S で検索」「ApifyでX検索」「ハッシュタグ調べて」などで使う。

## 前提

- Apifyアカウントに **支払い方法登録済み** (無料 $5 付与後, 従量課金)
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在 (`apify-mcp` スキルで管理)
- netloom v0.4.3+（`/Users/bookair18/.local/bin/netloom`）または PATH 上の `netloom`
- MCPは `apify-mcp` スキル参照。API直叩きでも可（MCP不調時のフォールバック）

## 料金モデル (2025-12-21, build 1.0.7)

| イベント | 説明 | 単価 (FREE) | GOLD+ |
|---------|------|------------|-------|
| `apify-actor-start` | 起動1回あたり (1GBごとに1イベント, 最低1) | **$0.002** | $0.002 |
| `apify-default-dataset-item` | 取得1件あたり (primary) | **$0.0025** | **$0.0015** |

計算例: `maxPages=1` で20件取得 → `0.002 + 20×0.0025 = $0.052` (2026-09-01実績 `CBD` run `3hlnEK3HYK5YD39t3` dataset `AKYjQqltnyLELMyIm` 20件, 6.1秒)

> Instagram `TxU0ZBQIHdR20dr9C` と同単価 ($2.50/1,000件)。YouTube `$0.0005`/件の5倍、TikTok `$0.0004`/件の約6倍。

## Input Schema

Build `4ibfZfLdIX1UXNe1Y` (2026-03-03) 時点:

```json
{
  "title": "Twitter Search Input",
  "type": "object",
  "required": ["query"],
  "properties": {
    "query":    { "type": "string",  "description": "Search query", "default": "new york" },
    "section":  { "type": "string",  "description": "Section: top, latest, people, photos, videos", "default": "top" },
    "maxPages": { "type": "integer", "description": "Maximum number of pages to fetch (pagination handled automatically)", "default": 1, "minimum": 1, "maximum": 100 }
  }
}
```

| フィールド | 必須 | 例 | 備考 |
|-----------|------|---|------|
| `query` | ✅ | `"CBD"` / `"#AI filter:verified"` / `"from:elonmusk"` / `"CBXリキッド"` | X検索クエリ。高度な演算子可 (`from:`, `to:`, `filter:verified`, `lang:ja`, `until:`, `since:`) |
| `section` | — | `"top"` (default) / `"latest"` / `"people"` / `"photos"` / `"videos"` | 検索タブ。`top`=人気順, `latest`=新着順 |
| `maxPages` | — | `1` (default, 約20件) / `3` で60件程度 | ページ数。**課金は取得件数**で決まる (1 page ≒ 15-25 tweets) |

> YouTube `search_term` / TikTok `keyword` / Instagram `query` と同様に **1実行1キーワード**。複数キーワードは複数回実行 (並列可だが課金も件数倍)。

### クエリ例 (X高度な検索)

| 用途 | query 例 |
|------|---------|
| キーワード | `CBD` / `CBXリキッド` |
| ハッシュタグ | `#CBDoil` / `#H4CBH` |
| メンション | `@username` |
| 会話 | `from:elonmusk` / `to:username` |
| フィルタ | `CBD filter:verified` / `CBD filter:media` |
| 言語 | `CBD lang:ja` / `CBD lang:en` |
| 期間 | `CBD since:2026-08-01 until:2026-09-01` |
| 複合 | `CBX OR CBD filter:verified -filter:retweets` |

## Output Schema (主要フィールド)

全件 `type: "tweet"`, null-safe。CSV/Excel 出力も可。

| フィールド | 説明 |
|-----------|------|
| `tweet_id` / `conversation_id` | ツイートID / スレッドID (`https://x.com/{screen_name}/status/{tweet_id}`) |
| `screen_name` / `text` / `created_at` | 作者ハンドル / 本文 / 投稿日時 (`Sun Aug 23 00:48:48 +0000 2026`) |
| `favorites` / `retweets` / `replies` / `quotes` / `bookmarks` / `views` | いいね/RT/返信/引用/ブックマーク/表示回数 |
| `lang` / `source` / `sensitive` | 言語コード / 投稿クライアント / センシティブフラグ |
| `entities.hashtags[]` / `entities.user_mentions[]` / `entities.urls[]` | ハッシュタグ/メンション/URL配列 |
| `user_info.screen_name` / `user_info.name` / `user_info.followers_count` / `user_info.favorites_count` / `user_info.verified` / `user_info.description` / `user_info.avatar` / `user_info.location` | 作者プロフィール |
| `media.photo[]` / `media.video[]` | 画像 (`media_url_https`) / 動画 (`variants[].url`, `duration`, `aspect_ratio`) |
| `quoted.*` / `quoted/author.*` | 引用ツイートの同型データ (あれば) |

サンプル (1件抜粋, `AKYjQqltnyLELMyIm` より):

```json
{
  "type": "tweet",
  "tweet_id": "2091326755332091909",
  "screen_name": "DrDavidivw",
  "text": "DR. LEE MERRITT - CANCER IS REALLY PARASITES! ... FENBENDAZOLE CBD OIL ...",
  "created_at": "Sun Aug 23 00:48:48 +0000 2026",
  "favorites": 709, "retweets": 338, "replies": 12, "quotes": 8, "bookmarks": 476, "views": "20608",
  "lang": "en",
  "entities": {"hashtags": [], "user_mentions": []},
  "user_info": {"screen_name": "DrDavidivw", "name": "Dr. David", "followers_count": 35710, "verified": true, "location": "California"},
  "media": {"video": [{"media_url_https": "https://pbs.twimg.com/...", "duration": 83266, "variants": [{"url": "https://video.twimg.com/...mp4"}]}]}
}
```

完全なCSVサンプル: Actorページの Output タブ + `https://console.apify.com/view/runs/3hlnEK3HYK5YD39t3#output` で確認可

## 実行方法

### 方法A — netloom (推奨, API課金)

```bash
# 1. 実行 (CBD例, API課金, top 1page ≒20件)
R=$(netloom apify run --actor cPYLH3QT9GyzKhB4S --wait 45 \
  --input '{"query":"CBD","section":"top","maxPages":1}')
RUN_ID=$(echo "$R" | jq -r '.data.id // .id')
DS=$(echo "$R" | jq -r '.data.defaultDatasetId // .defaultDatasetId')

# 2. 結果取得
netloom apify dataset --dataset-id "$DS" --limit 20 --as json \
  | jq '.[0] | {tweet_id, screen_name, text: .text[0:80], favorites, retweets}'

# 3. 課金確認
netloom apify run-status --run-id "$RUN_ID" \
  | jq '.data | {status, usageTotalUsd, chargedEventCounts}'
```

### 方法B — netloom で既存 dataset / run を確認

```bash
source .env.d/apify.env

# 1. データセット取得 (JSON)
netloom apify dataset --dataset-id AKYjQqltnyLELMyIm --limit 20 --as json \
  | jq '.[0] | {tweet_id, screen_name, text: .text[0:80], favorites, retweets}'

# 2. CSVで保存
netloom apify dataset --dataset-id AKYjQqltnyLELMyIm --as csv --out /tmp/x_search_CBD.csv

# 3. 課金確認
netloom apify run-status --run-id 3hlnEK3HYK5YD39t3 \
  | jq '.data | {status, usageTotalUsd, chargedEventCounts}'

# 4. 高度なクエリ例 (最新順, フィルタ)
netloom apify run --actor cPYLH3QT9GyzKhB4S --wait 60 \
  --input '{"query":"CBXリキッド lang:ja filter:verified","section":"latest","maxPages":2}' | jq .
```

### 方法C — MCP は管理・検索用途のみ

Actor 実行・dataset 取得・run status は netloom を使う。MCP サーバー起動、actor 検索、docs 検索、actor details 取得は `apify-mcp` スキルを参照。

## 検証実績 (2026-09-01)

- Actor `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search, 1.0.7, 4,118 runs, 188 users)
- Input `query="CBD" section="top" maxPages=1` → 20件取得, 6.1秒, `usageTotalUsd $0.052` (`start $0.002 + 20×$0.0025`)
- Run `3hlnEK3HYK5YD39t3` / Dataset `AKYjQqltnyLELMyIm` (20 tweets, `DrDavidivw` 等, CBD/fenbendazole 関連ツイート, `views` は string型)
- 出力 `https://console.apify.com/actors/cPYLH3QT9GyzKhB4S/runs/3hlnEK3HYK5YD39t3#output` で全件確認可 (要 `APIFY_TOKEN`)

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `maxPages` を1-3に制限。`1 page ≒ 20件 → $0.052`, `5 pages ≒ 100件 → $0.252`。`maxPages=100` は最大2000件超で `$5` 超の可能性 |
| 課金確認 | `get-actor-run` / `GET /v2/actor-runs/{runId}` の `usageTotalUsd` / `chargedEventCounts` で都度確認。`https://console.apify.com/actors/runs` でも確認可 |
| 無料枠 | Apify新規は $5 無料クレジット。FREE tierは $0.0025/件, GOLD以上は $0.0015/件 (Instagram/TikTok query-level1 割増は X には無し) |
| レート | 連続実行は `waitSecs` 45秒 + 1秒間隔。X側のレート制限は cookieless のため緩いが、短時間に同一クエリを連打すると一時的に0件になる場合あり |

## 制約・注意

- 公開ツイートのみ。非公開/削除済みは取得不可。ログイン不要 (cookieless)
- 1実行1クエリ。複数キーワードは複数回実行 (並列可だが課金も件数倍)
- `section` の挙動: `top`=人気順 (エンゲージメント高), `latest`=時系列新着, `people`=ユーザ検索, `photos`/`videos`=メディア付きのみ
- `views` は **string型** で返る場合あり (`"20608"`)。数値比較時は `int()` 変換
- 日本語クエリ可 (`CBXリキッド` / `CBD オイル` 等) — ただしXでは英語と分けて検索した方がヒット率高。`lang:ja` 併用推奨
- 高度な演算子は X本家の検索構文に準拠。`OR` は大文字、`-` で除外 (`CBD -filter:retweets`)
- レート: 短時間に同一KWで連打すると X側で一時的に空結果。1秒間隔を空ける

## 出力先

| 種別 | パス/URL |
|------|----------|
| MCP生JSON | `tools/call` の `content[0].text` (標準出力) |
| Dataset JSON | `https://api.apify.com/v2/datasets/{datasetId}/items?clean=true&format=json` |
| Dataset CSV | `.../items?clean=true&format=csv` |
| ローカル保存例 | `/tmp/x_search_{query}.json` / `/tmp/x_search_{query}.csv` |
| コンソール | `https://console.apify.com/actors/cPYLH3QT9GyzKhB4S/runs/{runId}` (本件は `.../runs/3hlnEK3HYK5YD39t3#output`) |

## 他SNSとの比較

| 項目 | X `cPYLH3QT9GyzKhB4S` | Instagram `TxU0ZBQIHdR20dr9C` | YouTube `gJvjeCYNraSfhIaNd` | TikTok `jQfZ1h9FrcWcliKZX` |
|------|---------------------|------------------------------|---------------------------|--------------------------|
| 入力 | `query` + `section` + `maxPages` | `query` + `maxPages` | `search_term` + `max_videos` | `keyword` + `limit` |
| 単価 (FREE) | $0.0025/件 + $0.002/start | $0.0025/件 + $0.002/start | $0.0005/件 + $0.00005/start | $0.0004/件 + $0.00023/start |
| 1回(20件)コスト | **$0.052** | $0.052 | $0.010 | $0.008 +小クエリ割増 |
| フィルタ | `section`/`filter:`/`lang:` | なし | なし | `region`/`publishTime`/`sortType` |
| 出力 | `tweet_id/text/views/media/user_info` | `id/caption/ig_play_count` | `videoId/title/views/duration` | `aweme_id/desc/statistics` |

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `401 Unauthorized` / `Invalid token` | `APIFY_TOKEN` 未設定・誤り・失効 | `https://console.apify.com/settings/integrations` で再発行 → `echo 'APIFY_TOKEN=apify_api_...' > .env.d/apify.env && chmod 600 .env.d/apify.env` |
| `402 Payment required` / `Not enough usage credits` | 無料枠枯渇・支払い方法未登録 | Console → Billing で支払い方法登録。`maxPages=1` で再試行 |
| 0件 / 少ない | クエリがニッチ / X検索で0件 | X本家 (https://x.com/search) で `query` を手動検索して件数確認。`section` を `latest` に変更、演算子を外して再試行 |
| `views` が stringでソートできない | X APIの仕様 (string型) | `int(tweet["views"])` に変換してから比較 |
| `Tool not found` | `.mcp.json` の `TOOLS` 制限 | `apify-hosted` (`mcp-remote https://mcp.apify.com`) を使用, またはAPI直叩き (方法B) |
| Tokenがログに平文出力された | `cat .env.d/apify.env` を実行 | 直ちに `Rotate Token` (Console → Integrations → Rotate) |
| `section=people` でツイートが取れない | peopleはユーザ検索 (ツイートではない) | `section=top` または `latest` に戻す。ユーザ検索は別 Actor `twitter-search-users` を使用 |

## 関連

- 管理スキル: `apify-mcp` (MCP起動・認証・ツール一覧) — 本スキルは `cPYLH3QT9GyzKhB4S` 専用のAPI課金実行スキル
- 姉妹: `apify-instagram-search` (`TxU0ZBQIHdR20dr9C` $2.50/1k) / `apify-youtube-search` (`gJvjeCYNraSfhIaNd` $0.50/1k) / `apify-tiktok-search` (`jQfZ1h9FrcWcliKZX` $0.40/1k + 小クエリ割増) — Xは Instagram と同額
- 代替: `apify/rag-web-browser` (汎用Web検索)
- 参照MCP: `serpbear` (順位取得), `ga4` / `google-search-console`
