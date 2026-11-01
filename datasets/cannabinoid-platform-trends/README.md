# Cannabinoid Platform Trends

**表示名:** カンナビノイド 横断集計（配布用データセット）— **研究名・ID・リリース名を揃えている**（リリース名は DOI 安定のため固定）
**Study ID:** `cannabinoid-platform-trends`（ID とディレクトリ名は安定識別子。配布データパッケージ `metadata/datapackage.json` の resource 名がこれを参照する）

**配布名:** この研究の集計結果は、リリース「Japan Cannabinoid Platform Trends Dataset 2026」（DOI [10.5281/zenodo.23390594](https://doi.org/10.5281/zenodo.23390594)）の中核をなす。研究名とリリース名が違うのは、リリース名を DOI 安定のために固定しているため。

This study is the dataset-release track for comparing domestic cannabinoid
trend observations across platforms. The first release slice uses only:

- Google Trends 5-year summary evidence (`google_trends`)
- Adopted YouTube search-result aggregate evidence (`youtube`)

X is excluded from this release scope by owner decision on 2026-10-15. X
aggregate outputs remain separate and are not used in this dataset.

## Research question

> 日本国内の検索需要（Google Trends、`geo=JP`）と、国単位のフィルタを持たない COL-033 の YouTube 検索結果（liquid 6 run）の間に、どのような観測上の差異があるか？

This dataset does **not** rank platforms on one common scale. Google Trends values and YouTube returned counts measure different phenomena, so each row keeps its source-specific metric and unit.

The YouTube side has no API geo filter. Its Japanese product queries (`<compound> リキッド`) give an approximate query-language market restriction, not a geographic guarantee. This dataset does not claim that its YouTube rows are a count of Japanese videos.

## Distribution scope (explicit)

- **YouTube is limited to the COL-033 declaration** (`metadata/provenance/declarations/20261015-youtube-csv-adoption.json`): **6 liquid runs from the `youtube-consistency` study** (CBD ×2, CBN, CRDH, H4CBH, HHBD). 5 compounds, 6 runs; CBD has 2 runs with different `dateFilter`/observed windows.
- The raw study [`datasets/cannabinoid-raw-collection/`](../cannabinoid-raw-collection/) holds **8 adopted YouTube runs** (7 liquid primary + 1 retained HHC compound-term run). **They are outside this release slice.**
- Therefore `HHC / youtube / not_collected` in `platform_coverage.csv` means "no run **in this COL-033 slice**", **not** "HHC was never collected". The raw study has both HHC liquid and HHC compound-term runs adopted (2 runs).
- The same payload can have two run ids: the distribution uses the `youtube-consistency` id, and the raw study uses the `cannabinoid-raw-collection` id. The link is `environment.previous_study_run_id` in the raw-study declaration. `make audit-distribution-scope` reports the mapping and any drift.
- The committed `source_run_index.csv` carries a legacy `maxResults=999999` placeholder for the six runs. The COL-033 declaration does not record that limit. This is reported by `make audit-distribution-scope`; correcting the committed release values is a release decision and is not done by this audit.

## Files

Processed files live in `data/processed/`:

| File | Rows | Purpose |
|------|------|---------|
| `trend_observations.csv` | 76 | Source-specific observations by compound, platform, metric, period, query, and run. |
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
