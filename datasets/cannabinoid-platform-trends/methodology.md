# Cannabinoid Platform Trends — Methodology

**Study ID:** `cannabinoid-platform-trends`
**Created:** 2026-10-15
**Last Updated:** 2026-10-15

## 1. Research question

日本国内において、各カンナビノイド成分の国内トレンドと、Google Trends / YouTube で観測できる差異は何か？

This is a dataset question. The release object is a set of processed tables
with provenance and schema, not a narrative HTML page.

## 2. Release scope

Included sources:

| Source | Included evidence | Unit |
|--------|-------------------|------|
| Google Trends | 5-year summary evidence from `docs/audits/gt-summary.json` | Relative index (`0..100`) and derived weekly counts |
| YouTube | COL-033 adopted Apify YouTube search exports from `metadata/provenance/declarations/20261015-youtube-csv-adoption.json` | Search-result returned count |

Excluded sources:

| Source | State | Reason |
|--------|-------|--------|
| X | Excluded | Owner decision on 2026-10-15. X aggregate outputs are separate and not part of this release slice. |

## 3. Inputs

The executable transformation reads these committed inputs:

1. `docs/audits/gt-summary.json`
   - Google Trends 5-year summary for 14 compounds.
   - Evidence is derived from cataloged Google Trends raw runs; the summary is
     already the publication-safe source for this slice.
2. `metadata/provenance/declarations/20261015-youtube-csv-adoption.json`
   - Six adopted YouTube runs from COL-033.
   - The declaration distinguishes API request `dateFilter` from observed video
     publication-date bounds.
3. `metadata/queries/query-registry.json`
   - Canonical query and compound identifiers.

No raw observations are edited or normalized in place.

## 4. Transformation

The transformation is implemented in `src/processing/platform_trends.py` and
exposed as:

```bash
make platform-trends
```

It produces:

1. `trend_observations.csv`
   - One row per source-specific metric observation.
   - Google Trends rows include 5-year mean, peak value, latest value, and
     zero/non-zero week counts when available.
   - YouTube rows include only adopted run-level returned counts.
2. `platform_coverage.csv`
   - One row per compound × included platform.
   - YouTube gaps are `not_collected`, not zero.
3. `metric_dictionary.csv`
   - Defines each metric and marks cross-platform comparability as `no`.
4. `source_run_index.csv`
   - Links each observation source back to run IDs and provenance references.
5. `manifest.json`
   - Records sources, excluded sources, output names, and row counts.

## 5. Derived fields

| Field | Derivation |
|-------|------------|
| `observation_id` | Deterministic identifier from source/run/metric. |
| `status` | `observed_nonzero` when numeric value is non-zero; `observed_zero` when the observed numeric value is exactly zero; `missing` when no numeric value exists. |
| `period_start` / `period_end` | Google Trends: data period recorded in the summary when available. YouTube: observed video publication-date bounds from the declaration. |
| `platform_coverage.status` | `observed` when a source has adopted evidence for the compound; `not_collected` when the release slice has no adopted run for that compound/platform. |
| `publication_eligible` | Mechanical publication posture only (`yes`, `yes_aggregate_only`, or `not_applicable`); it is not release approval. |

## 6. Validation

Minimum checks:

- Output row counts reconcile with `manifest.json`.
- YouTube returned counts reconcile with the COL-033 declaration:
  `224 + 395 + 456 + 468 + 352 + 393 = 2288`.
- No `x` platform rows are emitted.
- Metrics preserve source-specific units and mark cross-platform comparability
  as `no`.
- YouTube gaps are `not_collected`, not `observed_zero`.
- `processing.cli audit-processed` verifies the processed outputs can be
  re-derived from committed inputs.

## 7. Limitations

- Google Trends values are relative indices, not absolute search volume.
- YouTube values are search-result sample returned counts, not a platform
  census.
- `dateFilter` is an API request parameter; observed YouTube video
  publication-date bounds are not the search condition.
- Cross-platform values must not be compared as one numeric scale.
- X is intentionally absent from this release slice.

## 8. Evidence level

- Google Trends numeric values in this dataset are derived from committed
  summary evidence.
- YouTube returned counts are observed run-level counts from the adoption
  declaration.
- Cross-platform interpretation remains analysis, not an observed field.
