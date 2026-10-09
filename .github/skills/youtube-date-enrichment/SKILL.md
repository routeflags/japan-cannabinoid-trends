---
name: youtube-date-enrichment
description: |
  YouTube 動画の絶対公開日時を取得するスキル。
  Apify で videoId を収集し、YouTube Data API で publishedAt を取得する。
  「YouTube 日付取得」「投稿日ソート」「絶対日付」などで使う。
---

# YouTube Date Enrichment スキル

Apify で収集した YouTube 動画の videoId から、絶対公開日時（publishedAt）を取得するスキル。

---

## トリガー

- 「YouTube 日付取得」
- 「投稿日ソート」
- 「絶対日付取得」
- 「videoId から日付」

---

## 前提条件

| 項目 | 必要なもの |
|------|-----------|
| Apify | `.env.d/apify.env` に `APIFY_TOKEN` |
| YouTube Data API | `YOUTUBE_API_KEY` 環境変数 |

### YouTube Data API キーの取得

1. https://console.cloud.google.com/ にアクセス
2. YouTube Data API v3 を有効化
3. API キーを発行
4. 環境変数に設定:

```bash
export YOUTUBE_API_KEY="AIza..."
```

---

## ワークフロー

```
Step 1: Apify で videoId を収集
        ↓
Step 2: YouTube Data API で publishedAt を取得
        ↓
Step 3: 日付でソート
```

---

## 実行方法

### Step 1: Apify で videoId 収集

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# 検索実行
R=$(curl -s -X POST "https://api.apify.com/v2/acts/gJvjeCYNraSfhIaNd/runs?waitForFinish=90" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_term":"CBD リキッド","max_videos":100}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > /tmp/youtube_raw.json

echo "取得件数: $(jq 'length' /tmp/youtube_raw.json)"
```

### Step 2: YouTube Data API で日付取得

```bash
# videoId を抽出
VIDEO_IDS=$(jq -r '.[].id.videoId' /tmp/youtube_raw.json | head -50 | paste -sd, -)

# API 呼び出し（最大50件/リクエスト）
curl -s "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=${VIDEO_IDS}&key=${YOUTUBE_API_KEY}" \
  > /tmp/youtube_dates.json

# 結果確認
jq '.items[] | {videoId: .id, publishedAt: .snippet.publishedAt}' /tmp/youtube_dates.json | head -10
```

### Step 3: データ統合・ソート

```python
import json
from datetime import datetime

# 検索結果を読み込み
with open('/tmp/youtube_raw.json') as f:
    search_results = json.load(f)

# 日付データを読み込み
with open('/tmp/youtube_dates.json') as f:
    date_data = json.load(f)

# videoId → publishedAt のマップ作成
date_map = {item['id']: item['snippet']['publishedAt'] 
            for item in date_data.get('items', [])}

# 統合
enriched = []
for video in search_results:
    vid = video.get('id', {}).get('videoId')
    if vid and vid in date_map:
        enriched.append({
            'videoId': vid,
            'title': video.get('snippet', {}).get('title', ''),
            'channel': video.get('snippet', {}).get('channelTitle', ''),
            'views': video.get('snippet', {}).get('views', 0),
            'publishedAt': date_map[vid],
            'url': f'https://youtube.com/watch?v={vid}'
        })

# 日付でソート
enriched.sort(key=lambda x: x['publishedAt'], reverse=True)

# 結果出力
for v in enriched[:10]:
    print(f"{v['publishedAt'][:10]} | {v['title'][:50]} | {v['views']:,}")
```

---

## 制約

| 項目 | 制限 |
|------|------|
| **YouTube API クォータ** | 10,000 units/日 |
| **videos.list** | 50件/リクエスト、1 unit |
| **1000件** | 約20 units |
| **Apify max_videos** | 100件/実行 |

---

## 出力フォーマット

```json
{
  "videoId": "abc123",
  "title": "動画タイトル",
  "channel": "チャンネル名",
  "views": 12345,
  "publishedAt": "2026-01-15T12:00:00Z",
  "url": "https://youtube.com/watch?v=abc123"
}
```

---

## 関連スキル

| スキル | 用途 |
|--------|------|
| `apify-youtube-search` | Apify での検索 |
| `research-youtube-search` | 研究用データ収集 |
