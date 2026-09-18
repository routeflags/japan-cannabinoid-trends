---
name: apify-x-search
description: |
  Apify Twitter Search スキル。X (Twitter) の投稿をキーワード検索で取得する。
  日付指定（since/until）、セクション指定（latest/top）、ページ指定に対応。
  「X検索」「Twitter検索」「CBXリキッドのX投稿」「Xのトレンド」などで使う。
---

# Apify X (Twitter) 検索スキル

Apify Actor `cPYLH3QT9GyzKhB4S`（patient_discovery/twitter-search）を使って、X (Twitter) の投稿をキーワード検索で取得する。

- Actor: `cPYLH3QT9GyzKhB4S` / patient_discovery/twitter-search — Twitter Search Scraper (No Login, Cookieless)
- 課金: **PAY_PER_EVENT** — `Actor Start $0.002` + `result $0.0025/件` (FREE)
- 認証: `.env.d/apify.env` の `APIFY_TOKEN`

## トリガー

「X検索」「Twitter検索」「CBXリキッドのX投稿」「Xのトレンド調べて」などで使う。

## 前提

- Apifyアカウントに支払い方法登録済み
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在
- Node.js v18+ または curl

## 入力スキーマ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `query` | string | ✅ | 検索クエリ（X の検索演算子が使える） |
| `section` | string | — | top / latest / people / photos / videos（デフォルト: top） |
| `maxPages` | integer | — | 取得ページ数 1-100（デフォルト: 1） |

### 日付指定（重要）

Actor に専用の日付パラメータはない。**`query` 内に X の検索演算子として `since:` / `until:` を書く。**

```
"CBX リキッド since:2026-08-01 until:2026-08-08"
```

### X の検索演算子

| 演算子 | 使い方 | 例 |
|--------|--------|-----|
| `since:YYYY-MM-DD` | 指定日以降 | `since:2026-05-01` |
| `until:YYYY-MM-DD` | 指定日以前 | `until:2026-06-01` |
| `from:username` | 特定ユーザーの投稿 | `from:elonmusk` |
| `filter:verified` | 認証済みユーザーのみ | `CBD filter:verified` |
| `filter:media` | メディア付き投稿 | `CBX filter:media` |
| `-filter:retweets` | RTを除外 | `CBX -filter:retweets` |
| `lang:ja` | 日本語のみ | `CBX lang:ja` |

## 実行方法

### 方法A — API直叩き（推奨）

```bash
source .env.d/apify.env

# 基本検索（日付指定なし）
curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド","section":"latest","maxPages":1}' \
  | jq '{id: .data.id, status: .data.status, datasetId: .data.defaultDatasetId}'

# 日付指定検索
curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド since:2026-08-01 until:2026-08-08","section":"latest","maxPages":2}' \
  | jq '{id: .data.id, status: .data.status, datasetId: .data.defaultDatasetId}'
```

### データ取得（重要: chargedEventCounts を信じない）

```bash
# ❌ 旧方法（信頼できない）
# chargedEventCounts はデータ件数を正確に反映しない場合がある

# ✅ 新方法（データセットの中身を確認）
DS="datasetId"  # 上記の実行で返った値
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json&limit=5" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  | jq '.[] | {tweet_id, screen_name, created_at, text: .text[0:80]}'
```

### 月次データ取得（推奨パターン）

```bash
source .env.d/apify.env

# 月次データを取得する関数
collect_month() {
  local YEAR=$1
  local MONTH=$2
  local NEXT_MONTH
  if [ "$MONTH" -eq 12 ]; then
    NEXT_MONTH="$((YEAR+1))-01-01"
  else
    NEXT_MONTH="$YEAR-$(printf '%02d' $((MONTH+1)))-01"
  fi
  local FIRST_DAY="$YEAR-$(printf '%02d' $MONTH)-01"
  
  echo "=== $YEAR年$MONTH月データ取得 ==="
  
  R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
    -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
    -d "{\"query\":\"CBX リキッド since:$FIRST_DAY until:$NEXT_MONTH\",\"section\":\"latest\",\"maxPages\":2}")
  
  DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
  
  # chargedEventCounts を確認（参考程度に）
  CHARGED=$(echo "$R" | jq -r '.data.chargedEventCounts["apify-default-dataset-item"] // 0')
  echo "chargedEventCounts: $CHARGED"
  
  # データセットの中身を確認（正規の件数）
  ACTUAL=$(curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
    -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length')
  echo "実際の件数: $ACTUAL"
  
  # 保存
  mkdir -p "data/x_cbx_${YEAR}$(printf '%02d' $MONTH)"
  curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
    -H "Authorization: Bearer $APIFY_TOKEN" \
    > "data/x_cbx_${YEAR}$(printf '%02d' $MONTH)/cbx_${YEAR}$(printf '%02d' $MONTH).json"
  
  echo "保存完了: data/x_cbx_${YEAR}$(printf '%02d' $MONTH)/cbx_${YEAR}$(printf '%02d' $MONTH).json"
}

# 使用例
collect_month 2026 5
collect_month 2026 6
collect_month 2026 7
```

## 出力データの構造

| フィールド | 説明 |
|-----------|------|
| `tweet_id` | ツイートID |
| `screen_name` | ユーザー名 |
| `created_at` | 投稿日時（UTC） |
| `text` | ツイート本文 |
| `lang` | 言語コード |
| `views` | 閲覧数 |
| `likes` | いいね数 |
| `reposts` | リポスト数 |
| `replies` | 返信数 |
| `url` | ツイートURL |

## 費用管理

| 項目 | コスト |
|------|--------|
| Actor Start | $0.002/回 |
| 取得1件 | $0.0025/件 |
| 月次データ（100件想定） | $0.002 + 100×$0.0025 = $0.252 |
| 5ヶ月分（500件想定） | 約$1.26 |

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| chargedEventCounts = 0 だがデータがある | Actor の reporting 不正確 | `get-dataset-items` で中身を確認 |
| 全てのクエリで0件 | 一時的な障害の可能性 | 時間を置いて再試行 |
| `401 Unauthorized` | APIFY_TOKEN が無効 | `.env.d/apify.env` を確認 |
| 日付指定が効かない | `since:` / `until:` の書式ミス | `since:YYYY-MM-DD until:YYYY-MM-DD` の形式で |

## 重要な教訓

1. **`chargedEventCounts` を信用してはいけない** — 課金フィールドであり、データ件数を正確に反映しない場合がある
2. **必ずデータセットの中身を確認する** — `get-dataset-items` で実際の件数を確認してから判断する
3. **推測を事実として扱わない** — 「0件」だから「ブロックされている」とは限らない
4. **日付指定は `query` 内に書く** — Actor に専用パラメータはない

## 関連

- 管理スキル: `apify-mcp`（MCP起動・認証）
- 姉妹スキル: `apify-instagram-search` / `apify-youtube-search` / `apify-tiktok-search`
- パンチパターン: `projects/ec/research/20260917/punch-pattern-apify-date-filter.md`
