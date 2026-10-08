# Japan Cannabinoid Trends Dataset 2026: English Summary

| Item | Content |
|------|---------|
| **Version** | 1.9.0 |
| **Release Date** | 2026-10-05 |
| **DOI** | [10.5281/zenodo.23164973](https://doi.org/10.5281/zenodo.23164973) |
| **Publisher** | Routeflags Co., Ltd. |
| **License** | CC BY 4.0 |

---

## Executive Summary

This dataset provides longitudinal monitoring of cannabinoid-related trends in Japan, covering search interest, social media discourse, regulatory status, and product safety data for 12 cannabinoids. The dataset is designed to support research on emerging psychoactive substances, regulatory science, and public health surveillance.

---

## Key Findings

### 1. Search Interest Hierarchy (Common Scale)

Google Trends data reveals a clear hierarchy of search interest among cannabinoids in Japan (common scale, CBD=100):

| Compound | Common Scale | Individual Index | Regulatory Status |
|----------|:------------:|:----------------:|-------------------|
| CBD | **47** | 46.8 | Conditionally legal |
| THC | 12 | 64.4 | Regulated |
| CBG | 3 | 62.9 | Conditionally legal |
| HHC | 1 | 37.6 | Designated drug |
| THCH | 0 | 3.0 | Designated drug |

**Finding:** CBD dominates search interest, with THC a distant second. [OBSERVED]

### 2. Regulatory Timeline (Japan)

| Compound | Regulation Date | Current Status |
|----------|:---------------:|----------------|
| THC | 1948- | Regulated (Cannabis Control Act) |
| HHC | 2022-03-17 | Designated drug |
| THC-O | 2023-03-20 | Designated drug |
| THCH | 2023-08-04 | Designated drug |
| HHCH | 2023-12-02 | Designated drug |
| CBD/CBG | 2024-12-12 | Conditionally legal (residual THC limits) |
| CBN | 2026-06-01 | Designated drug |

### 3. CBN Pre/Post Regulation Analysis

X/Twitter engagement for CBN-related content decreased after regulation:

| Metric | Pre-regulation (Jan-May 2026) | Post-regulation (Jun-Oct 2026) |
|--------|:----------------------------:|:------------------------------:|
| Average likes | 18.6 | 9.8 |
| Unique users | 64 | 70 |

**Note:** This is a temporal association; causation cannot be inferred. [OBSERVED]

### 4. Social Media Discourse Patterns

Content classification of X/Twitter posts (n=389, kappa ≥ 0.61):

| Compound | Product Promotion | Review | Conversation | Other |
|----------|:-----------------:|:------:|:------------:|:-----:|
| CBD | 15% | 15% | 30% | 40% |
| CBG | **56%** | 7% | 12% | 25% |
| CBN | 17% | 11% | 28% | 44% |
| THC | 7% | 10% | **40%** | 43% |

**Finding:** CBG shows highest product promotion (56%); THC shows highest conversation rate (40%). [OBSERVED]

---

## Data Sources

| Source | Type | Period | Records |
|--------|------|--------|---------|
| Google Trends | Search interest | 2025-09 to 2026-10 | Weekly time series |
| X (Twitter) | Social media | 2026-07 to 2026-10 | 389 posts |
| YouTube | Video content | Various | 180+ videos |
| COA (Certificate of Analysis) | Product safety | 2026-05 to 2026-06 | 8 compounds |
| Regulatory sources | Government | Current | 12 compounds |

---

## Methodology

### Data Collection

- **Google Trends:** Unofficial API (google-trends-mcp), geo=JP, timeframe=today 12-m
- **X/Twitter:** Apify actor (cPYLH3QT9GyzKhB4S), lang:ja, section=latest
- **YouTube:** Apify actor (gJvjeCYNraSfhIaNd) for Japanese keywords
- **Regulatory data:** MHLW, e-Gov, National Police Agency primary sources

### Data Processing

- **Deduplication:** By unique ID (tweet_id, videoId)
- **Language filtering:** Japanese character detection in titles/content
- **Content classification:** Keyword-based rule system with Cohen's kappa validation
- **Normalization:** Google Trends common-scale for cross-compound comparison

### Quality Controls

- **Inter-rater reliability:** Cohen's kappa calculated for all classifications (0.61-0.80)
- **Confidence intervals:** Wilson score intervals for proportion estimates
- **Limitations disclosed:** All reports include explicit limitation statements

---

## Research Applications

This dataset can support research on:

1. **Regulatory science:** How regulatory changes affect search interest and social media discourse
2. **Public health surveillance:** Early warning indicators for emerging psychoactive substances
3. **Digital epidemiology:** Cross-platform analysis of substance-related content
4. **Drug policy:** Evidence base for regulatory decision-making
5. **Market research:** Consumer interest patterns in the cannabinoid sector

---

## Limitations

1. **Google Trends is a relative index:** Values represent relative search interest (0-100), not absolute search volume
2. **SNS samples are non-random:** X/Twitter data uses `section=latest`, introducing recency bias
3. **Small sample sizes:** Some analyses have n<100, with corresponding wide confidence intervals
4. **Observational design:** Temporal associations cannot establish causation
5. **Platform-specific biases:** Each platform (Google, X, YouTube) has its own user demographics and content policies

---

## Citation

KATO, Kyoji. (2026). Japan Cannabinoid Trends Dataset 2026: Google Trends, Social Media, Regulatory Status, and Early Warning Index. Version 1.9.0. Routeflags Co., Ltd. [Dataset]. DOI: [10.5281/zenodo.23164973](https://doi.org/10.5281/zenodo.23164973)

---

## Conflict of Interest Disclosure

The publisher operates an e-commerce business in the cannabinoid sector. This commercial relationship may represent a potential conflict of interest. The methodology and source information are provided to allow independent evaluation of the findings.

---

## Contact

- **Repository:** https://github.com/routeflags/japan-cannabinoid-trends
- **DOI:** https://doi.org/10.5281/zenodo.23164973
- **ORCID:** https://orcid.org/0009-0007-5131-0374
