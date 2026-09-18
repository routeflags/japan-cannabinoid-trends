# CBX リキッド X 26週間トレンド調査 計画書

**作成日:** 2026-09-17
**対象:** CBX リキッドの X (Twitter) 上のトレンド把握
**手法:** Apify Actor による週次データ取得

---

## 1. 調査概要

| 項目 | 値 |
|------|-----|
| 対象キーワード | `CBX リキッド` |
| 対象期間 | 2026-03-19 〜 2026-09-17（26週間） |
| 単位 | 1週間 |
| 取得上限/週 | 最大100投稿 |
| 合計最大取得量 | 26週 × 100件 = 2,600件 |
| 取得方法 | `latest`（投稿日時降順） |
| Actor | `cPYLH3QT9GyzKhB4S`（patient_discovery/twitter-search） |

---

## 2. 対象期間

| 週 | 期間 |
|----|------|
| W01 | 2026-03-19 〜 2026-03-26 |
| W02 | 2026-03-26 〜 2026-04-02 |
| W03 | 2026-04-02 〜 2026-04-09 |
| W04 | 2026-04-09 〜 2026-04-16 |
| W05 | 2026-04-16 〜 2026-04-23 |
| W06 | 2026-04-23 〜 2026-04-30 |
| W07 | 2026-04-30 〜 2026-05-07 |
| W08 | 2026-05-07 〜 2026-05-14 |
| W09 | 2026-05-14 〜 2026-05-21 |
| W10 | 2026-05-21 〜 2026-05-28 |
| W11 | 2026-05-28 〜 2026-06-04 |
| W12 | 2026-06-04 〜 2026-06-11 |
| W13 | 2026-06-11 〜 2026-06-18 |
| W14 | 2026-06-18 〜 2026-06-25 |
| W15 | 2026-06-25 〜 2026-07-02 |
| W16 | 2026-07-02 〜 2026-07-09 |
| W17 | 2026-07-09 〜 2026-07-16 |
| W18 | 2026-07-16 〜 2026-07-23 |
| W19 | 2026-07-23 〜 2026-07-30 |
| W20 | 2026-07-30 〜 2026-08-06 |
| W21 | 2026-08-06 〜 2026-08-13 |
| W22 | 2026-08-13 〜 2026-08-20 |
| W23 | 2026-08-20 〜 2026-08-27 |
| W24 | 2026-08-27 〜 2026-09-03 |
| W25 | 2026-09-03 〜 2026-09-10 |
| W26 | 2026-09-10 〜 2026-09-17 |

---

## 3. 検索クエリ

```
CBX リキッド since:YYYY-MM-DD until:YYYY-MM-DD
```

| パラメータ | 値 |
|-----------|-----|
| `query` | `CBX リキッド since:{start} until:{end}` |
| `section` | `latest` |
| `maxPages` | `5`（最大100件取得） |

### maxPages の根拠

| maxPages | 想定件数 | コスト/回 |
|----------|---------|----------|
| 1 | ~20件 | ~$0.05 |
| 3 | ~60件 | ~$0.15 |
| **5** | **~100件** | **~$0.25** |
| 10 | ~200件 | ~$0.50 |

`maxPages: 5` で最大100件。月間推定投稿数（~100件/月 = ~25件/週）を十分にカバーできる。

---

## 4. コスト見積もり

### 最大コスト（全週100件取得時）

| 項目 | コスト |
|------|--------|
| Actor Start | 26回 × $0.002 = $0.052 |
| Items | 2,600件 × $0.0025 = $6.50 |
| **合計** | **$6.55** |

### 推定コスト（投稿数次第）

| 期間 | 推定投稿数 | 推定コスト |
|------|-----------|----------|
| W01-W06（3月〜4月） | ~150件 | ~$0.43 |
| W07-W13（5月〜6月） | ~200件 | ~$0.55 |
| W14-W20（7月） | ~200件 | ~$0.55 |
| W21-W26（8月〜9月） | ~150件 | ~$0.43 |
| **合計** | **~700件** | **~$1.96** |

---

## 5. 実行手順

### 5.1 環境準備

```bash
cd /Users/bookair18/OS/media/06_symphony/symphony_workspaces/projects/ec/research/20260917
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env
```

### 5.2 週次データ取得スクリプト

```bash
#!/bin/bash
# cbx_x_26week_collector.sh
# Usage: bash cbx_x_26week_collector.sh

KEYWORD="CBX リキッド"
SECTION="latest"
MAX_PAGES=5
OUTPUT_DIR="x_cbx_26week"
START_DATE="2026-03-19"
END_DATE="2026-09-17"

mkdir -p "$OUTPUT_DIR"

# 26週分をループ
current="$START_DATE"
week=1

while [ "$current" < "$END_DATE" ]; do
  # 7日後の日付を計算
  next=$(date -j -v+7d -f "%Y-%m-%d" "$current" +%Y-%m-%d 2>/dev/null || \
         date -d "$current + 7 days" +%Y-%m-%d)
  
  # 終了日を超えたら終了
  if [ "$next" > "$END_DATE" ]; then
    next="$END_DATE"
  fi
  
  printf -v week_str "W%02d" $week
  echo "=== ${week_str}: ${current} 〜 ${next} ==="
  
  # API 実行
  R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
    -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
    -d "{\"query\":\"${KEYWORD} since:${current} until:${next}\",\"section\":\"${SECTION}\",\"maxPages\":${MAX_PAGES}}")
  
  DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
  RUN_ID=$(echo "$R" | jq -r '.data.id')
  
  # データ件数を確認
  ACTUAL=$(curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
    -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length')
  
  echo "  DatasetID: $DS"
  echo "  件数: ${ACTUAL}件"
  
  # 保存
  curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
    -H "Authorization: Bearer $APIFY_TOKEN" \
    > "${OUTPUT_DIR}/${week_str}_${current}.json"
  
  # 次の週へ
  current="$next"
  week=$((week + 1))
  
  # レート制限対策（1秒待機）
  sleep 1
done

echo "=== 完了 ==="
echo "保存先: ${OUTPUT_DIR}/"
ls -la "${OUTPUT_DIR}/"
```

### 5.3 手動実行（1週ずつ）

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# W01: 2026-03-19 〜 2026-03-26
R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド since:2026-03-19 until:2026-03-26","section":"latest","maxPages":5}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
echo "W01 DatasetID: $DS"
echo "W01 件数: $(curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length')"

# W02: 2026-03-26 〜 2026-04-02
R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド since:2026-03-26 until:2026-04-02","section":"latest","maxPages":5}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
echo "W02 DatasetID: $DS"
echo "W02 件数: $(curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length')"
```

---

## 6. データ検証

### 6.1 各週の検証

```bash
# 各週の件数と投稿日時範囲を確認
for f in x_cbx_26week/W*.json; do
  WEEK=$(basename "$f" .json)
  COUNT=$(jq 'length' "$f")
  FIRST=$(jq -r '.[0].created_at' "$f" 2>/dev/null)
  LAST=$(jq -r '.[-1].created_at' "$f" 2>/dev/null)
  echo "${WEEK}: ${COUNT}件 (${FIRST} 〜 ${LAST})"
done
```

### 6.2 重複排除

```bash
# 全ファイルを結合して tweet_id で重複排除
cat x_cbx_26week/W*.json | jq -s 'add | unique_by(.tweet_id) | length'
```

### 6.3 月次集計

```bash
# 月別の件数を集計
cat x_cbx_26week/W*.json | jq -s 'add | group_by(.created_at[0:7]) | map({month: .[0].created_at[0:7], count: length})'
```

---

## 7. 成果物

### 7.1 データファイル

| パターン | 内容 |
|---------|------|
| `x_cbx_26week/W01_2026-03-19.json` | 1週目の投稿データ |
| `x_cbx_26week/W02_2026-03-26.json` | 2週目の投稿データ |
| ... | ... |
| `x_cbx_26week/W26_2026-09-10.json` | 26週目の投稿データ |

### 7.2 集計ファイル

| ファイル | 内容 |
|---------|------|
| `x_cbx_26week_summary.csv` | 週次件数・投稿者数・エンゲージメント |
| `x_cbx_26week_monthly.csv` | 月次集計 |

### 7.3 レポート

| ファイル | 内容 |
|---------|------|
| `cbx_x_26week_trend_report.md` | 26週間のトレンドレポート |

---

## 8. 既存データとの整合性

| 既存データ | 整合性 |
|-----------|--------|
| 8月データ（日別Latest, 101件） | 新データで上書き（同一方法ではないため） |
| 9月データ（20件） | 新データに含まれる（W25-W26） |

**注意:** 既存の8月データは「日別Latest」で取得しており、新しい「週次since/until」とは取得方法が異なります。月間比較には新しい方法で再取得したデータを使う必要があります。

---

## 9. 完了条件

| # | 条件 | 確認方法 |
|---|------|---------|
| 1 | 26ファイルが存在する | `ls x_cbx_26week/W*.json \| wc -l` |
| 2 | 各ファイルにデータが存在する | `jq 'length' x_cbx_26week/W*.json` |
| 3 | 投稿日時が対象期間内である | 各ファイルの `created_at` を確認 |
| 4 | 重複排除が可能である | `tweet_id` のユニーク数を確認 |
| 5 | 月次集計が可能である | 月別件数を集計 |
| 6 | レポートが作成される | `cbx_x_26week_trend_report.md` |

---

## 10. リスクと対処

| リスク | 対処 |
|--------|------|
| 0件が返る | 期間を変えて再試行。または「該当期間に投稿なし」と記録 |
| chargedEventCounts が不正確 | 必ず `get-dataset-items` で実件数を確認 |
| コスト超過 | maxPages:5 で上限を固定 |
| レート制限 | 各実行間に1秒待機 |
