# youtube-mcp セットアップガイド（OpenCode 用）

| 項目 | 内容 |
|------|------|
| **作成日** | 2026-10-02 |
| **対象** | OpenCode + PPiai/youtube-mcp |
| **目的** | 期間指定可能な YouTube データ収集の実現 |

---

## 1. 概要

PPiai/youtube-mcp を OpenCode に統合し、期間指定可能な YouTube 検索を可能にする。

### Apify Actor との比較

| 項目 | Apify Actor | youtube-mcp |
|------|-------------|-------------|
| **期間指定** | ❌ 不可 | ✅ **可能** |
| **日付** | 相対日付 | **絶対日付** |
| **コスト** | 従量課金 | **無料**（API キー必要） |
| **セットアップ** | 簡単 | 中程度 |
| **MCP 統合** | あり | あり |

---

## 2. 前提条件

| 項目 | 状態 | 確認方法 |
|------|------|---------|
| **Python 3.10+** | 要確認 | `python3 --version` |
| **uv / uvx** | 要確認 | `uv --version` |
| **YouTube Data API v3 キー** | 未取得 | Google Cloud Console |

---

## 3. セットアップ手順

### Step 1: YouTube Data API v3 キー取得

1. https://console.cloud.google.com/ にアクセス
2. プロジェクト作成
3. YouTube Data API v3 を有効化
4. API キーを発行
5. キーを控える

### Step 2: 環境変数に保存

```bash
# .env.d/youtube.env を作成
cat > /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env << 'EOF'
YOUTUBE_API_KEY=ここに取得したAPIキーを貼り付け
MCP_TRANSPORT=stdio
EOF

# パーミッション設定
chmod 600 /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env
```

### Step 3: uvx の確認・インストール

```bash
# uvx の確認
uvx --version

# 無い場合のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 4: opencode.json に追加

```json
{
  "mcpServers": {
    "youtube": {
      "command": "run-with-env.sh",
      "args": [
        "/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env",
        "uvx",
        "youtube-mcp"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**または、環境変数を直接指定する場合:**

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["youtube-mcp"],
      "env": {
        "YOUTUBE_API_KEY": "ここにAPIキー",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### Step 5: OpenCode 再起動

OpenCode を再起動して MCP サーバーを読み込む。

---

## 4. 使用可能なツール

| ツール | 説明 | 期間指定 |
|--------|------|:--------:|
| `search_videos` | 動画検索 | ✅ |
| `search_channels` | チャンネル検索 | — |
| `get_video_details` | 動画詳細情報 | — |
| `get_channel_details` | チャンネル詳細情報 | — |
| `get_trending_videos` | トレンド動画 | — |
| `get_channel_videos` | チャンネルの動画 | — |
| `get_video_comments` | コメント取得 | — |
| `search_playlists` | プレイリスト検索 | — |

---

## 5. 使用例

### 期間指定付き検索

```
CBN の YouTube 動画を2026年9月中で検索して
```

内部では以下が実行される：

```python
search_videos(
    query="CBN",
    published_after="2026-09-01T00:00:00Z",
    published_before="2026-10-01T00:00:00Z",
    max_results=50
)
```

### トレンド検索

```
日本の YouTube トレンドを取得して
```

```python
get_trending_videos(region_code="JP")
```

---

## 6. クォータ計算

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

---

## 7. 収集スクリプト例

```python
#!/usr/bin/env python3
"""
youtube-mcp を使用した期間指定付き YouTube データ収集
"""

import json
import os
from datetime import datetime
from pathlib import Path
import requests

# API キー読み込み
env_path = "/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/youtube.env"
with open(env_path) as f:
    for line in f:
        if line.startswith("YOUTUBE_API_KEY="):
            API_KEY = line.strip().split("=")[1]

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

## 8. トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `YOUTUBE_API_KEY not set` | 環境変数未設定 | `.env.d/youtube.env` を確認 |
| `API key not valid` | キーが不正 | Google Cloud Console で再確認 |
| `API has not been used` | 未有効化 | YouTube Data API v3 を有効化 |
| `Quota exceeded` | 使用制限 | 日次 10,000 units が上限 |
| `uvx command not found` | uv 未インストール | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## 9. セキュリティ注意事項

| 項目 | 内容 |
|------|------|
| **API キーの秘匿** | 公開リポジトリにコミットしない |
| **.gitignore** | `.env.d/youtube.env` を追加 |
| **キーの制限** | Google Cloud Console で YouTube Data API v3 のみに制限 |
| **クォータ監視** | 日次 10,000 units を超えないように注意 |

---

## 10. 次のステップ

| ステップ | 内容 |
|----------|------|
| 1 | YouTube Data API v3 キーを取得 |
| 2 | `.env.d/youtube.env` に保存 |
| 3 | `opencode.json` に youtube-mcp を追加 |
| 4 | OpenCode を再起動 |
| 5 | 動作確認（CBN 検索テスト） |
| 6 | 本番データ収集開始 |

---

## 11. 関連ドキュメント

- [PPiai/youtube-mcp](https://github.com/PPiai/youtube-mcp)
- [YouTube Data API v3](https://developers.google.com/youtube/v3/getting-started)
- [OpenCode MCP 設定](../opencode.json)
