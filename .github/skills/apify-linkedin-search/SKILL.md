---
name: apify-linkedin-search
description: |
  Apify LinkedIn検索スキル(API課金)でプロフィールをキーワード検索するスキル。「LinkedIn検索」「リンクドイン調べて」「LinkedIn スクレイピング」などで使う。
---

# Apify LinkedIn 検索スキル (API課金)

`https://console.apify.com/actors/M2FMdjRVeF1HPGFcc` = `harvestapi/linkedin-profile-search` を **API課金** で実行し、LinkedIn プロフィールをキーワードで検索するスキル。Cookies不要・ログイン不要で、プロフィールURL/経歴/学歴/所在地/フォロワー/スキル/推薦等の構造化データを JSON/CSV で取得する。

- Actor: `M2FMdjRVeF1HPGFcc` / `harvestapi/linkedin-profile-search` — LinkedIn Profile Search Scraper No Cookies ✅ Find all people 📧
- 上流: https://console.apify.com/actors/M2FMdjRVeF1HPGFcc / https://apify.com/harvestapi/linkedin-profile-search
- 課金: **PAY_PER_EVENT** — `search-page $0.10/ページ(25件)` + `full-profile $0.004/件` / `full+email $0.01/件` + `minimal $0.10` (FREE〜DIAMOND共通, 現行 build 0.0.265)
- 認証: `.env.d/apify.env` の `APIFY_TOKEN` (https://console.apify.com/settings/integrations で発行, `chmod 600`)

## トリガー

「LinkedIn 検索して」「リンクドイン調べて」「LinkedIn スクレイピング」「M2FMdjRVeF1HPGFcc で検索」「ApifyでLinkedIn検索」などで使う。

## 前提

- Apifyアカウントに **支払い方法登録済み** (無料 $5 付与後, 従量課金, minimal $0.10)
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在 (`apify-mcp` スキルで管理)
- netloom v0.4.3+（`/Users/bookair18/.local/bin/netloom`）または PATH 上の `netloom`
- MCPは `apify-mcp` スキル参照。API直叩きでも可（MCP不調時のフォールバック）

## 料金モデル (2026-09-03, build 0.0.265, run jPYfwI1hwOG2phE75 実績)

| イベント | 説明 | 単価 (FREE) | GOLD+ |
|---------|------|------------|-------|
| `search-page` | 検索1ページあたり (最大25 short profiles) | **$0.10** | $0.05 (GOLD+) |
| `full-profile` | 詳細プロフィール1件あたり (Full モード) | **$0.004** | $0.004 |
| `full-profile-with-email` | 詳細+メール探索1件あたり | **$0.01** | $0.01 |
| `minimal` | 最低課金 | **$0.10** | $0.10 |

計算例: `searchQuery="weed" profileScraperMode=Full maxItems=20` 1ページ20件取得 → `0.10 + 20×0.004 = $0.18` (実績 `jPYfwI1hwOG2phE75` 20.5秒, `bRGOoafmRLKx0ZilP`)

> Instagram `TxU0ZBQIHdR20dr9C` $0.0025/件、YouTube $0.0005/件、TikTok $0.0004/件、X $0.0025/件に対し、LinkedInは **ページ課金 + プロフィール課金** の2段階。Shortは $4/1k、Full+emailは $10/1k。
> 25件/ページで Full なら `$0.10 + 25×0.004 = $0.20/ページ = $8/1k` 相当。

## Input Schema

Build `rN8UwvEPlEHaGsjFK` (0.0.265, 2026-08-24) 時点:

```json
{
  "title": "Search LinkedIn Profiles",
  "type": "object",
  "properties": {
    "searchQuery": { "type": "string", "description": "Query to search LinkedIn profiles (fuzzy search, operators可)", "maxLength": 300 },
    "profileScraperMode": { "type": "string", "enum": ["Short","Full","Full + email search"], "default": "Full" },
    "maxItems": { "type": "integer", "description": "Maximum number of profiles to scrape (50で課金 $0.30)", "prefill": 20 },
    "locations": { "type": "array", "items": {"type":"string"}, "description": "例: San Francisco / United Kingdom (UKはUkraineに誤爆するため正式名推奨)", "maxItems": 70 },
    "currentCompanies": { "type": "array", "items": {"type":"string"}, "description": "Full LinkedIn URLs", "maxItems": 50 },
    "currentJobTitles": { "type": "array", "items": {"type":"string"}, "maxItems": 50 }
  }
}
```

| フィールド | 必須 | 例 | 備考 |
|-----------|------|---|------|
| `searchQuery` | 推奨 | `"weed"` / `"Founder"` / `"Marketing Manager"` / `"John Doe"` | LinkedIn fuzzy search。`https://www.linkedin.com/help/linkedin/answer/a524335` の演算子可 |
| `profileScraperMode` | — | `"Full"` (default) / `"Short"` / `"Full + email search"` | Short はページのみ $0.10、Full は +$0.004/件、email は +$0.01/件 |
| `maxItems` | — | `20` (本run) / `100` で $0.50 (`0.10×4 + 100×0.004`) | 上限なしだが課金は件数比例。1000件 Full → $4.10 |
| `locations` | — | `["San Francisco"]` / `["United Kingdom"]` | LinkedIn autocompleteの先頭候補が適用される。`UK→Ukraine` 誤爆注意 |
| `currentCompanies` | — | `["https://www.linkedin.com/company/california-grown-hemp/"]` | 現職企業URLで絞り込み |
| `currentJobTitles` / `pastJobTitles` / `schools` / `seniorityLevelIds` / `industryIds` / `functionIds` | — | `["Software Engineer"]` / `["120"]` Senior / `["4"]` Software | 詳細フィルタは30+項目。`include` と `exclude*` の両方あり |
| `startPage` / `takePages` | — | `1` / `2` で50件 | ページング。1ページ25件 |
| `autoQuerySegmentation` | — | `false` (本run) / `true` で broad query を国/州/役職で自動分割 | 大量取得時に LinkedIn 上限回避 |

> `searchQuery` は YouTube `search_term` / TikTok `keyword` / X `query` と同様に **1実行1キーワード**。複数キーワードは複数回実行。

### フィルタ例

| 用途 | input 例 |
|------|---------|
| キーワード | `{"searchQuery":"weed","maxItems":20}` |
| 地域 | `{"searchQuery":"Founder","locations":["United States"],"maxItems":50}` |
| 職種 | `{"searchQuery":"Marketing Manager","currentJobTitles":["Marketing Manager"]}` |
| 企業 | `{"searchQuery":"Engineer","currentCompanies":["https://www.linkedin.com/company/openai/"]}` |
| 除外 | `{"searchQuery":"Founder","excludeLocations":["Ukraine"],"excludeIndustryIds":["4"]}` |
| 大量 | `{"searchQuery":"Founder","maxItems":500,"autoQuerySegmentation":true}` |

## Output Schema (主要フィールド)

全件 JSON, null-safe。CSV/Excel 出力も可。Dataset `bRGOoafmRLKx0ZilP` 20件 (本run `jPYfwI1hwOG2phE75`)。

| フィールド | 説明 |
|-----------|------|
| `linkedinUrl` / `publicIdentifier` / `id` / `objectUrn` | プロフィールURL (`https://linkedin.com/in/...`) / ID |
| `firstName` / `lastName` / `headline` / `about` | 氏名 / 見出し / 自己紹介 |
| `location.linkedinText` / `location.parsed.{country,state,city}` / `location.countryCode` | 所在地 (例: `Santa Cruz, California, United States` / `US`) |
| `currentPosition[]` / `experience[]` | 現職・職歴 `{companyName, companyLinkedinUrl, companyId, position, duration, startDate, endDate}` |
| `education[]` / `certifications[]` / `courses[]` | 学歴・資格 |
| `connectionsCount` / `followerCount` / `verified` / `premium` / `creator` / `influencer` | ネットワーク指標 |
| `profilePicture.url` / `coverPicture.url` / `photo` | 画像URL群 (sizes 100〜800) |
| `skills[]` / `topSkills[]` | スキル一覧 |
| `emails[]` | メール (Full+email モードのみ, 本runは `[]`) |
| `languages[]` / `interests[]` / `featured.slides[]` | 言語・興味・注目コンテンツ |

サンプル (1件抜粋, `bRGOoafmRLKx0ZilP` より):

```json
{
  "linkedinUrl": "https://www.linkedin.com/in/california-grown-weed-10a12719a",
  "publicIdentifier": "california-grown-weed-10a12719a",
  "firstName": "California ",
  "lastName": "Grown Weed",
  "headline": "& California Grown Hemp",
  "location": { "linkedinText": "Santa Cruz, California, United States", "countryCode": "US" },
  "connectionsCount": 2663, "followerCount": 2731,
  "currentPosition": [{ "companyName": "California Grown Hemp", "companyLinkedinUrl": "https://www.linkedin.com/company/california-grown-hemp/", "duration": "7 yrs 9 mos", "startDate": {"month":"Jan","year":2019} }],
  "about": "California Grown Hemp is the largest hemp farming operations in California...",
  "verified": false, "premium": false, "influencer": false
}
```

完全なCSV: Console `https://console.apify.com/actors/M2FMdjRVeF1HPGFcc/runs/jPYfwI1hwOG2phE75#output` で確認可

## 実行方法

### 方法A — netloom (推奨, API課金)

```bash
# 1. 実行 (weed例, API課金, Full 20件 ≒1ページ)
R=$(netloom apify run --actor M2FMdjRVeF1HPGFcc --wait 60 \
  --input '{"searchQuery":"weed","profileScraperMode":"Full","maxItems":20}')
RUN_ID=$(echo "$R" | jq -r '.data.id // .id')
DS=$(echo "$R" | jq -r '.data.defaultDatasetId // .defaultDatasetId')

# 2. 結果取得
netloom apify dataset --dataset-id "$DS" --limit 20 --as json \
  | jq '.[0] | {linkedinUrl, headline, location: .location.linkedinText, connectionsCount}'

# 3. 課金確認
netloom apify run-status --run-id "$RUN_ID" \
  | jq '.data | {status, usageTotalUsd, chargedEventCounts}'
```

### 方法B — netloom と KVS API

```bash
source .env.d/apify.env

# 1. 実行 (run, waitForFinish=60で同期待ち)
netloom apify run --actor M2FMdjRVeF1HPGFcc --wait 60 \
  --input '{"searchQuery":"weed","profileScraperMode":"Full","maxItems":20}' \
  | jq '{id: (.data.id // .id), status: (.data.status // .status), datasetId: (.data.defaultDatasetId // .defaultDatasetId)}'

# → {"id":"jPYfwI1hwOG2phE75","status":"SUCCEEDED","defaultDatasetId":"bRGOoafmRLKx0ZilP"}

# 2. データセット取得 (JSON)
netloom apify dataset --dataset-id bRGOoafmRLKx0ZilP --limit 20 --as json \
  | jq '.[0] | {linkedinUrl, headline, location: .location.linkedinText, connectionsCount}'

# 3. CSVで保存
netloom apify dataset --dataset-id bRGOoafmRLKx0ZilP --as csv --out /tmp/linkedin_search_weed.csv

# 4. 課金確認
netloom apify run-status --run-id jPYfwI1hwOG2phE75 \
  | jq '.data | {status, usageTotalUsd, chargedEventCounts}'

# 5. 地域フィルタ例 (日本, Short 25件)
netloom apify run --actor M2FMdjRVeF1HPGFcc --wait 60 \
  --input '{"searchQuery":"Founder","profileScraperMode":"Short","maxItems":25,"locations":["Japan"]}' | jq .

# 6. INPUT確認 (KVS)
#    store id は run ごとに変わる。run の defaultKeyValueStoreId から取る
STORE_ID=$(netloom apify run-status --run-id jPYfwI1hwOG2phE75 --format json \
  | jq -r '.data.defaultKeyValueStoreId')
netloom apify key-value-store --store-id "$STORE_ID" --key INPUT --format json | jq .
```

### 方法C — MCP は管理・検索用途のみ

Actor 実行・dataset 取得・run status・KVS INPUT 取得は netloom を使う（KVS は `run-status` の `defaultKeyValueStoreId` を経由）。MCP は actor 検索・docs 検索・MCP サーバー管理の用途に限る。

## 検証実績 (2026-09-03)

- Actor `M2FMdjRVeF1HPGFcc` (harvestapi/linkedin-profile-search, 0.0.265, rN8UwvEPlEHaGsjFK, No Cookies)
- Input `searchQuery="weed" profileScraperMode=Full maxItems=20` → 20件取得, 20.5秒, `usageTotalUsd $0.18` (`search-page $0.10 + 20×$0.004`)
- Run `jPYfwI1hwOG2phE75` / Dataset `bRGOoafmRLKx0ZilP` / KVS `RfgHluUVfS9i3nz4j` (INPUT + crawling-state)。**KVS の id は run ごとに変わる**（現在は `run-status` の `defaultKeyValueStoreId` から取る。この固定値は当時の記録）
- 出力 `https://console.apify.com/actors/M2FMdjRVeF1HPGFcc/runs/jPYfwI1hwOG2phE75#output` で全件確認可 (要 `APIFY_TOKEN`)

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `maxItems` を20-50に制限。`Short 25件 $0.10` vs `Full 25件 $0.20`。`100件 Full $0.50`。1000件 Full → $4.10 (`0.10×40 + 1000×0.004`) |
| 最低課金 | `minimal $0.10`  — 1件でも $0.10。テストは `profileScraperMode=Short maxItems=1` で $0.10に抑える |
| 課金確認 | `get-actor-run` / `GET /v2/actor-runs/{runId}` の `usageTotalUsd` / `chargedEventCounts` で都度確認 |
| email探索 | `Full + email search` は $0.01/件 (Fullの2.5倍)。必要時のみ使用 |
| レート | 連続実行は `waitSecs` 60秒 + 1秒間隔。LinkedIn側レートは寛容だが `autoQuerySegmentation` で回避可能 |
| 大量取得 | broad query は `autoQuerySegmentation:true` で国/州/役職に自動分割し LinkedIn上限を回避 |

## 制約・注意

- 公開プロフィールのみ。非公開/制限付きは取得不可。Cookies不要 (No Cookies)
- 1実行1クエリ。複数キーワードは複数回実行 (並列可だが課金も件数倍)
- `profileScraperMode` の挙動: `Short`=ページ結果のみ (25件/$0.10)、`Full`=詳細+経歴、`Full+email`=メール探索付き
- `searchQuery` は LinkedIn 演算子可 (`AND OR NOT "" ()`)。詳細は `https://www.linkedin.com/help/linkedin/answer/a524335`
- `locations` は LinkedIn autocomplete依存。`UK→Ukraine` 誤爆など、正式名 (`United Kingdom`) を推奨
- 日本語クエリ可だが英語で検索した方がヒット高。`locations:["Japan"]` 併用推奨
- レート: 短時間に同一KWで連打すると一時的に空結果。1秒間隔を空ける + `autoQuerySegmentation` 活用

## 出力先

| 種別 | パス/URL |
|------|----------|
| MCP生JSON | `tools/call` の `content[0].text` (標準出力) |
| Dataset JSON | `https://api.apify.com/v2/datasets/{datasetId}/items?clean=true&format=json` |
| Dataset CSV | `.../items?clean=true&format=csv` |
| ローカル保存例 | `/tmp/linkedin_search_{query}.json` / `/tmp/linkedin_search_{query}.csv` |
| コンソール | `https://console.apify.com/actors/M2FMdjRVeF1HPGFcc/runs/{runId}` (本件は `.../runs/jPYfwI1hwOG2phE75#output`) |
| KVS INPUT | `https://api.apify.com/v2/key-value-stores/{storeId}/records/INPUT` |

## 他SNSとの比較

| 項目 | LinkedIn `M2FMdjRVeF1HPGFcc` | X `cPYLH3QT9GyzKhB4S` | Instagram `TxU0ZBQIHdR20dr9C` | YouTube `gJvjeCYNraSfhIaNd` | TikTok `jQfZ1h9FrcWcliKZX` |
|------|-----------------------------|---------------------|------------------------------|---------------------------|--------------------------|
| 入力 | `searchQuery` + `profileScraperMode` + `maxItems` | `query` + `section` + `maxPages` | `query` + `maxPages` | `search_term` + `max_videos` | `keyword` + `limit` |
| 単価 (FREE) | **$0.004/件 + $0.10/ページ** (Full) | $0.0025/件 + $0.002/start | $0.0025/件 + $0.002/start | $0.0005/件 + $0.00005/start | $0.0004/件 + $0.00023/start |
| 1回(20件)コスト | **$0.18** (1ページ) | $0.052 | $0.052 | $0.010 | $0.008 |
| 1000件コスト | **$4.10** (40ページ + Full) | $2.50 | $2.50 | $0.50 | $0.40 |
| フィルタ | 30+ (地域/企業/職種/学歴/役職/業界) | `section`/`filter:` | なし | なし | `region`/`publishTime` |
| 出力 | `linkedinUrl/headline/experience/education` | `tweet_id/text/views` | `id/caption/ig_play_count` | `videoId/title/views` | `aweme_id/desc/statistics` |

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `401 Unauthorized` / `Invalid token` | `APIFY_TOKEN` 未設定・誤り・失効 | `https://console.apify.com/settings/integrations` で再発行 → `echo 'APIFY_TOKEN=apify_api_...' > .env.d/apify.env && chmod 600 .env.d/apify.env` |
| `402 Payment required` / `Not enough usage credits` | 無料枠枯渇・支払い方法未登録 | Console → Billing で支払い方法登録。`maxItems=1 profileScraperMode=Short` で再試行 ($0.10) |
| 0件 / 少ない | クエリがニッチ / LinkedInで0件 | LinkedIn本家 `https://linkedin.com/search/results/people/?keywords=weed` で件数確認。`searchQuery` を広く (`weed→cannabis`)、演算子を外して再試行 |
| `locations` で0件 | 国フィルタが強すぎ (`UK→Ukraine`) | `United Kingdom` 等正式名で再試行。`locations` を外して全世界に |
| `excluded` で大量除外 | 除外フィルタが広すぎ | `exclude*` を1つずつ外して検証 |
| `Tool not found` | `.mcp.json` の `TOOLS` 制限 | `apify-hosted` (`mcp-remote https://mcp.apify.com`) を使用, またはAPI直叩き (方法B) |
| Tokenがログに平文出力された | `cat .env.d/apify.env` を実行 | 直ちに `Rotate Token` (Console → Integrations → Rotate) |
| `maxItems` 大で高額 | 上限なしで大量件数 | 事前に `maxItems=20` で件数確認, `autoQuerySegmentation` と `takePages` で分割 |

## 関連

- 管理スキル: `apify-mcp` (MCP起動・認証・ツール一覧) — 本スキルは `M2FMdjRVeF1HPGFcc` 専用のAPI課金実行スキル
- 姉妹: `apify-instagram-search` (`TxU0ZBQIHdR20dr9C`) / `apify-youtube-search` (`gJvjeCYNraSfhIaNd` $0.50/1k) / `apify-tiktok-search` (`jQfZ1h9FrcWcliKZX` $0.40/1k) / `apify-twitter-search` (`cPYLH3QT9GyzKhB4S` $2.50/1k) — LinkedInは **ページ課金+件数課金** の2層
- 代替: `apify/rag-web-browser` (汎用Web検索)
- 参照MCP: `serpbear` (順位取得), `ga4` / `google-search-console`
