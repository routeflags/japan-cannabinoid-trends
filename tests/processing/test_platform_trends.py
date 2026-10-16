"""Cross-platform cannabinoid trend dataset builder tests.

The dataset release scope for 2026-10-15 includes Google Trends and YouTube
aggregate evidence only. X is deliberately excluded, and YouTube video-level
records must not be redistributed.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from processing.platform_trends import (
    COVERAGE_COLUMNS,
    METRIC_COLUMNS,
    OBSERVATION_COLUMNS,
    RUN_INDEX_COLUMNS,
    build_platform_trends,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_build_platform_trends_outputs_expected_release_slice(tmp_path) -> None:
    manifest = build_platform_trends(REPO_ROOT, tmp_path)

    assert manifest["dataset_id"] == "cannabinoid-platform-trends"
    assert manifest["excluded_sources"] == {
        "x": (
            "Excluded from this dataset release by owner decision on 2026-10-15. "
            "X coarse aggregates remain separate and are not part of the "
            "cross-platform release scope."
        )
    }
    assert manifest["row_counts"] == {
        "trend_observations": 68,
        "platform_coverage": 28,
        "metric_dictionary": 6,
        "source_run_index": 20,
    }

    observations = _rows(tmp_path / "trend_observations.csv")
    coverage = _rows(tmp_path / "platform_coverage.csv")
    metrics = _rows(tmp_path / "metric_dictionary.csv")
    run_index = _rows(tmp_path / "source_run_index.csv")

    assert tuple(observations[0]) == OBSERVATION_COLUMNS
    assert tuple(coverage[0]) == COVERAGE_COLUMNS
    assert tuple(metrics[0]) == METRIC_COLUMNS
    assert tuple(run_index[0]) == RUN_INDEX_COLUMNS
    assert len(observations) == manifest["row_counts"]["trend_observations"]
    assert len(coverage) == manifest["row_counts"]["platform_coverage"]
    assert len(metrics) == manifest["row_counts"]["metric_dictionary"]
    assert len(run_index) == manifest["row_counts"]["source_run_index"]


def test_x_is_excluded_and_youtube_gaps_are_not_zero(tmp_path) -> None:
    build_platform_trends(REPO_ROOT, tmp_path)

    observations = _rows(tmp_path / "trend_observations.csv")
    coverage = _rows(tmp_path / "platform_coverage.csv")

    assert {row["platform"] for row in observations} == {"google_trends", "youtube"}
    assert {row["platform"] for row in coverage} == {"google_trends", "youtube"}
    assert "x" not in {row["platform"] for row in observations + coverage}

    cbx_youtube = next(
        row
        for row in coverage
        if row["compound"] == "CBX" and row["platform"] == "youtube"
    )
    assert cbx_youtube["status"] == "not_collected"
    assert cbx_youtube["run_count"] == "0"
    assert "not observed zero" in cbx_youtube["notes"]


def test_youtube_counts_reconcile_without_video_level_redistribution(tmp_path) -> None:
    build_platform_trends(REPO_ROOT, tmp_path)

    observations = _rows(tmp_path / "trend_observations.csv")
    coverage = _rows(tmp_path / "platform_coverage.csv")
    run_index = _rows(tmp_path / "source_run_index.csv")

    youtube = [row for row in observations if row["platform"] == "youtube"]
    assert len(youtube) == 6
    assert sum(int(row["value"]) for row in youtube) == 2288
    assert {row["metric"] for row in youtube} == {"returned_count"}
    assert all("dateFilter" in row["limitations"] for row in youtube)

    cbd_youtube = next(
        row
        for row in coverage
        if row["compound"] == "CBD" and row["platform"] == "youtube"
    )
    assert cbd_youtube["status"] == "observed"
    assert cbd_youtube["run_count"] == "2"

    youtube_runs = [row for row in run_index if row["platform"] == "youtube"]
    assert len(youtube_runs) == 6
    assert all(
        row["publication_status"] == "aggregate_only; raw records not redistributed"
        for row in youtube_runs
    )
    banned_fields = {"video_id", "url", "title", "channel", "author", "views"}
    for table_name in (
        "trend_observations.csv",
        "platform_coverage.csv",
        "source_run_index.csv",
    ):
        header = set(_rows(tmp_path / table_name)[0])
        assert banned_fields.isdisjoint(header)


def test_metric_dictionary_blocks_common_scale_interpretation(tmp_path) -> None:
    build_platform_trends(REPO_ROOT, tmp_path)

    metrics = _rows(tmp_path / "metric_dictionary.csv")

    assert {row["comparable_across_platforms"] for row in metrics} == {"no"}
    assert {
        (row["metric"], row["unit"])
        for row in metrics
        if row["platform"] == "youtube"
    } == {("returned_count", "search_result_count")}
    assert any(
        row["unit"] == "google_trends_index_0_100"
        for row in metrics
        if row["platform"] == "google_trends"
    )


def test_platform_trends_build_is_deterministic(tmp_path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    build_platform_trends(REPO_ROOT, first)
    build_platform_trends(REPO_ROOT, second)

    for name in (
        "trend_observations.csv",
        "platform_coverage.csv",
        "metric_dictionary.csv",
        "source_run_index.csv",
        "manifest.json",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    assert json.loads((first / "manifest.json").read_text(encoding="utf-8")) == json.loads(
        (second / "manifest.json").read_text(encoding="utf-8")
    )
