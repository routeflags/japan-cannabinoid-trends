# Cannabinoid Platform Trends — Methodology

**Study ID:** `cannabinoid-platform-trends`
**Created:** 2026-10-15
**Last Updated:** 2026-11-01

## 1. Research question

日本国内の検索需要（Google Trends、`geo=JP`）と、国単位のフィルタを持たない COL-033 の YouTube 検索結果（liquid 6 run）の間に、どのような観測上の差異があるか？

This is a dataset question. The release object is a set of processed tables
with provenance and schema, not a narrative HTML page.

## 2. Release scope

Included sources:

| Source | Included evidence | Unit |
|--------|-------------------|------|
| Google Trends | 5-year summary evidence from `docs/audits/gt-summary.json` | Relative index (`0..100`) and derived weekly counts |
| YouTube | **COL-033 only**: 6 adopted liquid runs from `metadata/provenance/declarations/20261015-youtube-csv-adoption.json` | Search-result returned count |

Excluded sources:

| Source | State | Reason |
|--------|-------|--------|
| X | Excluded | Owner decision on 2026-10-15. X aggregate outputs are separate and not part of this release slice. |
| YouTube runs outside COL-033 | Excluded from this slice | The raw study `cannabinoid-raw-collection` has 8 adopted YouTube runs (7 liquid primary + 1 retained HHC compound-term run). They are not in this distribution. |

### 2.1 YouTube scope and the `not_collected` meaning

- The YouTube slice is the COL-033 declaration only: **6 runs, 5 compounds** (CBD ×2, CBN, CRDH, H4CBH, HHBD). All six are `product_liquid` runs from the `youtube-consistency` study.
- The raw study's HHC liquid and HHC compound-term runs are **adopted raw**, but they are **outside this release slice**. A `not_collected` YouTube row in `platform_coverage.csv` means "no run in this COL-033 slice"; it does **not** mean the compound was never collected.
- The same payload can appear under two run ids: the distribution uses the `youtube-consistency` id; the raw study uses the `cannabinoid-raw-collection` id. The raw declaration records `environment.previous_study_run_id`, and `source_run_index.csv` keeps the distribution id. Do not treat the two ids as two payloads.
- The YouTube actor has no API geo filter. The Japanese product term `リキッド` gives an approximate query-language market restriction, not a geographic guarantee. This dataset does not claim a Japanese census.

## 3. Inputs

The executable transformation reads these committed inputs:

1. `docs/audits/gt-summary.json`
   - Google Trends 5-year summary for 14 compounds.
   - Evidence is derived from cataloged Google Trends raw runs; the summary is
     already the publication-safe source for this slice.
2. `metadata/provenance/declarations/20261015-youtube-csv-adoption.json`
   - Six adopted liquid YouTube runs from COL-033 (5 compounds; CBD ×2).
   - The declaration distinguishes API request `dateFilter` from observed video
     publication-date bounds.
   - The raw study's HHC runs and the other raw-study liquid runs are not part
     of this input and not part of this release slice.
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
- YouTube gaps are `not_collected`, not `observed_zero`. A gap means the
  COL-033 slice has no run, not that the raw study never collected the compound.
- `make audit-distribution-scope` reports the COL-033 scope, the per-compound
  raw-study runs it excludes, the distribution-to-raw run-id mapping, and any
  request-parameter drift. It is report-only; `--strict` turns drift into a
  non-zero exit.
- `processing.cli audit-processed` verifies the processed outputs can be
  re-derived from committed inputs.

## 7. Limitations

- Google Trends values are relative indices, not absolute search volume.
- YouTube values are search-result sample returned counts, not a platform
  census.
- `dateFilter` is an API request parameter; observed YouTube video
  publication-date bounds are not the search condition.
- YouTube has no API geo filter; the Japanese product term is an approximate
  query-language restriction, not a geographic guarantee.
- The committed `source_run_index.csv` carries a legacy `maxResults=999999`
  placeholder for the six COL-033 runs. The declaration does not record that
  limit. `make audit-distribution-scope` reports it; changing the committed
  release values requires the release process, not an audit.
- X is intentionally absent from this release slice.
- The release slice is COL-033-only. HHC liquid and HHC compound-term runs are
  adopted in the raw study but outside this distribution.

## 8. Evidence level

- Google Trends numeric values in this dataset are derived from committed
  summary evidence.
- YouTube returned counts are observed run-level counts from the adoption
  declaration.
- Cross-platform interpretation remains analysis, not an observed field.
