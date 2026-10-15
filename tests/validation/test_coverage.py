"""G3 coverage validation tests (c.md §9, §11, §14 T11-T15).

Two families:

- synthetic run directories exercise the status state machine
  (partial / complete / missing / unknown, pagination, failures, gaps,
  empty series);
- the two real legacy runs (``common-scale-missing`` and ``nodata``)
  demonstrate that missing data and a platform no-data response are
  classified differently and are never converted to ``observed_zero`` (P7).

Read-only: the real datasets are only read.
"""

import json
from pathlib import Path

from validation.cli import EXIT_CONFIG, EXIT_IO, EXIT_OK
from validation.cli import main as validation_main
from validation.core import validate_document
from validation.coverage import (
    COVERAGE_MANIFEST_FILENAME,
    coverage_manifest_path_for_run,
    dump_coverage_manifest,
    evaluate_coverage,
    write_coverage_manifest,
)
from validation.schema_registry import get_schema
from validation.schemas.coverage import (
    COVERAGE_MANIFEST_SCHEMA_ID,
    COVERAGE_MANIFEST_SCHEMA_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_GT = (
    REPO_ROOT
    / "datasets"
    / "cannabinoid-multi-trends"
    / "data"
    / "raw"
    / "google_trends"
)
COMMON_SCALE_MISSING = LEGACY_GT / "20261008T164651Z-google-trends-common-scale-missing"
NODATA = LEGACY_GT / "20261002T064135Z-google-trends-nodata"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _provenance(**overrides):
    provenance = {
        "window_id": "2026-10-01_2026-10-08",
        "requested_start": "2026-10-01T00:00:00Z",
        "requested_end_exclusive": "2026-10-08T00:00:00Z",
        "granularity": "day",
        "timezone": "UTC",
        "reference_time": "2026-10-07T12:00:00Z",
        "exact_window_match": False,
        "submitted_parameters": {"tool": "interest_over_time", "timeframe": "today 1-m"},
    }
    provenance.update(overrides)
    return provenance


def _write_run(tmp_path: Path, *, run_id: str, provenance=None, execution=None, payloads=None):
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    document = {"run_id": run_id}
    if provenance is not None:
        document["temporal_provenance"] = provenance
    if execution is not None:
        document["execution"] = execution
    (run_dir / "run_metadata.json").write_text(
        json.dumps(document), encoding="utf-8"
    )
    for name, payload in (payloads or {}).items():
        (run_dir / name).write_text(json.dumps(payload), encoding="utf-8")
    return run_dir


def _series(dates):
    return {"keyword": "T", "timeframe": "today 1-m", "data": [
        {"date": date, "value": (index % 9) + 1} for index, date in enumerate(dates)
    ]}


# ---------------------------------------------------------------------------
# synthetic state machine
# ---------------------------------------------------------------------------


def test_partial_when_boundaries_unverified(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-partial",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert coverage["status"] == "partial"
    assert "boundary_semantics_unverified" in coverage["reasons"]
    # The collector coverage is the nominal resolution of the recorded spec.
    assert coverage["collector"] == {
        "start": "2026-09-07T12:00:00Z",
        "end_exclusive": "2026-10-07T12:00:00Z",
        "basis": "nominal_resolution",
        "timeframe": "today 1-m",
    }
    # Observed comes from the bucket labels (7-day span), never from a claim.
    assert coverage["observed"]["start"] == "2026-09-20T00:00:00Z"
    assert coverage["observed"]["end_exclusive"] == "2026-10-11T00:00:00Z"
    # Verified stays empty: the requested window is not verified.
    assert coverage["verified_intervals"] == []
    assert coverage["unknown_intervals"] == [coverage["requested"]]


def test_incomplete_pagination_forbids_complete(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-pagination",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": False},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    manifest = evaluate_coverage(run_dir)
    assert manifest["coverage"]["status"] == "partial"
    assert manifest["coverage"]["pagination_exhausted"] is False
    assert "pagination_not_exhausted" in manifest["coverage"]["reasons"]
    assert manifest["coverage"]["verified_intervals"] == []


def test_complete_requires_exact_window_and_verified_bounds(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-complete",
        provenance=_provenance(exact_window_match=True),
        execution={"status": "success", "returned_count": 7, "pagination_exhausted": True},
        payloads={
            "payload.json": _series(
                [
                    "2026-10-01",
                    "2026-10-02",
                    "2026-10-03",
                    "2026-10-04",
                    "2026-10-05",
                    "2026-10-06",
                    "2026-10-07",
                ]
            )
        },
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert coverage["status"] == "complete"
    assert coverage["verified_intervals"] == [coverage["requested"]]
    assert coverage["unknown_intervals"] == []


def test_failed_collection_is_missing_and_never_a_zero(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-failed",
        provenance=_provenance(),
        execution={
            "status": "failed",
            "returned_count": 0,
            "errors": [{"code": "TRANSPORT_ERROR", "message": "no session"}],
        },
        payloads={"payload.json": {"error": {"message": "no session"}}},
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert coverage["status"] == "missing"
    assert "collection_failed" in coverage["reasons"]
    assert coverage["missing_intervals"] == [coverage["requested"]]
    assert "observed_zero" not in json.dumps(manifest)


def test_empty_series_is_unknown_not_zero(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-empty",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 0, "pagination_exhausted": True},
        payloads={"payload.json": {"keyword": "THCV", "timeframe": "today 1-m", "data": []}},
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert coverage["status"] == "unknown"
    assert coverage["reasons"] == ["no_observations_no_evidence"]
    assert coverage["states"]["THCV"]["state"] == "unknown"
    assert "observed_zero" not in json.dumps(manifest)


def test_label_gap_is_reported_and_not_padded(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-gap",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3},
        payloads={
            "payload.json": _series(["2026-01-01", "2026-02-05", "2026-03-01"])
        },
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert "label_gap_detected" in coverage["reasons"]
    assert coverage["label_gap_days"] == 35
    # Three points stay three points: the blank stretch is not zero-filled.
    assert coverage["states"]["T"]["point_count"] == 3
    assert coverage["states"]["T"]["zero_count"] == 0


# ---------------------------------------------------------------------------
# ISS-20261015-WIN-003: expected day/week/month buckets in coverage
# ---------------------------------------------------------------------------


def test_day_granularity_reports_expected_buckets_and_a_missing_day(tmp_path):
    """One absent day is missing evidence, never an observed zero; the
    status state machine is unchanged (partial: boundaries unverified)."""
    run_dir = _write_run(
        tmp_path,
        run_id="run-day-buckets",
        provenance=_provenance(),  # day, 2026-10-01..08 UTC
        execution={"status": "success", "returned_count": 6, "pagination_exhausted": True},
        payloads={
            "payload.json": _series(
                [
                    "2026-10-01",
                    "2026-10-02",
                    "2026-10-03",
                    # 2026-10-04 is absent: a gap, not a zero.
                    "2026-10-05",
                    "2026-10-06",
                    "2026-10-07",
                ]
            )
        },
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert coverage["expected_granularity"] == "day"
    assert [bucket["start"] for bucket in coverage["expected_intervals"]] == [
        f"2026-10-0{day}T00:00:00Z" for day in range(1, 8)
    ]
    assert coverage["missing_expected_intervals"] == [
        {"start": "2026-10-04T00:00:00Z", "end_exclusive": "2026-10-05T00:00:00Z"}
    ]
    # Missing stays missing: no zero is synthesized anywhere.
    assert "observed_zero" not in json.dumps(manifest)
    assert coverage["status"] == "partial"
    assert coverage["unknown_intervals"] == [coverage["requested"]]


def test_week_granularity_sunday_start_in_asia_tokyo(tmp_path):
    """Week buckets follow the provenance week_start/timezone; a fully
    covered window reports no missing buckets."""
    run_dir = _write_run(
        tmp_path,
        run_id="run-week-buckets",
        provenance=_provenance(
            requested_start="2026-10-01T00:00:00Z",
            requested_end_exclusive="2026-10-15T00:00:00Z",
            granularity="week",
            timezone="Asia/Tokyo",
            week_start="sunday",
        ),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={
            # One label inside each expected Sunday-start bucket.
            "payload.json": _series(["2026-10-02", "2026-10-05", "2026-10-12"])
        },
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert coverage["expected_granularity"] == "week"
    assert coverage["expected_intervals"] == [
        {"start": "2026-10-01T00:00:00Z", "end_exclusive": "2026-10-03T15:00:00Z"},
        {"start": "2026-10-03T15:00:00Z", "end_exclusive": "2026-10-10T15:00:00Z"},
        {"start": "2026-10-10T15:00:00Z", "end_exclusive": "2026-10-15T00:00:00Z"},
    ]
    assert coverage["missing_expected_intervals"] == []
    assert "observed_zero" not in json.dumps(manifest)


def test_month_granularity_reports_expected_buckets(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-month-buckets",
        provenance=_provenance(
            requested_start="2025-11-15T00:00:00Z",
            requested_end_exclusive="2026-02-01T00:00:00Z",
            granularity="month",
            timezone="UTC",
        ),
        execution={"status": "success", "returned_count": 2, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2025-11-20", "2026-01-10"])},
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert coverage["expected_granularity"] == "month"
    assert coverage["expected_intervals"] == [
        {"start": "2025-11-15T00:00:00Z", "end_exclusive": "2025-12-01T00:00:00Z"},
        {"start": "2025-12-01T00:00:00Z", "end_exclusive": "2026-01-01T00:00:00Z"},
        {"start": "2026-01-01T00:00:00Z", "end_exclusive": "2026-02-01T00:00:00Z"},
    ]
    assert coverage["missing_expected_intervals"] == [
        {"start": "2025-12-01T00:00:00Z", "end_exclusive": "2026-01-01T00:00:00Z"}
    ]
    assert "observed_zero" not in json.dumps(manifest)


def test_legacy_run_without_exact_window_reports_no_expected_buckets():
    """Runs without requested_start/end keep the legacy shape: no expected
    intervals are invented."""
    manifest = evaluate_coverage(NODATA)
    coverage = manifest["coverage"]
    assert coverage["expected_granularity"] is None
    assert coverage["expected_intervals"] == []
    assert coverage["missing_expected_intervals"] == []
    assert coverage["status"] == "missing"


# ---------------------------------------------------------------------------
# real legacy examples (c.md §9 / §11 / P7)
# ---------------------------------------------------------------------------


def test_common_scale_missing_is_partial_with_zero_point_caveats():
    manifest = evaluate_coverage(COMMON_SCALE_MISSING)
    coverage = manifest["coverage"]
    assert coverage["status"] == "partial"
    assert "relative_window_not_resolved" in coverage["reasons"]
    assert "coverage_not_verified" in coverage["reasons"]
    assert "zero_points_not_observed_zero" in coverage["reasons"]
    # The relative request is recorded verbatim; a legacy relative period is
    # never converted into an absolute window (P1).
    assert coverage["requested"] is None
    assert coverage["requested_relative"]["timeframes"] == ["today 12-m"]
    assert coverage["requested_relative"]["reference"] == "2026-10-09"
    assert coverage["requested_relative"]["resolved_absolute_window"] is None
    # Observed bounds come from the payload labels; the interior zeros are
    # recorded as counts with a below-threshold caveat, never as observed
    # zeros.
    assert coverage["observed"]["start"] == "2025-10-05T00:00:00Z"
    assert coverage["observed"]["end_exclusive"] == "2026-10-11T00:00:00Z"
    assert coverage["states"]["H4CBH"]["state"] == "observed_nonzero"
    assert coverage["states"]["H4CBH"]["zero_count"] == 5
    assert coverage["states"]["HHBD"]["state"] == "observed_nonzero"
    assert coverage["states"]["HHBD"]["zero_count"] == 18
    assert coverage["states"]["CRDH"]["point_count"] == 53
    assert coverage["states"]["CRDH"]["zero_count"] == 52
    assert all(
        entry["state"] != "observed_zero"
        for entry in coverage["states"].values()
    )


def test_nodata_is_missing_below_threshold_and_not_a_zero():
    manifest = evaluate_coverage(NODATA)
    coverage = manifest["coverage"]
    assert coverage["status"] == "missing"
    assert "platform_no_data" in coverage["reasons"]
    assert coverage["states"]["THCV"]["state"] == "below_threshold"
    assert coverage["states"]["THC-O"]["state"] == "below_threshold"
    assert coverage["states"]["THCV"]["zero_count"] == 0
    assert coverage["requested_relative"]["timeframes"] == ["today 12-m"]
    assert coverage["requested_relative"]["reference"] == "2026-10-02T06:41:35Z"
    assert all(
        entry["state"] != "observed_zero"
        for entry in coverage["states"].values()
    )


def test_missing_run_metadata_is_unknown(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    manifest = evaluate_coverage(empty)
    assert manifest["coverage"]["status"] == "unknown"
    assert manifest["coverage"]["reasons"] == ["run_metadata_missing"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_coverage_run_cli_reports_the_nodata_example(capsys):
    code = validation_main(
        ["coverage-run", "--file", str(NODATA), "--format", "json"]
    )
    captured = capsys.readouterr()
    manifest = json.loads(captured.out)
    assert code == EXIT_OK
    assert manifest["coverage"]["status"] == "missing"
    assert manifest["run_id"] == "20261002T064135Z-google-trends-nodata"
    assert "COVERAGE missing" in captured.err


def test_coverage_run_cli_missing_target_exit_3(capsys, tmp_path):
    code = validation_main(
        ["coverage-run", "--file", str(tmp_path / "nowhere")]
    )
    assert code == EXIT_IO


# ---------------------------------------------------------------------------
# ISS-20261015-COV-004: coverage manifest persistence
# ---------------------------------------------------------------------------


def _assert_valid_manifest(manifest: dict) -> None:
    """The emitted manifest carries its schema identity and validates."""
    assert manifest["schema_id"] == "coverage-manifest-v1"
    assert manifest["schema_id"] == COVERAGE_MANIFEST_SCHEMA_ID
    assert manifest["schema_version"] == COVERAGE_MANIFEST_SCHEMA_VERSION
    assert manifest["schema_version"] == "1.0.0"
    schema = get_schema("coverage-manifest-v1")
    result = validate_document(manifest, schema)
    assert result.valid is True, result.errors


def test_manifest_carries_schema_identity_and_validates(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-schema",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    manifest = evaluate_coverage(run_dir)
    _assert_valid_manifest(manifest)
    # Existing fields stay backward-compatible for current consumers.
    assert manifest["coverage_version"] == "1.0.0"
    assert manifest["profile"] == "g3_coverage"
    assert manifest["run_id"] == "run-schema"
    assert manifest["window_id"] == "2026-10-01_2026-10-08"
    assert manifest["coverage"]["status"] == "partial"


def test_legacy_and_missing_metadata_manifests_validate():
    for target in (COMMON_SCALE_MISSING, NODATA):
        _assert_valid_manifest(evaluate_coverage(target))


def test_missing_run_metadata_manifest_validates(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    manifest = evaluate_coverage(empty)
    assert manifest["run_id"] is None
    assert manifest["window_id"] is None
    _assert_valid_manifest(manifest)


def test_dump_is_byte_identical_on_repeated_evaluation(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-deterministic",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    first = dump_coverage_manifest(evaluate_coverage(run_dir))
    second = dump_coverage_manifest(evaluate_coverage(run_dir))
    assert first == second
    assert first.endswith("\n")
    assert first.encode("utf-8").decode("utf-8") == first


def test_undetermined_expected_buckets_do_not_crash_and_stay_missing(tmp_path):
    """An exact window that cannot be bucketed records undetermined evidence
    instead of crashing, and no missing interval becomes an observed zero."""
    run_dir = _write_run(
        tmp_path,
        run_id="run-undetermined",
        provenance=_provenance(requested_start="not-a-date"),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    manifest = evaluate_coverage(run_dir)
    coverage = manifest["coverage"]
    assert "expected_buckets_undetermined" in coverage["reasons"]
    assert coverage["expected_granularity"] is None
    assert coverage["expected_intervals"] == []
    assert "observed_zero" not in json.dumps(manifest)
    _assert_valid_manifest(manifest)


def test_coverage_run_without_persist_is_read_only(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-readonly",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    before = sorted(path.name for path in run_dir.iterdir())
    code = validation_main(
        ["coverage-run", "--file", str(run_dir), "--format", "json"]
    )
    assert code == EXIT_OK
    assert sorted(path.name for path in run_dir.iterdir()) == before
    assert not (run_dir / COVERAGE_MANIFEST_FILENAME).exists()


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_coverage_run_persist_writes_canonical_manifest(tmp_path, capsys):
    run_dir = _write_run(
        tmp_path,
        run_id="run-persist",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    metadata_hash = _sha256(run_dir / "run_metadata.json")
    payload_hash = _sha256(run_dir / "payload.json")
    expected = coverage_manifest_path_for_run(run_dir)
    assert expected == run_dir / "coverage-manifest.json"

    code = validation_main(
        ["coverage-run", "--file", str(run_dir), "--persist", "--format", "json"]
    )
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert expected.is_file()
    persisted = json.loads(expected.read_text(encoding="utf-8"))
    _assert_valid_manifest(persisted)
    # The persisted file is the evaluated manifest, serialized deterministically.
    assert expected.read_text(encoding="utf-8") == dump_coverage_manifest(
        evaluate_coverage(run_dir)
    )
    assert f"coverage manifest persisted: {expected}" in captured.err
    # Raw observations are immutable: payload and run metadata are untouched.
    assert _sha256(run_dir / "run_metadata.json") == metadata_hash
    assert _sha256(run_dir / "payload.json") == payload_hash
    # Re-running persist is byte-identical: the persisted manifest itself is
    # not payload evidence, so re-evaluation sees the same run.
    code = validation_main(
        ["coverage-run", "--file", str(run_dir), "--persist", "--format", "json"]
    )
    assert code == EXIT_OK
    assert expected.read_text(encoding="utf-8") == dump_coverage_manifest(
        evaluate_coverage(run_dir)
    )


def test_coverage_run_persist_accepts_metadata_file_target(tmp_path):
    run_dir = _write_run(
        tmp_path,
        run_id="run-persist-file-target",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    code = validation_main(
        [
            "coverage-run",
            "--file", str(run_dir / "run_metadata.json"),
            "--persist",
        ]
    )
    assert code == EXIT_OK
    assert (run_dir / COVERAGE_MANIFEST_FILENAME).is_file()


def test_coverage_run_persist_with_output_exits_2_and_writes_nothing(
    tmp_path, capsys
):
    run_dir = _write_run(
        tmp_path,
        run_id="run-conflict",
        provenance=_provenance(),
        execution={"status": "success", "returned_count": 3, "pagination_exhausted": True},
        payloads={"payload.json": _series(["2026-09-20", "2026-09-27", "2026-10-04"])},
    )
    elsewhere = tmp_path / "elsewhere.json"
    code = validation_main(
        [
            "coverage-run",
            "--file", str(run_dir),
            "--persist",
            "--output", str(elsewhere),
        ]
    )
    assert code == EXIT_CONFIG
    assert not (run_dir / COVERAGE_MANIFEST_FILENAME).exists()
    assert not elsewhere.exists()


def test_coverage_run_persist_missing_target_exits_3(tmp_path):
    missing = tmp_path / "nowhere"
    code = validation_main(["coverage-run", "--file", str(missing), "--persist"])
    assert code == EXIT_IO
    assert not (tmp_path / COVERAGE_MANIFEST_FILENAME).exists()


def test_write_coverage_manifest_cleans_temp_file_on_failure(tmp_path):
    manifest = evaluate_coverage(
        _write_run(
            tmp_path / "src",
            run_id="run-tmp-cleanup",
            provenance=_provenance(),
            execution={"status": "success"},
            payloads={"payload.json": _series(["2026-10-04"])},
        )
    )
    # Pointing the write at an existing directory fails the replace; the temp
    # file must not remain and no partial manifest may appear.
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    try:
        write_coverage_manifest(manifest, blocked)
    except (OSError, IsADirectoryError):
        pass
    else:
        raise AssertionError("expected the directory-target write to fail")
    assert not (tmp_path / "blocked.tmp").exists()
    assert blocked.is_dir() and not any(blocked.iterdir())
