"""YouTube Apify dateFilter window compiler tests (WIN-002 MVP).

The compiler is deliberately limited to the measured COL-033
``dateFilter=year`` case.  These tests use synthetic windows only; no live
Apify call and no raw CSV payload are used.
"""

import json

from collection.adapters import get_window_compiler, registered_sources
from collection.adapters.youtube.compiler import YouTubeApifyWindowCompiler
from collection.core.cli import EXIT_CONFIG, EXIT_GATE, EXIT_OK
from collection.core.cli import main as collection_main
from validation.windows import check_window_compiler

from conftest import REPO_CONFIG, REPO_METADATA

REFERENCE_TIME = "2026-10-11T19:19:02Z"
YEAR_WINDOW = {
    "window_id": "youtube-datefilter-year-evidence",
    "timezone": "UTC",
    "start": "2025-10-11T00:00:00Z",
    "end_exclusive": "2026-10-10T00:00:00Z",
    "granularity": "day",
}


def _expect_refusal(window, **kwargs):
    try:
        YouTubeApifyWindowCompiler().compile(
            window,
            reference_time=kwargs.pop("reference_time", REFERENCE_TIME),
            **kwargs,
        )
    except Exception as error:  # noqa: BLE001 - asserted below
        return error
    raise AssertionError("compilation should have been refused")


def test_youtube_compiler_satisfies_common_contract_and_dispatch():
    compiler = YouTubeApifyWindowCompiler()
    assert check_window_compiler(compiler) == []
    assert compiler.collector_id == "youtube-apify-scraper"
    assert isinstance(get_window_compiler("youtube-apify-scraper"), YouTubeApifyWindowCompiler)
    # Window compilation does not make YouTube a live collection source.
    assert "youtube" not in registered_sources()


def test_compile_measured_year_filter_keeps_request_and_observed_window_separate():
    compiled = YouTubeApifyWindowCompiler().compile(
        YEAR_WINDOW,
        reference_time=REFERENCE_TIME,
        capabilities={"absolute_date_range": "unknown", "relative_date_range": "unknown"},
    )

    assert compiled.parameters == {"dateFilter": "year"}
    assert compiled.collector_window_type == "relative_duration"
    assert compiled.exact is False
    assert compiled.boundary_semantics == "observed_range_consistent_with_measured_year_filter"
    assert compiled.reference_time == REFERENCE_TIME
    assert compiled.resolved_start == "2025-10-11T00:00:00Z"
    assert compiled.resolved_end_exclusive == "2026-10-11T00:00:00Z"
    assert compiled.requested_start == YEAR_WINDOW["start"]
    assert compiled.requested_end_exclusive == YEAR_WINDOW["end_exclusive"]
    assert any("not be treated as the API search condition" in text for text in compiled.limitations)


def test_compile_refuses_unmeasured_shorter_date_filters():
    month_like_window = {
        "window_id": "youtube-month-like",
        "timezone": "UTC",
        "start": "2026-09-10T00:00:00Z",
        "end_exclusive": "2026-10-10T00:00:00Z",
        "granularity": "day",
    }

    error = _expect_refusal(month_like_window, reference_time="2026-10-10T20:59:30Z")
    assert error.codes == ["no_verified_date_filter_matches"]


def test_compile_refuses_unbounded_all_filter_shape():
    five_year_window = {
        "window_id": "youtube-all-like",
        "timezone": "UTC",
        "start": "2021-10-11T00:00:00Z",
        "end_exclusive": "2026-10-10T00:00:00Z",
        "granularity": "day",
    }

    error = _expect_refusal(five_year_window)
    assert error.codes == ["no_verified_date_filter_matches"]


def test_compile_rejects_invalid_inputs():
    assert _expect_refusal(YEAR_WINDOW, reference_time=None).codes == [
        "reference_time_missing"
    ]
    assert _expect_refusal(YEAR_WINDOW, reference_time="not-a-date").codes == [
        "reference_time_invalid"
    ]
    bad_timezone = {
        **YEAR_WINDOW,
        "timezone": "Not/AZone",
    }
    assert _expect_refusal(bad_timezone).codes == ["timezone_unknown"]
    reversed_window = {
        **YEAR_WINDOW,
        "start": "2026-10-10T00:00:00Z",
        "end_exclusive": "2025-10-11T00:00:00Z",
    }
    assert _expect_refusal(reversed_window).codes == ["window_invalid"]


def test_compile_refuses_absolute_or_relative_capability_conflicts():
    assert _expect_refusal(
        YEAR_WINDOW,
        capabilities={"absolute_date_range": "supported"},
    ).codes == ["absolute_path_not_implemented"]
    assert _expect_refusal(
        YEAR_WINDOW,
        capabilities={"relative_date_range": "unsupported"},
    ).codes == ["relative_date_filter_unsupported"]


def test_compile_window_cli_supports_youtube_year_filter(capsys, tmp_path):
    window_path = tmp_path / "youtube-year-window.json"
    window_path.write_text(json.dumps(YEAR_WINDOW), encoding="utf-8")

    code = collection_main(
        [
            "compile-window",
            "--window",
            str(window_path),
            "--collector",
            "youtube-apify-scraper",
            "--reference-time",
            REFERENCE_TIME,
            "--config-dir",
            str(REPO_CONFIG),
            "--metadata-dir",
            str(REPO_METADATA),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert code == EXIT_OK
    assert report["refused"] is False
    assert report["compiled"]["parameters"] == {"dateFilter": "year"}
    assert "parameters=dateFilter=year" in captured.err


def test_compile_window_cli_refuses_unmeasured_youtube_window(capsys, tmp_path):
    window = {**YEAR_WINDOW, "start": "2026-09-10T00:00:00Z"}
    window_path = tmp_path / "youtube-month-like-window.json"
    window_path.write_text(json.dumps(window), encoding="utf-8")

    code = collection_main(
        [
            "compile-window",
            "--window",
            str(window_path),
            "--collector",
            "youtube-apify-scraper",
            "--reference-time",
            "2026-10-10T20:59:30Z",
            "--config-dir",
            str(REPO_CONFIG),
            "--metadata-dir",
            str(REPO_METADATA),
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert code == EXIT_GATE
    assert report["refused"] is True
    assert report["reason_codes"] == ["no_verified_date_filter_matches"]


def test_compile_window_cli_still_rejects_unknown_collector(capsys, tmp_path):
    window_path = tmp_path / "youtube-year-window.json"
    window_path.write_text(json.dumps(YEAR_WINDOW), encoding="utf-8")

    code = collection_main(
        [
            "compile-window",
            "--window",
            str(window_path),
            "--collector",
            "youtube-apify-missing",
            "--reference-time",
            REFERENCE_TIME,
            "--config-dir",
            str(REPO_CONFIG),
            "--metadata-dir",
            str(REPO_METADATA),
        ]
    )

    assert code == EXIT_CONFIG
