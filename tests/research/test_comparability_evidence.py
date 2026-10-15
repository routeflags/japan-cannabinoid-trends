"""Per-condition evidence pins for CS08-CS13 (ISS-20261015-CMP-005).

Contract sources: ``docs/specs/collection-pipeline.md`` §7.1 (the comparable
definition), ``docs/provenance/comparability-evidence-cs08-cs13.md`` (the
emission conditions), ``research.comparability`` (the gate).

Each test drops exactly one evidence item from an otherwise complete synthetic
pair and pins the downgrade: every CS08-CS13 item is load-bearing, and no real
repository pair is claimed ``comparable`` (that direction is owned by
``test_comparability_gate.py::test_comparable_is_unreachable_on_repository_data``
and ``test_comparable_definition_with_complete_evidence``; neither is
duplicated here).
"""

import pytest

from research.comparability import check_cross_study_comparability


def _complete_entry(**overrides):
    base = {
        "catalog_entry_id": "study-x:run-x",
        "study_id": "study-x",
        "run_id": "run-x",
        "artifact_id": "artifact-x",
        "source_id": "x",
        "compound_ids": ["compound_cbx"],
        "query_ids": ["cbx-general-ja"],
        "intent_ids": ["compound_general"],
        "window_id": "2026-09-jst",
        "terms": [],
        "timeframe": "2026-09",
        "geo": "JP",
        "measurement_id": "social_post_count",
        "unit": "posts",
        "granularity": "month",
        "time_axis": "posted_at",
        "collection_timestamp": "2026-10-01T00:00:00Z",
        "sampling": "top_n:100",
        "coverage": "complete",
        "missingness": "observed_zero",
        "availability": "approved",
    }
    base.update(overrides)
    return base


def _other(**overrides):
    base = _complete_entry(run_id="run-y", artifact_id="artifact-y")
    base.update(overrides)
    return base


def test_full_evidence_is_comparable_by_definition():
    verdict = check_cross_study_comparability(_complete_entry(), _other())
    assert verdict["status"] == "comparable"
    assert verdict["reasons"] == ["all_cs_conditions_satisfied"]


@pytest.mark.parametrize(
    ("drop", "reason"),
    [
        ({"sampling": None}, "cs08_sampling_review_required"),
        ({"coverage": None}, "cs09_coverage_review_required"),
        ({"coverage": "partial"}, "cs09_coverage_partial"),
        ({"missingness": None}, "cs10_missingness_review_required"),
        ({"artifact_id": None}, "cs12_provenance_partial"),
        ({"availability": "private"}, "cs13_publication_review_required"),
        ({"availability": None}, "cs13_publication_review_required"),
    ],
)
def test_each_missing_evidence_item_downgrades_to_conditional(drop, reason):
    """One gap anywhere in CS08-CS10/CS12-CS13 costs ``comparable``."""

    verdict = check_cross_study_comparability(_complete_entry(**drop), _other())
    assert verdict["status"] == "conditional"
    assert reason in verdict["reasons"]


def test_missing_coverage_blocks_comparison():
    verdict = check_cross_study_comparability(
        _complete_entry(), _other(coverage="missing")
    )
    assert verdict["status"] == "not_comparable"
    assert verdict["reasons"] == ["cs09_coverage_missing"]


def test_missing_run_identity_is_unknown_not_a_verdict():
    verdict = check_cross_study_comparability(
        _complete_entry(run_id=None), _other()
    )
    assert verdict["status"] == "unknown"
    assert verdict["reasons"] == ["provenance_unknown"]


def _relative_entry(**overrides):
    base = _complete_entry(
        measurement_id="search_interest_index",
        unit="relative_index_0_100",
        **overrides,
    )
    return base


def test_shared_declared_scale_passes_cs11():
    verdict = check_cross_study_comparability(
        _relative_entry(normalization_scale="comparison:[CBX]"),
        _relative_entry(
            run_id="run-y",
            artifact_id="artifact-y",
            normalization_scale="comparison:[CBX]",
        ),
    )
    assert verdict["status"] == "comparable"
    assert verdict["checks"]["CS11"]["result"] == "pass"


def test_untraceable_scale_downgrades_to_conditional():
    verdict = check_cross_study_comparability(
        _relative_entry(), _relative_entry(run_id="run-y", artifact_id="artifact-y")
    )
    assert verdict["status"] == "conditional"
    assert "cs11_normalization_review_required" in verdict["reasons"]
    assert verdict["checks"]["CS11"]["result"] == "review"
