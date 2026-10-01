# CBX Liquid Online Trend — Methodology

**Study ID:** cbx-liquid-online-trend
**Created:** 2026-10-01
**Last Updated:** 2026-10-01

---

## 1. Research Question

What is the volume, content, and temporal pattern of Japanese-language X (Twitter) posts referencing "CBX リキッド" (CBX vape liquid)?

---

## 2. Scope

| 項目 | 値 |
|------|-----|
| プラットフォーム | X (Twitter) のみ |
| 検索クエリ | `CBX リキッド`（固定） |
| 言語 | 日本語中心 |
| 期間 | 2026-08-01 〜 継続 |
| 収集頻度 | 週次 |

**なぜ単一クエリか:**
- 複数クエリは結果のばらつきを増やす
- 単一クエリなら同一条件での反復観測が可能
- データ品質の検証が容易

---

## 3. Collection Parameters

| パラメータ | 値 | 理由 |
|-----------|-----|------|
| Actor | `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search) | 既存データと同一 |
| `query` | `CBX リキッド` | 固定クエリ |
| `section` | `latest` | 新着順 |
| `maxPages` | `2` | 約40件/回（週次に十分） |

### 実行コマンド

```bash
source .env.d/apify.env

R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド","section":"latest","maxPages":2}')

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')

# 保存先: data/raw/x/<run-id>/
RUN_DIR="datasets/cbx-liquid-online-trend/data/raw/x/${RUN_ID}"
mkdir -p "$RUN_DIR"

curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > "$RUN_DIR/records.json"

# メタデータ保存
curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID" \
  -H "Authorization: Bearer $APIFY_TOKEN" > "$RUN_DIR/run_metadata.json"

echo "保存完了: $RUN_DIR"
echo "件数: $(jq 'length' "$RUN_DIR/records.json")"
```

---

## 4. Run Identity

各収集実行は以下の形式で一意に識別される:

```
YYYYMMDDTHHMMSSZ-x-cbx-liquid
```

例: `20261001T120000Z-x-cbx-liquid`

---

## 5. Deduplication

| 項目 | 値 |
|------|-----|
| 重複排除キー | `tweet_id` |
| ルール | 月内重複を排除 |
| 集計単位 | 週次 |

---

## 6. Known Limitations

| 制約 | 影響 | 対策 |
|------|------|------|
| X API のシャドウバン | カンナビノイドキーワードで 0 件になる可能性 | 0 件でも `observed_zero` として記録 |
| 過去データ遡及不可 | 週次収集以外は取得不可 | 週次週次収集を継続 |
| chargedEventCounts 不正確 | 課金フィールドが信頼できない | 必ず dataset 件数を直接確認 |
| 検索結果の非決定性 | 同一クエリでも結果が変動 | 複数回収集してばらつきを記録 |

---

## 7. Cost Tracking

| 項目 | 単価 | 件数/週 | 月額 |
|------|------|---------|------|
| X Search | $0.0025/件 | ~40 件 | — |
| Actor 起動 | $0.002/回 | 4 回/月 | — |
| **月額合計** | | ~160 件 | **~$0.42** |

---

## 8. Citation

```
Routeflags Co., Ltd. (2026).
CBX Liquid Online Trend Dataset.
Version 1.0.
[Dataset].
```

**Conflict of Interest:** The publisher operates an e-commerce business in the cannabinoid sector. Source data, methodology, and limitations are provided to support independent evaluation.
