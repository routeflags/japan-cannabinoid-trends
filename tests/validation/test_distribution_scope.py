"""The release slice's YouTube scope versus the raw study.

The dangerous reading is `HHC / youtube / not_collected` being taken as "HHC
was never collected".  The report has to keep the distribution slice (COL-033,
6 liquid runs) next to the raw study (8 adopted runs) and name the gap.
"""

from __future__ import annotations

from pathlib import Path

from validation.distribution_scope import build_distribution_scope

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_release_slice_is_the_six_col_033_liquid_runs() -> None:
    report = build_distribution_scope(REPO_ROOT)

    assert report["distribution_study_id"] == "cannabinoid-platform-trends"
    assert report["distribution_youtube_run_count"] == 6
    assert len(report["distribution_youtube_compounds"]) == 5
    assert report["distribution_query_intents"] == ["product_liquid"]
    assert report["distribution_youtube_study_ids"] == ["youtube-consistency"]


def test_hhc_is_a_scope_gap_not_an_absent_collection() -> None:
    report = build_distribution_scope(REPO_ROOT)

    assert report["scope_gap_compounds"] == ["HHC"]
    hhc = next(
        row for row in report["by_compound"] if row["compound_id"] == "compound_hhc"
    )
    assert hhc["distribution_status"] == "not_collected"
    assert hhc["raw_study_run_count"] == 2
    assert hhc["raw_study_intents"] == ["compound_general", "product_liquid"]
    assert hhc["scope_gap"] is True
    assert hhc["release_slice_excluded"] is True


def test_every_distribution_run_maps_to_a_raw_study_run() -> None:
    report = build_distribution_scope(REPO_ROOT)

    assert all(entry["mapped"] for entry in report["run_id_mapping"])
    assert all(
        entry["mapping_basis"] == "environment.previous_study_run_id"
        for entry in report["run_id_mapping"]
    )


def test_legacy_max_results_placeholder_is_reported() -> None:
    report = build_distribution_scope(REPO_ROOT)

    assert report["finding_count"] == 6
    assert {finding["kind"] for finding in report["findings"]} == {
        "unsupported_max_results"
    }
    assert {finding["documented_value"] for finding in report["findings"]} == {
        999999
    }


def test_report_is_deterministic() -> None:
    assert build_distribution_scope(REPO_ROOT) == build_distribution_scope(REPO_ROOT)
