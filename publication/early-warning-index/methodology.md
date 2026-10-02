# Methodology — Japan Cannabinoid Early Warning Index v1

| 項目 | 内容 |
|------|------|
| **Version** | v1.0 |
| **Date** | 2026-10-02 |
| **Research ID** | MNT-20261002 / EXP-20261002 |

---

## 1. Research Question

When did each cannabinoid first appear in Japanese Google search data, and what is its current regulatory status?

---

## 2. Data Sources

### Google Trends

| Parameter | Value |
|-----------|-------|
| **Source** | Google Trends (trends.google.com) |
| **Geo** | JP (Japan) |
| **Timeframes** | `today 5-y` (5-year), `today 12-m` (12-month) |
| **Collection date** | 2026-10-02 |
| **MCP server** | google-trends-mcp |

### Regulatory Information

| Source | URL |
|--------|-----|
| MHLW Designated Drugs | https://www.mhlw.go.jp/bunya/iyakuhin/yakubuturanyou/scheduled-drug/list.html |
| MHLW CBN Designation | https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iyakuhin/yakubuturanyou/other/CBN_shitei.html |
| National Institute of Health Sciences | https://www.ncd.mhlw.go.jp/ |

---

## 3. Compound Selection

Twelve cannabinoids were selected based on:

1. **Market presence:** Compounds currently or recently available in Japan
2. **Regulatory relevance:** Compounds subject to or candidate for regulation
3. **Research gap:** Compounds with limited English-language documentation

### Compounds Tracked

| Category | Compounds |
|----------|-----------|
| Major Phytocannabinoids | CBD, THC |
| Minor Phytocannabinoids | CBN, CBG, THCV, THCH |
| Semi-Synthetic | HHC, THC-O, H4CBH, HHBD |
| Synthetic | HHCH, CRDP |

---

## 4. First-Mention Detection Method

### Algorithm

```
1. Retrieve 5-year Google Trends data for each compound
2. Identify all non-zero data points
3. Apply left-censoring rule:
   - If first data point (2021-09-26) is non-zero:
     → Record as "2021-09-26以前" (left_censored = true)
   - If first non-zero point is later:
     → Record exact date (left_censored = false)
4. Record first_value, peak_value, peak_week
```

### Persistence Classification

| Class | Definition |
|-------|------------|
| **Year-round** | Data present in >90% of weeks |
| **Intermittent** | Data present in 10-90% of weeks |
| **Low-volume** | Data present in <10% of weeks |
| **Very low** | Data present in <5% of weeks |
| **Pre-regulation spike** | Peak followed by near-zero after regulation |

---

## 5. Regulatory Status Classification

| Status | Definition |
|--------|------------|
| **Regulated** | Subject to specific legal restriction |
| **Designated Drug** | Listed as designated drug under PMD Act |
| **Narcotics** | Listed under Narcotics and Psychotropics Control Act |
| **Unregulated (conditional)** | Legal under conditions (e.g., THC-free) |
| **Unregulated (caution)** | Not specifically regulated but monitoring recommended |

### Regulatory History Fields

The dataset records three distinct regulatory timepoints:

| Field | Definition | Example (THCH) |
|-------|------------|----------------|
| **first_regulation_date** | Initial individual designation | 2023-08-04 |
| **generic_designation_date** | Group/generic designation (if applicable) | 2023-09-10 |
| **current_status** | Current regulatory status | Designated Drug |

---

## 6. Emergence Score System

### Definition

The Emergence Score (ES) is a composite indicator of compound emergence intensity, calculated from four components:

```
ES = f(growth, acceleration, persistence, novelty)
```

### Scoring Rubric

| Score | Classification | Definition |
|:-----:|----------------|------------|
| **0** | Not detected | No data in Google Trends |
| **1** | Sporadic detection | Isolated non-zero weeks, no sustained pattern |
| **2** | Sustained detection | Regular appearance but low growth rate |
| **3** | Rapid growth | Significant increase in search interest |
| **4** | High-growth emerging | Rapid growth + recent emergence + regulatory attention |

### Component Criteria

| Component | Measurement | Weight |
|-----------|-------------|:------:|
| **Growth** | Peak value / mean value ratio | High |
| **Acceleration** | Rate of change in recent periods | Medium |
| **Persistence** | Share of non-zero weeks | Medium |
| **Novelty** | Recency of first mention | High |

### Scoring Examples

| Compound | ES | Rationale |
|----------|:--:|-----------|
| CBD | 1 | Baseline compound, stable year-round presence |
| HHC | 3 | Low-volume but rapid growth before regulation |
| HHCH | 4 | High growth + recent emergence + regulatory intervention |
| H4CBH | 4 | Recent emergence + high initial values |

### Limitations of Emergence Score

1. **Relative index:** Based on Google Trends relative values, not absolute search volume
2. **Qualitative:** Score reflects patterns, not statistical significance
3. **Context-dependent:** May not apply equally across different market conditions
4. **Not predictive:** Describes past emergence, not future trajectory

---

## 7. Cohort Classification

### Baseline vs Emerging

| Cohort | Compounds | Definition |
|--------|-----------|------------|
| **Baseline** | CBD, THC, CBN, CBG, THCV | Pre-existing market presence (first mention ≤ 2021-12-31) |
| **Emerging** | HHC, THC-O, THCH, HHCH, CRDP, H4CBH, HHBD | Recently appeared (first mention ≥ 2022-01-01) |

### Analytical Use

Baseline compounds serve as **reference series** for monitoring emerging compounds, enabling:
- Context for relative interest levels
- Comparison of emergence patterns
- Control for market-wide search trends

---

## 8. Data Processing

### Raw Data Location

```
datasets/cannabinoid-multi-trends/data/raw/google_trends/
├── {run-id}-google-trends-{compound}-12m/
│   ├── records_{compound}_12m.json
│   └── run_metadata.json
└── {run-id}-google-trends-{compound}-5y/
    ├── records_{compound}_5y.json
    └── run_metadata.json
```

### Processed Output

```
datasets/cannabinoid-multi-trends/data/processed/
└── early-warning-index-v1.csv
```

---

## 9. Quality Controls

| Control | Implementation |
|---------|---------------|
| **Data validation** | Verify non-zero points against raw JSON |
| **Cross-reference** | Regulatory status verified against MHLW sources |
| **Left-censoring** | Explicitly flagged for pre-2021 compounds |
| **Relative index caveat** | Documented in all outputs |
| **COI disclosure** | Included in landing page |

---

## 10. Limitations

1. **Relative indices:** Google Trends values (0-100) measure relative interest, not absolute search volume.
2. **5-year window:** Google Trends maximum timeframe is `today 5-y`; pre-2021 emergence cannot be detected.
3. **Polysemy:** CBD and THC are ambiguous terms that may include non-cannabinoid searches (e.g., place names, other abbreviations).
4. **Low-volume censoring:** Queries below Google Trends threshold may appear as zero even when searches occur.
5. **Single source:** Only Google Trends data used; other search platforms not included.
6. **Regulatory snapshot:** Regulatory status current as of 2026-10-02; subject to change.

---

## 11. Reproducibility

### Collection Script

Google Trends data collected via MCP server `google-trends-mcp` with parameters:
- `geo`: JP
- `timeframe`: `today 12-m`, `today 5-y`
- `terms`: [compound_name]

### Run Metadata

Each collection run recorded in:
```
datasets/cannabinoid-multi-trends/data/raw/google_trends/{run-id}/run_metadata.json
```

Includes: run_id, study_id, source, collection_timestamp, queries.

---

## 12. Citation

When citing this methodology or dataset:

> KATO, Kyoji. (2026). Japan Cannabinoid Emerging Compound Early Warning Index v1 [Methodology]. Routeflags Co., Ltd. https://github.com/routeflags/japan-cannabinoid-trends/blob/main/publication/early-warning-index/methodology.md

---

## Conflict of Interest Disclosure

The publisher operates an e-commerce business in the cannabinoid sector. This commercial relationship may represent a potential conflict of interest. The methodology and source information are provided to allow independent evaluation of the findings.
