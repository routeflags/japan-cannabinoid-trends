# YouTube Data API v3 セットアップガイド

| 項目 | 内容 |
|------|------|
| **作成日** | 2026-10-02 |
| **目的** | 期間指定可能な YouTube データ収集の実現 |
| **コスト** | 無料（適度な使用） |

---

## 1. 概要

YouTube Data API v3 を使用すると、**期間指定**（`publishedAfter`, `publishedBefore`）が可能になり、Apify Actor ではできなかった時系列分析ができる。

### Apify Actor との比較

| 項目 | Apify Actor | YouTube Data API v3 |
|------|-------------|---------------------|
| **期間指定** | ❌ 不可 | ✅ 可能 |
| **日付** | 相対日付 | 絶対日付（RFC 3339） |
| **コスト** | 従量課金 | 無料（クォータ制） |
| **クォータ** | なし | 10,000 units/日 |
| **最大件数** | 100件/実行 | 50件/ページ（ページング可） |

---

## 2. セットアップ手順

### Step 1: Google Cloud アカウント作成

1. https://console.cloud.google.com/ にアクセス
2. Google アカウントでログイン
3. 新規プロジェクトを作成

### Step 2: YouTube Data API v3 を有効化

1. メニューから「API とサービス」→「ライブラリ」
2. 「YouTube Data API v3」を検索
3. 「有効化」をクリック

### Step 3: API キー発行

1. メニューから「認証情報」
2. 「認証情報を作成」→「API キー」
3. キーを控える
4. 「キーを制限」→「YouTube Data API v3」を選択して制限

### Step 4: 環境変数に保存

```bash
# .env.d/youtube.env に保存
YOUTUBE_API_KEY=AIzaSy...（実際のキー）
```

```bash
# .gitignore に追加
.env.d/youtube.env
```

---

## 3. 使用方法

### 基本的な検索（期間指定なし）

```python
import requests

API_KEY = "YOUR_API_KEY"
url = "https://www.googleapis.com/youtube/v3/search"

params = {
    "key": API_KEY,
    "part": "snippet",
    "q": "CBN",
    "type": "video",
    "maxResults": 50,
    "regionCode": "JP",
    "relevanceLanguage": "ja"
}

response = requests.get(url, params=params)
data = response.json()
```

### 期間指定付き検索

```python
# RFC 3339 形式: YYYY-MM-DDThh:mm:ss.sZ
params = {
    "key": API_KEY,
    "part": "snippet",
    "q": "CBN",
    "type": "video",
    "maxResults": 50,
    "publishedAfter": "2026-09-01T00:00:00Z",
    "publishedBefore": "2026-10-01T00:00:00Z",
    "regionCode": "JP"
}
```

### ページング（大量データ）

```python
all_videos = []
next_page_token = None

while True:
    params = {
        "key": API_KEY,
        "part": "snippet",
        "q": "CBN",
        "type": "video",
        "maxResults": 50,
        "pageToken": next_page_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    all_videos.extend(data["items"])
    
    next_page_token = data.get("nextPageToken")
    if not next_page_token:
        break
```

---

## 4. クォータ計算

### 使用単位

| 操作 | 消費単位 |
|------|---------|
| search.list | 100 units |
| videos.list | 1 unit |
| channels.list | 1 unit |

### 日次クォータ: 10,000 units

```
10,000 units ÷ 100 units/search = 100回/日 の検索が可能
```

### 研究用途での試算

| 用途 | 検索回数 | 消費単位 |
|------|:-------:|---------|
| 7キーワード × 月次 | 7回/月 | 700 units |
| 7キーワード × 週次 | 7回/週 | 700 units |
| 期間分割（月次×12ヶ月） | 84回/年 | 8,400 units |

**結論:** 研究用途ではクォータに余裕あり

---

## 5. 取得できるデータ

### search.list のレスポンス

```json
{
  "items": [
    {
      "id": {
        "kind": "youtube#video",
        "videoId": "xxxxx"
      },
      "snippet": {
        "publishedAt": "2026-09-15T10:30:00Z",  // ← 絶対日付
        "title": "CBNとは？効果と安全性",
        "description": "...",
        "channelTitle": "CBD情報局",
        "thumbnails": {...},
        "tags": ["CBD", "CBN", "カンナビノイド"]
      }
    }
  ],
  "nextPageToken": "..."
}
```

### 追加情報を取得する場合

```python
# videos.list で詳細情報を取得（追加 1 unit）
video_ids = [item["id"]["videoId"] for item in data["items"]]

params = {
    "key": API_KEY,
    "part": "snippet,statistics,contentDetails",
    "id": ",".join(video_ids)
}

# statistics に再生数、いいね数、コメント数が含まれる
```

---

## 6. 収集スクリプト例

```python
#!/usr/bin/env python3
"""
YouTube Data API v3 による期間指定付きデータ収集
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# API キー読み込み
API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY を環境変数に設定してください")

def search_youtube(keyword, start_date, end_date, max_results=50):
    """期間指定付き YouTube 検索"""
    url = "https://www.googleapis.com/youtube/v3/search"
    
    params = {
        "key": API_KEY,
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": min(max_results, 50),
        "publishedAfter": f"{start_date}T00:00:00Z",
        "publishedBefore": f"{end_date}T00:00:00Z",
        "regionCode": "JP",
        "relevanceLanguage": "ja"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    return response.json()

def save_data(data, keyword, start_date, end_date, study_id):
    """データを保存"""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    slug = keyword.lower().replace(" ", "-")
    run_id = f"{timestamp}-youtube-{slug}-{start_date}-to-{end_date}"
    
    save_dir = Path(f"datasets/{study_id}/data/raw/youtube/{run_id}")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # データ保存
    with open(save_dir / "records.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # メタデータ保存
    metadata = {
        "run_id": run_id,
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "item_count": len(data.get("items", [])),
        "collected_at": timestamp,
        "source": "youtube-data-api-v3"
    }
    
    with open(save_dir / "run_metadata.json", "w") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"保存完了: {save_dir}")
    print(f"件数: {len(data.get('items', []))}")
    
    return save_dir

# 実行例
if __name__ == "__main__":
    keyword = "CBN"
    start_date = "2026-09-01"
    end_date = "2026-10-01"
    study_id = "cannabinoid-multi-trends"
    
    data = search_youtube(keyword, start_date, end_date)
    save_data(data, keyword, start_date, end_date, study_id)
```

---

## 7. Apify との使い分け

### YouTube Data API v3 を使う場合

| 用途 | 推奨度 |
|------|:------:|
| 期間指定が必要な分析 | ⭐⭐⭐⭐⭐ |
| 規制前後の比較 | ⭐⭐⭐⭐⭐ |
| 時系列データ構築 | ⭐⭐⭐⭐⭐ |
| 精確な日付が必要 | ⭐⭐⭐⭐⭐ |

### Apify Actor を使う場合

| 用途 | 推奨度 |
|------|:------:|
| クイックな概略把握 | ⭐⭐⭐⭐ |
| API キー不要で使いたい | ⭐⭐⭐⭐ |
| 追加フィールドが必要 | ⭐⭐⭐ |
| 低コストで大量取得 | ⭐⭐⭐ |

---

## 8. 注意事項

| 項目 | 内容 |
|------|------|
| **API キーの秘匿** | 公開リポジトリにコミットしない |
| **クォータ超過** | 日次 10,000 units が上限 |
| **結果の偏り** | 検索アルゴリズムに依存 |
| **レート制限** | 短時間に大量リクエストを送らない |
| **利用規約** | YouTube API Services の規約を遵守 |

---

## 9. 次のステップ

| ステップ | 内容 |
|----------|------|
| 1 | Google Cloud アカウントでプロジェクト作成 |
| 2 | YouTube Data API v3 を有効化 |
| 3 | API キーを発行 |
| 4 | `.env.d/youtube.env` に保存 |
| 5 | スクリプトでテスト実行 |
| 6 | 既存の Apify 収集と比較検証 |

---

## 10. 関連ドキュメント

- [YouTube Data API v3 概要](https://developers.google.com/youtube/v3/getting-started)
- [Search.list リファレンス](https://developers.google.com/youtube/v3/docs/search/list)
- [クォータ情報](https://developers.google.com/youtube/v3/daily-quota-limit)
