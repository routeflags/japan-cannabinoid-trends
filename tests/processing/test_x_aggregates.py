"""Aggregator tests for ISS-20261014-PUB-029 option ii.

The private per-post input is read-only and never committed; the real-data
test runs only where the non-published copy is present and otherwise skips
(the rule itself is covered by fixtures unconditionally).
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from processing.aggregate_x import (
    AGGREGATOR_VERSION,
    INPUT_COLUMNS,
    MONTHLY_COLUMNS,
    WEEKLY_COLUMNS,
    AggregateError,
    aggregate_rows,
    bin_engagement,
    bin_text_length,
    month_of,
    parse_created_at,
    read_private_input,
    scan_output_for_identifiers,
    week_monday_of,
    write_aggregate_csv,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIVATE = "datasets/cbx-social-trends/data/private/x_cbx_202608_summary_anonymized.csv"
EXPECTED_INPUT_SHA = "f27f979a19e7e4925ae0b5d442beeec027e667ce5b10247934066a5b1ed463a6"

requires_private = pytest.mark.skipif(
    not (REPO_ROOT / PRIVATE).is_file(),
    reason="non-published X per-post input not present in this checkout",
)


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "tweet_id_hash": "abc",
        "createdAt": "2026-08-05T04:45:25.000Z",
        "week": "W1",
        "lang": "ja",
        "author_id": "author_001",
        "views": "10",
        "likes": "3",
        "reposts": "1",
        "replies": "0",
        "has_text": "yes",
        "text_length": "70",
        "topic_id": "topic_ingredient",
        "intent_id": "intent_informational",
        "format_id": "format_text",
        "platform": "x_twitter",
        "language": "ja",
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", "0"),
        ("1", "1"),
        ("4", "1"),
        ("5", "2"),
        ("19", "2"),
        ("20", "3"),
        ("99", "3"),
        ("100", "4"),
        ("499", "4"),
        ("500", "5"),
        ("1999", "5"),
        ("2000", "6"),
        ("9999", "6"),
        ("10000", "7"),
        ("17247", "7"),
        ("", ""),
    ],
)
def test_engagement_bin_boundaries(value: str, expected: str) -> None:
    assert bin_engagement(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", "0"),
        ("1", "1"),
        ("20", "1"),
        ("21", "2"),
        ("50", "2"),
        ("51", "3"),
        ("100", "3"),
        ("101", "4"),
        ("200", "4"),
        ("201", "5"),
        ("280", "5"),
        ("281", "6"),
        ("", ""),
    ],
)
def test_text_length_bin_boundaries(value: str, expected: str) -> None:
    assert bin_text_length(value) == expected


def test_missing_and_zero_are_distinct() -> None:
    assert bin_engagement("") == ""
    assert bin_engagement("0") == "0"
    assert bin_text_length("") == ""
    assert bin_text_length("0") == "0"


@pytest.mark.parametrize("value", ["-1", "-0", "1.5", "1.0", "abc", "NULL", "1,000", "  "])
def test_invalid_counts_are_rejected(value: str) -> None:
    if value.strip() == "":
        assert bin_engagement(value) == ""
        return
    with pytest.raises(AggregateError):
        bin_engagement(value)


def test_negative_and_decimal_text_lengths_are_rejected() -> None:
    for value in ("-5", "12.5", "large"):
        with pytest.raises(AggregateError):
            bin_text_length(value)


def test_month_and_week_normalization() -> None:
    assert month_of(parse_created_at("2026-08-03T09:21:35Z")) == "2026-08-01"
    assert month_of(parse_created_at("2026-09-02T02:10:00Z")) == "2026-09-01"
    assert week_monday_of(parse_created_at("2026-08-05T04:45:25.000Z")) == "2026-08-03"
    assert week_monday_of(parse_created_at("2026-08-31T00:01:33.000Z")) == "2026-08-31"


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(AggregateError, match="no timezone"):
        parse_created_at("2026-08-05T04:45:25")


def test_invalid_datetime_becomes_unknown_period() -> None:
    weekly, monthly, diagnostics = aggregate_rows([_row(createdAt="not-a-date")])
    assert weekly[0]["week_start"] == ""
    assert monthly[0]["month"] == ""
    assert diagnostics["unknown_period_rows"] == 1


def test_totals_reconcile_on_fixtures() -> None:
    rows = [
        _row(createdAt="2026-08-05T04:45:25.000Z"),
        _row(createdAt="2026-08-05T11:35:00.000Z"),
        _row(createdAt="2026-09-02T02:10:00.000Z", topic_id="topic_review"),
    ]
    weekly, monthly, diagnostics = aggregate_rows(rows)
    assert sum(int(r["post_count"]) for r in weekly) == 3
    assert sum(int(r["post_count"]) for r in monthly) == 3
    assert diagnostics["input_rows"] == 3


def test_identical_posts_share_one_group() -> None:
    rows = [_row(), _row()]
    weekly, monthly, _ = aggregate_rows(rows)
    assert len(weekly) == 1 and weekly[0]["post_count"] == "2"
    assert len(monthly) == 1 and monthly[0]["post_count"] == "2"


def test_output_carries_no_per_post_content() -> None:
    rows = [_row(), _row(createdAt="2026-09-02T02:10:00.000Z")]
    weekly, monthly, _ = aggregate_rows(rows)
    assert tuple(weekly[0]) == WEEKLY_COLUMNS
    assert tuple(monthly[0]) == MONTHLY_COLUMNS
    assert scan_output_for_identifiers(WEEKLY_COLUMNS, weekly) == []
    assert scan_output_for_identifiers(MONTHLY_COLUMNS, monthly) == []
    blob = "\n".join(str(v) for r in weekly + monthly for v in r.values())
    assert "author_001" not in blob
    assert "abc" not in blob.replace("CBX", "")


def test_determinism_and_idempotency(tmp_path: Path) -> None:
    rows = [_row(), _row(createdAt="2026-09-02T02:10:00.000Z")]
    first_w, first_m, _ = aggregate_rows(rows)
    second_w, second_m, _ = aggregate_rows(rows)
    assert first_w == second_w and first_m == second_m
    target = tmp_path / "weekly.csv"
    write_aggregate_csv(target, WEEKLY_COLUMNS, first_w)
    before = target.read_bytes()
    write_aggregate_csv(target, WEEKLY_COLUMNS, second_w)
    assert target.read_bytes() == before


def test_small_cells_are_reported_not_removed() -> None:
    rows = [_row(), _row(createdAt="2026-09-02T02:10:00.000Z")]
    weekly, _, _ = aggregate_rows(rows)
    assert all(int(r["post_count"]) == 1 for r in weekly)
    assert len(weekly) == 2


def test_wrong_header_is_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(AggregateError, match="input header"):
        read_private_input(bad)


@requires_private
def test_private_input_totals_reconcile() -> None:
    rows, digest = read_private_input(REPO_ROOT / PRIVATE)
    assert digest == EXPECTED_INPUT_SHA
    assert len(rows) == 147
    assert tuple(rows[0]) == INPUT_COLUMNS
    weekly, monthly, diagnostics = aggregate_rows(rows)
    assert sum(int(r["post_count"]) for r in weekly) == 147
    assert sum(int(r["post_count"]) for r in monthly) == 147
    assert diagnostics["legacy_week_unknown_with_valid_timestamp"] == 3
    assert scan_output_for_identifiers(WEEKLY_COLUMNS, weekly) == []
    assert scan_output_for_identifiers(MONTHLY_COLUMNS, monthly) == []


@requires_private
def test_private_input_is_unmodified_by_aggregation(tmp_path: Path) -> None:
    from processing.aggregate_x import sha256_file

    before = sha256_file(REPO_ROOT / PRIVATE)
    rows, _ = read_private_input(REPO_ROOT / PRIVATE)
    aggregate_rows(rows)
    write_aggregate_csv(tmp_path / "w.csv", WEEKLY_COLUMNS, aggregate_rows(rows)[0])
    assert sha256_file(REPO_ROOT / PRIVATE) == before == EXPECTED_INPUT_SHA


def test_aggregator_version_is_recorded() -> None:
    assert AGGREGATOR_VERSION == "1.0.0"
