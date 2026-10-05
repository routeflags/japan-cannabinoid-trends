# Academic Research Review: YouTube Data Collections

| 項目 | 内容 |
|------|------|
| **Review Date** | 2026-10-05 |
| **Reviewer** | Academic Research Agent |
| **Repository** | japan-cannabinoid-trends |
| **Publisher** | Routeflags Co., Ltd. (COI: cannabinoid e-commerce) |
| **Scope** | YouTube Data API v3 collections in `datasets/cannabinoid-multi-trends/data/raw/youtube/` and `datasets/cbx-social-trends/data/raw/youtube/` |

---

## Executive Summary

### Key Findings

1. **The Japanese keyword collection completely failed.** All 40 files in the `20261004T144147Z-youtube-japanese-keywords-10years/` directory contain HTTP 429 quota error responses, not video data. The collection log confirms 0 records for all four Japanese keywords (CBD オイル, カンナビノイド, CBN オイル, カンナビジェロール). The task description's claim of "2,999 records for CBD オイル" is not supported by the actual data files.

2. **The English CBD 10-year collection is partially usable but methodologically limited.** The collection contains 3,831 records (3,211 unique videoIds, 16.2% duplicate rate), with 423 Japanese-language videos (11.0%). However, data for 2023 is anomalously low (61 records vs. 500+ in other years), and 2025 has zero records due to quota exhaustion. The data represents YouTube search results, not a random sample of Japanese cannabinoid content.

3. **CBG, THC, and CBN collections are insufficient for research.** CBG has 50 records (2017 only), THC has 50 records (2023 only), and CBN has 0 records. All are predominantly English content with 0% Japanese representation. These datasets cannot support any claims about Japanese market dynamics.

4. **The CBX リキッド collection is the most research-usable YouTube dataset.** With 125 records over 12 months (2025-10 to 2026-09), 68% Japanese-language content, and a documented monthly trend showing increase from 2026-07 (19→26→31 videos), this dataset supports descriptive claims about YouTube content trends for this specific query.

5. **API quota constraints fundamentally limit the data.** The YouTube Data API v3 provides 100 search queries per day, not the 10,000 assumed in the collection plan. This constraint caused complete failure of Japanese keyword collection and partial failure of English collections. The quota limitation is honestly documented in error responses but not reflected in the research reports.

---

## Research Question

**Is the YouTube data collection in this repository methodologically sound, and what research claims can it support?**

Sub-questions:
1. Are collection parameters appropriate for studying Japanese cannabinoid content trends?
2. Is data quality adequate for descriptive analysis?
3. How does YouTube data complement Google Trends and X/Twitter data?
4. What limitations constrain the use of this data?

---

## Search Scope

### Data Sources Reviewed

| Source | Location | Collection Date | Method |
|--------|----------|-----------------|--------|
| Japanese keywords (10 years) | `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T144147Z-youtube-japanese-keywords-10years/` | 2026-10-04 | YouTube Data API v3 |
| English CBD (10 years) | `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142147Z-youtube-cbd-10years/` | 2026-10-04 | YouTube Data API v3 |
| English CBG/THC/CBN (10 years) | `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142*Z-youtube-*-10years/` | 2026-10-04 | YouTube Data API v3 |
| Apify snapshot (7 keywords) | `datasets/cannabinoid-multi-trends/data/raw/youtube/20261002T064*Z-youtube-*/` | 2026-10-02 | Apify Actor `gJvjeCYNraSfhIaNd` |
| CBX 12-months | `datasets/cbx-social-trends/data/raw/youtube/20261004T135232Z-youtube-cbx-12months/` | 2026-10-04 | YouTube Data API v3 |
| CBX リキッド 12-months | `datasets/cbx-social-trends/data/raw/youtube/20261004T135457Z-youtube-cbx-rikiddo-12months/` | 2026-10-04 | YouTube Data API v3 |

### Research Documents Reviewed

- `research/20261004-youtube-data-collection-plan.md`
- `research/20261004-youtube-phase1-report.md`
- `research/20261004-youtube-language-filter-analysis.md`
- `research/20261004-cbx-youtube-12months-report.md`
- `research/20261004-cbx-rikiddo-youtube-12months-report.md`
- `datasets/cannabinoid-multi-trends/methodology.md`
- `datasets/cannabinoid-multi-trends/data/processed/collection-summary.md`
- `datasets/cannabinoid-multi-trends/data/processed/early-warning-index-v1.csv`

---

## Data Collection Assessment

### 1. Japanese Keyword Collection (2026-10-04)

**Status: FAILED — 0 usable records**

| Keyword | Claimed Records | Actual Records | Success Rate |
|---------|:---------------:|:--------------:|:------------:|
| CBD オイル | 2,999 | 0 | 0/10 years |
| カンナビノイド | ~2,000 | 0 | 0/10 years |
| CBN オイル | 0 | 0 | 0/10 years |
| カンナビジェロール | 4 | 0 | 0/10 years |

**Evidence:** All 40 JSON files in the collection directory contain identical HTTP 429 error responses:

```json
{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota metric 'Search Queries' and limit 'Search Queries per day' of service 'youtube.googleapis.com'",
    "status": "RESOURCE_EXHAUSTED"
  }
}
```

The collection log (`collection_log.txt`) confirms 0 records for all keyword-year combinations.

**Assessment:** The Japanese keyword collection is completely unusable. The discrepancy between the task description's claimed record counts and the actual data files represents a documentation error that must be corrected before any publication.

**Evidence Confidence: HIGH** (direct inspection of data files and collection logs)

---

### 2. English CBD 10-Year Collection (2026-10-04)

**Status: PARTIAL SUCCESS — 3,831 records, 3,211 unique**

| Year | Records | Unique IDs | Notes |
|------|:-------:|:----------:|-------|
| 2016 | 507 | 397 | Complete |
| 2017 | 504 | 403 | Complete |
| 2018 | 457 | 374 | Complete |
| 2019 | 532 | 464 | Complete |
| 2020 | 540 | 456 | Complete |
| 2021 | 533 | 467 | Complete |
| 2022 | 550 | 469 | Complete |
| 2023 | 61 | 59 | **Anomalous low** (quota?) |
| 2024 | 147 | 122 | Partial |
| 2025 | 0 | 0 | **Failed** (quota exhausted) |

**Language Distribution:**
- Total videos: 3,831 (3,211 unique)
- Japanese videos: 423 (11.0%)
- English/other: 3,408 (89.0%)
- Duplicate rate: 16.2%

**Assessment:** The CBD collection has substantial data for 2016-2022, but 2023-2025 data is incomplete. The 11% Japanese representation is expected when using English keywords with `regionCode=JP` (which does not filter by language). The data can support descriptive claims about YouTube search results for "CBD" but cannot represent Japanese cannabinoid video content trends.

**Evidence Confidence: MODERATE** (substantial data for most years, but incomplete recent data and language mismatch)

---

### 3. English CBG/THC/CBN Collections (2026-10-04)

**Status: NEARLY USELESS — Insufficient data for research**

| Keyword | Total Records | Years with Data | Japanese Content |
|---------|:------------:|:---------------:|:----------------:|
| CBG | 50 | 2017 only | 0% |
| THC | 50 | 2023 only | 0% |
| CBN | 0 | None | N/A |

**Assessment:** These collections cannot support any research claims. Single-year snapshots of 50 English-language videos do not represent Japanese cannabinoid content trends. The CBN collection failed completely due to quota exhaustion.

**Evidence Confidence: HIGH** (data files show insufficient records for analysis)

---

### 4. Apify Snapshot Collections (2026-10-02)

**Status: SMALL BUT VALID — 182 records across 7 keywords**

| Keyword | Records | max_videos | Japanese % |
|---------|:-------:|:----------:|:----------:|
| CBD | 22 | 100 | Low |
| THC | 25 | 100 | Low |
| CBG | 34 | 50 | Low |
| HHC | 28 | 50 | Low |
| THCV | 23 | 50 | Low |
| CBD オイル | 23 | 50 | Medium |
| THC オイル | 27 | 50 | Medium |
| **Total** | **182** | | **8.8%** |

**Assessment:** These are snapshot collections (single point in time), not longitudinal data. The small sample size (182 records) and low Japanese representation (8.8%) limit their utility. They can support descriptive claims about YouTube search results at the collection date but cannot represent market trends.

**Evidence Confidence: LOW-MODERATE** (valid snapshot data, but small sample and limited Japanese content)

---

### 5. CBX 12-Month Collection (2026-10-04)

**Status: MOST SUCCESSFUL — 600 records, 232 CBX-related**

| Month | Total | CBX-related | Excluded (Honda) |
|-------|:-----:|:-----------:|:----------------:|
| 2025-10 | 50 | 19 | 29 |
| 2025-11 | 50 | 13 | 37 |
| 2025-12 | 50 | 14 | 34 |
| 2026-01 | 50 | 18 | 32 |
| 2026-02 | 50 | 24 | 26 |
| 2026-03 | 50 | 15 | 34 |
| 2026-04 | 50 | 22 | 21 |
| 2026-05 | 50 | 20 | 22 |
| 2026-06 | 50 | 18 | 29 |
| 2026-07 | 50 | 20 | 29 |
| 2026-08 | 50 | 25 | 20 |
| 2026-09 | 50 | 24 | 26 |

**Key Observations:**
- 57% of results are Honda CBX400F motorcycle content (correctly excluded)
- CBX-related content is relatively stable (13-25 per month)
- The 50-record monthly cap (API limit) prevents observing true volume
- Japanese content is minimal when using English keyword "CBX"

**Assessment:** This collection demonstrates the polysemy problem with "CBX" (Honda motorcycle vs. cannabinoid). The filtering methodology is transparent, but the 50-record API cap means we cannot observe true content volume—only the top 50 search results per month.

**Evidence Confidence: MODERATE** (transparent methodology, but API cap limits completeness)

---

### 6. CBX リキッド 12-Month Collection (2026-10-04)

**Status: HIGHEST QUALITY — 125 records, 68% Japanese**

| Month | Records | Trend |
|-------|:-------:|-------|
| 2025-10 | 13 | Baseline |
| 2025-11 | 3 | Low |
| 2025-12 | 8 | Low |
| 2026-01 | 1 | Lowest |
| 2026-02 | 4 | Low |
| 2026-03 | 6 | Low |
| 2026-04 | 7 | Low |
| 2026-05 | 2 | Low |
| 2026-06 | 5 | Low |
| 2026-07 | 19 | **Increase begins** |
| 2026-08 | 26 | **Continued increase** |
| 2026-09 | 31 | **Peak** |

**Key Observations:**
- 68% Japanese-language content (85/125 videos)
- Clear temporal pattern: stable low volume (2025-10 to 2026-06), then increase (2026-07 to 2026-09)
- Specific query ("CBX リキッド") reduces polysemy compared to "CBX"
- Monthly counts are below the 50-record API cap, suggesting these may represent actual volume

**Assessment:** This is the most research-usable YouTube dataset. The specific query, Japanese-language focus, and consistent monthly collection support descriptive claims about YouTube content trends. The observed increase from 2026-07 is an **observation**, not a causal finding.

**Evidence Confidence: MODERATE-HIGH** (specific query, Japanese focus, consistent methodology, transparent limitations)

---

## Data Quality Assessment

### Completeness Matrix

| Dataset | Target | Achieved | Completeness | Quality |
|---------|--------|----------|:------------:|---------|
| Japanese keywords (4 × 10 years) | 40 collections | 0 | **0%** | Failed |
| English CBD (10 years) | 10 years | 8 years | **80%** | Moderate |
| English CBG (10 years) | 10 years | 1 year | **10%** | Insufficient |
| English THC (10 years) | 10 years | 1 year | **10%** | Insufficient |
| English CBN (10 years) | 10 years | 0 years | **0%** | Failed |
| Apify snapshot (7 keywords) | 7 keywords | 7 keywords | **100%** | Low (small n) |
| CBX 12-months | 12 months | 12 months | **100%** | Moderate |
| CBX リキッド 12-months | 12 months | 12 months | **100%** | **Highest** |

### Language Appropriateness

| Dataset | Keyword Language | Japanese Content | Appropriateness for JP Market |
|---------|:----------------:|:----------------:|:------------------------------:|
| Japanese keywords | Japanese | 0% (failed) | N/A |
| English CBD | English | 11% | **Low** |
| English CBG/THC | English | 0% | **None** |
| Apify snapshot | Mixed | 8.8% | **Low** |
| CBX | English | 0% | **None** (polysemy) |
| CBX リキッド | Japanese-English | 68% | **Moderate-High** |

**Assessment:** Using English keywords with `regionCode=JP` does not filter by language. The YouTube API's `regionCode` parameter affects search ranking but returns content from all languages. Only Japanese keywords or `relevanceLanguage=ja` parameter would capture Japanese content effectively. The CBX リキッド collection demonstrates this with 68% Japanese content.

### Missing Data Documentation

**Strengths:**
- Error responses are preserved in raw data files (429 quota errors)
- Collection logs document success/failure per keyword-year
- Monthly summaries include limitations arrays

**Weaknesses:**
- The collection plan assumed 10,000 units/day quota (actual: 100 units/day)
- 2023 CBD anomaly (61 records vs. 500+) is not explained in research reports
- Japanese keyword failure is not reflected in downstream research documents
- The task description's claimed record counts (2,999 for CBD オイル) do not match actual data

---

## Usability Determination

### What the YouTube Data CAN Support

#### Tier 1: Strongest Claims (CBX リキッド dataset)

| Claim Type | Example | Evidence Level |
|------------|---------|:--------------:|
| Descriptive trend | "YouTube videos mentioning 'CBX リキッド' increased from 5/month (2026-06) to 31/month (2026-09)" | OBSERVED |
| Language distribution | "68% of CBX リキッド YouTube videos (2025-10 to 2026-09) were Japanese-language" | OBSERVED |
| Temporal pattern | "CBX リキッド YouTube content showed a step increase beginning 2026-07" | OBSERVED |

**Claim Discipline:** These are observational claims about YouTube search results. They do not establish market size, consumer behavior, or causal relationships.

#### Tier 2: Moderate Claims (English CBD dataset)

| Claim Type | Example | Evidence Level |
|------------|---------|:--------------:|
| Language distribution | "11% of YouTube videos returned for 'CBD' search (2016-2024) contained Japanese text" | OBSERVED |
| Content availability | "YouTube search results for 'CBD' with regionCode=JP include predominantly English content" | OBSERVED |

**Claim Discipline:** These claims describe YouTube API search behavior, not Japanese cannabinoid content trends.

#### Tier 3: Limited Claims (Other datasets)

| Dataset | Claim Support |
|---------|---------------|
| Apify snapshot | Descriptive counts at single time point |
| CBX (English) | Polysemy demonstration (Honda vs. cannabinoid) |
| CBG/THC/CBN | None (insufficient data) |

### What the YouTube Data CANNOT Support

| Claim Type | Reason |
|------------|--------|
| Japanese cannabinoid video content trends | Japanese keyword collection failed |
| Market-wide content analysis | Search results ≠ market; API caps prevent completeness |
| Causal claims about regulatory events | Temporal correlation ≠ causation |
| Cross-compound comparisons | Unequal data quality across compounds |
| Consumer behavior inference | Video publication ≠ consumption |

---

## Methodological Issues

### 1. API Quota Constraint (Critical)

**Issue:** The YouTube Data API v3 provides 100 search queries per day. The collection plan (`research/20261004-youtube-data-collection-plan.md`) assumed 10,000 units/day, which is incorrect.

**Impact:**
- Japanese keyword collection: 40 queries needed → complete failure
- English CBD: 10 years × (1 + pagination) queries → partial failure in 2023-2025
- CBG/THC/CBN: Multiple years attempted → only 1 year succeeded per keyword

**Evidence:** Error responses in data files show `quota_limit_value: 100` for `defaultSearchListPerDayPerProject`.

**Assessment:** The quota constraint is a fundamental limitation that was not properly accounted for in the collection plan. This is a methodological flaw, not a data quality issue.

---

### 2. Language Filtering Mismatch (Critical)

**Issue:** `regionCode=JP` does not filter by language. English keywords return predominantly English content even with JP region specification.

**Impact:**
- English CBD: 89% non-Japanese content
- English CBG/THC: 100% non-Japanese content
- Cannot represent Japanese cannabinoid content trends

**Evidence:** Language filter analysis (`research/20261004-youtube-language-filter-analysis.md`) correctly identifies this issue and recommends Japanese keyword collection—which then failed due to quota.

**Assessment:** The methodology correctly identified the problem but could not implement the solution due to quota constraints.

---

### 3. Search Result Non-Randomness (Moderate)

**Issue:** YouTube search results are relevance-ranked, not random samples or chronological listings. The API returns the "top" 50 results per query, which are algorithmically determined.

**Impact:**
- Cannot infer total video volume from search result counts
- Results may be biased toward popular, recent, or engagement-optimized content
- Yearly comparisons are confounded by changing YouTube algorithms

**Assessment:** This is an inherent limitation of YouTube search data that should be documented in all analyses. The CBX リキッド monthly counts (all below 50) may represent actual volume, but this cannot be confirmed.

---

### 4. Pagination Duplicates (Moderate)

**Issue:** YouTube search pagination returns overlapping results, creating duplicates.

**Impact:**
- English CBD: 16.2% duplicate rate (3,831 records → 3,211 unique)
- Overstates content volume if not deduplicated

**Assessment:** The language filter analysis correctly identifies unique videoId counts. Deduplication must be applied before any analysis.

---

### 5. Polysemy Problem (Moderate)

**Issue:** "CBX" refers to both Honda motorcycles and cannabinoid products.

**Impact:**
- CBX collection: 57% Honda CBX400F content
- Requires manual filtering or specific queries

**Assessment:** The repository correctly identifies this problem and implements "CBX リキッド" as a specific query. This is good methodological practice.

---

### 6. Temporal Coverage Gaps (Moderate)

**Issue:** Several datasets have incomplete temporal coverage.

**Impact:**
- English CBD: 2023 has 61 records (vs. 500+ other years); 2025 has 0
- CBG: Only 2017; THC: Only 2023
- Japanese keywords: No data

**Assessment:** Temporal gaps prevent longitudinal analysis for most compounds. Only CBD (2016-2022) and CBX リキッド (2025-10 to 2026-09) have sufficient temporal coverage.

---

## Integration Recommendations

### Position in Multi-Source Framework

| Source | What It Measures | Confidence | YouTube Complementarity |
|--------|------------------|:----------:|-------------------------|
| Google Trends | Search interest (relative index 0-100) | MODERATE-HIGH | **Moderate** — different phenomenon (search vs. video publication) |
| X/Twitter | SNS discourse (post counts) | LOW-MODERATE | **Moderate** — platform-specific; both show temporal patterns |
| YouTube | Video content (search results) | **LOW** (except CBX リキッド: MODERATE-HIGH) | **Low** — methodologically limited |
| Regulatory | Legal framework (dates, status) | HIGH | **N/A** — different domain |

### Integration Principles

1. **Do not equate metrics.** YouTube video counts, Google Trends indices, and X post counts measure different phenomena. Cross-source analysis must preserve source-specific units.

2. **Temporal alignment with regulatory events.** The CBX リキッド increase (2026-07 to 2026-09) can be described alongside regulatory timelines, but causal claims require stronger evidence.

3. **Language-specific analysis.** Japanese-language YouTube content should be analyzed separately from English content. The CBX リキッド dataset (68% Japanese) is suitable; English CBD data (11% Japanese) is not.

4. **Triangulation, not substitution.** YouTube data can complement Google Trends and X data when they show consistent temporal patterns. It cannot substitute for them when data quality is insufficient.

### Recommended Integration for v1.9.0

| Integration | Data to Use | Claim Type | Confidence |
|-------------|-------------|------------|:----------:|
| CBX リキッド temporal trend | CBX リキッド 12-months | OBSERVED descriptive | MODERATE-HIGH |
| YouTube language distribution | English CBD + CBX リキッド | OBSERVED descriptive | MODERATE |
| Cross-platform CBX analysis | CBX リキッド (YT) + CBX X data | OBSERVED temporal alignment | MODERATE |

**Excluded from v1.9.0 integration:**
- Japanese keyword data (failed collection)
- English CBG/THC/CBN data (insufficient)
- Cross-compound YouTube comparisons (unequal data quality)

---

## Recommendations

### Immediate Actions (Before v1.9.0 Release)

| Priority | Action | Rationale |
|:--------:|--------|-----------|
| **1** | Correct documentation of Japanese keyword collection failure | Task description claims 2,999 records; actual data shows 0 |
| **2** | Exclude failed collections from release | Japanese keywords, CBN, incomplete CBG/THC |
| **3** | Include CBX リキッド dataset with limitations | Highest quality YouTube data; supports descriptive claims |
| **4** | Document API quota constraint in methodology | 100 queries/day, not 10,000 as planned |
| **5** | Add language distribution analysis | English CBD (11%) vs. CBX リキッド (68%) |

### Future Collection Improvements

| Priority | Improvement | Expected Impact |
|:--------:|-------------|-----------------|
| **1** | Request YouTube API quota increase | Enables Japanese keyword collection |
| **2** | Use `relevanceLanguage=ja` parameter | Filters Japanese content without Japanese keywords |
| **3** | Implement multi-day collection for large datasets | Spreads quota across multiple days |
| **4** | Add content relevance filtering | Reduces polysemy and irrelevant results |
| **5** | Collect view counts and engagement metrics | Enables analysis beyond publication counts |

### Methodology Documentation Updates

| Document | Update Required |
|----------|-----------------|
| `datasets/cannabinoid-multi-trends/methodology.md` | Add YouTube API quota constraint (100/day) |
| `research/20261004-youtube-data-collection-plan.md` | Correct quota assumption (10,000 → 100) |
| `research/20261004-youtube-phase1-report.md` | Correct CBD record counts (actual: 3,831, not 0) |
| `research/20261004-youtube-language-filter-analysis.md` | Update Japanese video counts (423, not 653) |

---

## Suitability for Publication

### v1.9.0 Release Decision

| Dataset | Include? | Conditions |
|---------|:--------:|------------|
| Japanese keywords | **No** | Complete failure; 0 usable records |
| English CBD (10 years) | **Conditional** | With limitations disclosure; exclude 2023-2025 |
| English CBG/THC/CBN | **No** | Insufficient data (50 or 0 records) |
| Apify snapshot | **Optional** | Only as snapshot evidence; not longitudinal |
| CBX 12-months | **Optional** | With polysemy limitation disclosure |
| CBX リキッド 12-months | **Yes** | With methodology and limitations |

### Publication Gate Checklist

| Criterion | Status | Notes |
|-----------|:------:|-------|
| Provenance documented | ✅ | Run IDs, collection timestamps present |
| Methodology documented | ⚠️ | Quota constraint incorrectly stated |
| Data completeness | ❌ | Japanese keywords failed; CBG/THC/CBN insufficient |
| Limitations disclosed | ⚠️ | Partially documented; quota issue missing |
| Reproducibility | ⚠️ | Raw data preserved; collection scripts not fully documented |
| Privacy review | ✅ | Public YouTube data; no PII |
| Conflict of interest | ✅ | Publisher COI disclosed in research framework |

### Overall Assessment

**READY_WITH_MINOR_CHANGES** — The CBX リキッド dataset is publication-ready with proper methodology documentation. Other YouTube datasets should be excluded or included with strong limitations disclosure. The Japanese keyword collection failure must be corrected in documentation before release.

---

## Evidence Confidence Summary

| Dataset | Evidence Confidence | Basis |
|---------|:-------------------:|-------|
| CBX リキッド 12-months | **MODERATE-HIGH** | Specific query, Japanese focus, consistent methodology, transparent limitations |
| English CBD (2016-2022) | **MODERATE** | Substantial data, but language mismatch and non-random sampling |
| English CBD (2023-2025) | **LOW** | Incomplete data due to quota exhaustion |
| Apify snapshot | **LOW-MODERATE** | Valid snapshot, but small sample and limited Japanese content |
| CBX 12-months (English) | **LOW-MODERATE** | Polysemy problem; 50-record API cap |
| Japanese keywords | **N/A** | Complete failure; 0 records |
| English CBG/THC/CBN | **N/A** | Insufficient data (50 or 0 records) |

---

## Claim Discipline Notes

### Strong Evidence (Justified Language)

- "The CBX リキッド YouTube collection contains 125 videos over 12 months" — **demonstrates** (direct observation)
- "68% of CBX リキッド videos were Japanese-language" — **shows** (direct observation)
- "All Japanese keyword collection files contain quota error responses" — **is supported by** (direct inspection)

### Moderate Evidence (Appropriate Hedging)

- "CBX リキッド YouTube content **suggests** an increase beginning 2026-07" — temporal pattern, not causal
- "English keywords **are associated with** predominantly non-Japanese content" — API behavior, not market analysis
- "YouTube search results **support a possible** descriptive trend for CBX リキッド" — limited to search results

### Preliminary Evidence (Appropriate Qualification)

- "**Preliminary data suggests** CBX リキッド content increased in mid-2026" — small sample, observational
- "**Has been observed in** YouTube search results that English keywords return mostly English content" — API behavior observation

### Claims to Avoid

- ❌ "Japanese cannabinoid video content increased" — Japanese keyword collection failed
- ❌ "CBG/THC/CBN have low YouTube presence in Japan" — insufficient data; English keywords not valid for JP market
- ❌ "Regulatory events caused YouTube content changes" — temporal correlation ≠ causation
- ❌ "YouTube data demonstrates market trends" — search results ≠ market

---

## Research Log

```yaml
review_date: 2026-10-05
reviewer: Academic Research Agent

sources_reviewed:
  japanese_keyword_collection: 20261004T144147Z-youtube-japanese-keywords-10years
  english_cbd_10years: 20261004T142147Z-youtube-cbd-10years
  english_cbg_10years: 20261004T142430Z-youtube-cbg-10years
  english_thc_10years: 20261004T142508Z-youtube-thc-10years
  english_cbn_10years: 20261004T142547Z-youtube-cbn-10years
  apify_snapshot: 20261002T064*Z-youtube-*
  cbx_12months: 20261004T135232Z-youtube-cbx-12months
  cbx_rikiddo_12months: 20261004T135457Z-youtube-cbx-rikiddo-12months

research_documents_reviewed:
  - research/20261004-youtube-data-collection-plan.md
  - research/20261004-youtube-phase1-report.md
  - research/20261004-youtube-language-filter-analysis.md
  - research/20261004-cbx-youtube-12months-report.md
  - research/20261004-cbx-rikiddo-youtube-12months-report.md
  - datasets/cannabinoid-multi-trends/methodology.md
  - datasets/cannabinoid-multi-trends/data/processed/collection-summary.md
  - datasets/cannabinoid-multi-trends/data/processed/early-warning-index-v1.csv

data_inspection:
  japanese_keywords: 40 files, all quota errors (429)
  english_cbd: 3831 records, 3211 unique, 423 Japanese (11%)
  english_cbg: 50 records (2017 only), 0 Japanese
  english_thc: 50 records (2023 only), 0 Japanese
  english_cbn: 0 records (failed)
  apify_snapshot: 182 records, 16 Japanese (8.8%)
  cbx_12months: 600 records, 232 CBX-related, 57% Honda excluded
  cbx_rikiddo_12months: 125 records, 85 Japanese (68%)

key_findings:
  - Japanese keyword collection failed completely (quota exhaustion)
  - English keyword collections have low Japanese representation (0-11%)
  - CBX リキッド is the most research-usable YouTube dataset
  - API quota constraint (100/day) was not properly planned for
  - YouTube search results are not random samples

publication_decision: READY_WITH_MINOR_CHANGES
  - Include CBX リキッド dataset with limitations
  - Exclude failed/insufficient collections
  - Correct documentation of quota constraint and record counts
```

---

## References

### Data Sources

1. YouTube Data API v3 search results — `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T144147Z-youtube-japanese-keywords-10years/` (FAILED — quota errors)
2. YouTube Data API v3 search results — `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142147Z-youtube-cbd-10years/` (PARTIAL — 3,831 records)
3. YouTube Data API v3 search results — `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142430Z-youtube-cbg-10years/` (INSUFFICIENT — 50 records)
4. YouTube Data API v3 search results — `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142508Z-youtube-thc-10years/` (INSUFFICIENT — 50 records)
5. YouTube Data API v3 search results — `datasets/cannabinoid-multi-trends/data/raw/youtube/20261004T142547Z-youtube-cbn-10years/` (FAILED — 0 records)
6. Apify Actor `gJvjeCYNraSfhIaNd` — `datasets/cannabinoid-multi-trends/data/raw/youtube/20261002T064*Z-youtube-*/` (SNAPSHOT — 182 records)
7. YouTube Data API v3 search results — `datasets/cbx-social-trends/data/raw/youtube/20261004T135232Z-youtube-cbx-12months/` (MODERATE — 600 records)
8. YouTube Data API v3 search results — `datasets/cbx-social-trends/data/raw/youtube/20261004T135457Z-youtube-cbx-rikiddo-12months/` (**HIGHEST QUALITY** — 125 records)

### Research Documents

9. YouTube データ収集計画書 — `research/20261004-youtube-data-collection-plan.md`
10. YouTube データ収集レポート（フェーズ1） — `research/20261004-youtube-phase1-report.md`
11. YouTube データ 言語フィルタ付き再分析 — `research/20261004-youtube-language-filter-analysis.md`
12. CBX YouTube データ収集レポート（12ヶ月） — `research/20261004-cbx-youtube-12months-report.md`
13. CBX リキッド YouTube データ収集レポート（12ヶ月） — `research/20261004-cbx-rikiddo-youtube-12months-report.md`
14. Methodology — `datasets/cannabinoid-multi-trends/methodology.md`
15. Collection Summary — `datasets/cannabinoid-multi-trends/data/processed/collection-summary.md`
16. Early Warning Index v1 — `datasets/cannabinoid-multi-trends/data/processed/early-warning-index-v1.csv`

---

*This review was conducted by the Academic Research Agent on 2026-10-05. All data file inspections were performed directly on the repository contents. No unavailable metadata was invented. Citation counts were not treated as evidence quality.*
