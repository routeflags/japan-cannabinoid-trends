"""Boundary evidence table + promotion rule tests (ISS-20261015-GT-001).

The offline evidence case reads the *tracked* recorded 5y run (read-only);
the rest builds synthetic run directories.  Nothing here writes into
``datasets/`` or promotes anything.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from validation.boundary import (
    MEASUREMENT_PROTOCOL_ID,
    build_boundary_report,
    evaluate_promotion_rule,
    scan_boundary_rows,
)
from validation.cli import main as validation_main
from validation.windows import parse_datetime, resolve_relative_timeframe

REPO_ROOT = Path(__file__).resolve().parents[2]
RECORDED_5Y_RUN = (
    REPO_ROOT
    / "datasets"
    / "cannabinoid-raw-collection"
    / "data"
    / "raw"
    / "google_trends"
    / "20261012T064246Z-google-trends-ja-rikiddo-5y-main5"
)

STUDY = "cbx-search-trends"


# ---------------------------------------------------------------------------
# synthetic run directories
# ---------------------------------------------------------------------------


def _weekly_labels(timeframe: str, reference: str, *, timezone_name: str = "Asia/Tokyo"):
    """Plausible weekly bucket labels for a consistent measurement run.

    The first label is the Sunday on/before the nominal start; labels follow
    every 7 days while they start before the nominal end (the last bucket then
    brackets the nominal end the way a real series does).
    """
    start, end = resolve_relative_timeframe(
        timeframe, parse_datetime(reference), timezone_name
    )
    label = start.date() - timedelta(days=(start.weekday() + 1) % 7)
    labels = []
    while datetime.combine(label, datetime.min.time(), timezone.utc) < end:
        labels.append(label.isoformat())
        label += timedelta(days=7)
    return labels


def _write_run(
    datasets_root: Path,
    run_id: str,
    *,
    timeframe: str = "today 12-m",
    reference: str = "2026-11-01T03:00:00Z",
    labels=None,
    status: str = "success",
    measurement: bool = True,
    raw_artifact: bool = True,
    with_payload: bool = True,
) -> Path:
    run_dir = datasets_root / STUDY / "data" / "raw" / "google_trends" / run_id
    run_dir.mkdir(parents=True)
    labels = _weekly_labels(timeframe, reference) if labels is None else labels

    if with_payload:
        (run_dir / "records_probe.json").write_text(
            json.dumps(
                {
                    "keyword": "CBX",
                    "geo": "JP",
                    "timeframe": timeframe,
                    "collected_at": reference,
                    "data": [
                        {"date": label, "value": index + 1}
                        for index, label in enumerate(labels)
                    ],
                }
            ),
            encoding="utf-8",
        )

    artifacts = []
    if raw_artifact:
        (run_dir / "mcp-tool-result.json").write_text(
            json.dumps({"content": [{"type": "text", "text": "probe"}]}),
            encoding="utf-8",
        )
        artifacts.append(
            {
                "artifact_id": f"{run_id}-mcp-tool-result-json",
                "path": "mcp-tool-result.json",
                "artifact_type": "raw_response",
                "format": "json",
                "schema_id": "google-trends-mcp-tool-result-v1",
                "byte_length": 1,
                "sha256": "0" * 64,
                "layer": "raw",
                "completeness": "complete",
            }
        )
    (run_dir / "artifact-manifest.json").write_text(
        json.dumps({"schema_version": "1.0.0", "run_id": run_id, "artifacts": artifacts}),
        encoding="utf-8",
    )

    provenance = {
        "window_id": f"{timeframe}@{reference}",
        "requested_start": reference,
        "requested_end_exclusive": reference,
        "granularity": "week",
        "timezone": "Asia/Tokyo",
        "reference_time": reference,
        "exact_window_match": False,
        "limitations": ["nominal resolution recorded"],
        "submitted_parameters": {"timeframe": timeframe},
        "observed_min_timestamp": f"{labels[0]}T00:00:00Z" if labels else None,
        "observed_max_timestamp": f"{labels[-1]}T00:00:00Z" if labels else None,
    }
    document = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "study_id": STUDY,
        "source_id": "google-trends",
        "collector": {"collector_id": "google-trends-mcp"},
        "collection_started_at": reference,
        "collection_finished_at": reference,
        "query_provenance": {"submitted_query": "CBX"},
        "temporal_provenance": provenance,
        "execution": {"status": status, "returned_count": len(labels), "errors": []},
        "artifact_manifest": "artifact-manifest.json",
    }
    if measurement:
        document["environment"] = {
            "measurement": {
                "protocol": MEASUREMENT_PROTOCOL_ID,
                "instrument": {"kind": "mcp_session"},
            }
        }
    (run_dir / "run_metadata.json").write_text(
        json.dumps(document, indent=2), encoding="utf-8"
    )
    return run_dir


def _row(run_id: str, timeframe: str, day: str, **overrides) -> dict:
    row = {
        "run_id": run_id,
        "path": f"datasets/{STUDY}/data/raw/google_trends/{run_id}/run_metadata.json",
        "evidence_class": "measurement",
        "measurement_protocol": MEASUREMENT_PROTOCOL_ID,
        "timeframe": timeframe,
        "reference_time": f"{day}T03:00:00Z",
        "execution_status": "success",
        "raw_artifact_present": True,
        "verdict": "consistent",
        "reasons": [],
        "observed_first": "2025-11-02",
        "observed_end_exclusive": "2026-11-02T00:00:00Z",
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# rows
# ---------------------------------------------------------------------------


def test_row_for_a_measurement_run_is_consistent(tmp_path):
    _write_run(tmp_path, "20261101T030000Z-google-trends-boundary-12m")
    rows = scan_boundary_rows(tmp_path, study=STUDY)
    assert len(rows) == 1
    row = rows[0]
    assert row["evidence_class"] == "measurement"
    assert row["timeframe"] == "today 12-m"
    assert row["reference_time"] == "2026-11-01T03:00:00Z"
    assert row["nominal_start"] == "2025-11-01T03:00:00Z"
    assert row["nominal_end_exclusive"] == "2026-11-01T03:00:00Z"
    assert row["verdict"] == "consistent"
    assert abs(row["first_offset_days"]) <= 7
    assert abs(row["last_end_offset_days"]) <= 7
    assert row["raw_artifact_present"] is True


def test_row_for_the_tracked_recorded_5y_run(tmp_path):
    """The one offline evidence row: the real 2026-10-12 5y run.

    It corroborates the nominal model but is recorded_legacy (session-recorded
    reference, transformed labels), so it can never promote.
    """

    assert RECORDED_5Y_RUN.is_dir(), "the tracked 5y run is part of the repository"
    report = build_boundary_report(REPO_ROOT / "datasets", study="cannabinoid-raw-collection")
    row = next(
        entry
        for entry in report["rows"]
        if entry["run_id"] == "20261012T064246Z-google-trends-ja-rikiddo-5y-main5"
    )
    assert row["evidence_class"] == "recorded_legacy"
    assert row["timeframe"] == "today 5-y"
    assert row["reference_time"] == "2026-10-12T06:42:46.688Z"
    assert row["nominal_start"] == "2021-10-12T06:42:46.688000Z"
    assert row["nominal_end_exclusive"] == "2026-10-12T06:42:46.688000Z"
    assert row["observed_first"] == "2021-10-10"
    assert row["observed_last"] == "2026-10-11"
    assert row["observed_end_exclusive"] == "2026-10-18T00:00:00Z"
    assert row["first_offset_days"] == -2.28
    assert row["last_end_offset_days"] == 5.72
    assert row["verdict"] == "consistent"
    # ... and it is not part of the promotion cohort.
    assert report["rule"]["cohort_run_count"] == 0
    assert report["rule"]["eligible"] is False


def test_failed_and_no_data_runs_are_insufficient_evidence(tmp_path):
    _write_run(
        tmp_path,
        "20261101T030100Z-google-trends-boundary-12m",
        status="failed",
    )
    _write_run(
        tmp_path,
        "20261101T030200Z-google-trends-boundary-12m",
        with_payload=False,  # a summary-only record (legacy no-data style)
        labels=[],
    )
    rows = {row["run_id"]: row for row in scan_boundary_rows(tmp_path, study=STUDY)}
    assert rows["20261101T030100Z-google-trends-boundary-12m"]["verdict"] == "insufficient_evidence"
    assert "collection_failed" in rows["20261101T030100Z-google-trends-boundary-12m"]["reasons"]
    assert rows["20261101T030200Z-google-trends-boundary-12m"]["verdict"] == "insufficient_evidence"
    assert "no_series_observed" in rows["20261101T030200Z-google-trends-boundary-12m"]["reasons"]


def test_unregistered_timeframe_and_missing_reference_are_flagged(tmp_path):
    _write_run(
        tmp_path,
        "20261101T030300Z-google-trends-boundary-12m",
        timeframe="today 10-y",
        labels=[],
    )
    rows = scan_boundary_rows(tmp_path, study=STUDY)
    assert rows[0]["verdict"] == "insufficient_evidence"
    assert "unregistered_timeframe" in rows[0]["reasons"]


def test_series_with_a_long_hole_and_a_stale_end_is_inconsistent(tmp_path):
    # Gaps 7 / 302 give a gcd of 1: the step estimate is conservative (the last
    # bucket end is read as one day after the last label), and the series ends
    # two months before the nominal end - outside the tolerance.
    labels = ["2025-11-02", "2025-11-09", "2026-09-06"]
    _write_run(
        tmp_path,
        "20261101T030400Z-google-trends-boundary-12m",
        labels=labels,
    )
    row = scan_boundary_rows(tmp_path, study=STUDY)[0]
    assert row["verdict"] == "inconsistent"
    assert "offset_outside_one_weekly_bucket" in row["reasons"]


def test_irregular_label_step_is_insufficient(tmp_path):
    # A two-day step is neither daily nor weekly: the labels cannot anchor a
    # boundary comparison at all.
    labels = ["2025-11-02", "2025-11-04", "2025-11-06"]
    _write_run(
        tmp_path,
        "20261101T030450Z-google-trends-boundary-12m",
        labels=labels,
    )
    row = scan_boundary_rows(tmp_path, study=STUDY)[0]
    assert row["verdict"] == "insufficient_evidence"
    assert "irregular_label_step" in row["reasons"]


def test_regular_but_shifted_series_is_inconsistent(tmp_path):
    labels = _weekly_labels("today 12-m", "2026-11-01T03:00:00Z")[:40]
    _write_run(
        tmp_path,
        "20261101T030500Z-google-trends-boundary-12m",
        labels=labels,
    )
    row = scan_boundary_rows(tmp_path, study=STUDY)[0]
    # first offset is fine, but the series stops 42 days early (last_end far
    # below the nominal end): regular weekly step, inconsistent verdict.
    assert row["verdict"] == "inconsistent"
    assert row["last_end_offset_days"] < -7
    assert "offset_outside_one_weekly_bucket" in row["reasons"]


# ---------------------------------------------------------------------------
# promotion rule (spec §3)
# ---------------------------------------------------------------------------

REQUIRED = ("today 1-m", "today 3-m", "today 12-m", "today 5-y")


def _full_cohort(*, day_a="2026-11-01", day_b="2026-11-10") -> list:
    rows = []
    for index, timeframe in enumerate(REQUIRED):
        for day in (day_a, day_b):
            rows.append(
                _row(
                    f"{day.replace('-', '')}T03{index:02d}00Z-google-trends-boundary-x",
                    timeframe,
                    day,
                )
            )
    return rows


def test_rule_is_eligible_on_a_complete_consistent_cohort():
    verdict = evaluate_promotion_rule(_full_cohort())
    assert verdict["eligible"] is True, verdict["reasons"]
    assert verdict["cohort_run_count"] == 8
    for timeframe, entry in verdict["timeframes"].items():
        assert entry["satisfied"] is True
        assert entry["consistent_runs"] == 2
        assert entry["reference_span_days"] == 9


def test_rule_requires_a_full_reference_week_span():
    verdict = evaluate_promotion_rule(_full_cohort(day_b="2026-11-05"))
    assert verdict["eligible"] is False
    assert "timeframe_not_satisfied:today 1-m" in verdict["reasons"]
    assert "reference_span_below_minimum" in verdict["timeframes"]["today 1-m"]["reasons"]


def test_rule_requires_two_distinct_reference_days():
    verdict = evaluate_promotion_rule(_full_cohort(day_b="2026-11-01"))
    assert verdict["eligible"] is False
    assert "insufficient_reference_days" in verdict["timeframes"]["today 1-m"]["reasons"]


def test_rule_requires_two_consistent_runs():
    rows = _full_cohort()
    rows[0]["verdict"] = "inconsistent"
    verdict = evaluate_promotion_rule(rows)
    assert verdict["eligible"] is False
    assert "insufficient_consistent_runs" in verdict["timeframes"]["today 1-m"]["reasons"]


def test_rule_ignores_runs_without_a_present_raw_artifact():
    rows = _full_cohort()
    rows[0]["raw_artifact_present"] = False
    verdict = evaluate_promotion_rule(rows)
    assert verdict["eligible"] is False
    assert "insufficient_consistent_runs" in verdict["timeframes"]["today 1-m"]["reasons"]


def test_rule_counts_distinct_runs_not_rows():
    """R2 requires two runs; two rows sharing a run_id are one run and must not
    satisfy the minimum on their own (found by the 2026-10-15 review, D5)."""

    rows = _full_cohort()
    shared = "20261101T030000Z-google-trends-boundary-1m"
    for row in rows:
        if row["timeframe"] == "today 1-m":
            row["run_id"] = shared
    verdict = evaluate_promotion_rule(rows)

    entry = verdict["timeframes"]["today 1-m"]
    assert entry["consistent_runs"] == 1
    assert entry["consistent_run_ids"] == [shared]
    assert "insufficient_consistent_runs" in entry["reasons"]
    assert verdict["eligible"] is False


def test_rule_blocks_on_a_failed_run_in_the_cohort():
    rows = _full_cohort()
    rows.append(
        _row(
            "20261101T039900Z-google-trends-boundary-x",
            "today 12-m",
            "2026-11-01",
            verdict="insufficient_evidence",
            reasons=["collection_failed"],
            execution_status="failed",
        )
    )
    verdict = evaluate_promotion_rule(rows)
    assert verdict["eligible"] is False
    assert "failed_run_in_cohort" in verdict["reasons"]
    assert verdict["failed_run_ids"] == ["20261101T039900Z-google-trends-boundary-x"]


def test_rule_ignores_non_measurement_rows():
    rows = _full_cohort()
    for row in rows:
        row["evidence_class"] = "recorded_legacy"
    verdict = evaluate_promotion_rule(rows)
    assert verdict["eligible"] is False
    assert verdict["cohort_run_count"] == 0


# ---------------------------------------------------------------------------
# CLI + read-only behaviour
# ---------------------------------------------------------------------------


def test_boundary_report_cli_is_read_only_and_deterministic(tmp_path, capsys):
    _write_run(tmp_path, "20261101T030000Z-google-trends-boundary-12m")
    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))

    code = validation_main(
        ["boundary-report", "--datasets-root", str(tmp_path), "--format", "json"]
    )
    first = capsys.readouterr().out
    code2 = validation_main(
        ["boundary-report", "--datasets-root", str(tmp_path), "--format", "json"]
    )
    second = capsys.readouterr().out

    assert code == 0 and code2 == 0
    assert first == second
    report = json.loads(first)
    assert report["protocol"] == MEASUREMENT_PROTOCOL_ID
    assert report["row_count"] == 1
    assert report["measurement_row_count"] == 1
    assert report["rows"][0]["verdict"] == "consistent"
    assert report["rule"]["eligible"] is False  # a single run never promotes

    after = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    assert after == before


def test_boundary_report_cli_run_mode_and_study_filter(tmp_path, capsys):
    run_dir = _write_run(tmp_path, "20261101T030000Z-google-trends-boundary-12m")
    code = validation_main(
        [
            "boundary-report",
            "--datasets-root",
            str(tmp_path),
            "--study",
            "no-such-study",
            "--format",
            "json",
        ]
    )
    assert code == 0
    assert json.loads(capsys.readouterr().out)["row_count"] == 0

    code = validation_main(
        [
            "boundary-report",
            "--run",
            str(run_dir),
            "--datasets-root",
            str(tmp_path),
            "--format",
            "json",
        ]
    )
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["row_count"] == 1
    assert report["rows"][0]["run_id"] == "20261101T030000Z-google-trends-boundary-12m"
