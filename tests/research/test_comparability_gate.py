"""G7 comparability gate tests (CS01-CS13, G7-T10/T11/T12/T13/T14).

Contract sources: g.md \u00a78 (gate), \u00a79 (reference code), \u00a717.

The ``comparable`` verdict is defined (synthetic complete evidence) but
unreachable on repository data by construction: legacy runs carry no
sampling / coverage / normalization-scale / approval evidence, so the
strongest verdict on real pairs is ``conditional``.
"""

from pathlib import Path

from research.catalog import build_catalog
from research.comparability import (
    check_cross_study_comparability,
    check_measurement_pair,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"

PHASE_A = "20261012T055259Z-google-trends-ja-rikiddo-phase-a-12m"
REPEAT = "20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m"
CBX_SEARCH = "20261001T115959Z-google-trends-cbx-rikiddo"


def _by_run() -> dict:
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    return {e["run_id"]: e for e in catalog["entries"]}


def _measurement(**overrides) -> dict:
    base = {
        "compound_id": "compound_cbx",
        "query_intent": "compound_general",
        "granularity": "month",
        "time_axis": "posted_at",
        "measurement_id": "social_post_count",
        "unit": "posts",
    }
    base.update(overrides)
    return base


def _complete_entry(**overrides) -> dict:
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


# ---------------------------------------------------------------------------
# Measurement-level gate (delegates to validation.comparability)
# ---------------------------------------------------------------------------

def test_g7_t10_measurement_mismatch_is_detected():
    verdict = check_measurement_pair(
        _measurement(),
        _measurement(measurement_id="video_publication_count", unit="videos"),
    )
    assert verdict["status"] == "not_comparable"
    assert "measurement_mismatch" in verdict["reasons"]


def test_g7_t12_x_posts_vs_youtube_videos_never_share_a_unit():
    verdict = check_measurement_pair(
        _measurement(),
        _measurement(measurement_id="video_publication_count", unit="videos"),
    )
    assert verdict["status"] == "not_comparable"
    assert "unit_mismatch" in verdict["reasons"]


def test_g7_t11_gt_different_scales_refuse_direct_comparison():
    verdict = check_measurement_pair(
        _measurement(
            measurement_id="search_interest_index",
            unit="relative_index_0_100",
            normalization_scale="comparison:[CBX]",
        ),
        _measurement(
            measurement_id="search_interest_index",
            unit="relative_index_0_100",
            normalization_scale="comparison:[CBX,CBD]",
        ),
    )
    assert verdict["status"] == "not_comparable"
    assert "normalization_scale_mismatch" in verdict["reasons"]


def test_measurement_metadata_gap_yields_unknown():
    verdict = check_measurement_pair({}, {})
    assert verdict["status"] == "unknown"


# ---------------------------------------------------------------------------
# Entry-level gate on repository data
# ---------------------------------------------------------------------------

def test_repeat_collection_pair_is_conditional_not_comparable():
    """Strongest verdict on real data: same fetch group, review required."""
    runs = _by_run()
    verdict = check_cross_study_comparability(runs[PHASE_A], runs[REPEAT])
    assert verdict["status"] == "conditional"
    assert "cs11_renormalization_instability_review_required" in verdict["reasons"]
    assert verdict["checks"]["CS11"]["result"] == "pass"


def test_cross_study_different_scales_are_not_comparable():
    runs = _by_run()
    verdict = check_cross_study_comparability(runs[CBX_SEARCH], runs[PHASE_A])
    assert verdict["status"] == "not_comparable"
    assert verdict["reasons"] == ["cs11_normalization_scale_mismatch"]


def test_g7_t13_missing_coverage_blocks_comparison():
    verdict = check_cross_study_comparability(
        _complete_entry(coverage="complete"),
        _complete_entry(run_id="run-y", artifact_id="artifact-y", coverage="missing"),
    )
    assert verdict["status"] == "not_comparable"
    assert verdict["reasons"] == ["cs09_coverage_missing"]


def test_g7_t14_insufficient_metadata_yields_unknown():
    assert check_cross_study_comparability({}, {})["status"] == "unknown"
    verdict = check_cross_study_comparability(
        _complete_entry(compound_ids=[]), _complete_entry(run_id="run-y")
    )
    assert verdict["status"] == "unknown"


def test_unsupported_purpose_yields_unknown():
    runs = _by_run()
    verdict = check_cross_study_comparability(runs[PHASE_A], runs[REPEAT], purpose="vibes")
    assert verdict["status"] == "unknown"
    assert verdict["reasons"] == ["unsupported_comparison_purpose"]


def test_comparable_is_unreachable_on_repository_data():
    """No real-data pair may return ``comparable`` (evidence is absent)."""
    runs = _by_run()
    entries = list(runs.values())
    for pos, left in enumerate(entries):
        for right in entries[pos + 1:]:
            verdict = check_cross_study_comparability(left, right)
            assert verdict["status"] != "comparable", (
                left.get("run_id"),
                right.get("run_id"),
            )


def test_comparable_definition_with_complete_evidence():
    """What ``comparable`` requires: full CS01-CS13 evidence on both sides."""
    verdict = check_cross_study_comparability(
        _complete_entry(),
        _complete_entry(run_id="run-y", artifact_id="artifact-y"),
    )
    assert verdict["status"] == "comparable"
    assert verdict["reasons"] == ["all_cs_conditions_satisfied"]
