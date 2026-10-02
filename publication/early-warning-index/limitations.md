# Limitations — Japan Cannabinoid Early Warning Index v1

| 項目 | 内容 |
|------|------|
| **Version** | v1.0 |
| **Date** | 2026-10-02 |

---

## Important Limitations

### 1. Google Trends Data Nature

**Issue:** Google Trends values are relative indices (0-100), not absolute search volumes.

**Implication:** A value of 100 means "peak relative interest" for that query in that period—not 100 searches. Values cannot be compared across different queries or time periods for absolute volume estimation.

**Mitigation:** All outputs explicitly state values are relative indices.

---

### 2. Five-Year Data Window

**Issue:** Google Trends maximum timeframe is `today 5-y` (approximately 2021-09-26 to 2026-10-03).

**Implication:** Compounds that appeared before September 2021 cannot have their true first-mention date determined. For such compounds, we record "2021-09-26以前" (before September 26, 2021).

**Affected compounds:** CBD, THC, CBN (left-censored = true)

---

### 3. Polysemy Risk

**Issue:** Some compound names are ambiguous terms that may include non-cannabinoid searches.

**Implication:**
- **CBD:** May include searches for other meanings (e.g., place names, abbreviations)
- **THC:** May include searches related to drug policy news rather than consumer interest

**Mitigation:** Compound classification and context should be considered when interpreting results.

---

### 4. Low-Volume Query Censoring

**Issue:** Google Trends may return zero for queries below a certain search volume threshold.

**Implication:** Compounds with very low search volume may show as zero even when some searches occur. This affects primarily THCH and HHC.

**Mitigation:** Persistence classes distinguish between "no data" and "low but present data."

---

### 5. Single Data Source

**Issue:** Only Google Trends data was used for search interest metrics.

**Implication:** Search behavior on other platforms (Bing, Yahoo! Japan, social media) is not captured. Japanese internet users may use different search engines.

**Mitigation:** Future versions may incorporate additional data sources.

---

### 6. Regulatory Status Snapshot

**Issue:** Regulatory information is current as of 2026-10-02.

**Implication:** Japanese cannabinoid regulation is evolving rapidly. Compounds currently unregulated may be regulated in the future.

**Mitigation:** Regulatory status includes "monitoring" classifications for at-risk compounds. Update schedule recommended.

---

### 7. No Causal Inference

**Issue:** This dataset describes temporal patterns, not causal relationships.

**Implication:** The correlation between regulatory action and search interest decline (HHCH case) does not prove causation. Other factors (media coverage, market withdrawal) may contribute.

**Mitigation:** All findings use descriptive language ("associated with," "coincided with") rather than causal claims ("caused").

---

### 8. Commercial Conflict of Interest

**Issue:** The publisher operates an e-commerce business in the cannabinoid sector.

**Implication:** There is a potential conflict of interest that could influence research direction, interpretation, or reporting.

**Mitigation:** 
- Explicit COI disclosure in all outputs
- Methodology documented for independent evaluation
- Data available for public inspection
- Compound-level (not brand-level) analysis

---

### 9. Non-Probability Observations

**Issue:** Google Trends data represents aggregate search behavior, not a representative sample of Japanese consumers.

**Implication:** Results cannot be generalized to "Japanese consumer preferences" or "market demand."

**Mitigation:** All findings limited to "Google Trends data shows" language.

---

### 10. Temporal Precision

**Issue:** Google Trends data is reported at weekly granularity.

**Implication:** Exact dates of emergence or regulation cannot be pinpointed to the day.

**Mitigation:** All dates rounded to week-level precision.

---

## Summary

This dataset provides a structured overview of cannabinoid emergence patterns and regulatory status in Japan based on Google Trends data. While valuable for identifying trends and regulatory timelines, it should be interpreted with awareness of the limitations above. The data is most appropriate for:

- Identifying relative patterns of emergence
- Documenting regulatory timelines
- Generating hypotheses for further research
- Supporting evidence-based policy discussion

It is **not** appropriate for:

- Estimating absolute market size
- Predicting future trends
- Establishing causal relationships
- Representing Japanese consumer preferences broadly

---

## Conflict of Interest Disclosure

The publisher operates an e-commerce business in the cannabinoid sector. This commercial relationship may represent a potential conflict of interest. The source data, methodology, and limitations are provided to support independent evaluation of the findings.
