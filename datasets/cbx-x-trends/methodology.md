# CBX X (Twitter) Trends — Methodology

**Study ID:** cbx-x-trends
**Created:** 2026-09-18
**Last Updated:** 2026-09-18
**Status:** ACTIVE

---

## 1. Research Question

What is the volume, composition, and temporal pattern of Japanese-language X (Twitter) posts referencing CBX (cannabioxepane) vape liquid, and how does this compare with other cannabinoid search and social data sources in the Japanese market?

---

## 2. Data Sources

| Source | Type | Collection Method | Period | Records |
|--------|------|-------------------|--------|---------|
| X (Twitter) — Daily | Social | Apify Twitter Search | 2026-08-01 ~ 2026-09-08 | 2,376 (raw) / 147 (processed) |
| X (Twitter) — 26-week | Social | Apify Twitter Search | 2026-03-19 ~ 2026-09-17 | 381 (raw) |
| Google Search Console | Search | GSC CSV export | 2026-07 (monthly) | 200 queries |
| YouTube | Video | Apify YouTube Search | 2026-09-07 | 50 (CBX-related: 0) |
| Instagram | Social | Apify Instagram Search | 2026-09-10 | 6 (CBX-related: 0) |
| TikTok | Social | Apify TikTok Search | 2026-09-10 | 20 (description empty) |
| COA (Certificate of Analysis) | Lab report | KCA Labs + Anresco | 2026-05 ~ 2026-06 | 2 PDFs |

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
| X (Twitter) | `tweet_id` | Exact match, keep first occurrence | 2,376 (daily) / 381 (26-week) | 147 (processed CSV) |
| GSC | `query` | Exact match | 200 | 200 (no duplicates) |

**Note:** The processed CSV (147 rows) represents deduplicated tweets from the August daily collection. The 26-week raw data (381 items) has not yet been deduplicated into a single processed file.

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
| YouTube | Query returned 0 CBX-related results | Needs re-collection with different query |
| Instagram | Shadow ban suspected; results unrelated | Needs re-collection |
| TikTok | Description fields empty; CBX relevance unclear | Needs re-collection |

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
| X 26-week | cPYLH3QT9GyzKhB4S | 381 | ~$0.95 |
| YouTube | gJvjeCYNraSfhIaNd | 50 | ~$0.025 |
| Instagram | TxU0ZBQIHdR20dr9C | 6 | ~$0.017 |
| TikTok | jQfZ1h9FrcWcliKZX | 20 | ~$0.008 |
| **Total** | | | **~$6.94** |

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
