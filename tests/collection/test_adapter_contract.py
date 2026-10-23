"""Adapter contract tests (G1 §8 / §15) for the Google Trends adapter.

Offline only: replay fixtures, no live collection.
"""

import pytest

from collection.core.contracts import (
    SUPPORT_VALUES,
    TransportError,
    check_adapter_contract,
)

from conftest import (
    FIXTURE_12M,
    FIXTURE_5Y,
    RECORDED_CBD_5Y,
    build_replay_adapter,
    load_json,
    make_plan,
)

from collection.adapters.google_trends import (
    GoogleTrendsMcpAdapter,
    SessionMcpTransport,
)


# ---------------------------------------------------------------------------
# Contract shape
# ---------------------------------------------------------------------------


def test_adapter_identity_matches_the_registry_entry(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    entry = next(
        collector
        for collector in registries.collectors
        if collector.get("collector_id") == "google-trends-mcp"
    )
    assert adapter.collector_id == entry["collector_id"]
    assert adapter.adapter_id == entry["adapter_id"]
    assert adapter.source_id == entry["source_id"]
    assert adapter.version == entry["version"]


def test_adapter_satisfies_the_common_contract(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    assert check_adapter_contract(adapter) == []


def test_capabilities_are_reported_from_the_registry(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    capabilities = adapter.capabilities()
    assert capabilities == {
        "absolute_date_range": "unknown",
        "relative_date_range": "supported",
        "language_filter": "unknown",
        "geo_filter": "supported",
        "pagination": "unknown",
        "stable_item_id": "unknown",
    }
    for value in capabilities.values():
        assert value in SUPPORT_VALUES
    # The adapter hands out a copy - callers cannot mutate its state.
    capabilities["geo_filter"] = "unsupported"
    assert adapter.capabilities()["geo_filter"] == "supported"


def test_check_adapter_contract_reports_violations():
    class BrokenAdapter:
        adapter_id = "broken@1"
        source_id = "google-trends"
        collector_id = "google-trends-mcp"
        version = "0.0.1"

        def capabilities(self):
            return {"geo_filter": "maybe"}  # not in the tri-state vocabulary

        def validate_plan(self, plan):
            return []

        # collect / extract_observations / describe_execution are missing

    violations = check_adapter_contract(BrokenAdapter())
    assert any("missing method: collect" in violation for violation in violations)
    assert any("invalid value" in violation for violation in violations)


# ---------------------------------------------------------------------------
# validate_plan
# ---------------------------------------------------------------------------


def test_validate_plan_accepts_the_replay_plan(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    assert adapter.validate_plan(make_plan()) == []


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (lambda plan: plan["query"].update({"text": ""}), "query.text"),
        (lambda plan: plan["query"].update({"timeframe": "today 2-y"}), "timeframe"),
        (lambda plan: plan["query"].update({"geo": "japan"}), "query.geo"),
        (lambda plan: plan.pop("window"), "window.start"),
    ],
)
def test_validate_plan_rejects_unverified_requests(registries, mutate, expected):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    plan = make_plan()
    mutate(plan)
    violations = adapter.validate_plan(plan)
    assert any(expected in violation for violation in violations)


# ---------------------------------------------------------------------------
# collect / extract / describe (replay)
# ---------------------------------------------------------------------------


def test_collect_replays_the_recorded_response(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    fixture = load_json(FIXTURE_12M)
    result = adapter.collect(make_plan())

    assert result.status == "success"
    assert result.raw == fixture["response"]
    assert result.returned_count == 52
    assert len(result.observations) == 52
    assert result.errors == []
    assert result.completeness == "complete"
    assert result.submitted_parameters["timeframe"] == "today 12-m"
    assert result.temporal["granularity"] == "week"
    assert result.temporal["week_start"] == "sunday"


def test_collect_refuses_a_mismatching_replay(registries):
    """A fixture may only answer the request it records (no fabricated data)."""
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    plan = make_plan(timeframe="today 5-y")
    result = adapter.collect(plan)
    assert result.status == "failed"
    assert result.errors and result.errors[0]["code"] == "TRANSPORT_ERROR"
    assert result.returned_count == 0
    assert result.observations == []
    assert result.completeness == "missing"


def test_live_transport_refuses_without_an_approved_session(registries):
    transport = SessionMcpTransport()
    with pytest.raises(TransportError):
        transport.call("interest_over_time", {})
    adapter = GoogleTrendsMcpAdapter(transport, capabilities={})
    result = adapter.collect(make_plan())
    assert result.status == "failed"
    assert result.returned_count == 0


def test_collect_with_live_callable_uses_it(registries):
    """The live path is a plain callable injection; the tests provide a fake."""
    calls = []

    def fake_call(tool, params):
        calls.append((tool, params))
        return {"keyword": "CBX リキッド", "data": [{"date": "2026-09-13", "value": 44}]}

    adapter = GoogleTrendsMcpAdapter(SessionMcpTransport(fake_call), capabilities={})
    result = adapter.collect(make_plan())
    assert result.status == "success"
    assert calls == [
        (
            "interest_over_time",
            {"terms": ["CBX リキッド"], "geo": "JP", "timeframe": "today 12-m"},
        )
    ]


def test_extract_observations_rejects_malformed_payloads(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    assert adapter.extract_observations(None) == []
    assert adapter.extract_observations({"data": "nope"}) == []
    assert adapter.extract_observations({"data": [{"date": 1, "value": 2}]}) == []
    assert adapter.extract_observations({"data": [{"date": "2026-01-01", "value": "x"}]}) == []


def test_describe_execution_records_the_collection_mode(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)
    description = adapter.describe_execution()
    assert description["collection_mode"] == "recorded_replay"
    assert description["fixture"] == str(FIXTURE_12M)
    assert description["package"] == "google-trends-mcp"
    assert description["version"] == "0.1.1"


# ---------------------------------------------------------------------------
# Real recorded data (read-only compatibility check)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not RECORDED_CBD_5Y.is_file(), reason="recorded dataset not present")
def test_extraction_on_the_real_recorded_series(registries):
    """The extractor handles the shape the repository actually recorded
    (read-only; the file is never modified)."""
    recorded = load_json(RECORDED_CBD_5Y)
    before = RECORDED_CBD_5Y.read_bytes()
    adapter = build_replay_adapter(registries, FIXTURE_5Y)
    observations = adapter.extract_observations(recorded)
    assert len(observations) > 200
    assert all(isinstance(point["date"], str) for point in observations)
    assert all(0 <= point["value"] <= 100 for point in observations)
    dates = [point["date"] for point in observations]
    assert dates == sorted(dates)
    assert RECORDED_CBD_5Y.read_bytes() == before  # read-only


def test_fixtures_are_explicitly_synthetic():
    for path in (FIXTURE_12M, FIXTURE_5Y):
        fixture = load_json(path)
        assert fixture["fixture_kind"] == "recorded_replay"
        assert "NOT a captured response" in fixture["description"]
        assert "data" in fixture["response"]


# ---------------------------------------------------------------------------
# A response the parser refuses is still evidence
# ---------------------------------------------------------------------------


def test_unparseable_response_keeps_the_verbatim_answer():
    """Google Trends answers a below-threshold term with an error result, not
    an empty table.  The adapter must record a *failed* collection (missing,
    never zero) and keep the verbatim response as the payload: discarding the
    answer loses the only evidence of why there is no series."""

    answer = {
        "isError": True,
        "content": [
            {"type": "text", "text": "Error: Not enough data to show a series"}
        ],
    }

    def call(tool, params):
        return answer

    adapter = GoogleTrendsMcpAdapter(SessionMcpTransport(call=call))
    result = adapter.collect(make_plan())

    assert result.status == "failed"
    assert result.completeness == "missing"
    assert result.returned_count == 0
    assert result.observations == []
    assert result.raw == answer
    assert result.errors[0]["code"] == "PARSE_FAILED"
    assert result.errors[0]["reason_codes"] == ["collection_failed"]
    assert "Not enough data" in result.errors[0]["message"]
