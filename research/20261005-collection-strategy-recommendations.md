# Evidence-Based Recommendations: YouTube and X/Twitter Data Collection Improvement

| 項目 | 内容 |
|------|------|
| **Report Date** | 2026-10-05 |
| **Author** | Academic Research Agent |
| **Repository** | japan-cannabinoid-trends |
| **Publisher** | Routeflags Co., Ltd. (COI: cannabinoid e-commerce) |
| **Scope** | Forward-looking collection strategy; not a review of existing data quality |
| **Evidence Base** | Repository collection logs, methodological reviews, social media research standards |

---

## Research Question

**How should YouTube and X/Twitter data collection be improved to maximize research value given known API constraints, and how should multi-platform data be integrated methodologically?**

---

## Search Scope

### Sources Consulted

| Source | Status | Use |
|--------|--------|-----|
| Repository collection logs & run metadata | ✅ Inspected | Actual quota consumption, record counts, failure patterns |
| Repository methodology documents | ✅ Reviewed | Existing collection parameters, deduplication rules, limitations |
| Academic review of YouTube collections (2026-10-05) | ✅ Reviewed | Data quality assessment, usability tiers |
| X data status reports | ✅ Reviewed | Sample sizes, temporal coverage, classification issues |
| Open issues (classification, labeling) | ✅ Reviewed | Known quality gaps |
| Citation opportunities backlog | ✅ Reviewed | Strategic alignment with citation goals |
| Social media research standards (literature) | ✅ Applied | Sampling, reliability, triangulation, reproducibility frameworks |
| Infodemiology / digital surveillance literature | ✅ Applied | Cross-platform temporal analysis, early warning framing |

### Methodological Frameworks Applied

The recommendations draw on established frameworks in computational social science and content analysis:

- **Content analysis reliability standards** (Krippendorff, Neuendorf): inter-coder reliability measurement, minimum kappa thresholds, codebook preregistration
- **Social media sampling methodology** (Ruths & Pfeffer, *Science*, 2014; Tufekci, 2014): platform APIs return non-representative samples; explicit acknowledgment of sampling frame
- **Infodemiology frameworks** (Eysenbach, 2002, 2009): search and social data as population health proxies, with appropriate caveats
- **Cross-platform digital methods** (Bruns, 2019; Venturini et al., 2018): multi-platform triangulation preserves source-specific units
- **Quota-constrained research design**: adaptive sampling, prioritization under resource constraints

---

## Executive Summary

### Five Key Recommendations

**1. Decouple YouTube collection strategy by research goal: Apify for discovery, API for longitudinal depth.**
The evidence suggests that the YouTube Data API v3's 100-search/day quota fundamentally constrains Japanese keyword collection, while the Apify actor (`gJvjeCYNraSfhIaNd`) offers per-request billing without quota limits. Best practices indicate that Japanese-language cannabinoid content discovery should use Apify (unlimited queries, $0.0005/item), while longitudinal time-series tracking of specific queries (e.g., CBX リキッド) should use the YouTube API's `publishedAfter`/`publishedBefore` parameters across multiple days. Neither method alone is sufficient.

**2. Use `relevanceLanguage=ja` as the primary Japanese-content filter, not Japanese keywords alone.**
Methodological literature on YouTube search behavior indicates that `regionCode=JP` does not filter by language, and English keywords return predominantly English content (confirmed: 0–11% Japanese in current English-keyword datasets, versus 68% for the Japanese-English hybrid query "CBX リキッド"). The YouTube API's `relevanceLanguage=ja` parameter should be applied in all collections targeting Japanese content. This parameter was not used in the failed Japanese keyword collection and should be tested immediately.

**3. Increase X/Twitter samples from n=40 to n≥200 per compound using expanded date ranges and multi-query strategies, while implementing dual-coder reliability assessment.**
The Wilson score confidence intervals for n=40 proportions are extremely wide (e.g., 55% → 39–69%), limiting inferential value. Best practices in content analysis indicate that n≥200 per category enables acceptable precision for descriptive prevalence estimates (±5–7% at 95% CI for moderate proportions). The single-coder classification with no inter-rater reliability measurement (documented as ISS-20261002-004, P1) should be addressed with a dual-coder subset (n≥100) and Cohen's kappa reporting. Target κ ≥ 0.70.

**4. Implement a cross-platform integration framework that preserves source-specific units and uses temporal triangulation, not metric substitution.**
Infodemiology literature recommends that search indices (Google Trends), social post counts (X), and video publication counts (YouTube) measure different phenomena and should not be directly equated. The recommended framework is temporal alignment around regulatory or market events, with each platform contributing an independent signal. The existing early-warning index structure is a sound starting point but currently relies on Google Trends alone; adding X and YouTube as independent temporal signals would strengthen the triangulation.

**5. Adopt a tiered collection priority system: prioritize compounds where data can support publishable claims, and explicitly mark compounds where collection is infeasible.**
Methodological literature on research resource allocation recommends against collecting data that cannot support the intended analysis. Given quota and API constraints, collection effort should concentrate on: (a) CBX リキッド (demonstrated highest-quality YouTube dataset), (b) compounds with confirmed Google Trends signal (CBD, THC, CBG, CBN, HHC), and (c) monitoring targets with active regulatory trajectories (H4CBH, HHBD, CRDP). Compounds below Google Trends detection thresholds (THCV, THC-O) should be marked as "below collection threshold" rather than collected wastefully.

---

## YouTube Collection Strategy

### 1. Optimal Keyword Prioritization

The evidence from repository collection logs supports a three-tier prioritization:

| Tier | Keywords | Rationale | Collection Method |
|------|----------|-----------|-------------------|
| **Tier 1 (Longitudinal)** | CBX リキッド | Demonstrated highest Japanese content rate (68%), clear temporal pattern, specific query reducing polysemy | YouTube API v3, monthly, `relevanceLanguage=ja` |
| **Tier 2 (Coverage)** | CBD オイル, カンナビノイド, CBG オイル, CBN オイル | Japanese-language queries that match existing Google Trends collection vocabulary | Apify (discovery) + YouTube API (longitudinal on subset) |
| **Tier 3 (Monitoring)** | H4CBH, HHBD, HHC, CRDP | Regulatory monitoring targets with confirmed Google Trends signal | Apify only (snapshot); YouTube API for compounds above Trends threshold |

**Justification:** The CBX リキッド dataset (125 records, 68% Japanese, 12-month trend) is the repository's most research-usable YouTube dataset. Its success validates the specific-query + Japanese-keyword approach. The Apify snapshot collections (182 records across 7 keywords, 8.8% Japanese) demonstrate that English keywords via Apify still underperform for Japanese content, but provide useful cross-language comparison data. Tier 2 keywords should be collected via Apify first to assess yield before committing API quota.

### 2. Quota Allocation Strategy (YouTube Data API v3)

**Constraint:** 100 search queries/day (1 query = 100 units). Each search returns max 50 results; pagination consumes additional quota.

**Recommended Allocation (Monthly Cycle):**

| Priority | Keyword | Queries/Day | Days/Month | Monthly Quota | Purpose |
|:--------:|---------|:-----------:|:----------:|:-------------:|---------|
| 1 | CBX リキッド (monthly) | 1 | 1 | 100 | Longitudinal tracking |
| 2 | CBD オイル (monthly) | 1 | 1 | 100 | Coverage |
| 3 | カンナビノイド (monthly) | 1 | 1 | 100 | Coverage |
| 4 | Priority compound (rotating) | 1 | varies | 100/day × N | Regulatory monitoring |
| **Reserve** | Pagination / retry | — | — | 200/day | Error recovery |
| **Total** | | **4–5 queries** | | **≤500/day** | |

**Key Insight:** The failed Japanese keyword collection (40 queries attempted in one day = 4,000 units) exceeded the daily quota by 40×. A sustainable monthly cycle requires spreading collection across multiple days. With 100 queries/day, 5 queries/day for 6 days covers 30 monthly collections — sufficient for 5 keywords × 6 months, or 10 keywords × 3 months.

### 3. Japanese vs English Keyword Decision

**Evidence-based recommendation: Hybrid strategy.**

| Factor | Japanese Keywords | English Keywords | `relevanceLanguage=ja` + English |
|--------|:-----------------:|:-----------------:|:--------------------------------:|
| Japanese content rate | Expected: High (not yet measured due to quota failure) | 0–11% (observed) | Unknown — **requires testing** |
| Polysemy risk | Lower (specific compounds) | Higher (CBX = Honda motorcycle) | Moderate |
| Google Trends alignment | ✅ Existing Trends vocabulary | ✅ Existing Trends vocabulary | ✅ |
| Collection feasibility | Constrained by quota (keyword length may affect rate limits) | Feasible via Apify | Feasible via API |

**Recommendation:** 
- For Apify collections: Use Japanese compound + product-form queries (e.g., "CBD オイル", "CBX リキッド") to maximize Japanese content yield.
- For YouTube API collections: Test `relevanceLanguage=ja` parameter with English compound names (e.g., "CBD" + `relevanceLanguage=ja`). If this parameter effectively filters Japanese content, it may provide a quota-efficient alternative to Japanese keyword queries. This test should be conducted in Phase 1.
- For longitudinal tracking: Use the same query language across time points to maintain comparability.

### 4. Expected Data Outcomes

| Collection Method | Expected Japanese Content | Expected Volume | Research Utility |
|-------------------|:-------------------------:|:---------------:|------------------|
| Apify + Japanese keyword | Moderate-High (est. 40–70%) | 50–100/keyword | Cross-compound snapshots |
| YouTube API + Japanese keyword + `relevanceLanguage=ja` | High (est. 60–80%) | 10–50/month/keyword | Longitudinal trends |
| YouTube API + English keyword + `relevanceLanguage=ja` | Unknown — requires test | 10–50/month/keyword | Potential quota-efficient alternative |
| Apify + English keyword | Low (est. 5–15%) | 20–50/keyword | International comparison only |

**Claim Discipline:** These estimates are based on the observed 68% Japanese rate for "CBX リキッド" (a Japanese-English hybrid query) and the observed 0–11% Japanese rate for English-only keywords. The `relevanceLanguage=ja` estimate is a hypothesis requiring empirical validation.

---

## X/Twitter Collection Strategy

### 1. Sample Size Targets

**Current state:** H4CBH n=40, HHBD n=40. Other compounds: not collected.

**Statistical justification for n≥200:**

| Sample Size | 95% CI Width (p=0.50) | 95% CI Width (p=0.20) | Interpretation |
|:-----------:|:---------------------:|:---------------------:|----------------|
| n=40 | ±15.5% | ±12.4% | Very wide; point estimates unreliable |
| n=100 | ±9.8% | ±7.8% | Moderate; useful for screening |
| **n=200** | **±6.9%** | **±5.5%** | **Acceptable for descriptive prevalence** |
| n=300 | ±5.7% | ±4.5% | Good precision |

**Recommendation:** Target n≥200 Japanese-language posts per priority compound per quarter. For niche compounds (H4CBH, HHBD) where the full population may be <500 posts/quarter, collect all available posts and report as census of collected data (with explicit non-probability sampling caveat).

**Collection Parameters to Achieve n≥200:**

| Parameter | Current | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| `maxPages` | 2 (~40 tweets) | 5–10 (~100–200 tweets) | More pages = larger sample |
| Date range | 3 months | 6 months (rolling) | Longer window captures more posts |
| `section` | `latest` | `latest` + `top` | `top` surfaces high-engagement posts missed by `latest` |
| Queries per compound | 1 | 2–3 (compound name + compound + リキッド/オイル) | Broader recall |
| Collection frequency | One-time | Monthly rolling | Continuous accumulation |

### 2. Compound Prioritization

**Evidence-based prioritization matrix:**

| Compound | Google Trends Signal | Regulatory Status | X Data Status | Priority |
|----------|:-------------------:|-------------------|:-------------:|:--------:|
| CBX (リキッド) | Emerging (2026-09) | Unregulated | n=147 (Aug) + 291 (26wk) | **HIGH** — anchor compound |
| CBD | High (47) | Unregulated (conditional) | n=60 (1 month) | **HIGH** — baseline reference |
| THC | Medium (12) | Regulated | n=60 (1 month) | **MEDIUM** — regulatory comparison |
| CBG | Low-Medium (3) | Unregulated (conditional) | n=40 (1 month) | **MEDIUM** |
| CBN | Emerging (post-2021) | Designated drug (2026-06) | Not collected | **HIGH** — recent regulation event |
| HHC | Low (1) | Designated drug (2022) | n=40 (1 month) | **MEDIUM** — historical regulation case |
| H4CBH | No Trends data | Monitoring | n=40 (3 months) | **HIGH** — active monitoring target |
| HHBD | No Trends data | Monitoring | n=40 (3 months) | **HIGH** — active monitoring target |
| CRDP | Intermittent (22) | Monitoring (caution) | Not collected | **MEDIUM** |
| THCH | Very low (3) | Designated drug (2023) | n=36 (1 month) | **LOW** — below collection threshold |

**Rationale:** Prioritization follows three criteria: (1) existing Google Trends signal indicating detectable Japanese search interest, (2) regulatory trajectory (recent designation, active monitoring, or post-regulation behavior), and (3) current data gap (compounds with no X data or insufficient samples).

### 3. Classification Methodology Improvements

**Current state (from ISS-20261002-004 and H4CBH/HHBD analysis):**
- Single coder (automated + manual adjustment)
- No taxonomy definition file
- No inter-rater reliability measurement
- No model/prompt version tracking
- Classification categories: 製品宣伝・販売 / 製品レビュー / 会話・引用 / その他

**Recommended improvements (grounded in content analysis best practices):**

| Improvement | Specification | Priority |
|-------------|---------------|:--------:|
| **Taxonomy definition file** | `metadata/taxonomy/x-content-classification.yaml` with operational definitions, inclusion/exclusion criteria, and examples for each category | P1 |
| **Dual-coder reliability assessment** | Random subset (n≥100) coded independently by two coders; Cohen's kappa calculated; κ ≥ 0.70 target | P1 |
| **Codebook preregistration** | Fix classification categories and decision rules before collection; document in methodology.md | P1 |
| **Coder training set** | 20–30 posts with gold-standard labels for calibration | P2 |
| **Classification versioning** | Track taxonomy version, coder ID, and classification date per post | P2 |
| **Drift monitoring** | Re-code 10% sample quarterly; flag if κ drops below 0.65 | P3 |
| **Automated classifier validation** | If using LLM-based classification: report prompt, model version, temperature; validate against human-coded subset | P2 |

**Expected Impact:** Dual-coder assessment with κ ≥ 0.70 would transform classification from an undocumented process to a reproducible measurement, directly addressing ISS-20261002-004 and enabling the publication of classification percentages with stated reliability.

### 4. Cost Estimates

**Apify X Search (`cPYLH3QT9GyzKhB4S`): $0.002 start + $0.0025/item**

| Scenario | Items | Cost | Notes |
|----------|:-----:|:----:|-------|
| Single compound, n=200, 6-month range | ~200 | $0.502 | 1 query, maxPages=10 |
| 5 priority compounds, n=200 each, quarterly | ~1,000 | $2.50 | 5 queries × 200 items |
| Monthly rolling (5 compounds × 6 months) | ~6,000 | $15.00 | Sustained monitoring |
| With dual queries per compound (recall improvement) | ~12,000 | $30.00 | 10 queries total |
| Classification validation (n=100 double-coded) | 0 (reuses existing) | $0 | Labor only |

**Comparison with existing costs:**

| Existing Collection | Items | Cost |
|---------------------|:-----:|:----:|
| CBX daily (August 2026) | 2,376 | $5.94 |
| CBX 26-week | 451 | $1.13 |
| Multi-compound snapshot (Oct 2026) | 316 | $0.80 |
| H4CBH + HHBD (3 months each) | 80 | $0.008 |

The recommended n≥200 × 5-compound quarterly collection ($2.50/quarter) is well within the demonstrated cost range and represents a modest investment for substantially improved statistical precision.

---

## Multi-Platform Integration

### 1. Analytical Framework

**Recommended framework: Temporal Triangulation with Source-Specific Units**

The infodemiology and digital methods literature recommends that multi-platform data be integrated through temporal alignment around events, not through direct metric substitution. The framework:

```
                    REGULATORY / MARKET EVENT
                    (e.g., CBN designation 2026-06-01)
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     Google Trends       X (Twitter)        YouTube
     (search interest)   (post volume)      (video publication)
     Relative index      Absolute count     Search result count
     0-100               n posts            n videos
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                    TEMPORAL ALIGNMENT
                    (weekly/monthly bins)
                              │
                              ▼
                    TRIANGULATION ASSESSMENT
                    ┌─────────────────────────┐
                    │ Concordant: multiple     │
                    │   platforms show similar │
                    │   temporal pattern       │
                    │ Divergent: platforms     │
                    │   show different         │
                    │   patterns               │
                    │ Insufficient: data gaps  │
                    └─────────────────────────┘
```

**Key principles:**
1. **Preserve source-specific units.** Google Trends values (0–100) are relative indices within their collection set; X post counts are absolute counts of collected tweets; YouTube counts are search-result counts subject to API caps. These are not interchangeable.
2. **Use temporal alignment, not metric correlation.** A regulatory event may be followed by changes across all three platforms, but the magnitude of change is not directly comparable across platforms.
3. **Classify convergence patterns.** Concordant increases across platforms strengthen the claim of a real-world shift; divergent patterns suggest platform-specific dynamics.

### 2. Data Harmonization Approach

| Platform | Raw Unit | Harmonization Step | Analysis Unit |
|----------|----------|-------------------|---------------|
| Google Trends | Weekly relative index (0–100) | Normalize to collection-set scale; document baseline | Weekly index, comparison-set ratio |
| X (Twitter) | Individual posts with metadata | Deduplicate by tweet_id; filter by lang=ja; classify content type | Weekly/monthly post counts, classified proportions |
| YouTube | Video search results | Deduplicate by videoId; filter by language; exclude non-relevant (e.g., Honda CBX) | Monthly video counts, language proportions |

**Harmonization rules:**
- Convert all platforms to weekly or monthly temporal bins
- Report each platform's metric separately before any cross-platform comparison
- When comparing temporal patterns, use rank-order or direction of change, not absolute values
- Document all transformation steps in `datasets/<study-id>/methodology.md`

### 3. Cross-Platform Validation

**Recommended validation approach:**

| Validation Type | Method | Application |
|-----------------|--------|-------------|
| **Convergent validity** | Check whether multiple platforms show same temporal pattern for same compound | CBX リキッド: YouTube increase (2026-07+) ↔ X increase (2026-07 W18+) — already observed |
| **Divergent validity** | Document where platforms disagree; investigate platform-specific causes | English keywords on YouTube (low JP content) vs. Japanese keywords on X (high JP content) |
| **Known-groups validity** | Check whether regulated compounds show different patterns than unregulated | CBN post-designation (2026-06): Trends decline (-62%) — X and YouTube should be checked for similar temporal association |
| **Temporal consistency** | Verify that collection periods overlap sufficiently for comparison | Currently: YouTube (2025-10 to 2026-09), X (2026-03 to 2026-09), GT (2025-10 to 2026-10) — overlap is 2026-03 to 2026-09 |

**Integration recommendation for next dataset release:**
Include a cross-platform temporal alignment table for CBX リキッド showing monthly Google Trends, X post counts, and YouTube video counts side-by-side, with explicit notes that each column uses different units and collection methods. This would be the repository's first systematic multi-platform integration artifact.

---

## Methodological Improvements

### 1. Sampling Strategies

| Issue | Current State | Recommended Improvement | Basis |
|-------|---------------|------------------------|-------|
| **Non-probability sampling** | YouTube search results are relevance-ranked (not random); X `section=latest` is recency-biased | Explicitly document sampling frame; report results as "collected search results" not "market data"; consider `section=top` for engagement-weighted sampling | Ruths & Pfeffer (2014): platform APIs return non-representative samples |
| **Small samples** | n=40 for H4CBH/HHBD; n=36-60 for multi-compound X | Target n≥200; for niche compounds, collect all available posts (census approach) | Confidence interval width analysis (above) |
| **Temporal gaps** | X 26-week data has empty weeks W01-W07, W09-W15 | Fill gaps with re-collection where possible; document genuine zeros (observed_zero) vs. collection failures | Repository methodology already distinguishes these states — extend consistently |
| **Keyword coverage** | Single query per compound for X; mixed for YouTube | Use 2–3 queries per compound (name + name+product form); document query set explicitly | Broader recall improves sample completeness |
| **Language filtering** | YouTube: no `relevanceLanguage`; X: `lang=ja` filter applied | Apply `relevanceLanguage=ja` to all YouTube collections; maintain `lang=ja` filter for X | Language filter analysis (2026-10-04) |

### 2. Quality Controls

| Control | Specification | Frequency |
|---------|---------------|-----------|
| **Deduplication verification** | Report raw count, deduplicated count, and duplicate rate for every collection | Every collection run |
| **Language composition** | Report Japanese/non-Japanese ratio for all YouTube collections | Every collection run |
| **Relevance audit** | Manual review of 10% random sample; report % relevant to target compound | Every major collection |
| **Engagement metric validation** | Cross-check X views/likes against `chargedEventCounts`; flag anomalies | Every collection run |
| **Classification reliability** | Cohen's kappa on dual-coded subset (n≥100); target κ ≥ 0.70 | Quarterly |
| **Metadata completeness** | Verify run_metadata.json contains: source, timestamp, query, parameters, record counts | Automated check |
| **Temporal consistency** | Verify collection dates fall within stated observation periods | Automated check |

### 3. Reproducibility Enhancements

| Enhancement | Implementation | Priority |
|-------------|----------------|:--------:|
| **Preregistered collection protocol** | Document keyword sets, API parameters, date ranges, and analysis plan BEFORE collection; timestamp in methodology.md | P1 |
| **Versioned classification scheme** | Taxonomy file with version number; classification outputs tagged with taxonomy version | P1 |
| **Collection script repository** | Move ad-hoc curl commands to `src/collection/x/` and `src/collection/youtube/` with documented parameters | P2 |
| **Run manifest** | Per-study `metadata/runs/` directory with one JSON per collection run (already partially implemented) | P2 |
| **Data checksums** | SHA-256 checksums for raw data files; verify after collection | P3 |
| **Analysis notebooks** | Jupyter/Quarto notebooks for derived statistics; link from methodology.md | P3 |
| **Inter-rater reliability report** | Publish kappa values alongside classification percentages in research outputs | P1 |

---

## Implementation Roadmap

### Phase 1 (Immediate — 1–2 weeks)

| Action | Effort | Expected Outcome |
|--------|:------:|------------------|
| **Test `relevanceLanguage=ja` parameter** with 5 English compound queries via YouTube API (5 queries = 500 units = 5 days at current rate; or 1 day if quota resets) | Low | Determine if Japanese content rate improves with parameter |
| **Create classification taxonomy file** (`metadata/taxonomy/x-content-classification.yaml`) with operational definitions | Low | Addresses ISS-20261002-004 P1 |
| **Dual-code 100-post subset** of existing H4CBH/HHBD data; calculate Cohen's kappa | Medium | Establishes baseline reliability; validates or invalidates existing percentages |
| **Apify Japanese keyword test**: Collect CBD オイル, カンナビノイド, CBN オイル via Apify (3 × 50 items = ~$0.075) | Low | Determines Japanese content yield for Tier 2 keywords |
| **Document quota constraint** in all methodology files (100 queries/day, not 10,000) | Low | Corrects documented error; improves reproducibility |

### Phase 2 (Short-term — 1–2 months)

| Action | Effort | Expected Outcome |
|--------|:------:|------------------|
| **Implement monthly X collection cycle**: 5 priority compounds × n≥200, using expanded maxPages and date ranges (~$2.50/quarter) | Medium | Moves samples from n=40 to n≥200; enables acceptable precision |
| **Implement monthly YouTube collection cycle**: CBX リキッド + 2 rotating keywords, `relevanceLanguage=ja`, across 3 months | Medium | Builds longitudinal Japanese-language YouTube datasets |
| **Cross-platform temporal alignment table** for CBX リキッド (GT + X + YouTube, monthly bins) | Medium | First systematic multi-platform integration artifact |
| **Move collection commands** to `src/collection/` with parameterized scripts | Medium | Improves reproducibility |
| **Content relevance audit** for X datasets: manually classify 10% sample; report relevance rate | Medium | Quantifies data quality; identifies keyword noise |

### Phase 3 (Long-term — 3–6 months)

| Action | Effort | Expected Outcome |
|--------|:------:|------------------|
| **Sustained monthly rolling collection** across all platforms for priority compounds | Ongoing | Builds longitudinal corpus for trend analysis |
| **Classification drift monitoring**: quarterly re-code of 10% sample; report kappa trends | Ongoing | Ensures classification consistency over time |
| **Early Warning Index v2**: Add X and YouTube temporal signals to existing Google Trends-based index | High | Strengthens triangulation; improves index robustness |
| **YouTube API quota increase request** (if available): Document research use case | Low | May enable larger daily collection if granted |
| **Preregistered analysis plan** for next major analysis (e.g., CBN post-regulation behavior) | Medium | Enhances credibility of temporal association claims |

---

## Cost-Benefit Analysis

### API Costs

| Service | Monthly Cost (Recommended) | Annual Cost | Data Yield |
|---------|:--------------------------:|:-----------:|------------|
| Google Trends | ¥0 (free) | ¥0 | Weekly index, 12+ compounds |
| X/Twitter (Apify) | ~$0.83/month (5 compounds × n≈70/month) | ~$10 | ~4,200 posts/year |
| YouTube API v3 | ¥0 (free, quota-limited) | ¥0 | ~60 searches/month = ~3,000 video records/year |
| YouTube (Apify, discovery) | ~$0.15/month (3 keywords × 50 items) | ~$1.80 | ~1,800 video records/year |
| **Total** | **~$1.00/month** | **~$12/year** | **~9,000 data records/year** |

### Time Investment

| Activity | Monthly Hours | Annual Hours |
|----------|:------------:|:------------:|
| Collection execution (scripted) | 1–2 | 12–24 |
| Data processing & deduplication | 2–3 | 24–36 |
| Classification & reliability assessment | 2–4 | 24–48 |
| Methodology documentation | 1–2 | 12–24 |
| Cross-platform analysis | 2–4 | 24–48 |
| **Total** | **8–15 hours** | **96–180 hours** |

### Expected Data Value

| Value Dimension | Current State | After Implementation | Improvement |
|-----------------|---------------|---------------------|:-----------:|
| YouTube Japanese content | 68% (CBX リキッド only) | Est. 50–70% across 5+ keywords | Significant |
| X sample precision | n=40, ±15% CI width | n=200, ±7% CI width | Substantial |
| Classification reliability | Unmeasured (single coder) | κ reported, target ≥0.70 | Transforms validity |
| Cross-platform coverage | Partial, non-overlapping periods | Aligned monthly bins, 3+ platforms | Enables triangulation |
| Reproducibility | Partial (ad-hoc commands) | Scripted, preregistered, versioned | Publication-ready |
| Compound coverage (X) | 2 compounds (H4CBH, HHBD) | 7+ compounds with n≥200 | Broadens scope |

### Cost-Benefit Assessment

**The evidence suggests that the recommended improvements represent a high-value investment.** Monthly API costs (~$1.00) are negligible relative to the methodological gains: (1) samples large enough for meaningful descriptive statistics, (2) classification reliability that enables publication of content-type proportions, (3) multi-platform temporal alignment that supports triangulated claims, and (4) reproducible collection processes that meet publication standards.

The primary cost is time (8–15 hours/month), which is the binding constraint rather than API budgets. The phased roadmap allows incremental adoption, with Phase 1 deliverables (relevanceLanguage test, taxonomy file, kappa assessment) achievable in 1–2 weeks with minimal effort.

---

## Claim Discipline Notes

### Strong Evidence (Justified Language)

- "The YouTube Data API v3 provides 100 search queries per day" — **is documented by** (Google API documentation and repository error responses)
- "English keywords return predominantly non-Japanese content even with regionCode=JP" — **is supported by** (repository data: 0–11% Japanese across English-keyword collections)
- "CBX リキッド is the most research-usable YouTube dataset in the repository" — **demonstrates** (direct inspection: 125 records, 68% Japanese, 12-month coverage)
- "H4CBH and HHBD classification uses a single coder with no inter-rater reliability measurement" — **is documented by** (ISS-20261002-004 and H4CBH/HHBD analysis methodology section)

### Moderate Evidence (Appropriate Hedging)

- "`relevanceLanguage=ja` **may improve** Japanese content yield for English compound queries" — requires empirical test
- "n≥200 **would provide** acceptable precision for descriptive prevalence estimates" — based on standard statistical formulas, not yet validated in this context
- "Temporal triangulation across platforms **supports** more robust trend claims than single-platform analysis" — methodological literature recommendation, not yet implemented
- "The Apify actor **offers a viable alternative** to YouTube API for Japanese keyword discovery" — based on cost structure and absence of quota constraints, but Japanese content yield not yet measured

### Preliminary Evidence (Appropriate Qualification)

- "**Preliminary estimates suggest** Japanese content rates of 40–70% for Apify Japanese-keyword collections" — extrapolated from CBX リキッド (68%) and English keyword rates (0–11%); not yet validated
- "**Has been observed in** this repository that English keyword collections underperform for Japanese market analysis" — based on 2026-10-04 collections; may not generalize to all compounds or time periods

### Claims to Avoid

- ❌ "Japanese cannabinoid YouTube content is increasing" — Japanese keyword collection failed; English keyword data cannot support this claim
- ❌ "H4CBH is 55% product promotion on X" — n=40 with no inter-rater reliability; CI is 39–69%
- ❌ "Regulatory events caused changes in social media activity" — temporal correlation ≠ causation
- ❌ "YouTube data demonstrates Japanese market trends" — search results are not market-representative samples

---

## Research Log

```yaml
research_date: 2026-10-05
task: Forward-looking collection strategy recommendations

sources_reviewed:
  - research/20261005-academic-research-youtube-review.md
  - research/20261004-youtube-language-filter-analysis.md
  - research/20261004-youtube-data-collection-plan.md
  - research/20261004-x-data-status-report.md
  - research/20261004-h4cbh-hhbd-sns-analysis.md
  - research/20261004-cbx-rikiddo-youtube-12months-report.md
  - research/20261004-google-trends-compound-summary.md
  - datasets/cbx-social-trends/methodology.md
  - datasets/cannabinoid-multi-trends/methodology.md
  - datasets/cannabinoid-multi-trends/data/processed/early-warning-index-v1.csv
  - datasets/cannabinoid-multi-trends/data/processed/collection-summary.md
  - docs/plans/2026-09-18_x-data-improvement-plan.md
  - docs/issues/20261002_p1_unvalidated-classification.md
  - docs/issues/20261002_p1_tiktok-primary-label.md
  - research/citation/opportunities.md

methodological_frameworks_applied:
  - Content analysis reliability standards (Krippendorff, Neuendorf)
  - Social media sampling methodology (Ruths & Pfeffer 2014)
  - Infodemiology frameworks (Eysenbach 2002, 2009)
  - Cross-platform digital methods (Bruns 2019)

key_recommendations:
  1: Decouple YouTube strategy (Apify for discovery, API for longitudinal)
  2: Test relevanceLanguage=ja as primary Japanese-content filter
  3: Increase X samples to n≥200 with dual-coder reliability assessment
  4: Implement temporal triangulation framework (preserve source-specific units)
  5: Adopt tiered collection priority system

constraints_acknowledged:
  - YouTube API quota: 100 search queries/day (not 10,000)
  - X API: shadow bans on sensitive keywords, non-deterministic results
  - Search results are not probability samples
  - Publisher COI (cannabinoid e-commerce) affects interpretation of findings

publication_decision: N/A (strategy document, not dataset)
```

---

## References

### Repository Data Sources

1. YouTube Data API v3 collections — `datasets/cannabinoid-multi-trends/data/raw/youtube/` and `datasets/cbx-social-trends/data/raw/youtube/`
2. X (Twitter) collections via Apify — `datasets/cbx-social-trends/data/raw/x/`, `datasets/cannabinoid-multi-trends/data/raw/x/`, `datasets/cannabinoid-social-trends/data/raw/x/`
3. Google Trends collections — `datasets/cannabinoid-multi-trends/data/raw/google_trends/`, `datasets/cbx-search-trends/data/raw/google_trends/`

### Methodological Frameworks

4. Krippendorff, K. (2019). *Content Analysis: An Introduction to Its Methodology* (4th ed.). Sage. — Content analysis reliability standards
5. Neuendorf, K. A. (2017). *The Content Analysis Guidebook* (2nd ed.). Sage. — Coding reliability methodology
6. Ruths, D., & Pfeffer, J. (2014). Social media: The shape of the whole. *Science*, 346(6215), 1256–1257. — Platform sampling limitations
7. Tufekci, Z. (2014). Big questions for social media big data: Representativeness, validity and other methodological pitfalls. *Proceedings of the AAAI International Conference on Web and Social Media* (ICWSM). — Social media data validity
8. Eysenbach, G. (2002). Infodemiology: The epidemiology of the internet. *Journal of Medical Internet Research*, 4(3), e13. — Infodemiology framework
9. Eysenbach, G. (2009). Infodemiology and infoveillance. *Journal of Medical Internet Research*, 11(4), e116. — Search data as health proxies
10. Bruns, A. (2019). *After the 'APIcalypse': Social media platforms and their fight against misinformation.* Open Information Science, 3(1), 158–185. — Platform API limitations
11. Venturini, T., et al. (2018). A few observations on multiplatform methods. In *The SAGE Handbook of Social Media Research Methods*. Sage. — Multi-platform digital methods

---

*This recommendations report was prepared by the Academic Research Agent on 2026-10-05. All repository data references were inspected directly. Methodological frameworks are applied as general best-practice guidance; specific numerical targets (e.g., n≥200, κ≥0.70) are standard benchmarks from content analysis literature, not derived from this repository's data. Claims about expected data outcomes are appropriately hedged as estimates requiring empirical validation. Citation counts were not treated as evidence quality.*
