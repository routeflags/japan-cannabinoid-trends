"""Build the cross-platform cannabinoid trend dataset (Google Trends + YouTube).

The release dataset answers a dataset-level research question:

*How do cannabinoid-related domestic trend observations differ across
platforms?*

X is deliberately excluded from this release slice by owner decision
(2026-10-15).  Social per-post data remains outside the release dataset; this
builder only reads committed Google Trends summary evidence and the committed
YouTube adoption declaration.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

__all__ = [
    "OBSERVATION_COLUMNS",
    "COVERAGE_COLUMNS",
    "METRIC_COLUMNS",
    "RUN_INDEX_COLUMNS",
    "build_platform_trends",
]


OBSERVATION_COLUMNS = (
    "observation_id",
    "compound",
    "compound_id",
    "platform",
    "source",
    "metric",
    "unit",
    "period_start",
    "period_end",
    "granularity",
    "value",
    "status",
    "query_id",
    "query_text",
    "run_id",
    "collection_method",
    "observation_scope",
    "provenance_ref",
    "limitations",
)

COVERAGE_COLUMNS = (
    "compound",
    "compound_id",
    "platform",
    "status",
    "metric_available",
    "unit",
    "run_count",
    "latest_run_id",
    "period_start",
    "period_end",
    "publication_eligible",
    "notes",
)

METRIC_COLUMNS = (
    "metric",
    "unit",
    "platform",
    "meaning",
    "comparable_across_platforms",
    "evidence_level",
    "limitations",
)

RUN_INDEX_COLUMNS = (
    "run_id",
    "source",
    "platform",
    "study_id",
    "collector",
    "query_id",
    "query_text",
    "collection_timestamp",
    "request_parameters",
    "observed_period_start",
    "observed_period_end",
    "processed_artifact",
    "provenance_ref",
    "publication_status",
)

DATASET_ID = "cannabinoid-platform-trends"
GT_SUMMARY = "docs/audits/gt-summary.json"
YOUTUBE_DECLARATION = "metadata/provenance/declarations/20261015-youtube-csv-adoption.json"
QUERY_REGISTRY = "metadata/queries/query-registry.json"


@dataclass(frozen=True)
class QueryInfo:
    query_id: str
    compound_id: str
    canonical_text: str


def _read_json(repo_root: Path, relative: str) -> dict:
    return json.loads((repo_root / relative).read_text(encoding="utf-8"))


def _write_csv(path: Path, columns: tuple[str, ...], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _queries(repo_root: Path) -> tuple[dict[str, QueryInfo], dict[str, QueryInfo]]:
    by_id: dict[str, QueryInfo] = {}
    general_by_compound: dict[str, QueryInfo] = {}
    for entry in _read_json(repo_root, QUERY_REGISTRY)["queries"]:
        info = QueryInfo(
            query_id=entry["query_id"],
            compound_id=entry["compound_id"],
            canonical_text=entry["canonical_text"],
        )
        by_id[info.query_id] = info
        if info.query_id.endswith("-general-ja"):
            compound = info.query_id[: -len("-general-ja")].upper().replace("-", "-")
            general_by_compound[compound] = info
    return by_id, general_by_compound


def _compound_from_query_id(query_id: str) -> str:
    suffixes = ("-liquid-ja", "-general-ja", "-oil-ja", "-cannabinoid-ja", "-cannabis-ja")
    for suffix in suffixes:
        if query_id.endswith(suffix):
            return query_id[: -len(suffix)].upper()
    return query_id.split("-", 1)[0].upper()


def _period_from_gt(entry: dict) -> tuple[str, str, str]:
    period = entry.get("stats", {}).get("data_period")
    if isinstance(period, str):
        match = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})\s+〜\s+([0-9]{4}-[0-9]{2}-[0-9]{2})$", period)
        if match:
            return match.group(1), match.group(2), "week"
    return "", "", "week"


def _status_for_value(value: object) -> str:
    try:
        return "observed_nonzero" if float(value) != 0.0 else "observed_zero"
    except (TypeError, ValueError):
        return "missing"


def _metric_rows() -> list[dict[str, str]]:
    return [
        {
            "metric": "relative_interest_mean_5y",
            "unit": "google_trends_index_0_100_mean",
            "platform": "google_trends",
            "meaning": "Mean of weekly Google Trends relative interest values in the available 5-year run.",
            "comparable_across_platforms": "no",
            "evidence_level": "derived",
            "limitations": (
                "Google Trends values are source-normalized relative indices, not "
                "absolute search volume. Each run is normalized to its own peak, "
                "so a mean is not comparable between compounds either; use the "
                "common-scale comparison runs for that."
            ),
        },
        {
            "metric": "relative_interest_peak_value",
            "unit": "google_trends_index_0_100",
            "platform": "google_trends",
            "meaning": "Maximum weekly Google Trends relative interest value in the available 5-year run.",
            "comparable_across_platforms": "no",
            "evidence_level": "derived",
            "limitations": (
                "Peak value is within-run normalized; it is not comparable to "
                "YouTube counts, and not comparable between compounds (every run "
                "peaks at 100)."
            ),
        },
        {
            "metric": "relative_interest_latest_value",
            "unit": "google_trends_index_0_100",
            "platform": "google_trends",
            "meaning": "Latest weekly Google Trends relative interest value in the available 5-year run.",
            "comparable_across_platforms": "no",
            "evidence_level": "observed",
            "limitations": (
                "Latest value depends on the run window and Google Trends "
                "normalization; it is not comparable between compounds."
            ),
        },
        {
            "metric": "nonzero_weeks",
            "unit": "weeks",
            "platform": "google_trends",
            "meaning": "Number of weeks with non-zero Google Trends relative interest, when the run records it.",
            "comparable_across_platforms": "no",
            "evidence_level": "derived",
            "limitations": "Unavailable for legacy baseline runs that did not record zero/non-zero counts.",
        },
        {
            "metric": "zero_weeks",
            "unit": "weeks",
            "platform": "google_trends",
            "meaning": "Number of weeks with zero Google Trends relative interest, when the run records it.",
            "comparable_across_platforms": "no",
            "evidence_level": "derived",
            "limitations": "Zero means Google Trends returned 0 for the normalized series; it is not YouTube absence.",
        },
        {
            "metric": "returned_count",
            "unit": "search_result_count",
            "platform": "youtube",
            "meaning": "Number of records returned by the Apify YouTube scraper run.",
            "comparable_across_platforms": "no",
            "evidence_level": "observed",
            "limitations": "Search-result sample count; not a YouTube census and not comparable to Google Trends indices.",
        },
    ]


def build_platform_trends(repo_root: str | Path, output_dir: str | Path) -> dict:
    repo_root = Path(repo_root)
    output_dir = Path(output_dir)
    query_by_id, general_query_by_compound = _queries(repo_root)
    gt_summary = _read_json(repo_root, GT_SUMMARY)
    youtube_declaration = _read_json(repo_root, YOUTUBE_DECLARATION)

    observations: list[dict[str, object]] = []
    coverage: list[dict[str, object]] = []
    run_index: list[dict[str, object]] = []
    target_compounds: set[str] = set()

    for entry in gt_summary["compounds"]:
        compound = entry["compound"]
        target_compounds.add(compound)
        query = general_query_by_compound.get(compound)
        compound_id = query.compound_id if query else f"compound_{compound.lower().replace('-', '_')}"
        query_id = query.query_id if query else ""
        query_text = query.canonical_text if query else compound
        period_start, period_end, granularity = _period_from_gt(entry)
        limitations = (
            "Google Trends relative index; not an absolute search count, not "
            "comparable to YouTube returned_count, and not comparable between "
            "compounds (each run is normalized to its own peak)."
        )
        if entry.get("unavailable"):
            limitations += " Some temporal completeness fields are unavailable for this run."
        metric_specs = (
            ("relative_interest_mean_5y", "google_trends_index_0_100_mean", entry["stats"].get("mean")),
            ("relative_interest_peak_value", "google_trends_index_0_100", entry["stats"].get("peak_value")),
            ("relative_interest_latest_value", "google_trends_index_0_100", entry["stats"].get("last_value")),
            ("nonzero_weeks", "weeks", entry["stats"].get("nonzero_weeks")),
            ("zero_weeks", "weeks", entry["stats"].get("zero_weeks")),
        )
        for metric, unit, value in metric_specs:
            if value is None:
                continue
            observations.append(
                {
                    "observation_id": f"gt-{compound.lower()}-{metric}",
                    "compound": compound,
                    "compound_id": compound_id,
                    "platform": "google_trends",
                    "source": "google_trends",
                    "metric": metric,
                    "unit": unit,
                    "period_start": period_start,
                    "period_end": period_end,
                    "granularity": granularity,
                    "value": value,
                    "status": _status_for_value(value),
                    "query_id": query_id,
                    "query_text": query_text,
                    "run_id": entry["run_id"],
                    "collection_method": "google_trends_collection",
                    "observation_scope": "jp_search_relative_interest",
                    "provenance_ref": f"{GT_SUMMARY}#{compound}",
                    "limitations": limitations,
                }
            )
        coverage.append(
            {
                "compound": compound,
                "compound_id": compound_id,
                "platform": "google_trends",
                "status": "observed",
                "metric_available": "relative_interest_mean_5y;relative_interest_peak_value;relative_interest_latest_value",
                "unit": "google_trends_index_0_100",
                "run_count": 1,
                "latest_run_id": entry["run_id"],
                "period_start": period_start,
                "period_end": period_end,
                "publication_eligible": "yes",
                "notes": "5-year Google Trends summary available. Direct comparison with YouTube counts is prohibited.",
            }
        )
        run_index.append(
            {
                "run_id": entry["run_id"],
                "source": "google_trends",
                "platform": "google_trends",
                "study_id": Path(entry["path"]).parts[1] if entry.get("path") else "",
                "collector": "google_trends",
                "query_id": query_id,
                "query_text": query_text,
                "collection_timestamp": "",
                "request_parameters": "geo=JP; timeframe=today 5-y",
                "observed_period_start": period_start,
                "observed_period_end": period_end,
                "processed_artifact": GT_SUMMARY,
                "provenance_ref": entry.get("path", ""),
                "publication_status": "published_summary",
            }
        )

    youtube_by_compound: dict[str, list[dict]] = {}
    for run in youtube_declaration["runs"]:
        query_id = run["query"]["query_id"]
        query = query_by_id[query_id]
        compound = _compound_from_query_id(query_id)
        target_compounds.add(compound)
        youtube_by_compound.setdefault(compound, []).append(run)
        window = run["window"]
        count = run["execution"]["returned_count"]
        observations.append(
            {
                "observation_id": f"yt-{run['run_id']}-returned_count",
                "compound": compound,
                "compound_id": query.compound_id,
                "platform": "youtube",
                "source": "apify_youtube_search",
                "metric": "returned_count",
                "unit": "search_result_count",
                "period_start": window["start"][:10],
                "period_end": window["end_exclusive"][:10],
                "granularity": "run",
                "value": count,
                "status": _status_for_value(count),
                "query_id": query_id,
                "query_text": run["query"]["keyword"],
                "run_id": run["run_id"],
                "collection_method": "apify_youtube_scraper",
                "observation_scope": "youtube_search_result_sample",
                "provenance_ref": YOUTUBE_DECLARATION,
                "limitations": "dateFilter is the API request parameter; period_start/end are observed video publish-date bounds, not the API condition. Search-result sample count, not a census.",
            }
        )
        run_index.append(
            {
                "run_id": run["run_id"],
                "source": "youtube",
                "platform": "youtube",
                "study_id": run["study_id"],
                "collector": run["collector_id"],
                "query_id": query_id,
                "query_text": run["query"]["keyword"],
                "collection_timestamp": run["timestamps"]["finished_at"],
                "request_parameters": f"dateFilter={run['collection_request']['date_filter']}; maxResults=999999",
                "observed_period_start": window["start"][:10],
                "observed_period_end": window["end_exclusive"][:10],
                "processed_artifact": YOUTUBE_DECLARATION,
                "provenance_ref": run["run_id"],
                "publication_status": "aggregate_only; raw records not redistributed",
            }
        )

    for compound in sorted(target_compounds):
        if compound in youtube_by_compound:
            runs = sorted(youtube_by_compound[compound], key=lambda item: item["timestamps"]["finished_at"])
            query = query_by_id[runs[-1]["query"]["query_id"]]
            coverage.append(
                {
                    "compound": compound,
                    "compound_id": query.compound_id,
                    "platform": "youtube",
                    "status": "observed",
                    "metric_available": "returned_count",
                    "unit": "search_result_count",
                    "run_count": len(runs),
                    "latest_run_id": runs[-1]["run_id"],
                    "period_start": min(run["window"]["start"][:10] for run in runs),
                    "period_end": max(run["window"]["end_exclusive"][:10] for run in runs),
                    "publication_eligible": "yes_aggregate_only",
                    "notes": "Adopted COL-033 YouTube run(s). Raw/video rows are not redistributed.",
                }
            )
        else:
            query = general_query_by_compound.get(compound)
            coverage.append(
                {
                    "compound": compound,
                    "compound_id": query.compound_id if query else f"compound_{compound.lower().replace('-', '_')}",
                    "platform": "youtube",
                    "status": "not_collected",
                    "metric_available": "",
                    "unit": "",
                    "run_count": 0,
                    "latest_run_id": "",
                    "period_start": "",
                    "period_end": "",
                    "publication_eligible": "not_applicable",
                    "notes": "No adopted YouTube run in COL-033. This is missing/not collected, not observed zero.",
                }
            )

    _write_csv(output_dir / "trend_observations.csv", OBSERVATION_COLUMNS, observations)
    _write_csv(output_dir / "platform_coverage.csv", COVERAGE_COLUMNS, coverage)
    _write_csv(output_dir / "metric_dictionary.csv", METRIC_COLUMNS, _metric_rows())
    _write_csv(output_dir / "source_run_index.csv", RUN_INDEX_COLUMNS, run_index)
    manifest = {
        "schema_version": "1.0.0",
        "dataset_id": DATASET_ID,
        "generated_by": "processing.platform_trends.build_platform_trends",
        "sources": [GT_SUMMARY, YOUTUBE_DECLARATION, QUERY_REGISTRY],
        "excluded_sources": {
            "x": "Excluded from this dataset release by owner decision on 2026-10-15. X coarse aggregates remain separate and are not part of the cross-platform release scope."
        },
        "outputs": {
            "trend_observations": "trend_observations.csv",
            "platform_coverage": "platform_coverage.csv",
            "metric_dictionary": "metric_dictionary.csv",
            "source_run_index": "source_run_index.csv",
        },
        "row_counts": {
            "trend_observations": len(observations),
            "platform_coverage": len(coverage),
            "metric_dictionary": len(_metric_rows()),
            "source_run_index": len(run_index),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
