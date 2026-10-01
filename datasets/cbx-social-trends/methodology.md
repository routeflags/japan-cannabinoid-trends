# CBX Social Media Trends — Methodology

**Study ID:** cbx-social-trends
**Created:** 2026-09-18
**Last Updated:** 2026-10-01
**Status:** ACTIVE
**Note:** 本 study は複数 SNS プラットフォームの CBX トレンドを横断的に収集する。GSC 検索データは `cbx-search-trends/`、COA 分析データは `cbx-product-coa/` に分離。

---

## 1. Research Question

What is the volume, composition, and temporal pattern of Japanese-language social media posts referencing CBX (cannabioxepane) across X (Twitter), YouTube, Instagram, and TikTok?

---

## 2. Data Sources

| Source | Type | Collection Method | Period | Records | Study |
|--------|------|-------------------|--------|---------|-------|
| X (Twitter) — Daily | Social | Apify Twitter Search | 2026-08-01 ~ 2026-09-08 | 2,376 (raw) → 147 (processed) | 本 study |
| X (Twitter) — 26-week | Social | Apify Twitter Search | 2026-03-19 ~ 2026-09-17 | 321 (weekly files) / 451 (all files) → 291 (unique) | 本 study |
| YouTube | Video | Apify YouTube Search | 2026-09-07 | 50 (CBX-related: 0) | 本 study |
| Instagram | Social | Apify Instagram Search | 2026-09-10 | 6 (CBX-related: 0) | 本 study |
| TikTok | Social | Apify TikTok Search | 2026-09-10 | 20 (description empty) | 本 study |
| ~~Google Search Console~~ | ~~Search~~ | ~~GSC CSV export~~ | ~~2026-07~~ | ~~200 queries~~ | `cbx-search-trends/` へ分離 |
| ~~COA~~ | ~~Lab report~~ | ~~KCA Labs + Anresco~~ | ~~2025-05~06~~ | ~~2 PDFs~~ | `cbx-product-coa/` へ分離 |

### 2.1 X データ件数の説明

X データには複数の集計値があるため、整理する:

| 集計値 | 意味 | 場所 |
|--------|------|------|
| **2,376** | 日別収集の raw データ（重複多数） | `data/raw/x/202608/` |
| **147** | 日別収集の processed データ（tweet_id で重複排除済み） | `data/processed/x_cbx_202608_summary.csv` |
| **321** | 26週収集の主要週別ファイル合計（W01-W26） | `data/raw/x/26week/W*.json` |
| **451** | 26週収集の全ファイル合計（detail/full 含む） | `data/raw/x/26week/` |
| **291** | 26週収集のユニーク tweet_id 数（重複排除後） | 算出値 |

> **注:** 26週データはまだ processed ファイルに統合されていない。将来的に重複排除した processed ファイルを作成予定。

---

## 3. Collection Parameters

### 3.1 X (Twitter) — Daily Collection

| Parameter | Value |
|-----------|-------|
| Actor | `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search) |
| Query | `CBX リキッド` |
| Section | `latest` |
| Max pages | 2 (~40 tweets/run) |
| Run frequency | Daily (2026-08-01 ~ 2026-08-31) |
| Collection tool | Apify API (Bearer token) |

**Run command pattern:**
```bash
curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"CBX リキッド","section":"latest","maxPages":2}'
```

**Date-filtered variant (26-week):**
```bash
-d '{"query":"CBX リキッド since:YYYY-MM-DD until:YYYY-MM-DD","section":"latest","maxPages":5}'
```

### 3.2 X (Twitter) — 26-Week Collection

| Parameter | Value |
|-----------|-------|
| Actor | Same as above |
| Query | `CBX リキッド since:{start} until:{end}` |
| Section | `latest` |
| Max pages | 5 (~100 tweets/week) |
| Week boundaries | Thursday-to-Thursday (W01: 2026-03-19 ~ 2026-03-26) |
| Run date | 2026-09-17 |

### 3.3 Google Search Console

| Parameter | Value |
|-----------|-------|
| Property | www.thch-vape.shop (all properties) |
| Period | 2026-07-01 ~ 2026-07-31 (monthly) |
| Export | CSV |
| Filter | All queries (CBX extracted post-hoc) |
| CBX extraction | Query contains "cbx" (case-insensitive) |

### 3.4 YouTube

| Parameter | Value |
|-----------|-------|
| Actor | `gJvjeCYNraSfhIaNd` (danek/youtube-search) |
| Query | `CBX リキッド` (initial — returned 0 CBX-related) |
| Max videos | 50 |
| Region | Japan (domestic) |
| Run date | 2026-09-07 |

### 3.5 Instagram

| Parameter | Value |
|-----------|-------|
| Actor | `TxU0ZBQIHdR20dr9C` (patient_discovery/instagram-search-reels) |
| Query | `CBXリキッド` |
| Max pages | 1 |
| Run date | 2026-09-10 |

### 3.6 TikTok

| Parameter | Value |
|-----------|-------|
| Actor | `jQfZ1h9FrcWcliKZX` (novi/tiktok-search-api) |
| Keyword | `CBXリキッド` |
| Limit | 20 |
| Region | `JP` |
| Sort type | 0 (Relevance) |
| Publish time | `ALL_TIME` |
| Run date | 2026-09-10 |

---

## 4. Deduplication

| Source | Key Field | Rule | Raw Count | Deduplicated |
|--------|-----------|------|-----------|--------------|
| X (Twitter) — Daily | `tweet_id` | Exact match, keep first occurrence | 2,376 | 147 (processed CSV) |
| X (Twitter) — 26-week | `tweet_id` | Exact match, keep first occurrence | 321 (weekly) / 451 (all files) | 291 (unique) |
| GSC | `query` | Exact match | 200 | 200 (no duplicates) |

**Note:** 
- 日別収集データ（147件）は processed CSV に重複排除済み
- 26週収集データ（291ユニーク）はまだ processed ファイルに統合されていない
- 26週データの raw ファイルは detail/full ファイルを含むため 451 件になるが、主要週別ファイルのみでは 321 件

---

## 5. Processing Pipeline

```
raw (Apify JSON)
  ↓
date normalization (ISO 8601)
  ↓
language filter (ja only)
  ↓
deduplication (tweet_id)
  ↓
processed CSV (147 rows)
```

**Processed CSV schema:**
```csv
tweet_id,createdAt,lang,username,author_name,views,likes,reposts,replies,url,text
```

---

## 6. Inclusion / Exclusion Criteria

| Criterion | Rule |
|-----------|------|
| Language | Japanese (`lang: ja`) |
| Topic | Must reference CBX (directly or in hashtag) |
| Platform | Public tweets only (no protected/deleted) |
| Date range | Within collection window |
| Excluded | Bot accounts (not formally filtered — manual review) |
| Excluded | Retweets (deduplication may retain them) |

---

## 7. Known Limitations

### 7.1 X API Restrictions

| Issue | Impact | Date observed |
|-------|--------|---------------|
| Shadow ban on cannabinoid keywords | 0 results for `CBX リキッド` queries | 2026-09-17 |
| `chargedEventCounts` unreliable | Must verify actual dataset item count | Ongoing |
| No retroactive search beyond recent | 5-7月 data unavailable via API | Confirmed 2026-09-17 |
| Daily collection gaps | Some days returned <10 items (API limits) | 2026-08 |

### 7.2 Other Platforms

| Platform | Issue | Status |
|----------|-------|--------|
| YouTube | Query returned 0 CBX-related results | ✅ Fixed 2026-10-01 (26 unique videos) |
| Instagram | Shadow ban suspected; results unrelated | Needs re-collection |
| TikTok | Description fields empty; CBX relevance unclear | Needs re-collection |

### 7.3 26-Week Data Gaps

| Week Range | Status | Explanation |
|------------|--------|-------------|
| W01-W07 (2026-03 ~ 2026-04) | ✅ Confirmed empty | Before CBX release (July 2026) |
| W09-W15 (2026-05 ~ 2026-06) | ✅ Confirmed empty | Before CBX release |
| W23 (2026-08-20 ~ 08-27) | ✅ Filled (33 items) | Re-collected 2026-10-01 |
| W26 (2026-09-10 ~ 09-17) | ✅ Filled (37 items) | Re-collected 2026-10-01 |

**Note:** Empty weeks before July 2026 are genuinely empty because CBX was not yet released in the Japanese market. This is an observed_zero, not a collection failure.

### 7.3 Data Quality

| Issue | Impact |
|-------|--------|
| 26-week data has many empty weeks (W01-W07, W09-W15, W23, W26) | Long-term trend analysis limited |
| Processed CSV covers only 35 days (8/5-9/8) | Not full month coverage |
| No formal bot/spam filtering | Engagement metrics may be inflated |
| Single query (`CBX リキッド`) | May miss posts using only `CBX` or other terms |

---

## 8. Cost Tracking

| Collection | Actor | Items | Cost (USD) |
|------------|-------|-------|------------|
| X daily (August) | cPYLH3QT9GyzKhB4S | ~2,376 | ~$5.94 |
| X 26-week | cPYLH3QT9GyzKhB4S | 451 | ~$1.13 |
| YouTube | gJvjeCYNraSfhIaNd | 50 | ~$0.025 |
| Instagram | TxU0ZBQIHdR20dr9C | 6 | ~$0.017 |
| TikTok | jQfZ1h9FrcWcliKZX | 20 | ~$0.008 |
| **Total** | | | **~$7.12** |

---

## 9. Reproducibility

To reproduce this dataset:

1. Set `APIFY_TOKEN` in `.env.d/apify.env`
2. Run the collection commands specified in Section 3
3. Deduplicate by `tweet_id`
4. Filter by `lang: ja`
5. Export to CSV with schema in Section 5

**Note:** X search results are non-deterministic. Repeated runs may return different results. Always preserve run metadata and dataset IDs.

---

## 10. Citation

```
Routeflags Co., Ltd. (2026).
CBX X (Twitter) Trends Dataset, August-September 2026.
Version 1.0.
[Dataset].
```

**License:** CC-BY-4.0 (pending review)

**Conflict of Interest:** The publisher operates an e-commerce business in the cannabinoid sector. This commercial relationship may represent a potential conflict of interest. Source data, methodology, and limitations are provided to support independent evaluation.
