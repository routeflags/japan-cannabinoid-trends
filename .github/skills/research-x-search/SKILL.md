---
name: research-x-search
description: |
  研究用の X (Twitter) 検索スキル。
  キーワード・期間・研究ID を指定して、X (Twitter) の投稿を収集する。
---

# Research X (Twitter) 検索スキル

研究用の X (Twitter) データ収集スキル。**任意のキーワード・観測期間・研究ID** で再利用できるよう抽象化されている。

各研究は `datasets/<study-id>/` 配下にデータを保存し、このスキルは収集と品質チェックのみを担当する。
研究計画書（`docs/plans/` 配下）に定められたパラメータをそのまま入力として使う。

---

## トリガー

- 「X の研究用データ取って」
- 「<キーワード> の X ツイート収集」
- 「<study-id> の X 収集」
- 「X トレンドデータ取得」
- 「<キーワード> を期間指定で X 検索」

---

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `keyword` | string | ✅ | — | 検索キーワード（研究対象に応じて指定） |
| `study_id` | string | ✅ | — | 研究ID。保存先 `datasets/<study_id>/data/raw/x/` に決定 |
| `section` | string | — | `latest` | top / latest |
| `maxPages` | integer | — | `2` | 取得ページ数 |
| `start_date` | string | — | なし | 観測期間 開始日 (YYYY-MM-DD) |
| `end_date` | string | — | なし | 観測期間 終了日 (YYYY-MM-DD) |
| `output_dir` | string | — | `datasets/<study_id>/data/raw/x/` | 保存先 |

> 観測期間 (`start_date` / `end_date`) はクエリの `since:` / `until:` に変換される。

> キーワード・期間は研究ごとに異なるため固定しない。研究計画書で定めた値をそのまま使う。

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

# パラメータ設定（研究ごとに指定）
KEYWORD="${1:?keyword required}"            # 例: "CBX リキッド", "CBD リキッド"
STUDY_ID="${2:?study_id required}"          # 例: "cbx-liquid-online-trend"
SECTION="${3:-latest}"
MAX_PAGES="${4:-2}"
OUTPUT_DIR="${5:-datasets/${STUDY_ID}/data/raw/x}"
START_DATE="${6:-}"                          # 例: "2026-08-01"（省略可）
END_DATE="${7:-}"                            # 例: "2026-08-08"（省略可）

# クエリ構築（期間指定は since:/until: に変換）
QUERY="$KEYWORD"
if [ -n "$START_DATE" ] && [ -n "$END_DATE" ]; then
  QUERY="${KEYWORD} since:${START_DATE} until:${END_DATE}"
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
  -H "Authorization: Bearer $APIFY_TOKEN" | jq --arg query "$QUERY" --arg keyword "$KEYWORD" --arg study "$STUDY_ID" '.data | {id, status, usageTotalUsd, startedAt, finishedAt, query: $query, keyword: $keyword, study_id: $study}' \
  > "$SAVE_DIR/run_metadata.json"

# 件数確認
COUNT=$(jq 'length' "$SAVE_DIR/records.json")
echo "========================================="
echo "研究ID: $STUDY_ID"
echo "キーワード: $KEYWORD"
echo "クエリ: $QUERY"
echo "期間: ${START_DATE:-指定なし} 〜 ${END_DATE:-指定なし}"
echo "保存先: $SAVE_DIR"
echo "件数: ${COUNT}"
echo "Cost: $(jq -r '.usageTotalUsd' "$SAVE_DIR/run_metadata.json")"
echo "========================================="
```

### 使用例

上記コマンドをスクリプトとして保存して使う場合の例（キーワード・研究IDは研究ごとに置き換える）:

```bash
# 1. キーワード + 研究ID 指定
bash research-x-search.sh "CBX リキッド" "cbx-liquid-online-trend"

# 2. 別キーワード + 別研究
bash research-x-search.sh "CBD リキッド" "cbd-liquid-online-trend"

# 3. キーワード + 研究ID + 期間指定（過去7日）
START=$(date -u -d "7 days ago" +"%Y-%m-%d" 2>/dev/null || date -u -v-7d +"%Y-%m-%d")
END=$(date -u +"%Y-%m-%d")
bash research-x-search.sh "CBX リキッド" "cbx-liquid-online-trend" "latest" "2" "" "$START" "$END"

# 4. 週次収集（週次計画の研究で毎週実行）
bash research-x-search.sh "<keyword>" "<study-id>" "latest" "2" "" "$START" "$END"
```

---

## データ品質チェック

収集後、必ず以下を確認:

```bash
SAVE_DIR="<保存先パス>"
KEYWORD="<使用したキーワード>"

# 1. 件数確認（0件でも observed_zero として記録）
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

# 5. キーワード含有確認（キーワードは研究ごとに変更）
echo "=== キーワード含有 ==="
jq -r '.[].text' "$SAVE_DIR/records.json" | grep -ci "$KEYWORD" || echo "0"
```

---

## 保存先

研究IDごとに保存先が分かれる。

```
datasets/<study-id>/data/raw/x/
└── {YYYYMMDDTHHMMSSZ}-x-{keyword-slug}/
    ├── records.json          ← 取得データ
    └── run_metadata.json     ← 実行メタデータ（query / keyword / study_id 付き）
```

**run-id 形式:** `YYYYMMDDTHHMMSSZ-x-{keyword-slug}`（keyword を小文字・ハイフン連結）
**例:** `20261001T120000Z-x-cbd-liquid`（キーワード `CBD リキッド` の場合）

---

## 費用

| 項目 | 単価 | 件数/回（maxPages=2 の目安） | 週次費用 |
|------|------|---------|---------|
| Actor 起動 | $0.002 | 1 | $0.002 |
| 取得 | $0.0025/件 | ~40（検索結果に依存） | ~$0.100 |
| **合計** | | | **~$0.102/回** |
| **月額** | | 週4回 | **~$0.41** |

---

## 制約・注意

| 制約 | 対策 |
|------|------|
| X API のシャドウバン | 0 件でも `observed_zero` として記録 |
| 過去データ遡及不可 | 週次収集を継続 |
| chargedEventCounts 不正確 | 必ず `records.json` の件数を確認 |
| 検索結果の非決定性 | 複数回収集、run-id で区別 |
| キーワード・期間の固定化 | 研究ごとに keyword / 期間 / 保存先をパラメータで渡す（スキル内にハードコードしない） |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 0 件 | X のシャドウバン | 時間を置いて再試行。0件でも `observed_zero` として記録 |
| 401 Unauthorized | APIFY_TOKEN 無効 | `.env.d/apify.env` を確認 |
| chargedEventCounts=0 だがデータあり | Actor の reporting 不正確 | `records.json` の件数を直接確認 |
| 件数が少なすぎる | maxPages 不足 | `maxPages: 5` で再試行 |

---

## 関連

- **研究計画書:** `docs/plans/` 配下（研究ごとに作成）
- **methodology:** `datasets/<study-id>/methodology.md`（研究ごとに作成）
- **上位スキル:** `apify-x-search`（汎用 X 検索）
- **管理スキル:** `apify-mcp`（MCP 起動・認証）
