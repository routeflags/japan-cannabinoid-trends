"""Comparability gate tests (P4-8 / CV-12).

Cases mirror the judgment tables of g.md §8.3 and c.md §12.2.
"""

from validation.comparability import compare_measurements, compare_temporal_windows


def _measurement(**overrides) -> dict:
    base = {
        "measurement_id": "social_post_count",
        "compound_id": "CBX",
        "intent_id": "compound_general",
        "granularity": "month",
        "time_axis": "publication_time",
        "unit": "posts",
    }
    base.update(overrides)
    return base


def test_matching_measurements_are_conditional():
    result = compare_measurements(_measurement(), _measurement())
    assert result.status == "conditional"
    assert "coverage_and_sampling_review_required" in result.reasons


def test_g7_x_posts_vs_youtube_videos_not_comparable():
    """g.md §8.3: different units / populations are not directly comparable."""
    youtube = _measurement(
        measurement_id="video_publication_count",
        unit="videos",
        observation_entity="video",
        time_axis="publication_time",
    )
    result = compare_measurements(_measurement(), youtube)
    assert result.status == "not_comparable"
    assert "measurement_mismatch" in result.reasons
    assert "unit_mismatch" in result.reasons


def test_different_intents_are_not_comparable():
    product = _measurement(intent_id="product_liquid")
    result = compare_measurements(_measurement(), product)
    assert result.status == "not_comparable"
    assert "intent_mismatch" in result.reasons


def test_different_granularity_is_not_comparable():
    result = compare_measurements(_measurement(), _measurement(granularity="week"))
    assert result.status == "not_comparable"
    assert "granularity_mismatch" in result.reasons


def test_g3_time_axis_mismatch_is_not_comparable():
    """c.md §12.1 T8: publication time vs observation time are different axes."""
    observed = _measurement(time_axis="observation_time")
    result = compare_measurements(_measurement(), observed)
    assert result.status == "not_comparable"
    assert "time_axis_mismatch" in result.reasons


def test_gt_same_scale_is_candidate():
    a = _measurement(
        measurement_id="search_interest_index",
        unit="relative_index_0_100",
        normalization_scale="set-A-2026",
    )
    b = dict(a)
    result = compare_measurements(a, b)
    assert result.status == "conditional"


def test_gt_different_scales_are_refused():
    """c.md G3-T14 / g.md G7-T11: different normalization sets are not
    directly comparable."""
    a = _measurement(
        measurement_id="search_interest_index",
        unit="relative_index_0_100",
        normalization_scale="set-A-2026",
    )
    b = dict(a, normalization_scale="set-B-2026")
    result = compare_measurements(a, b)
    assert result.status == "not_comparable"
    assert "normalization_scale_mismatch" in result.reasons


def test_gt_unknown_scale_is_unknown():
    a = _measurement(
        measurement_id="search_interest_index",
        unit="relative_index_0_100",
    )
    result = compare_measurements(a, dict(a))
    assert result.status == "unknown"
    assert result.reasons == ["normalization_scale_unknown"]


def test_gt_index_vs_post_count_not_comparable():
    """g.md §8.3: GT relative index vs X post count is not a direct quantity
    comparison."""
    gt = _measurement(
        measurement_id="search_interest_index",
        unit="relative_index_0_100",
        normalization_scale="set-A-2026",
    )
    result = compare_measurements(gt, _measurement())
    assert result.status == "not_comparable"


def test_missing_identity_fields_are_unknown():
    result = compare_measurements({}, _measurement())
    assert result.status == "unknown"
    assert result.reasons == ["insufficient_metadata"]


def test_result_is_deterministic_and_serializable():
    result = compare_measurements(_measurement(), _measurement())
    assert result.to_dict() == {
        "status": "conditional",
        "reasons": ["coverage_and_sampling_review_required"],
    }


# ---------------------------------------------------------------------------
# Temporal windows (c.md §12)
# ---------------------------------------------------------------------------


def _window(**overrides) -> dict:
    base = {
        "start": "2026-08-31T15:00:00Z",
        "end_exclusive": "2026-09-30T15:00:00Z",
        "timezone": "Asia/Tokyo",
        "granularity": "day",
    }
    base.update(overrides)
    return base


def test_identical_windows_are_conditional():
    result = compare_temporal_windows(_window(), _window())
    assert result.status == "conditional"


def test_different_windows_are_not_comparable():
    other = _window(start="2026-07-31T15:00:00Z", end_exclusive="2026-08-31T15:00:00Z")
    result = compare_temporal_windows(_window(), other)
    assert result.status == "not_comparable"
    assert "window_mismatch" in result.reasons


def test_timezone_mismatch_is_not_comparable():
    result = compare_temporal_windows(_window(), _window(timezone="UTC"))
    assert "timezone_mismatch" in result.reasons


def test_same_week_boundary_required_for_week_granularity():
    a = _window(granularity="week", week_start="monday")
    b = _window(granularity="week", week_start="sunday")
    result = compare_temporal_windows(a, b)
    assert "week_boundary_mismatch" in result.reasons


def test_non_exact_window_is_conditional_with_reason():
    result = compare_temporal_windows(_window(exact_window_match=False), _window())
    assert result.status == "conditional"
    assert "window_not_exact" in result.reasons


def test_missing_window_bounds_are_unknown():
    assert compare_temporal_windows({}, _window()).status == "unknown"
