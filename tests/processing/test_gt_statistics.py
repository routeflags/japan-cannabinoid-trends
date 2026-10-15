"""The Google Trends summary must be recomputed from the record, not typed.

ISS-20261015-GT-003 exists because three published 5-year averages could not be
reproduced from any committed record.  These tests fix both halves of the
answer: what a record can produce is computed (and equals what the pages show),
and what it cannot produce is reported as unavailable with the missing input
named - never invented.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from processing.gt_statistics import (
    PUBLICATION_COMPOUNDS,
    TIMEFRAMES,
    UNCOMPUTABLE_MARKER,
    build_gt_summary,
    classify_shape,
    find_run,
    load_record,
    page_filename,
    record_keyword,
    render_block,
    render_not_collected,
    replace_block,
    summarize_record,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"

SERIES = {
    "keyword": "THCH",
    "geo": "JP",
    "timeframe": "today 12-m",
    "collected_at": "2026-10-02",
    "data": [
        {"date": "2026-01-04", "value": 0},
        {"date": "2026-01-11", "value": 0},
        {"date": "2026-01-18", "value": 50},
        {"date": "2026-01-25", "value": 100},
        {"date": "2026-02-01", "value": 50},
    ],
}

BASELINE = {
    "compound": "CBD",
    "timeframe": "today 5-y",
    "collected_at": "2026-10-06",
    "data_points": 261,
    "first_value": 42,
    "last_value": 14,
    "peak_value": 100,
    "peak_date": "2025-08-31 to 2025-09-06",
    "avg_5y": 32.5,
}

PARTIAL = {
    "keyword": "H4CBH",
    "geo": "JP",
    "timeframe": "today 5-y",
    "collected_at": "2026-10-02",
    "first_mention": "2025-04-06",
    "first_value": 41,
    "peak": {"date": "2026-07-26", "value": 100},
    "data_summary": {
        "period_with_data": "2025-04-06 〜 2026-10-03 (断続的)",
        "data_points_nonzero": 65,
        "data_points_zero": 197,
    },
}

AVERAGED = {
    "keyword": "CRDH",
    "geo": "JP",
    "timeframe": "today 5-y",
    "collected_at": "2026-10-08",
    "first_mention": "2023-09-24",
    "first_value": 48,
    "peak": {"date": "2024-12-15", "value": 100},
    "data_summary": {
        "total_weeks": 261,
        "nonzero_weeks": 38,
        "zero_weeks": 223,
        "average_all": 15.3,
        "average_nonzero": 73.4,
    },
}


def test_shapes_are_recognised() -> None:
    assert classify_shape(SERIES) == "series"
    assert classify_shape(BASELINE) == "baseline"
    assert classify_shape(PARTIAL) == "partial"
    assert classify_shape(AVERAGED) == "averaged"


def test_series_is_recomputed_in_full() -> None:
    stats = summarize_record(SERIES)["stats"]

    assert stats["weeks"] == 5
    assert stats["mean"] == 40.0
    assert stats["peak_date"] == "2026-01-25"
    assert stats["peak_value"] == 100
    assert stats["last_value"] == 50
    assert stats["first_nonzero_date"] == "2026-01-18"
    assert stats["nonzero_weeks"] == 3
    assert stats["zero_weeks"] == 2


def test_baseline_passes_recorded_values_through() -> None:
    summary = summarize_record(BASELINE)

    assert summary["stats"]["mean"] == 32.5
    assert summary["stats"]["peak_date"] == "2025-08-31"
    assert summary["stats"]["last_value"] == 14
    assert "first_nonzero_date" in summary["unavailable"]


def test_average_is_unavailable_when_the_record_has_none() -> None:
    """The 2026-10-02 runs stored neither a series nor an average."""

    summary = summarize_record(PARTIAL)

    assert summary["stats"]["mean"] is None
    assert summary["stats"]["weeks"] == 262
    assert "平均値" in summary["unavailable"]["mean"]
    assert "last_value" in summary["unavailable"]
    assert summary["stats"]["peak_date"] == "2026-07-26"
    assert summary["stats"]["first_nonzero_date"] == "2025-04-06"


def test_recorded_average_is_used_when_present() -> None:
    assert summarize_record(AVERAGED)["stats"]["mean"] == 15.3


def test_render_marks_what_the_record_cannot_support() -> None:
    block = render_block(summarize_record(PARTIAL), run_id="run-1")

    assert block.count(UNCOMPUTABLE_MARKER) == 2
    assert "<code>run-1</code>" in block
    assert "非ゼロ 65 週" in block
    assert "初出 2025-04-06" in block


def test_render_keeps_recorded_precision() -> None:
    block = render_block(summarize_record(BASELINE), run_id="run-2")

    assert "<td><strong>32.5</strong></td>" in block
    assert "<td>14</td>" in block  # not 14.0: the record stored 14
    assert UNCOMPUTABLE_MARKER not in block


def test_not_collected_names_the_gap_and_the_absence_of_data() -> None:
    block = render_not_collected("THCH")

    assert "未取得" in block
    assert "需要ゼロを意味しない" in block


def test_find_run_ignores_the_product_line_series() -> None:
    """「○○ リキッド」 is a different query and must not stand in."""

    path = find_run(DATASETS, "CBN", TIMEFRAMES["5y"])

    assert path is not None
    record = load_record(path)
    assert record_keyword(record) == "CBN"
    assert record["timeframe"] == "today 5-y"
    assert "リキッド" not in record_keyword(record)


def test_replace_block_keeps_the_next_section() -> None:
    """A block anchor that consumes the next heading deletes the 12-month table:
    the replacement carries one table, so the page must still carry its own plus
    the 12-month one."""

    page = (REPO_ROOT / "publication" / "research_cbd.html").read_text(encoding="utf-8")
    replaced = replace_block(page, render_block(summarize_record(BASELINE), run_id="test"))

    assert "12ヶ月データサマリー" in replaced
    assert replaced.count("<table") == page.count("<table")
    assert "<td>12ヶ月平均</td>" in replaced


@pytest.fixture(scope="module")
def report() -> dict:
    return build_gt_summary(DATASETS, PUBLICATION_COMPOUNDS, TIMEFRAMES["5y"])


def test_report_recomputes_every_compound(report: dict) -> None:
    """14 of 14: CBX joined in 2026-10-15 (research_cbx.html), citing the only
    standalone CBX series - the boundary-measurement run."""

    by_compound = {entry["compound"]: entry for entry in report["compounds"]}

    assert report["summary"]["by_status"] == {"computed": 14}
    assert by_compound["CBD"]["stats"]["mean"] == 32.5
    # The re-collected compounds carry a weekly series, so their mean is
    # computed rather than passed through.
    for compound in ("CBN", "THC-O", "H4CBH", "HHBD", "HHCH", "CRDP", "THCH", "CBX"):
        assert by_compound[compound]["shape"] == "series", compound
        assert by_compound[compound]["stats"]["mean"] is not None, compound
    assert by_compound["CBX"]["run_id"] == "20261015T042857Z-google-trends-boundary-5y"


def test_means_are_no_longer_unavailable(report: dict) -> None:
    """This list was the reason the 5-year re-collection was requested."""

    assert report["summary"]["unavailable_mean"] == []


def test_every_page_carries_the_generated_block(report: dict) -> None:
    """The permanent loop: a page's 5-year block is the tool's output."""

    for entry in report["compounds"]:
        page = REPO_ROOT / "publication" / page_filename(entry["compound"])
        assert entry["block"] in page.read_text(encoding="utf-8"), entry["compound"]
