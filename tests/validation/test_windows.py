"""G3 temporal contract primitive tests (c.md §7, §10, §14).

Covers the §14 requirements G3-T03..T07 and the window-registry checks.
Ordering / timezone semantics of standalone window documents remain covered
by tests/validation/test_semantic.py (CV-08); this module exercises the
conversion and calendar helpers those checks build on.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from validation.cli import EXIT_DATA, EXIT_OK
from validation.cli import main as validation_main
from validation.core import validate_document
from validation.schemas.temporal import TEMPORAL_WINDOW_SCHEMA
from validation.semantic import check_temporal_semantics
from validation.windows import (
    WINDOW_MATCH_TOLERANCE,
    check_plan_window_registry,
    check_window_registry_files,
    day_buckets,
    find_window,
    load_window_documents,
    local_window_to_utc,
    month_buckets,
    parse_datetime,
    resolve_relative_timeframe,
    subtract_calendar_months,
    time_buckets,
    week_buckets,
    within_window_tolerance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WINDOWS_DIR = REPO_ROOT / "metadata" / "windows"

UTC = timezone.utc


# ---------------------------------------------------------------------------
# G3-T03: JST -> UTC conversion (c.md §7 exact expected values)
# ---------------------------------------------------------------------------


def test_local_window_to_utc_matches_the_spec_sample():
    result = local_window_to_utc(
        datetime(2026, 9, 1), datetime(2026, 10, 1), "Asia/Tokyo"
    )
    assert result == {
        "start": "2026-08-31T15:00:00Z",
        "end_exclusive": "2026-09-30T15:00:00Z",
    }


def test_local_window_to_utc_rejects_reversed_and_unknown_inputs():
    with pytest.raises(ValueError):
        local_window_to_utc(datetime(2026, 10, 1), datetime(2026, 9, 1), "Asia/Tokyo")
    with pytest.raises(ValueError):
        local_window_to_utc(datetime(2026, 9, 1), datetime(2026, 10, 1), "Not/AZone")


def test_aware_inputs_are_converted_not_overwritten():
    aware = datetime(2026, 9, 1, 9, 0, tzinfo=timezone(timedelta(hours=9)))
    result = local_window_to_utc(aware, aware + timedelta(days=1), "UTC")
    assert result["start"] == "2026-09-01T00:00:00Z"


# ---------------------------------------------------------------------------
# G3-T05: leap-year and month-end arithmetic
# ---------------------------------------------------------------------------


def test_subtract_calendar_months_clamps_month_end():
    assert subtract_calendar_months(datetime(2026, 3, 31, tzinfo=UTC), 1, "UTC") == datetime(
        2026, 2, 28, tzinfo=UTC
    )
    # Leap year: Feb 29 exists (G3-T05).
    assert subtract_calendar_months(datetime(2024, 3, 31, tzinfo=UTC), 1, "UTC") == datetime(
        2024, 2, 29, tzinfo=UTC
    )
    assert subtract_calendar_months(datetime(2026, 1, 31, tzinfo=UTC), 12, "UTC") == datetime(
        2025, 1, 31, tzinfo=UTC
    )


def test_resolve_12m_across_a_year_boundary():
    start, end = resolve_relative_timeframe(
        "today 12-m", datetime(2026, 1, 31, 12, 0, tzinfo=UTC), "UTC"
    )
    assert start == datetime(2025, 1, 31, 12, 0, tzinfo=UTC)
    assert end == datetime(2026, 1, 31, 12, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# G3-T07: relative periods require their reference time
# ---------------------------------------------------------------------------


def test_resolve_relative_timeframe_requires_an_aware_reference():
    with pytest.raises(ValueError):
        resolve_relative_timeframe("today 12-m", None, "UTC")
    with pytest.raises(ValueError):
        resolve_relative_timeframe("today 12-m", datetime(2026, 10, 13), "UTC")
    with pytest.raises(ValueError):
        resolve_relative_timeframe("today 2-y", datetime(2026, 10, 13, tzinfo=UTC), "UTC")


# ---------------------------------------------------------------------------
# G3-T06: DST switch is handled on the declared calendar
# ---------------------------------------------------------------------------


def test_dst_transition_keeps_local_wall_clock():
    """America/New_York: one month before 2026-11-05T12:00Z crosses the end
    of DST; the local wall-clock time is preserved and the UTC offset
    changes (EST -5 -> EDT -4)."""

    shifted = subtract_calendar_months(
        datetime(2026, 11, 5, 12, 0, tzinfo=UTC), 1, "America/New_York"
    )
    assert shifted == datetime(2026, 10, 5, 11, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# G3-T04: month buckets (month-end / year-end boundaries)
# ---------------------------------------------------------------------------


def test_month_buckets_break_on_local_month_boundaries():
    buckets = list(
        month_buckets(
            datetime(2025, 11, 15, tzinfo=UTC),
            datetime(2026, 3, 1, tzinfo=UTC),
            "UTC",
        )
    )
    assert buckets == [
        {"start": "2025-11-15T00:00:00Z", "end_exclusive": "2025-12-01T00:00:00Z"},
        {"start": "2025-12-01T00:00:00Z", "end_exclusive": "2026-01-01T00:00:00Z"},
        {"start": "2026-01-01T00:00:00Z", "end_exclusive": "2026-02-01T00:00:00Z"},
        {"start": "2026-02-01T00:00:00Z", "end_exclusive": "2026-03-01T00:00:00Z"},
    ]


def test_month_buckets_keep_a_leap_february_partial_start():
    buckets = list(
        month_buckets(
            datetime(2028, 1, 31, tzinfo=UTC),
            datetime(2028, 3, 2, tzinfo=UTC),
            "Asia/Tokyo",
        )
    )
    # 2028-01-31T00:00Z is 2028-01-31 09:00 JST: the first bucket ends at the
    # local Feb 1 boundary (2028-01-31T15:00Z).
    assert buckets == [
        {"start": "2028-01-31T00:00:00Z", "end_exclusive": "2028-01-31T15:00:00Z"},
        {"start": "2028-01-31T15:00:00Z", "end_exclusive": "2028-02-29T15:00:00Z"},
        {"start": "2028-02-29T15:00:00Z", "end_exclusive": "2028-03-02T00:00:00Z"},
    ]


def test_month_buckets_never_pad_or_zero_fill():
    with pytest.raises(ValueError):
        list(month_buckets(datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC)))
    with pytest.raises(ValueError):
        list(month_buckets(datetime(2026, 1, 1), datetime(2026, 3, 1)))


# ---------------------------------------------------------------------------
# ISS-20261015-WIN-003: day buckets (deterministic, half-open, partial kept)
# ---------------------------------------------------------------------------


def test_day_buckets_keep_partial_first_and_last_buckets():
    """PM plan AC1: 2026-10-01T12:00Z -> 2026-10-04T03:00Z (UTC)."""
    buckets = list(
        day_buckets(
            datetime(2026, 10, 1, 12, 0, tzinfo=UTC),
            datetime(2026, 10, 4, 3, 0, tzinfo=UTC),
            "UTC",
        )
    )
    assert buckets == [
        {"start": "2026-10-01T12:00:00Z", "end_exclusive": "2026-10-02T00:00:00Z"},
        {"start": "2026-10-02T00:00:00Z", "end_exclusive": "2026-10-03T00:00:00Z"},
        {"start": "2026-10-03T00:00:00Z", "end_exclusive": "2026-10-04T00:00:00Z"},
        {"start": "2026-10-04T00:00:00Z", "end_exclusive": "2026-10-04T03:00:00Z"},
    ]


def test_day_buckets_break_on_local_midnight_in_asia_tokyo():
    """Same window as above evaluated on Asia/Tokyo: local midnights are
    15:00Z of the previous day."""
    buckets = list(
        day_buckets(
            datetime(2026, 10, 1, 12, 0, tzinfo=UTC),
            datetime(2026, 10, 4, 3, 0, tzinfo=UTC),
            "Asia/Tokyo",
        )
    )
    assert buckets == [
        {"start": "2026-10-01T12:00:00Z", "end_exclusive": "2026-10-01T15:00:00Z"},
        {"start": "2026-10-01T15:00:00Z", "end_exclusive": "2026-10-02T15:00:00Z"},
        {"start": "2026-10-02T15:00:00Z", "end_exclusive": "2026-10-03T15:00:00Z"},
        {"start": "2026-10-03T15:00:00Z", "end_exclusive": "2026-10-04T03:00:00Z"},
    ]


def test_day_buckets_span_a_dst_transition_on_wall_clock():
    """America/New_York ends DST on 2026-11-01: the Nov 1 bucket is 25 hours
    long on the wall clock, never shifted."""
    buckets = list(
        day_buckets(
            datetime(2026, 10, 31, 4, 0, tzinfo=UTC),  # Oct 31 00:00 EDT
            datetime(2026, 11, 2, 5, 0, tzinfo=UTC),  # Nov 2 00:00 EST
            "America/New_York",
        )
    )
    assert buckets == [
        {"start": "2026-10-31T04:00:00Z", "end_exclusive": "2026-11-01T04:00:00Z"},
        {"start": "2026-11-01T04:00:00Z", "end_exclusive": "2026-11-02T05:00:00Z"},
    ]


def test_day_buckets_fail_closed():
    with pytest.raises(ValueError):
        list(day_buckets(datetime(2026, 10, 2), datetime(2026, 10, 3)))
    with pytest.raises(ValueError):
        list(day_buckets(datetime(2026, 10, 3, tzinfo=UTC), datetime(2026, 10, 2, tzinfo=UTC)))
    with pytest.raises(ValueError):
        list(
            day_buckets(
                datetime(2026, 10, 1, tzinfo=UTC),
                datetime(2026, 10, 2, tzinfo=UTC),
                "Not/AZone",
            )
        )


# ---------------------------------------------------------------------------
# ISS-20261015-WIN-003: week buckets honor week_start on the named calendar
# ---------------------------------------------------------------------------


def test_week_buckets_sunday_start_in_asia_tokyo():
    """2026-10-01 (Thu) -> 2026-10-15 (Thu) 00:00Z; Sundays Oct 4 / Oct 11
    JST are the boundaries (Oct 4 00:00 JST = Oct 3 15:00Z)."""
    buckets = list(
        week_buckets(
            datetime(2026, 10, 1, tzinfo=UTC),
            datetime(2026, 10, 15, tzinfo=UTC),
            "Asia/Tokyo",
            "sunday",
        )
    )
    assert buckets == [
        {"start": "2026-10-01T00:00:00Z", "end_exclusive": "2026-10-03T15:00:00Z"},
        {"start": "2026-10-03T15:00:00Z", "end_exclusive": "2026-10-10T15:00:00Z"},
        {"start": "2026-10-10T15:00:00Z", "end_exclusive": "2026-10-15T00:00:00Z"},
    ]


def test_week_buckets_monday_start_in_asia_tokyo():
    """Same window with Monday start: boundaries are Oct 5 / Oct 12 JST."""
    buckets = list(
        week_buckets(
            datetime(2026, 10, 1, tzinfo=UTC),
            datetime(2026, 10, 15, tzinfo=UTC),
            "Asia/Tokyo",
            "monday",
        )
    )
    assert buckets == [
        {"start": "2026-10-01T00:00:00Z", "end_exclusive": "2026-10-04T15:00:00Z"},
        {"start": "2026-10-04T15:00:00Z", "end_exclusive": "2026-10-11T15:00:00Z"},
        {"start": "2026-10-11T15:00:00Z", "end_exclusive": "2026-10-15T00:00:00Z"},
    ]


def test_week_buckets_starting_exactly_on_a_boundary():
    """A window starting at a Sunday midnight (UTC) yields whole weeks."""
    buckets = list(
        week_buckets(
            datetime(2026, 10, 4, tzinfo=UTC),  # a Sunday
            datetime(2026, 10, 18, tzinfo=UTC),
            "UTC",
            "sunday",
        )
    )
    assert buckets == [
        {"start": "2026-10-04T00:00:00Z", "end_exclusive": "2026-10-11T00:00:00Z"},
        {"start": "2026-10-11T00:00:00Z", "end_exclusive": "2026-10-18T00:00:00Z"},
    ]


def test_week_buckets_fail_closed():
    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 10, 8, tzinfo=UTC)
    with pytest.raises(ValueError):
        list(week_buckets(datetime(2026, 10, 1), end, "UTC", "sunday"))
    with pytest.raises(ValueError):
        list(week_buckets(end, start, "UTC", "sunday"))
    with pytest.raises(ValueError):
        list(week_buckets(start, end, "Not/AZone", "sunday"))
    for bad in ("friday", "", None, 0):
        with pytest.raises(ValueError):
            list(week_buckets(start, end, "UTC", bad))


# ---------------------------------------------------------------------------
# ISS-20261015-WIN-003: shared dispatcher
# ---------------------------------------------------------------------------


def test_time_buckets_dispatches_day_week_month():
    start = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    end = datetime(2026, 10, 4, 3, 0, tzinfo=UTC)
    assert list(time_buckets(start, end, "day", "UTC")) == list(
        day_buckets(start, end, "UTC")
    )
    assert list(time_buckets(start, end, "month", "UTC")) == list(
        month_buckets(start, end, "UTC")
    )
    week_start = datetime(2026, 10, 1, tzinfo=UTC)
    week_end = datetime(2026, 10, 15, tzinfo=UTC)
    assert list(time_buckets(week_start, week_end, "week", "UTC", "monday")) == list(
        week_buckets(week_start, week_end, "UTC", "monday")
    )
    with pytest.raises(ValueError):
        list(time_buckets(start, end, "hour", "UTC"))
    with pytest.raises(ValueError):
        list(time_buckets(start, end, "year", "UTC"))


# ---------------------------------------------------------------------------
# window matching tolerance / parsing
# ---------------------------------------------------------------------------


def test_within_window_tolerance_is_one_weekly_bucket():
    start = datetime(2025, 10, 12, tzinfo=UTC)
    end = datetime(2026, 10, 12, tzinfo=UTC)
    assert within_window_tolerance((start, end), (start, end)) is True
    off = timedelta(days=7)
    assert within_window_tolerance((start + off, end - off), (start, end)) is True
    too_far = timedelta(days=8)
    assert within_window_tolerance((start + too_far, end), (start, end)) is False
    assert WINDOW_MATCH_TOLERANCE == timedelta(days=7)


def test_parse_datetime_requires_an_explicit_timezone():
    assert parse_datetime("2026-10-13T00:00:00Z") == datetime(2026, 10, 13, tzinfo=UTC)
    for bad in ("2026-10-13T00:00:00", "", None, "not-a-date"):
        with pytest.raises(ValueError):
            parse_datetime(bad)


# ---------------------------------------------------------------------------
# window registry (metadata/windows)
# ---------------------------------------------------------------------------


def test_repository_window_registry_is_present_and_valid():
    documents = load_window_documents(WINDOWS_DIR)
    assert {document["window_id"] for document in documents} == {
        "2021-10-10_2026-10-12",
        "2021-10-17_2026-10-18",
        "2025-10-12_2026-10-12",
    }
    for document in documents:
        assert validate_document(document, TEMPORAL_WINDOW_SCHEMA).valid is True
        assert check_temporal_semantics(document) == []


def test_check_window_registry_files_flags_duplicates_and_stem_mismatch():
    items = [
        (Path("/x/a.json"), {"window_id": "a"}),
        (Path("/x/c.json"), {"window_id": "a"}),
    ]
    results = check_window_registry_files(items)
    assert results["/x/a.json"] == []
    codes = sorted(issue.code for issue in results["/x/c.json"])
    assert codes == ["WINDOW_FILE_STEM_MISMATCH", "WINDOW_ID_DUPLICATE"]


def test_check_plan_window_registry_matches_exactly_or_fails_closed():
    windows = load_window_documents(WINDOWS_DIR)
    registered = find_window(windows, "2025-10-12_2026-10-12")
    assert registered is not None
    assert check_plan_window_registry(dict(registered), windows) == []

    missing = check_plan_window_registry({"window_id": "nope"}, windows)
    assert [issue.code for issue in missing] == ["WINDOW_UNREGISTERED"]

    drifted = dict(registered)
    drifted["end_exclusive"] = "2026-10-05T00:00:00Z"
    issues = check_plan_window_registry(drifted, windows)
    assert [issue.code for issue in issues] == ["WINDOW_REGISTRY_MISMATCH"]
    assert issues[0].path == "/window/end_exclusive"

    # No window_id in the plan: the registry check does not apply (P6
    # backward compatibility for plans that predate the registry).
    assert check_plan_window_registry({"start": "x"}, windows) == []


# ---------------------------------------------------------------------------
# validate-registries integration
# ---------------------------------------------------------------------------


def test_validate_registries_covers_the_window_registry(capsys):
    code = validation_main(
        [
            "validate-registries",
            "--config-dir",
            str(REPO_ROOT / "config"),
            "--metadata-dir",
            str(REPO_ROOT / "metadata"),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    bundle = json.loads(captured.out)
    assert code == EXIT_OK
    window_targets = [
        report["target"]
        for report in bundle["reports"]
        if report["schema_id"] == "temporal-window-v1"
    ]
    assert len(window_targets) == len(list(WINDOWS_DIR.glob("*.json")))
    assert all("metadata/windows/" in target or "metadata\\windows\\" in target for target in window_targets)


def test_validate_registries_flags_a_reversed_window(capsys, tmp_path):
    metadata = tmp_path / "metadata"
    windows = metadata / "windows"
    windows.mkdir(parents=True)
    (windows / "2026-q4.json").write_text(
        json.dumps(
            {
                "window_id": "2026-q4",
                "timezone": "UTC",
                "start": "2026-12-01T00:00:00Z",
                "end_exclusive": "2026-10-01T00:00:00Z",
                "granularity": "day",
            }
        ),
        encoding="utf-8",
    )
    code = validation_main(
        [
            "validate-registries",
            "--config-dir",
            str(tmp_path / "empty-config"),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_DATA
    assert "TEMPORAL_ORDER_INVALID" in captured.err


def test_validate_registries_flags_duplicate_window_ids(capsys, tmp_path):
    metadata = tmp_path / "metadata"
    windows = metadata / "windows"
    windows.mkdir(parents=True)
    base = {
        "timezone": "UTC",
        "start": "2026-10-01T00:00:00Z",
        "end_exclusive": "2026-10-08T00:00:00Z",
        "granularity": "day",
    }
    (windows / "one.json").write_text(
        json.dumps({"window_id": "one", **base}), encoding="utf-8"
    )
    (windows / "two.json").write_text(
        json.dumps({"window_id": "one", **base}), encoding="utf-8"
    )
    code = validation_main(
        [
            "validate-registries",
            "--config-dir",
            str(tmp_path / "empty-config"),
            "--metadata-dir",
            str(metadata),
        ]
    )
    captured = capsys.readouterr()
    assert code == EXIT_DATA
    assert "WINDOW_ID_DUPLICATE" in captured.err
    assert "WINDOW_FILE_STEM_MISMATCH" in captured.err
