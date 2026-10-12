"""G1 §12 run-level comparability tests (L2, C1-C3).

``compare_runs`` is a comparison gate, not an adoption gate (P5): a run pair
can be ``not_comparable`` while every run is individually L1-valid.
"""

from validation.comparability import compare_runs


def _run(
    *,
    source_id: str = "google-trends",
    collector_id: str = "google-trends-mcp",
    query_id: str = "cbx-liquid-ja",
    submitted: str = "CBX リキッド",
    compound_id="compound_cbx",
    start: str = "2025-10-12T00:00:00Z",
    end: str = "2026-10-12T00:00:00Z",
    granularity: str = "week",
    timezone: str = "Asia/Tokyo",
    time_axis=None,
) -> dict:
    query = {"query_id": query_id, "submitted_query": submitted}
    if compound_id is not None:
        query["compound_id"] = compound_id
    temporal = {
        "requested_start": start,
        "requested_end_exclusive": end,
        "granularity": granularity,
        "timezone": timezone,
    }
    if time_axis is not None:
        temporal["time_axis"] = time_axis
    return {
        "source_id": source_id,
        "collector": {"collector_id": collector_id},
        "query_provenance": query,
        "temporal_provenance": temporal,
    }


def test_identical_runs_are_conditional_at_most():
    """The strongest current verdict is conditional (coverage / sampling
    review still required; `comparable` is not yet modelled)."""
    result = compare_runs(_run(), _run())
    assert result.status == "conditional"
    assert result.reasons == ["coverage_and_sampling_review_required"]


def test_query_mismatch_breaks_c1():
    result = compare_runs(_run(), _run(submitted="THC リキッド"))
    assert result.status == "not_comparable"
    assert result.reasons == ["c1_query_mismatch"]


def test_compound_mismatch_breaks_c1():
    result = compare_runs(_run(), _run(compound_id="compound_thc"))
    assert result.status == "not_comparable"
    assert result.reasons == ["c1_compound_mismatch"]


def test_compound_declared_on_one_side_only_is_unknown():
    result = compare_runs(_run(), _run(compound_id=None))
    assert result.status == "unknown"
    assert result.reasons == ["insufficient_metadata"]


def test_window_mismatch_breaks_c2():
    result = compare_runs(_run(), _run(end="2026-10-01T00:00:00Z"))
    assert result.status == "not_comparable"
    assert result.reasons == ["c2_window_mismatch"]


def test_granularity_and_timezone_mismatch_break_c2():
    result = compare_runs(
        _run(), _run(granularity="day", timezone="UTC")
    )
    assert result.status == "not_comparable"
    assert "c2_granularity_mismatch" in result.reasons
    assert "c2_timezone_mismatch" in result.reasons


def test_missing_temporal_block_is_unknown():
    broken = _run()
    broken.pop("temporal_provenance")
    result = compare_runs(_run(), broken)
    assert result.status == "unknown"


def test_different_sources_cannot_be_compared_as_amounts():
    """a.md §12.2: X posts vs Google Trends index - different units."""
    result = compare_runs(_run(), _run(source_id="x", collector_id="x-apify-twitter-search"))
    assert result.status == "not_comparable"
    assert result.reasons == ["c3_source_mismatch"]


def test_same_source_different_collector_is_conditional():
    result = compare_runs(_run(), _run(collector_id="google-trends-mcp@2"))
    assert result.status == "conditional"
    assert "c3_collector_mismatch" in result.reasons


def test_unsupported_purpose_is_unknown():
    result = compare_runs(_run(), _run(), purpose="causal_claim")
    assert result.status == "unknown"
    assert result.reasons == ["unsupported_comparison_purpose"]


def test_explicit_direct_comparison_purpose_is_modelled():
    result = compare_runs(_run(), _run(), purpose="direct_comparison")
    assert result.status == "conditional"
