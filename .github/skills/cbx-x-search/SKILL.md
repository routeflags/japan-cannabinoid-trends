---
name: cbx-x-search
description: |
  CBX リキッド研究用の X (Twitter) 検索スキル。
  キーワードと期間を指定して、X (Twitter) の投稿を収集する。
  「CBXのXデータ取って」「cbx-liquid-online-trendの収集」「XでCBX調べて」などで使う。
---

# CBX X (Twitter) 検索スキル

CBX リキッド研究のための X (Twitter) データ収集スキル。
研究計画書 `docs/plans/2026-10-01_cbx-liquid-research-plan.md` に準拠。

---

## トリガー

- 「CBX の X データ取って」
- 「cbx-liquid-online-trend の収集」
- 「X で CBX リキッド調べて」
- 「CBX リキッドのツイート収集」
- 「X トレンドデータ取得」

---

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `keyword` | string | ✅ | `CBX リキッド` | 検索キーワード |
| `section` | string | — | `latest` | top / latest |
| `maxPages` | integer | — | `2` | 取得ページ数 |
| `start_date` | string | — | なし | 開始日 (YYYY-MM-DD) |
| `end_date` | string | — | なし | 終了日 (YYYY-MM-DD) |
| `output_dir` | string | — | `datasets/cbx-liquid-online-trend/data/raw/x/` | 保存先 |

---

## 前提

- Apify アカウントに支払い方法登録済み
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在
- 環境変数のパス: `/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env`

---

## 実行コマンド

### 基本収集（キーワード指定）

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# パラメータ設定
KEYWORD="${1:-CBX リキッド}"
SECTION="${2:-latest}"
MAX_PAGES="${3:-2}"
OUTPUT_DIR="${4:-datasets/cbx-liquid-online-trend/data/raw/x}"

# クエリ構築
QUERY="$KEYWORD"
if [ -n "$5" ] && [ -n "$6" ]; then
  QUERY="${KEYWORD} since:$5 until:$6"
fi

# タイムスタンプと run-id
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
SAVE_RUN_ID="${TIMESTAMP}-x-$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"

# 収集実行
R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"$QUERY\",\"section\":\"$SECTION\",\"maxPages\":$MAX_PAGES}")

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')

# 保存先
SAVE_DIR="${OUTPUT_DIR}/${SAVE_RUN_ID}"
mkdir -p "$SAVE_DIR"

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > "$SAVE_DIR/records.json"

# メタデータ取得
curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq --arg query "$QUERY" --arg keyword "$KEYWORD" '.data | {id, status, usageTotalUsd, startedAt, finishedAt, query: $query, keyword: $keyword}' \
  > "$SAVE_DIR/run_metadata.json"

# 件数確認
COUNT=$(jq 'length' "$SAVE_DIR/records.json")
echo "========================================="
echo "キーワード: $KEYWORD"
echo "クエリ: $QUERY"
echo "期間: ${5:-指定なし} 〜 ${6:-指定なし}"
echo "保存先: $SAVE_DIR"
echo "件数: ${COUNT}"
echo "Cost: $(jq -r '.usageTotalUsd' "$SAVE_DIR/run_metadata.json")"
echo "========================================="
```

### 使用例

```bash
# 1. デフォルト（CBX リキッド、最新）
bash cbx-x-search.sh

# 2. キーワード指定
bash cbx-x-search.sh "CBD リキッド"

# 3. キーワード + セクション
bash cbx-x-search.sh "CBX リキッド" "latest" "5"

# 4. キーワード + 期間指定
bash cbx-x-search.sh "CBX リキッド" "latest" "5" "datasets/cbx-liquid-online-trend/data/raw/x" "2026-08-01" "2026-08-08"

# 5. 週次収集（現在の週）
START=$(date -u -d "7 days ago" +"%Y-%m-%d" 2>/dev/null || date -u -v-7d +"%Y-%m-%d")
END=$(date -u +"%Y-%m-%d")
bash cbx-x-search.sh "CBX リキッド" "latest" "2" "datasets/cbx-liquid-online-trend/data/raw/x" "$START" "$END"
```

---

## データ品質チェック

収集後、必ず以下を確認:

```bash
SAVE_DIR="<保存先パス>"

# 1. 件数確認
echo "=== 件数 ==="
jq 'length' "$SAVE_DIR/records.json"

# 2. 言語確認
echo "=== 言語分布 ==="
jq -r '.[].lang' "$SAVE_DIR/records.json" | sort | uniq -c

# 3. 日付範囲確認
echo "=== 日付範囲 ==="
echo "開始: $(jq -r '.[].created_at' "$SAVE_DIR/records.json" | sort | head -1)"
echo "終了: $(jq -r '.[].created_at' "$SAVE_DIR/records.json" | sort | tail -1)"

# 4. ユニーク ID 確認
echo "=== ユニーク tweet_id ==="
jq -r '.[].tweet_id' "$SAVE_DIR/records.json" | sort -u | wc -l

# 5. キーワード関連確認
echo "=== キーワード含有 ==="
jq -r '.[].text' "$SAVE_DIR/records.json" | grep -ci "${KEYWORD}" || echo "0"
```

---

## 保存先

```
datasets/cbx-liquid-online-trend/data/raw/x/
└── {YYYYMMDDTHHMMSSZ}-x-{keyword}/
    ├── records.json          ← 取得データ
    └── run_metadata.json     ← 実行メタデータ
```

**run-id 形式:** `YYYYMMDDTHHMMSSZ-x-{keyword}`
**例:** `20261001T120000Z-x-cbx-rikiddo`

---

## 費用

| 項目 | 単価 | 件数/回 | 週次費用 |
|------|------|---------|---------|
| Actor 起動 | $0.002 | 1 | $0.002 |
| 取得 | $0.0025/件 | ~40 | $0.100 |
| **合計** | | | **~$0.102/回** |
| **月額** | | 4回 | **~$0.41** |

---

## 制約・注意

| 制約 | 対策 |
|------|------|
| X API のシャドウバン | 0 件でも `observed_zero` として記録 |
| 過去データ遡及不可 | 週次週次収集を継続 |
| chargedEventCounts 不正確 | 必ず `records.json` の件数を確認 |
| 検索結果の非決定性 | 複数回収集、run-id で区別 |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 0 件 | X のシャドウバン | 時間を置いて再試行 |
| 401 Unauthorized | APIFY_TOKEN 無効 | `.env.d/apify.env` を確認 |
| chargedEventCounts=0 だがデータあり | Actor の reporting 不正確 | `records.json` の件数を直接確認 |
| 件数が少なすぎる | maxPages 不足 | `maxPages: 5` で再試行 |

---

## 関連

- **研究計画書:** `docs/plans/2026-10-01_cbx-liquid-research-plan.md`
- **methodology:** `datasets/cbx-liquid-online-trend/methodology.md`
- **上位スキル:** `apify-x-search`（汎用 X 検索）
- **管理スキル:** `apify-mcp`（MCP 起動・認証）
