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
| `dateFilter` | string | — | 日付フィルタ（hour/day/week/month/year） |
| `sortingOrder` | string | — | ソート順（relevance/rating/date/views） |

---

## 日付フィルタ

### 検索クエリ使用時

| `dateFilter` | 期間 |
|--------------|------|
| `hour` | 過去1時間 |
| `day` | 過去24時間 |
| `week` | 過去7日 |
| `month` | 過去30日 |
| `year` | 過去1年 |

### URL 使用時

| パラメータ | 内容 |
|------------|------|
| `oldestPostDate` | `YYYY-MM-DD` 形式 |
| `sortVideosBy` | `NEWEST`, `OLDEST`, `POPULAR` |

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

### 特定期間の動画を取得（URL使用時）

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# 2026年9月以降の動画を取得
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
