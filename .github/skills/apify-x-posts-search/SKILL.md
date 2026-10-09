---
name: apify-x-posts-search
description: |
  Apify x-posts-search スキル。X (Twitter) の投稿を日付指定付きで検索する。
  since:/until: による期間指定が動作する。
  「X投稿検索（日付指定）」「期間指定X検索」「X データ収集（期間）」などで使う。
---

# Apify X Posts Search スキル

Apify Actor `rBaTEHzveTxZPraGv`（x-posts-search）を使って、X (Twitter) の投稿を**日付指定付き**で取得する。

- Actor: `rBaTEHzveTxZPraGv` / x-posts-search — X (Twitter) Posts Search
- 課金: PAY_PER_EVENT（要確認）
- 認証: `.env.d/apify.env` の `APIFY_TOKEN`

---

## トリガー

- 「X投稿検索（日付指定）」
- 「期間指定X検索」
- 「X データ収集（期間）」
- 「since/until が使えるX検索」

---

## 既存 Actor との違い

| 項目 | apify-x-search (現行) | **apify-x-posts-search (本スキル)** |
|------|----------------------|-------------------------------------|
| Actor ID | `cPYLH3QT9GyzKhB4S` | **`rBaTEHzveTxZPraGv`** |
| 日付フィルタ | ❌ 機能しない | **✅ 動作する** |
| 出力形式 | tweet_id, created_at | postId, timestamp (Unix ms) |

---

## 前提

- Apifyアカウントに支払い方法登録済み
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在

---

## 入力スキーマ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `query` | string | ✅ | 検索クエリ（X の検索演算子が使える） |
| `maxItems` | integer | — | 取得上限（デフォルト: 10） |

### 日付指定（重要）

**`query` 内に X の検索演算子として `since:` / `until:` を書く。**

```
"CBD リキッド since:2026-09-01 until:2026-10-01"
```

---

## 出力スキーマ

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `postId` | string | ツイートID |
| `postText` | string | ツイート本文 |
| `postUrl` | string | ツイートURL |
| `timestamp` | integer | Unix タイムスタンプ（ミリ秒） |
| `author.name` | string | 作者名 |
| `author.screenName` | string | ユーザー名 |
| `author.userId` | string | ユーザーID |
| `favouriteCount` | integer | いいね数 |
| `repostCount` | integer | リポスト数 |
| `replyCount` | integer | リプライ数 |
| `quoteCount` | integer | 引用数 |
| `media` | array | メディア配列 |

---

## 実行方法

### 基本（日付指定なし）

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

R=$(curl -s -X POST "https://api.apify.com/v2/acts/rBaTEHzveTxZPraGv/runs?waitForFinish=90" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"CBD リキッド","maxItems":50}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

### 日付指定付き

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# 期間指定: since:YYYY-MM-DD until:YYYY-MM-DD
R=$(curl -s -X POST "https://api.apify.com/v2/acts/rBaTEHzveTxZPraGv/runs?waitForFinish=90" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"CBD リキッド since:2026-09-01 until:2026-10-01","maxItems":50}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN"
```

### 保存と日付変換

```python
import json
from datetime import datetime

# データ取得
data = json.load(open('/tmp/x_data.json'))

# timestamp を日付に変換
for item in data:
    ts = item.get('timestamp', 0)
    if ts:
        item['created_at_iso'] = datetime.fromtimestamp(ts / 1000).isoformat()

# 日付でソート
data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

# 保存
with open('/tmp/x_data_dated.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
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
from datetime import datetime
data = json.load(sys.stdin)
timestamps = [item.get('timestamp', 0) for item in data if item.get('timestamp')]
if timestamps:
    min_ts = datetime.fromtimestamp(min(timestamps) / 1000)
    max_ts = datetime.fromtimestamp(max(timestamps) / 1000)
    print(f'日付範囲: {min_ts.strftime(\"%Y-%m-%d\")} 〜 {max_ts.strftime(\"%Y-%m-%d\")}')
"
```

---

## 費用管理

| 項目 | 対策 |
|------|------|
| 予算超過防止 | `maxItems` を 50-100 に制限 |
| 課金確認 | 実行後に `get-actor-run` で確認 |

---

## 制約・注意

- 公開ツイートのみ。非公開/削除済みは取得不可
- 1実行1クエリ。複数キーワードは複数回実行
- `timestamp` は Unix ミリ秒。日付変換が必要
- `since:`/`until:` は X の検索演算子。Actor の仕様ではなく X 側の機能

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 0件 | クエリがニッチ | クエリを広げる |
| 日付フィルタが効かない | since:/until: の書式ミス | `YYYY-MM-DD` 形式で確認 |
| 401 Unauthorized | APIFY_TOKEN 無効 | `.env.d/apify.env` を確認 |

---

## 関連スキル

| スキル | 用途 |
|--------|------|
| `apify-x-search` | 日付フィルタ不要の検索（現行） |
| `apify-mcp` | MCP 起動・認証 |
| `research-x-search` | 研究用データ収集 |
