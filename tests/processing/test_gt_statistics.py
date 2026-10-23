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


def test_baseline_names_the_missing_raw_timeline() -> None:
    """ISS-20261012-CBD-004: the 5y baseline is summary-only; the recorded
    weeks/mean/peak values cannot be verified against a weekly series that
    was never stored."""

    unavailable = summarize_record(BASELINE)["unavailable"]

    assert "raw_timeline" in unavailable
    assert "summary-only" in unavailable["raw_timeline"]


def test_baseline_exposes_data_period_and_raw_timeline_as_unavailable() -> None:
    """E1/E2 guard (2026-10-16 外部 THCV 原稿での誤用例): the baseline shape
    carries neither endpoints nor a series.  ``stats`` must not hold a
    ``data_period``; the reason stays in ``unavailable`` instead of being
    invented or borrowed from another compound."""

    summary = summarize_record(BASELINE)

    assert "data_period" not in summary["stats"]
    assert "data_period" in summary["unavailable"]
    assert "記録していない" in summary["unavailable"]["data_period"]
    assert "raw_timeline" in summary["unavailable"]
    assert "summary-only" in summary["unavailable"]["raw_timeline"]


def test_baseline_block_carries_no_endpoints_or_series_claim() -> None:
    """E1/E2 guard: the generated block for a baseline summary must not
    imply a weekly raw series exists in the run.  No endpoint range, no
    ``データあり期間``/``初出`` extras, no ``系列`` language - only the
    relative window and the recorded week count."""

    block = render_block(summarize_record(BASELINE), run_id="run-2")

    assert "〜" not in block
    assert "データあり期間" not in block
    assert "初出" not in block
    assert "系列" not in block
    assert "261週" in block
    assert "<code>run-2</code>" in block


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
    standalone CBX series - the boundary-measurement run.

    CBD joined the series shape in 2026-10-15 (ISS-20261012-CBD-004): the bare
    ``CBD`` today 5-y raw timeline was recollected live as a new run, so its
    mean is computed from the weekly series rather than passed through.
    THC, CBG, HHC and THCV followed on 2026-10-23 (same recipe, one new window),
    so no compound's mean is passed through from a summary any more."""

    by_compound = {entry["compound"]: entry for entry in report["compounds"]}

    assert report["summary"]["by_status"] == {"computed": 14}
    assert by_compound["CBD"]["shape"] == "series"
    assert by_compound["CBD"]["stats"]["mean"] == 34.0229
    # The re-collected compounds carry a weekly series, so their mean is
    # computed rather than passed through.
    for compound in (
        "CBD",
        "CBN",
        "THC-O",
        "H4CBH",
        "HHBD",
        "HHCH",
        "CRDP",
        "THCH",
        "CBX",
        "THC",
        "CBG",
        "HHC",
        "THCV",
    ):
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


#: 2026-10-23: the four compounds that only had the 2026-10-08 summary-only
#: baseline run were recollected live, one run each (see the study methodology
#: §2.1.1).  The baseline run stays in raw; it is no longer cited anywhere.
RECOLLECTED_5Y = {
    "THC": "20261023T162500Z-google-trends-thc-5y",
    "CBG": "20261023T160420Z-google-trends-cbg-5y",
    "HHC": "20261023T160428Z-google-trends-hhc-5y",
    "THCV": "20261023T160436Z-google-trends-thcv-5y",
}


def test_report_cites_no_summary_only_run(report: dict) -> None:
    """E1/E2 guard on the committed surface external authors read
    (``docs/audits/gt-summary.json``): a summary-only run records no weekly
    timeline, so it must not be the cited source for any compound.  Every
    compound therefore reports ``shape=series`` with a period it can prove."""

    by_compound = {entry["compound"]: entry for entry in report["compounds"]}

    assert report["summary"]["by_shape"] == {"series": 14}
    for compound, entry in by_compound.items():
        assert entry["shape"] == "series", compound
        assert entry["run_id"] != "20261008T093228Z-google-trends-5y-baseline"
        assert entry["unavailable"] == {}, compound
        assert "data_period" in entry["stats"], compound


def test_recollected_compounds_cite_their_own_window(report: dict) -> None:
    """The four recollections share one window (2021-10-17 .. 2026-10-18), one
    week later than the runs collected on 2026-10-15.  Each page must quote the
    window of the run it cites."""

    by_compound = {entry["compound"]: entry for entry in report["compounds"]}

    for compound, run_id in RECOLLECTED_5Y.items():
        entry = by_compound[compound]
        assert entry["run_id"] == run_id, compound
        assert entry["stats"]["weeks"] == 262, compound
        assert entry["stats"]["data_period"] == "2021-10-17 〜 2026-10-18", compound
        assert by_compound["CBN"]["stats"]["data_period"] not in entry["block"]


def test_report_derives_each_period_from_its_own_run(report: dict) -> None:
    """E1 guard: no compound may borrow another compound's ``data_period``.
    Each period is recomputed from that compound's own record, and a block
    carries no other compound's range (THCV must not quote CBN's
    ``2021-10-10 〜 2026-10-11``)."""

    by_compound = {entry["compound"]: entry for entry in report["compounds"]}
    periods = {
        compound: entry["stats"]["data_period"]
        for compound, entry in by_compound.items()
    }

    for compound, entry in by_compound.items():
        record = load_record(REPO_ROOT / entry["path"])
        dates = [point["date"] for point in record["data"]]
        assert entry["stats"]["data_period"] == f"{dates[0]} 〜 {dates[-1]}"
        for other, period in periods.items():
            if other == compound or period == periods[compound]:
                continue
            assert period not in entry["block"], (compound, other)
