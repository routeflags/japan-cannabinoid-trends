---
name: apify-youtube-scraper
description: |
  Apify YouTube Scraper スキル（日付フィルタ対応）。
  「YouTube検索（日付指定）」「期間指定YouTube検索」「YouTube データ収集（期間）」
  「新しいYouTube Actor」などで使う。
---

# Apify YouTube Scraper スキル（日付フィルタ対応）

Apify Actor `h7sDV53CddomktSi5`（streamers/youtube-scraper）を使って、YouTube の動画を**日付指定付き**で取得する。

- Actor: `h7sDV53CddomktSi5` / streamers/youtube-scraper — YouTube Scraper
- 課金: PAY_PER_EVENT（$2.40/1,000件）
- 認証: `.env.d/apify.env` の `APIFY_TOKEN`

---

## トリガー

- 「YouTube検索（日付指定）」
- 「期間指定YouTube検索」
- 「YouTube データ収集（期間）」
- 「新しいYouTube Actor」
- 「日付フィルタ対応YouTube」

---

## 既存 Actor との違い

| 項目 | apify-youtube-search (現行) | **apify-youtube-scraper (本スキル)** |
|------|---------------------------|-------------------------------------|
| Actor ID | `gJvjeCYNraSfhIaNd` | **`h7sDV53CddomktSi5`** |
| 日付フィルタ | ❌ 機能しない | **✅ 動作する** |
| 絶対日付 | ❌ 相対表記 | **✅ ISO8601** |
| コスト | $0.50/1,000件 | $2.40/1,000件 |

---

## 前提

- Apifyアカウントに支払い方法登録済み
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在

---

## 入力スキーマ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `searchQueries` | array | ✅ | 検索クエリ（複数可） |
| `maxResults` | integer | — | 取得上限（デフォルト: 10） |
| `maxResultsShorts` | integer | — | Shorts 上限（0=除外） |
| `maxResultStreams` | integer | — | ストリーム上限（0=除外） |
| `dateFilter` | string | — | 日付フィルタ（hour/today/week/month/year） |
| `sortingOrder` | string | — | ソート順（relevance/rating/date/views） |

---

## 日付フィルタ

### 検索クエリ使用時

`dateFilter` は **相対期間のみ**。実行時点を基準とした**ローリング窓（直近N期間）**で、絶対日付（例: `2016-01-01`）は指定できない。

| `dateFilter` | 意味（実スキーム enumTitle） | **実挙動（2026-10-10 実測）** |
|--------------|------|------|
| `hour` | Last hour | 直近1時間 |
| `today` | Today | 直近24時間（要検証） |
| `week` | This week | **直近7日**（要検証） |
| `month` | This month | **直近30日**（実測済み） |
| `year` | This year | 直近365日（要検証） |

> ⚠️ **実測によりローリング窓であることを確認済み**。`month` は enumTitle が「This month」だが、実挙動は**暦月ではなく直近30日**。2026-10-10 の実行で `dateFilter: "month"` を指定すると **2026-09-10〜2026-10-09** の動画が返った（最古=09-10, 最新=10-09）。暦月（10-01〜10-09）ではなかった。
> ⚠️ 研究データの期間解釈を誤りやすい。**「今月分」を取得したい場合、`month` を使うと前月分が大量に混入する**。
> ⚠️ 絶対日付の期間指定が必要な場合は、この Actor では実現不可。
> ⚠️ 値は `day` ではなく **`today`**（当該Actorの実スキームに `day` は存在しない）。

### URL 使用時（channel URL 専用）

| パラメータ | 内容 |
|------------|------|
| `oldestPostDate` | `YYYY-MM-DD`。**下限のみ**（この日以降を取得）。上限は指定不可 |
| `sortVideosBy` | `NEWEST`, `OLDEST`, `POPULAR` |

> ⚠️ `oldestPostDate` は **channel URL 専用**（実スキーム sectionCaption:「applicable only to scraping by channels URL」）。検索結果ページURL（`/results?search_query=`）では機能しない。
> ⚠️ `oldestPostDate` を指定すると **`sortVideosBy` は自動的に `NEWEST` へリセットされる**（実スキーム明記）。`OLDEST` 昇順取得はできない。
> ⚠️ `startUrls` を指定すると `searchQueries` は無視される。したがって **キーワード検索＋絶対日付範囲はこのActorでは実現不可**。絶対日付の上下限が必要な場合は公式 YouTube Data API v3 の `publishedAfter`/`publishedBefore` を使用すること。

---

## 出力スキーマ

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `id` | string | 動画ID |
| `title` | string | タイトル |
| `date` | string | **絶対日付 (ISO8601)** |
| `channelName` | string | チャンネル名 |
| `viewCount` | integer | 再生数 |
| `duration` | string | 長さ (HH:MM:SS) |
| `likes` | integer | いいね数 |
| `commentsCount` | integer | コメント数 |
| `url` | string | 動画URL |

---

## 実行方法

### 基本（日付指定なし）

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

R=$(curl -s -X POST "https://api.apify.com/v2/acts/h7sDV53CddomktSi5/runs?waitForFinish=90" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "searchQueries": ["CBD リキッド"],
    "maxResults": 10,
    "maxResultsShorts": 0,
    "maxResultStreams": 0
  }')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

### 日付指定付き

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# 過去30日間の動画を取得
R=$(curl -s -X POST "https://api.apify.com/v2/acts/h7sDV53CddomktSi5/runs?waitForFinish=90" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "searchQueries": ["CBD リキッド"],
    "maxResults": 50,
    "maxResultsShorts": 0,
    "maxResultStreams": 0,
    "dateFilter": "month",
    "sortingOrder": "date"
  }')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

### 特定期間の動画を取得（channel URL 使用時）

> ⚠️ `oldestPostDate` は **channel URL 専用**。検索結果ページURL（`/results?search_query=`）では機能しない。
> ⚠️ 指定すると `sortVideosBy` は **`NEWEST` に自動リセット**される（`OLDEST` 昇順取得は不可）。
> ⚠️ 上限（〜まで）は指定できないため、必要ならクライアント側で `date` を絞り込む。

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# 2026年9月以降の動画を取得（対象チャンネルの /videos ページを指定）
R=$(curl -s -X POST "https://api.apify.com/v2/acts/h7sDV53CddomktSi5/runs?waitForFinish=90" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "startUrls": [{"url": "https://www.youtube.com/results?search_query=CBD+%E3%83%AA%E3%82%AD%E3%83%83%E3%83%89"}],
    "maxResults": 50,
    "maxResultsShorts": 0,
    "maxResultStreams": 0,
    "oldestPostDate": "2026-09-01",
    "sortVideosBy": "NEWEST"
  }')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

---

## データ品質チェック

```bash
DS="datasetId"

# 件数確認
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length'

# 日付範囲確認
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" | python3 -c "
import json
import sys
from datetime import datetime

data = json.load(sys.stdin)
dates = [item.get('date') for item in data if item.get('date')]
if dates:
    min_date = min(dates)
    max_date = max(dates)
    print(f'日付範囲: {min_date[:10]} 〜 {max_date[:10]}')
    print(f'総件数: {len(data)}')
"
```

---

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `maxResults` を 50-100 に制限 |
| 課金確認 | 実行後に `get-actor-run` で確認 |

---

## 制約・注意

- 公開動画のみ。限定公開/非公開は対象外
- `date` は **絶対日付 (ISO8601)** で返る
- 1実行1クエリ（複数クエリは `searchQueries` 配列で指定可）
- `dateFilter` は検索クエリ使用時のみ機能
- `oldestPostDate` は URL 使用時のみ機能

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `sortingOrder` エラー | 無効な値 | `relevance`, `rating`, `date`, `views` を使用 |
| `DATE_FILTER_TOO_STRICT` | 日付範囲が狭すぎ | `dateFilter` を緩める |
| 0件 | クエリがニッチ | クエリを広げる |
| 401 Unauthorized | APIFY_TOKEN 無効 | `.env.d/apify.env` を確認 |

---

## 関連スキル

| スキル | 用途 |
|--------|------|
| `apify-mcp` | MCP 起動・認証 |
| `apify-youtube-search` | 日付フィルタ不要の検索（低コスト） |
| `research-youtube-search` | 研究用データ収集 |
| `youtube-date-enrichment` | 日付取得（既存 Actor 用） |

---

## 検証実績

| 項目 | 内容 |
|------|------|
| **Actor** | `h7sDV53CddomktSi5` (streamers/youtube-scraper) |
| **テスト日** | 2026-10-10 |
| **Run ID** | `uQnbRltcZjXJlSsRa` |
| **Dataset ID** | `5RgsJnJGCELZqgkhM` |
| **検索クエリ** | `CBD リキッド` |
| **日付フィルタ** | `month` |
| **取得件数** | 5件 |
| **日付範囲** | 2026-09-15 〜 2026-10-01 |
