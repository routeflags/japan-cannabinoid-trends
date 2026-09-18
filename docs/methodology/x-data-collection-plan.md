# CBX リキッド X データ取得 計画書

**作成日:** 2026-09-17
**目的:** 8月以前（5〜7月）の X データを取得し、時系列データを整備する
**前提:** 8月データ（147件）が存在し、日付指定での取得が可能であることが確認済み

---

## 1. 背景

### 1.1 発見された問題

| # | 問題 | 根拠 |
|---|------|------|
| 1 | `cbx_x_data_integrity.md` に「過去データは遡及取得不可」と記載 | **誤り**。`since:` / `until:` で日付指定が可能 |
| 2 | `cbx_data_collection_report.md` に「X がシャドウバンしている」と記載 | **未確認**。`chargedEventCounts` の reporting 不正確の可能性 |
| 3 | 9月データの `chargedEventCounts` が 0 だった | 実際はデータセットに20件存在した |
| 4 | 5〜7月データが未取得 | 日付指定の方法を知らなかったため |

### 1.2 確認済みの事実

| # | 事実 | 検証方法 |
|---|------|---------|
| 1 | Actor `cPYLH3QT9GyzKhB4S` は正常に動作する | 9月17日に20件取得成功 |
| 2 | `since:` / `until:` で日付指定が可能 | 8月1日〜8日で5件取得成功 |
| 3 | `chargedEventCounts` は不正確な場合がある | 実件数と一致しないケースを確認 |
| 4 | 8月データ（147件）は既に存在する | ファイル確認済み |

---

## 2. 取得対象

### 2.1 対象期間

| 期間 | 状態 | 優先度 |
|------|------|--------|
| 2026年5月 | **未取得** | P1 |
| 2026年6月 | **未取得** | P1 |
| 2026年7月 | **未取得** | P1 |
| 2026年8月 | ✅ 取得済み（147件） | — |
| 2026年9月 | ✅ 取得済み（20件） | — |

### 2.2 検索クエリ

8月データと整合性を保つため、**同一クエリ** を使用する:

```
CBX リキッド
```

日付指定:

```
CBX リキッド since:2026-MM-01 until:2026-MM-01
```

### 2.3 取得設定

| パラメータ | 値 | 理由 |
|-----------|-----|------|
| `section` | `latest` | 8月データと同じ |
| `maxPages` | `2` | 月次データなので2ページ（約40件） |

---

## 3. 実行手順

### Step 1: 環境準備

```bash
cd /Users/bookair18/OS/media/06_symphony/symphony_workspaces/projects/ec/research/20260917
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env
```

### Step 2: 7月データ取得

```bash
R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド since:2026-07-01 until:2026-08-01","section":"latest","maxPages":2}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
echo "DatasetID: $DS"

# 実際の件数を確認
ACTUAL=$(curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length')
echo "7月データ件数: $ACTUAL"

# 保存
mkdir -p x_cbx_202607
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > x_cbx_202607/cbx_202607.json
```

### Step 3: 6月データ取得

```bash
R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド since:2026-06-01 until:2026-07-01","section":"latest","maxPages":2}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
echo "DatasetID: $DS"

ACTUAL=$(curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length')
echo "6月データ件数: $ACTUAL"

mkdir -p x_cbx_202606
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > x_cbx_202606/cbx_202606.json
```

### Step 4: 5月データ取得

```bash
R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド since:2026-05-01 until:2026-06-01","section":"latest","maxPages":2}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
echo "DatasetID: $DS"

ACTUAL=$(curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq 'length')
echo "5月データ件数: $ACTUAL"

mkdir -p x_cbx_202605
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > x_cbx_202605/cbx_202605.json
```

### Step 5: データ検証

```bash
# 各月の件数を確認
for m in 05 06 07; do
  FILE="x_cbx_2026${m}/cbx_2026${m}.json"
  if [ -f "$FILE" ]; then
    COUNT=$(jq 'length' "$FILE")
    echo "${m}月: ${COUNT}件"
    # 投稿日時の範囲を確認
    jq -r '.[].created_at' "$FILE" | sort | head -1
    jq -r '.[].created_at' "$FILE" | sort | tail -1
  else
    echo "${m}月: ファイルなし"
  fi
done

# 8月データとの整合性確認
echo "=== 8月データ（既存） ==="
wc -l ../20260915/mock/guide_cbx_rewrite.html
```

---

## 4. 整合性チェック

### 4.1 8月データとの整合性

| チェック項目 | 方法 | 基準 |
|-------------|------|------|
| 検索クエリ | `CBX リキッド` | 8月と同一 |
| セクション | `latest` | 8月と同一 |
| 重複排除 | `tweet_id` ベース | 月内重複を排除 |
| 投稿日時 | `created_at` フィールド | 対象期間内であること |

### 4.2 データ品質チェック

| チェック項目 | 方法 | 判定基準 |
|-------------|------|---------|
| 件数 | `jq 'length'` | 0件なら要調査 |
| 投稿日時 | `created_at` の範囲 | 対象期間内であること |
| 重複 | `tweet_id` のユニーク数 | 件数と一致すること |
| 日本語投稿 | `lang` フィールド | 日本語が中心であること |

---

## 5. 成果物

### 5.1 データファイル

| ファイル | 内容 |
|---------|------|
| `x_cbx_202605/cbx_202605.json` | 5月 X データ |
| `x_cbx_202606/cbx_202606.json` | 6月 X データ |
| `x_cbx_202607/cbx_202607.json` | 7月 X データ |
| `x_cbx_202608/` (既存) | 8月 X データ |
| `x_cbx_202609/cbx_20260917.json` (既存) | 9月 X データ |

### 5.2 レポート

| ファイル | 内容 |
|---------|------|
| `x_data_timeseries_report.md` | 5〜9月の時系列レポート |
| `cbx_x_data_integrity.md` (更新) | 誤記の修正 |

### 5.3 記事への影響

| ファイル | 変更内容 |
|---------|---------|
| `guide_cbx_rewrite.html` | X トレンドセクションに5〜7月データを追加 |

---

## 6. 費用見積もり

| 項目 | コスト |
|------|--------|
| 5月データ取得 | $0.002 + 件数×$0.0025 |
| 6月データ取得 | $0.002 + 件数×$0.0025 |
| 7月データ取得 | $0.002 + 件数×$0.0025 |
| **合計** | **約$0.01〜$0.15**（件数による） |

---

## 7. リスク

| リスク | 対処 |
|--------|------|
| 0件が返る | 期間を変えて再試行。または「該当期間に投稿なし」と記録 |
| chargedEventCounts が不正確 | 必ず `get-dataset-items` で実件数を確認 |
| 8月データとの整合性が取れない | 同一クエリ・同一設定で取得 |
| 費用超過 | 月次2ページ（約40件）に制限 |

---

## 8. 完了条件

| # | 条件 | 確認方法 |
|---|------|---------|
| 1 | 5〜7月のデータファイルが存在する | `ls x_cbx_20260{5,6,7}/` |
| 2 | 各月の件数が0件でない | `jq 'length'` |
| 3 | 投稿日時が対象期間内である | `jq '.[].created_at'` |
| 4 | 8月データとの整合性が取れる | 同一クエリ・同一設定 |
| 5 | 時系列レポートが作成される | `x_data_timeseries_report.md` |
| 6 | データ整合性ドキュメントが更新される | `cbx_x_data_integrity.md` |
