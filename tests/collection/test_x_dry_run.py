"""X dry-run / request-planning slice tests (COL-016 + WIN-002 safe slice).

Offline only: every request is planned, never sent.  No credentials are read,
no HTTP is issued, and no response body, tweet ID, user ID, text, URL, or
per-post record appears anywhere — only request-side facts (endpoint, query
text, absolute UTC bounds).  Synthetic query text is used throughout.
"""

import json

import pytest

from collection.adapters import (
    AdapterUnavailable,
    get_adapter_factory,
    get_window_compiler,
    registered_sources,
)
from collection.adapters.x import (
    ENDPOINT,
    METHOD,
    XApiDryRunAdapter,
    XApiWindowCompiler,
    XDryRunError,
    XRequestError,
    build_dry_run_adapter,
    build_search_request,
    plan_search_request,
)
from collection.core.contracts import SUPPORT_VALUES, check_adapter_contract
from validation.windows import check_window_compiler

QUERY = "synthetic-test-query"
START = "2026-08-01T00:00:00Z"
END = "2026-08-08T00:00:00Z"


def _plan(**overrides):
    plan = {
        "plan_id": "plan-x-dry-run-001",
        "study_id": "synthetic-study",
        "source_id": "x",
        "query": {"text": QUERY},
        "window": {
            "start": START,
            "end_exclusive": END,
            "granularity": "day",
            "timezone": "UTC",
        },
        "purpose": "COL-016 dry-run contract test (synthetic, nothing sent)",
    }
    plan.update(overrides)
    return plan


# ---------------------------------------------------------------------------
# R1: request planner — declared facts in, request parameters out, nothing sent
# ---------------------------------------------------------------------------


def test_build_search_request_plans_without_sending():
    request = build_search_request(query_text=QUERY, start_time=START, end_time=END)
    assert request == {
        "endpoint": ENDPOINT,
        "method": METHOD,
        "params": {"query": QUERY, "start_time": START, "end_time": END},
    }
    assert ENDPOINT == "https://api.x.com/2/tweets/search/all"
    assert METHOD == "GET"


def test_build_search_request_normalizes_utc_offsets_without_shifting():
    request = build_search_request(
        query_text=QUERY,
        start_time="2026-08-01T00:00:00+00:00",
        end_time="2026-08-08T00:00:00+00:00",
    )
    assert request["params"]["start_time"] == START
    assert request["params"]["end_time"] == END


def test_build_search_request_passes_max_results_through():
    request = build_search_request(
        query_text=QUERY, start_time=START, end_time=END, max_results=100
    )
    assert request["params"]["max_results"] == 100


def test_build_search_request_refuses_empty_query():
    for query_text in ("", "   "):
        with pytest.raises(XRequestError):
            build_search_request(query_text=query_text, start_time=START, end_time=END)


@pytest.mark.parametrize(
    "start_time,end_time",
    [
        ("2026-08-01T00:00:00", END),
        (START, "2026-08-08T00:00:00"),
        ("not-a-date", END),
    ],
    ids=["naive-start", "naive-end", "unparseable-start"],
)
def test_build_search_request_refuses_naive_or_unparseable_bounds(start_time, end_time):
    with pytest.raises(XRequestError):
        build_search_request(query_text=QUERY, start_time=start_time, end_time=end_time)


def test_build_search_request_refuses_non_utc_offsets():
    with pytest.raises(XRequestError):
        build_search_request(
            query_text=QUERY,
            start_time="2026-08-01T09:00:00+09:00",
            end_time="2026-08-08T09:00:00+09:00",
        )


def test_build_search_request_refuses_reversed_bounds():
    with pytest.raises(XRequestError):
        build_search_request(query_text=QUERY, start_time=END, end_time=START)


@pytest.mark.parametrize("limit", [0, -5, "100", 10.5, True])
def test_build_search_request_refuses_non_positive_max_results(limit):
    with pytest.raises(XRequestError):
        build_search_request(
            query_text=QUERY, start_time=START, end_time=END, max_results=limit
        )


def test_plan_search_request_maps_plan_facts_to_request_params():
    request = plan_search_request(_plan(), max_results=50)
    assert request["params"] == {
        "query": QUERY,
        "start_time": START,
        "end_time": END,
        "max_results": 50,
    }


def test_plan_search_request_refuses_a_plan_without_declared_facts():
    plan = _plan()
    del plan["query"]
    with pytest.raises(XRequestError):
        plan_search_request(plan)
    with pytest.raises(XRequestError):
        plan_search_request("not-a-plan")


def test_planned_requests_carry_no_credentials_or_response_fields(monkeypatch):
    monkeypatch.setenv("X_BEARER_TOKEN", "bogus-token-must-never-appear")
    monkeypatch.setenv("APIFY_TOKEN", "bogus-token-must-never-appear")
    request = plan_search_request(_plan())
    dump = json.dumps(request)
    assert "bogus-token-must-never-appear" not in dump
    for forbidden in ("tweet_id", "author_id", "Bearer", "next_token"):
        assert forbidden not in dump


# ---------------------------------------------------------------------------
# R2: dry-run adapter — common contract shape, collect always fails closed
# ---------------------------------------------------------------------------


def test_dry_run_adapter_satisfies_the_common_contract():
    assert check_adapter_contract(build_dry_run_adapter()) == []
    assert isinstance(build_dry_run_adapter(), XApiDryRunAdapter)


def test_dry_run_capabilities_stay_unknown():
    adapter = build_dry_run_adapter()
    capabilities = adapter.capabilities()
    assert capabilities == {
        "absolute_date_range": "unknown",
        "relative_date_range": "unknown",
        "language_filter": "unknown",
        "geo_filter": "unknown",
        "pagination": "unknown",
        "stable_item_id": "unknown",
    }
    for value in capabilities.values():
        assert value in SUPPORT_VALUES
    assert "supported" not in capabilities.values()
    capabilities["pagination"] = "supported"
    assert adapter.capabilities()["pagination"] == "unknown"


def test_dry_run_plan_request_compiles_without_collecting():
    request = build_dry_run_adapter().plan_request(_plan())
    assert request["endpoint"] == ENDPOINT
    assert request["params"]["query"] == QUERY


def test_dry_run_plan_request_refuses_undeclared_facts():
    with pytest.raises(XDryRunError):
        build_dry_run_adapter().plan_request({})


def test_dry_run_collect_fails_closed_without_a_live_transport():
    adapter = build_dry_run_adapter()
    result = adapter.collect(_plan())
    assert result.status == "failed"
    assert result.errors and result.errors[0]["code"] == "LIVE_TRANSPORT_UNIMPLEMENTED"
    assert result.completeness == "missing"
    assert result.observations == []
    assert result.pagination_exhausted is None
    assert adapter.extract_observations({"rows": [1, 2, 3]}) == []
    description = adapter.describe_execution()
    assert description["collection_mode"] == "dry_run_only"
    assert description["collector_id"] == "x-api-v2"
    assert "token" not in json.dumps(description).lower()


def test_dry_run_validate_plan_rejects_empty_query_and_window():
    adapter = build_dry_run_adapter()
    assert any(
        "query.text" in violation
        for violation in adapter.validate_plan({"query": {"text": ""}})
    )
    assert any(
        "window.start" in violation
        for violation in adapter.validate_plan({"query": {"text": QUERY}})
    )
    assert adapter.validate_plan(_plan()) == []


# ---------------------------------------------------------------------------
# R3: window compiler — absolute UTC windows to request parameters only
# ---------------------------------------------------------------------------


def test_x_compiler_satisfies_the_common_contract():
    compiler = XApiWindowCompiler()
    assert check_window_compiler(compiler) == []
    assert compiler.collector_id == "x-api-v2"


def test_compile_absolute_window_keeps_request_and_observed_separate():
    window = {
        "window_id": "synthetic-2026-08-week",
        "timezone": "UTC",
        "start": START,
        "end_exclusive": END,
        "granularity": "day",
    }
    compiled = XApiWindowCompiler().compile(window, reference_time=None)
    assert compiled.parameters == {"start_time": START, "end_time": END}
    assert compiled.collector_window_type == "absolute_datetime"
    assert compiled.exact is False
    assert compiled.boundary_semantics == "request_bounds_only_no_observed_range"
    assert compiled.reference_time is None
    assert compiled.resolved_start == START
    assert compiled.resolved_end_exclusive == END
    assert compiled.requested_start == START
    assert compiled.requested_end_exclusive == END
    assert any(
        "must be recorded separately" in text for text in compiled.limitations
    )


def test_compile_records_a_provided_reference_without_using_it():
    window = {"timezone": "UTC", "start": START, "end_exclusive": END}
    compiled = XApiWindowCompiler().compile(
        window, reference_time="2026-08-09T00:00:00Z"
    )
    assert compiled.reference_time == "2026-08-09T00:00:00Z"
    assert compiled.parameters == {"start_time": START, "end_time": END}


def _expect_refusal(window, **kwargs):
    try:
        XApiWindowCompiler().compile(
            window,
            reference_time=kwargs.pop("reference_time", None),
            **kwargs,
        )
    except Exception as error:  # noqa: BLE001 - asserted below
        return error
    raise AssertionError("compilation should have been refused")


def test_compile_rejects_invalid_windows():
    assert _expect_refusal("not-a-window").codes == ["window_invalid"]
    assert _expect_refusal({"start": "not-a-date", "end_exclusive": END}).codes == [
        "window_invalid"
    ]
    assert _expect_refusal({"start": "2026-08-01", "end_exclusive": END}).codes == [
        "window_invalid"
    ]
    assert _expect_refusal({"start": END, "end_exclusive": START}).codes == [
        "window_invalid"
    ]
    assert _expect_refusal(
        {"start": START, "end_exclusive": END, "timezone": "Not/AZone"}
    ).codes == ["timezone_unknown"]


def test_compile_rejects_a_naive_reference_time():
    window = {"timezone": "UTC", "start": START, "end_exclusive": END}
    assert _expect_refusal(window, reference_time="2026-08-09T00:00:00").codes == [
        "reference_time_invalid"
    ]


def test_compile_refuses_an_unsupported_absolute_capability():
    window = {"timezone": "UTC", "start": START, "end_exclusive": END}
    assert _expect_refusal(
        window, capabilities={"absolute_date_range": "unsupported"}
    ).codes == ["absolute_window_unsupported"]


# ---------------------------------------------------------------------------
# R4: dispatch stays closed — nothing here implies live X collection
# ---------------------------------------------------------------------------


def test_x_has_no_live_dispatch():
    """The slice is planning-only: ``x`` must not resolve to an adapter and
    the unregistered ``x-api-v2`` collector must not resolve to a compiler, so
    the pipeline cannot mistake planning for collection."""
    assert "x" not in registered_sources()
    with pytest.raises(AdapterUnavailable):
        get_adapter_factory("x")
    assert get_window_compiler("x-api-v2") is None
    assert get_window_compiler("x-apify-twitter-search") is None
