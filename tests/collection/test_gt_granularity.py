"""The Google Trends temporal granularity follows the returned series.

Why this exists: the adapter recorded ``granularity: week`` for every request,
but ``today 3-m`` comes back as 93 daily points.  The metadata contradicted the
payload (ISS-20261105-GT-031), and a reader could not tell whether the 3-month
series was weekly or daily from the run record alone.

The rule: the labels decide.  Consecutive days are ``day``, seven-day steps are
``week``.  A capture with no series keeps the timeframe's documented bucket.
The raw payload is never rewritten; this is metadata for future collections.
"""

import json

import pytest

from collection.adapters.google_trends.adapter import (
    default_granularity,
    series_granularity,
)

from conftest import FIXTURE_12M, build_replay_adapter, make_plan


def _daily_fixture(path, *, days=93, start="2026-08-04", timeframe="today 3-m"):
    from datetime import date, timedelta

    first = date.fromisoformat(start)
    response = {
        "keyword": "THCNM",
        "geo": "JP",
        "timeframe": timeframe,
        "collected_at": "2026-11-04T17:52:20Z",
        "data": [
            {"date": (first + timedelta(days=offset)).isoformat(), "value": offset % 7}
            for offset in range(days)
        ],
    }
    document = {
        "fixture_kind": "recorded_replay",
        "description": "Synthetic daily 3-month response (contract test only).",
        "request": {
            "tool": "interest_over_time",
            "params": {"terms": ["THCNM"], "geo": "JP", "timeframe": timeframe},
        },
        "response": response,
    }
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "dates,expected",
    [
        (["2026-08-04", "2026-08-05", "2026-08-06"], "day"),
        (["2026-08-04", "2026-08-11", "2026-08-18"], "week"),
        (["2026-08-04"], "week"),
        (["2026-08-04", "2026-08-06"], "week"),
        ([], "week"),
    ],
)
def test_the_label_spacing_decides_the_bucket(dates, expected):
    assert series_granularity(dates) == expected


def test_a_series_with_no_step_keeps_the_timeframe_default():
    assert series_granularity([], default="day") == "day"


@pytest.mark.parametrize(
    "timeframe,expected",
    [
        ("now 7-d", "day"),
        ("today 1-m", "day"),
        ("today 3-m", "day"),
        ("today 12-m", "week"),
        ("today 5-y", "week"),
        ("2025-01-01 2025-12-31", "week"),
    ],
)
def test_the_fallback_bucket_follows_the_timeframe(timeframe, expected):
    assert default_granularity(timeframe) == expected


def test_daily_three_month_payload_records_day(registries, tmp_path):
    """Regression: 93 daily points must not be labelled weekly."""

    fixture = _daily_fixture(tmp_path / "daily_3m.json")
    adapter = build_replay_adapter(registries, fixture)
    plan = make_plan(
        term="THCNM",
        timeframe="today 3-m",
        start="2026-08-06T00:00:00Z",
        end_exclusive="2026-11-04T00:00:00Z",
        window_id="2026-08-06_2026-11-04",
        granularity="day",
        week_start=None,
        query_id="thcnm-general-ja",
        compound_id="compound_thcnm",
    )

    result = adapter.collect(plan)

    assert result.status == "success"
    assert result.returned_count == 93
    assert result.temporal["granularity"] == "day"
    assert result.temporal["week_start"] is None
    assert "daily points" in result.temporal["boundary_semantics"]


def test_weekly_twelve_month_payload_still_records_week(registries):
    adapter = build_replay_adapter(registries, FIXTURE_12M)

    result = adapter.collect(make_plan())

    assert result.temporal["granularity"] == "week"
    assert result.temporal["week_start"] == "sunday"
