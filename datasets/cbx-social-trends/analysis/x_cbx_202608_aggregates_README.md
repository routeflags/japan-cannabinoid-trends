# X CBX weekly / monthly aggregates (2026-08)

**Issue:** ISS-20261014-PUB-029, option ii (owner-decided 2026-10-15).
Only the aggregator is implemented. The per-post anonymized CSV (issue
sections 2-2, 10, 11) is withdrawn history; section 2-3 input measurements
(147 rows / 16 cols) stay valid and sections 3-6 rules are reused as
pre-processing.

## What this is

Group counts over period x compound x classification x engagement-bin,
derived read-only from the private per-post X input
(`data/private/x_cbx_202608_summary_anonymized.csv`, 147 rows, 16 cols,
PRV-036 management, never modified). No per-post row is published.

## Files

| File | Content |
|------|---------|
| `data/processed/x_cbx_202608_weekly_aggregates.csv` | 122 groups; `week_start` (ISO Monday) x CBX x topic/intent/format x bins; `post_count` sums to 147 |
| `data/processed/x_cbx_202608_monthly_aggregates.csv` | 105 groups; `month` (YYYY-MM-01) x CBX x topic/intent/format x bins; `post_count` sums to 147 |
| `analysis/x_cbx_202608_aggregation_conditions.json` | dimensions, bin edges, datetime rules, provenance |
| `analysis/x_cbx_202608_aggregates_schema.json` | column names, types, nullability, meaning |
| `analysis/x_cbx_202608_aggregates_validation.json` | row counts, missing, errors, small cells, re-identifiability, hashes |

## Reproduce

```bash
PYTHONPATH=src python3 -m processing.cli aggregate-x \
  --input datasets/cbx-social-trends/data/private/x_cbx_202608_summary_anonymized.csv \
  --weekly-out datasets/cbx-social-trends/data/processed/x_cbx_202608_weekly_aggregates.csv \
  --monthly-out datasets/cbx-social-trends/data/processed/x_cbx_202608_monthly_aggregates.csv \
  --compound CBX \
  --report <validation-report-path>
```

Deterministic: identical input and conditions yield byte-identical outputs.
The private input is required locally; in a fresh clone (or CI) the
derivation reports `reproducible_requires_non_published_input`
(`python -m processing.cli audit-processed`).

## Reading the numbers

- `post_count` is a group size (derived). Period / compound / classification
  are observed group keys. Interpretation (why a week spikes) is not in these
  files.
- Missing (`""`) and zero (`0`) are distinct states; unknown periods group
  under `""` and are counted in the validation report (this run: none).
- Weekly periods observed: 2026-08-03 / 08-10 / 08-17 / 08-24 / 08-31 /
  09-07. Monthly: 2026-08-01 (65 groups) / 2026-09-01 (40 groups).
- Small cells are reported, not removed: weekly 106 of 122 groups hold a
  single post; monthly 83 of 105. The k-anonymity bar is undecided (issue
  section 8), so no suppression was applied. Do not treat a `post_count = 1`
  group as identifying a post: bins and week/month granularity apply, but
  uniqueness remains review material.

## Limits

- Source: one query (`CBX liquid`), Japanese, X only, 2026-08-05 to
  2026-09-08. Not comparable to search, video, session, or order metrics.
- Classification is the rule-based v1.0.0 run of 2026-10-02 reused as-is
  (`metadata/taxonomy/classification-rules.yaml`); `unclassified` is a
  fallback label, not missing.
- Publication needs the review envelope verdict
  (`metadata/publication/x-cbx-202608-weekly-aggregates/`,
  `metadata/publication/x-cbx-202608-monthly-aggregates/`). Implementation
  complete does not mean approved.

## Code

`src/processing/aggregate_x.py` (v1.0.0), tests
`tests/processing/test_x_aggregates.py`.
