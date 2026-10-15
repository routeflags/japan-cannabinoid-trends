# X CBX coarse monthly aggregates (2026-08)

**Issue:** ISS-20261014-PUB-029, option ii (owner-decided 2026-10-15).
Only the aggregator is implemented. The per-post anonymized CSV (issue
sections 2-2, 10, 11) is withdrawn history; section 2-3 input measurements
(147 rows / 16 cols) stay valid and sections 3-6 rules are reused as
pre-processing.

## What this is

Coarse monthly group counts over month x compound x one marginal breakdown
(topic, views tier, likes tier, reposts tier, replies tier), derived read-only from the private per-post X input
(`data/private/x_cbx_202608_summary_anonymized.csv`, 147 rows, 16 cols,
PRV-036 management, never modified). No per-post row is published.
The fine weekly/monthly crossed aggregate candidates were removed after the
owner selected coarser aggregation for publication.

## Files

| File | Content |
|------|---------|
| `data/processed/x_cbx_202608_monthly_coarse_aggregates.csv` | 28 groups; monthly marginal breakdowns; `post_count` total rows sum to 147 and every non-total cell is >=5 |
| `analysis/x_cbx_202608_aggregation_conditions.json` | dimensions, bin edges, datetime rules, provenance |
| `analysis/x_cbx_202608_aggregates_schema.json` | column names, types, nullability, meaning |
| `analysis/x_cbx_202608_aggregates_validation.json` | row counts, missing, errors, small cells, re-identifiability, hashes |

## Reproduce

```bash
PYTHONPATH=src python3 -m processing.cli aggregate-x \
  --input datasets/cbx-social-trends/data/private/x_cbx_202608_summary_anonymized.csv \
  --monthly-coarse-out datasets/cbx-social-trends/data/processed/x_cbx_202608_monthly_coarse_aggregates.csv \
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
- Monthly periods observed: 2026-08-01 and 2026-09-01. Totals are 101 and 46.
- Coarsening rule: week is removed; topic cells below 5 within a month are
  merged into `other_topic_lt5`; views/likes/reposts/replies use broad tiers.
  The published candidate has no non-total cell below 5.

## Limits

- Source: one query (`CBX liquid`), Japanese, X only, 2026-08-05 to
  2026-09-08. Not comparable to search, video, session, or order metrics.
- Classification is the rule-based v1.0.0 run of 2026-10-02 reused as-is
  (`metadata/taxonomy/classification-rules.yaml`); `unclassified` is a
  fallback label, not missing.
- Publication review envelope:
  `metadata/publication/x-cbx-202608-monthly-coarse-aggregates/`.

## Code

`src/processing/aggregate_x.py` (v1.0.0), tests
`tests/processing/test_x_aggregates.py`.
