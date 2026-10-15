"""YouTube Apify actor input planner tests (COL-016 safe slice).

Offline only: every input is planned, never sent.  No credentials are read,
no HTTP is issued, and no response body, video ID, title, URL, channel name,
view count, or per-video record appears anywhere -- only request-side facts
(actor id, search queries, date filter, result limits).  Synthetic query text
is used throughout.
"""

import json

import pytest

from collection.adapters import (
    AdapterUnavailable,
    get_adapter_factory,
    get_live_session,
    registered_sources,
)
from collection.adapters.youtube import (
    ACTOR_ID,
    SORTING_ORDERS,
    build_actor_input,
    plan_actor_input,
)
from collection.adapters.youtube.apify_csv import DATE_FILTERS, build_adapter
from collection.adapters.youtube.request import YouTubeApifyRequestError

QUERY = "synthetic-test-query"


def _plan(**overrides):
    plan = {
        "plan_id": "plan-youtube-request-001",
        "study_id": "synthetic-study",
        "source_id": "youtube",
        "query": {"text": QUERY},
        "window": {
            "start": "2020-09-30T00:00:00Z",
            "end_exclusive": "2026-10-06T00:00:00Z",
            "granularity": "day",
            "timezone": "UTC",
        },
        "purpose": "COL-016 request-planning contract test (synthetic, nothing sent)",
    }
    plan.update(overrides)
    return plan


# ---------------------------------------------------------------------------
# R1: actor input planner -- declared facts in, request input out, nothing sent
# ---------------------------------------------------------------------------


def test_build_actor_input_plans_without_sending():
    planned = build_actor_input(query_text=QUERY, date_filter="year")
    assert planned == {
        "actor_id": ACTOR_ID,
        "input": {"searchQueries": [QUERY], "dateFilter": "year"},
    }
    assert ACTOR_ID == "h7sDV53CddomktSi5"


def test_date_filter_vocabulary_is_shared_with_the_handover_wrapper():
    from collection.adapters.youtube import apify_csv

    assert apify_csv.DATE_FILTERS == DATE_FILTERS
    assert set(DATE_FILTERS) == {"all", "hour", "today", "week", "month", "year"}


@pytest.mark.parametrize("date_filter", ["hour", "today", "week", "month", "year"])
def test_measured_date_filters_pass_through(date_filter):
    planned = build_actor_input(query_text=QUERY, date_filter=date_filter)
    assert planned["input"]["dateFilter"] == date_filter


def test_all_omits_date_filter_for_the_unbounded_request():
    """The actor has no ``all`` value: the unbounded request carries no
    ``dateFilter`` (the skill's filter-less example is the unbounded shape)."""
    planned = build_actor_input(query_text=QUERY, date_filter="all")
    assert planned["input"] == {"searchQueries": [QUERY]}
    assert "dateFilter" not in planned["input"]


def test_counts_and_sorting_pass_through_when_declared():
    planned = build_actor_input(
        query_text=QUERY,
        date_filter="month",
        max_results=50,
        max_results_shorts=0,
        max_result_streams=0,
        sorting_order="date",
    )
    assert planned["input"] == {
        "searchQueries": [QUERY],
        "dateFilter": "month",
        "maxResults": 50,
        "maxResultsShorts": 0,
        "maxResultStreams": 0,
        "sortingOrder": "date",
    }
    assert set(SORTING_ORDERS) == {"relevance", "rating", "date", "views"}


def test_undeclared_optionals_are_omitted_never_defaulted():
    planned = build_actor_input(query_text=QUERY, date_filter="year")
    assert planned["input"] == {"searchQueries": [QUERY], "dateFilter": "year"}


@pytest.mark.parametrize("query_text", ["", "   ", None, 123, ["x"]])
def test_build_actor_input_refuses_undeclared_query(query_text):
    with pytest.raises(YouTubeApifyRequestError):
        build_actor_input(query_text=query_text, date_filter="year")


@pytest.mark.parametrize("date_filter", ["day", "", None, "ALL", "Year"])
def test_build_actor_input_refuses_unmeasured_date_filter(date_filter):
    with pytest.raises(YouTubeApifyRequestError):
        build_actor_input(query_text=QUERY, date_filter=date_filter)


@pytest.mark.parametrize("limit", [0, -5, "100", 10.5, True])
def test_build_actor_input_refuses_non_positive_max_results(limit):
    with pytest.raises(YouTubeApifyRequestError):
        build_actor_input(query_text=QUERY, date_filter="year", max_results=limit)


@pytest.mark.parametrize("count", [-1, "0", 1.5, True])
def test_build_actor_input_refuses_non_integer_shorts_streams(count):
    with pytest.raises(YouTubeApifyRequestError):
        build_actor_input(
            query_text=QUERY, date_filter="year", max_results_shorts=count
        )
    with pytest.raises(YouTubeApifyRequestError):
        build_actor_input(
            query_text=QUERY, date_filter="year", max_result_streams=count
        )


@pytest.mark.parametrize("sorting", ["newest", "popular", "", None.__class__])
def test_build_actor_input_refuses_unknown_sorting_order(sorting):
    with pytest.raises(YouTubeApifyRequestError):
        build_actor_input(
            query_text=QUERY, date_filter="year", sorting_order=sorting
        )


def test_plan_actor_input_maps_plan_query_with_explicit_date_filter():
    planned = plan_actor_input(_plan(), date_filter="year", max_results=50)
    assert planned == {
        "actor_id": ACTOR_ID,
        "input": {
            "searchQueries": [QUERY],
            "dateFilter": "year",
            "maxResults": 50,
        },
    }


def test_plan_window_is_observed_range_and_never_becomes_input():
    """Absolute window bounds must not leak into the actor input: keyword
    search + absolute range is impossible with this actor."""
    narrow = _plan()
    narrow["window"] = {
        "start": "2026-09-10T00:00:00Z",
        "end_exclusive": "2026-10-10T00:00:00Z",
        "granularity": "day",
        "timezone": "UTC",
    }
    wide = _plan()
    wide["window"] = {
        "start": "2008-08-01T00:00:00Z",
        "end_exclusive": "2026-09-24T00:00:00Z",
        "granularity": "day",
        "timezone": "UTC",
    }
    assert plan_actor_input(narrow, date_filter="all") == plan_actor_input(
        wide, date_filter="all"
    )
    assert plan_actor_input(narrow, date_filter="all")["input"] == {
        "searchQueries": [QUERY]
    }
    # A plan without a window still plans: windows are not inputs.
    nowindow = _plan()
    del nowindow["window"]
    assert plan_actor_input(nowindow, date_filter="year")["input"] == {
        "searchQueries": [QUERY],
        "dateFilter": "year",
    }


def test_plan_actor_input_refuses_a_plan_without_declared_facts():
    plan = _plan()
    del plan["query"]
    with pytest.raises(YouTubeApifyRequestError):
        plan_actor_input(plan, date_filter="year")
    with pytest.raises(YouTubeApifyRequestError):
        plan_actor_input("not-a-plan", date_filter="year")
    with pytest.raises(YouTubeApifyRequestError):
        plan_actor_input(_plan(), date_filter="day")


def test_planned_inputs_carry_no_credentials_or_response_fields(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "bogus-token-must-never-appear")
    monkeypatch.setenv("X_BEARER_TOKEN", "bogus-token-must-never-appear")
    planned = plan_actor_input(_plan(), date_filter="year", max_results=50)
    dump = json.dumps(planned)
    assert "bogus-token-must-never-appear" not in dump
    for forbidden in (
        "Bearer",
        "viewCount",
        "channelName",
        "commentsCount",
        "likes",
        "duration",
        "startUrls",
        "oldestPostDate",
        "sortVideosBy",
        "dataset_id",
        "next_token",
    ):
        assert forbidden not in dump


# ---------------------------------------------------------------------------
# R2: dispatch stays closed -- planning never implies live collection
# ---------------------------------------------------------------------------


def test_youtube_has_no_live_dispatch_or_session():
    """The slice is planning-only: ``youtube`` must not resolve to an adapter
    or a live session, so the pipeline cannot mistake planning for collection."""
    assert "youtube" not in registered_sources()
    with pytest.raises(AdapterUnavailable):
        get_adapter_factory("youtube")
    with pytest.raises(AdapterUnavailable):
        get_live_session("youtube")


def test_handover_adapter_still_fails_closed_with_the_same_error_code(registries):
    adapter = build_adapter(registries)
    result = adapter.collect({})
    assert result.status == "failed"
    assert result.errors and result.errors[0]["code"] == "LIVE_TRANSPORT_UNIMPLEMENTED"
    assert result.completeness == "missing"
    assert adapter.extract_observations({"rows": [1, 2, 3]}) == []


def test_capabilities_stay_unknown_until_measured_evidence(registries):
    adapter = build_adapter(registries)
    capabilities = adapter.capabilities()
    assert capabilities == {
        "absolute_date_range": "unknown",
        "relative_date_range": "unknown",
        "language_filter": "unknown",
        "geo_filter": "unknown",
        "pagination": "unknown",
        "stable_item_id": "unknown",
    }
    assert "supported" not in capabilities.values()
    entry = next(
        collector
        for collector in registries.collectors
        if collector.get("collector_id") == "youtube-apify-scraper"
    )
    assert entry["status"] == "unverified"
    assert entry["version"] == "unknown"
