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

> **重要（2026-10-13 追記）:** 上表の `data/raw/x/...` は本リポジトリに存在しない。
> `data/raw/` にあるのは `.gitkeep` のみである。日別・26週の raw（2,376 / 451 件）は
> 収集されたがリポジトリには保持されていない。
>
> `data/processed/x_cbx_202608_summary.csv` は **2026-10-13 に公開を取り下げた**。
> X の投稿本文・handle・表示名・URL を含んでいたためで、追跡を外し、
> `src/processing/reproduce.py` の `WITHDRAWN` に記録している（露出範囲は
> `docs/issues/closed/mitigated/20261013_p0_x-identity-published-in-all-releases.md`）。
> 2026-10-15 の owner 決定により、X 元投稿データは `data/private/` を含む
> リポジトリ配下に保存しない。したがって raw からの processed 再生成は不可能であり、
> **公開される X 投稿単位成果物は存在しない**
> （2026-10-13 に非匿名化版、2026-10-15 に匿名化版をそれぞれ取り下げ。投稿単位の X データは
> 匿名化後も公開しない: `ISS-20261015-COL-030` §4.1 / `ISS-20261015-PUB-035`）。
> 導出規則（`src/processing/anonymize.py`）は実行可能なまま、非公開入力を用いる
> fixture テストで検証されている。
> 再現には Section 3 の収集再実行が必要だが、X 検索は非決定論的なため同一の 147 件は
> 得られない。

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

Actor はすべて `gJvjeCYNraSfhIaNd`（danek/youtube-search）。

| # | 実行 | 保存先 | 実行日時 (UTC) | レコード数 | 記録済み | 未記録 |
|---|---|---|---:|---|---|
| 1 | 2026-09-07 初回 | loose ファイル `youtube_domestic_20260907_50.csv`（run ディレクトリ無し） | 2026-09-07 | 50（タイトルに `CBX` を含む 0 件） | 取得上限 50、実行日 | 検索語、実行時刻 |
| 2 | 2026-10-01 run 1 | `20261001T074851Z-youtube-cbx-rikiddo/` | 07:48:51–07:49:13 | 20 | actor、検索語 `CBX リキッド` | 取得上限 |
| 3 | 2026-10-01 run 2 | `20261001T075500Z-youtube-cbx-rikiddo-v2/` | 07:56:04–07:56:20 | 26 | actor、検索語 `CBX リキッド` | 取得上限 |
| 4 | 2026-10-04 v3 | `20261004T135232Z-youtube-cbx-12months/`, `20261004T135457Z-youtube-cbx-rikiddo-12months/` | — | 月別ファイル | v3 経路（月別・クォータ記録あり） | 採用対象外 |

- 公開集計（CBX 関連 24 件）の出所は **run 2**（26 レコードをフィルタ）。run 1 は置き換えられた初回実行。**この 24 件は記録値であり、宣言文書を経ていないため raw から再計算しない**（owner 2026-10-29: 当該 4 run は採用しない）。
- 2026-10-01 の 2 件の `run_metadata.json` は Apify の run envelope（`id` / `status` / 開始・終了時刻）だけで、検索語・取得上限・地域は含まない。検索語 `CBX リキッド` は README と research note の記録による。
- payload に絶対公開日は無い（`snippet.timestamp` が `2 weeks ago` のような相対表記のみ。ISO 日時の出現 0 件）。したがって公開日レンジは復元できず、`staging-declaration-v1` の `window` に観測レンジを書けない。採用方法は ISS-20261029-PRV-016 で決定する。
- 期間指定の入力が actor に無い。この系列は時系列比較に使わず、収集時点の検索結果件数としてのみ扱う。
- run 4 は撤回した v3 経路であり、データ成果物には使わない（`20261024_p1_youtube-v3-residual-raw.md`）。

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

上流（raw → 重複排除済み CSV）は raw が本リポジトリに無いため再現できない（Section 2.1
の注記）。一方、重複排除済み CSV → 匿名化済み CSV は実行可能な変換として
`src/processing/anonymize.py` に実装されており、導出規則のテスト（列単位の比較）が
`tests/processing/test_processed_artifacts.py` にある。

> **注記（2026-10-15）**: 変換の**成果物**（`x_cbx_202608_summary_anonymized.csv`）は
> 公開取り下げになった（投稿単位の X データは匿名化後も公開しない）ため、以前の
> `python -m processing.cli reproduce --artifact <匿名化版>` は実行できない
> （`src/processing/reproduce.py` の `WITHDRAWN`、`ISS-20261015-PUB-035`）。
> 変換の検証は、リポジトリに保存しない外部/一時入力を用いる fixture テストに限って継続する。

16 列中 `week` のみ 3 行で差があり（成果物が 2026-08-31 を `unknown` としている）、その差は
宣言済みとして `src/processing/reproduce.py` に日付付きで記録されている。

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

## 8. Reproducibility

To reproduce this dataset, separate the two steps:

**再現不能（収集）:**

1. Set `APIFY_TOKEN` in `.env.d/apify.env`
2. Run the collection commands specified in Section 3
3. Deduplicate by `tweet_id`
4. Filter by `lang: ja`

**再現可能（処理）:** 上記 4 で得た重複排除済み CSV からの匿名化規則は実行可能な変換として残るが、X 元投稿データはリポジトリ配下に保存しない。検証は外部/一時入力を使う場合に限る。
**匿名化版の成果物は 2026-10-15 に公開取り下げになった**（投稿単位の X データは匿名化後も公開しない。`ISS-20261015-COL-030` §4.1 / `ISS-20261015-PRV-036`）。

**Note:** X search results are non-deterministic. Repeated runs may return different results. Always preserve run metadata and dataset IDs. 手順 2 を再実行しても、本リポジトリの
147 件は再現されない。

---

## 9. Citation

```
Routeflags Co., Ltd. (2026).
CBX X (Twitter) Trends Dataset, August-September 2026.
Version 1.0.
[Dataset].
```

**License:** CC-BY-4.0 (pending review)

**Conflict of Interest:** The publisher operates an e-commerce business in the cannabinoid sector. This commercial relationship may represent a potential conflict of interest. Source data, methodology, and limitations are provided to support independent evaluation.
