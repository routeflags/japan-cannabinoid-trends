# Cannabinoid Platform Trends

**Study ID:** `cannabinoid-platform-trends`

This study is the dataset-release track for comparing domestic cannabinoid
trend observations across platforms. The first release slice uses only:

- Google Trends 5-year summary evidence (`google_trends`)
- Adopted YouTube search-result aggregate evidence (`youtube`)

X is excluded from this release scope by owner decision on 2026-10-15. X
aggregate outputs remain separate and are not used in this dataset.

## Research question

> 日本国内において、各カンナビノイド成分の国内トレンドと、Google Trends / YouTube で観測できる差異は何か？

This dataset does **not** rank platforms on one common scale. Google Trends
values and YouTube returned counts measure different phenomena, so each row
keeps its source-specific metric and unit.

## Files

Processed files live in `data/processed/`:

| File | Rows | Purpose |
|------|------|---------|
| `trend_observations.csv` | 66 | Source-specific observations by compound, platform, metric, period, query, and run. |
| `platform_coverage.csv` | 28 | Compound × platform coverage matrix, including `not_collected` states. |
| `metric_dictionary.csv` | 6 | Metric definitions, units, evidence level, and comparability constraints. |
| `source_run_index.csv` | 20 | Run-level provenance index for the observations. |
| `manifest.json` | 1 document | Build sources, excluded sources, output names, and row counts. |

Schema files live in `metadata/schema/`.

## Regeneration

Run production through the repository `Makefile`:

```bash
make platform-trends
```

Equivalent direct command:

```bash
.venv/bin/python -m processing.cli build-platform-trends \
  --output-dir datasets/cannabinoid-platform-trends/data/processed
```

The builder reads committed evidence only and writes new processed outputs. It
does not modify raw data.

## Publication and privacy posture

- No X data is included in this release slice.
- No YouTube per-video rows, IDs, URLs, titles, channel fields, or engagement
  values are redistributed.
- Missing / not-collected source coverage is recorded as `not_collected`, not
  as zero.
- Publication eligibility still depends on release review, citation metadata,
  and version/DOI consistency.
