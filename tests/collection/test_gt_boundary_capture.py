"""GT boundary-measurement capture tooling tests (ISS-20261015-GT-001).

Offline only: captures are synthetic verbatim tool results shaped like the
documented ``google-trends-mcp@0.1.1`` output (docs/specs/
gt-boundary-verification.md §4.4).  No live collection is executed; the format
hypothesis itself is verified against the first live capture by the protocol's
``verify`` step, not here.
"""

import json
from pathlib import Path

from validation.boundary import MEASUREMENT_PROTOCOL_ID, RAW_ARTIFACT_NAME
from validation.pipeline import validate_full
from validation.new_runs import audit_new_runs

from collection.adapters.google_trends.boundary import (
    MEASUREMENT_STUDY_ID,
    BoundaryCaptureError,
    main,
    parse_tool_result,
    stage_capture,
    verify_capture_manifest,
)
from collection.core.pipeline import adopt_staged

from conftest import (
    REPO_CONFIG,
    REPO_METADATA,
    load_json,
)

RUN_ID_12M = "20261101T030000Z-google-trends-boundary-12m"
RUN_ID_1M = "20261101T031000Z-google-trends-boundary-1m"

TEXT_12M = (
    "Interest over time for: CBX\n"
    "Geo: JP | Timeframe: today 12-m\n"
    "\n"
    "Date\tCBX\n"
    "Nov 2 – 8, 2025\t54\n"
    "Nov 9 – 15, 2025\t48\n"
    "Dec 28 – Jan 3, 2026\t39\n"
    "Oct 25 – 31, 2026\t12\n"
    "\n"
    "Averages: CBX=38\n"
)


def _envelope(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": False}


def _capture(
    *,
    run_id: str = RUN_ID_12M,
    timeframe: str = "today 12-m",
    term: str = "CBX",
    geo: str = "JP",
    started: str = "2026-11-01T03:00:00Z",
    finished: str = "2026-11-01T03:00:06Z",
    result=None,
    notes=None,
) -> dict:
    capture = {
        "run_id": run_id,
        "request": {
            "tool": "interest_over_time",
            "params": {"terms": [term], "geo": geo, "timeframe": timeframe},
        },
        "started_at": started,
        "finished_at": finished,
        "result": _envelope(TEXT_12M) if result is None else result,
    }
    if notes is not None:
        capture["notes"] = notes
    return capture


def _manifest(*captures) -> dict:
    return {
        "capture_version": "1.0.0",
        "instrument": {
            "kind": "mcp_session",
            "server": "google-trends-mcp",
            "server_version": "0.1.1",
        },
        "captures": list(captures),
    }


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / "datasets" / MEASUREMENT_STUDY_ID).mkdir(parents=True)
    return root


# ---------------------------------------------------------------------------
# parser (spec §4.4)
# ---------------------------------------------------------------------------


def test_parser_derives_bucket_start_dates_from_every_documented_label_shape():
    parsed = parse_tool_result(_envelope(TEXT_12M))
    assert parsed.terms == ("CBX",)
    assert parsed.geo == "JP"
    assert parsed.timeframe == "today 12-m"
    assert [(point.date, point.value) for point in parsed.points] == [
        ("2025-11-02", 54),
        ("2025-11-09", 48),
        ("2025-12-28", 39),  # cross-year range starts in the previous year
        ("2026-10-25", 12),
    ]


def test_parser_accepts_hyphen_and_iso_labels():
    text = (
        "Interest over time for: CBX\n"
        "Geo: JP | Timeframe: today 12-m\n\n"
        "Date\tCBX\n"
        "Sep 28 - Oct 4, 2025\t3\n"
        "2025-10-05\t4\n"
    )
    parsed = parse_tool_result(_envelope(text))
    assert [point.date for point in parsed.points] == ["2025-09-28", "2025-10-05"]


def test_parser_refuses_an_unknown_label_shape():
    text = (
        "Interest over time for: CBX\n"
        "Geo: JP | Timeframe: today 12-m\n\n"
        "Date\tCBX\n"
        "Week of Oct 12\t54\n"
    )
    try:
        parse_tool_result(_envelope(text))
    except BoundaryCaptureError as error:
        assert error.codes == ["label_format_unknown"]
    else:  # pragma: no cover - the parser must refuse
        raise AssertionError("unknown label shape must be refused")


def test_parser_refuses_non_integer_values():
    text = (
        "Interest over time for: CBX\n"
        "Geo: JP | Timeframe: today 12-m\n\n"
        "Date\tCBX\n"
        "Oct 12 – 18, 2025\t-\n"
    )
    try:
        parse_tool_result(_envelope(text))
    except BoundaryCaptureError as error:
        assert error.codes == ["value_not_integer"]
    else:  # pragma: no cover
        raise AssertionError("non-integer value must be refused")


def test_parser_treats_no_data_and_errors_as_distinct_states():
    """A no-data response is not an observed zero, and an error is not a
    series (both are refused as series; the error is labelled separately)."""

    no_data = (
        "Interest over time for: CBX\n"
        "Geo: JP | Timeframe: today 12-m\n\n"
        "Date\tCBX\n"
    )
    try:
        parse_tool_result(_envelope(no_data))
    except BoundaryCaptureError as error:
        assert error.codes == ["empty_series"]
    else:  # pragma: no cover
        raise AssertionError("an empty series must be refused")

    error_envelopes = [
        {"content": [{"type": "text", "text": "Error: rate limited (429)"}], "isError": True},
        {"content": [{"type": "text", "text": "Error: no data returned"}]},
    ]
    for envelope in error_envelopes:
        try:
            parse_tool_result(envelope)
        except BoundaryCaptureError as error:
            assert error.codes == ["collection_failed"]
        else:  # pragma: no cover
            raise AssertionError("an error result must be labelled as a failed collection")


def test_parser_refuses_a_response_without_a_header():
    text = "Something unexpected\nDate\tCBX\nOct 12 – 18, 2025\t54\n"
    try:
        parse_tool_result(_envelope(text))
    except BoundaryCaptureError as error:
        assert "text_line_unknown" in error.codes
    else:  # pragma: no cover
        raise AssertionError("a header-less response must be refused")


# ---------------------------------------------------------------------------
# manifest validation + verify (spec §4.3 / §4.4)
# ---------------------------------------------------------------------------


def test_verify_accepts_a_documented_capture_manifest():
    captures = verify_capture_manifest(_manifest(_capture()))
    assert [capture.status for capture in captures] == ["parsed"]
    assert captures[0].parsed.points[0].date == "2025-11-02"


def test_verify_marks_a_collection_failure_without_refusing_the_manifest():
    failure = _capture(
        run_id=RUN_ID_1M,
        timeframe="today 1-m",
        result={"content": [{"type": "text", "text": "Error: 429"}], "isError": True},
    )
    captures = verify_capture_manifest(_manifest(_capture(), failure))
    assert [capture.status for capture in captures] == ["parsed", "collection_failed"]


def test_verify_flags_a_format_mismatch_loudly():
    bad = _capture(
        result=_envelope(
            "Interest over time for: CBX\nGeo: JP | Timeframe: today 12-m\n\n"
            "Date\tCBX\nWeek of Oct 12\t54\n"
        )
    )
    captures = verify_capture_manifest(_manifest(bad))
    assert captures[0].status == "format_mismatch"
    assert captures[0].error.codes == ["label_format_unknown"]


def test_verify_refuses_an_echo_mismatch():
    """A response whose echoed timeframe does not match the request is refused
    (a misrouted capture must never be attributed to the requested period)."""

    text = TEXT_12M.replace("today 12-m", "today 5-y")
    captures = verify_capture_manifest(_manifest(_capture(result=_envelope(text))))
    assert captures[0].status == "format_mismatch"
    assert captures[0].error.codes == ["echo_mismatch"]


def test_parser_refuses_a_multi_term_comparison_table():
    text = (
        "Interest over time for: CBX, CBD\n"
        "Geo: JP | Timeframe: today 12-m\n\n"
        "Date\tCBX\tCBD\n"
        "Oct 12 – 18, 2025\t54\t21\n"
    )
    try:
        parse_tool_result(_envelope(text))
    except BoundaryCaptureError as error:
        assert error.codes == ["multi_term_unsupported"]
    else:  # pragma: no cover
        raise AssertionError("a comparison table must be refused")


def test_parser_refuses_an_impossible_calendar_date():
    """A label can name a day that does not exist; deriving a bucket start from
    it would fabricate an observation (found by the 2026-10-15 review, D1)."""

    for label in ("Feb 30, 2025", "Oct 0 – 6, 2025", "2025-13-45"):
        text = (
            "Interest over time for: CBX\n"
            "Geo: JP | Timeframe: today 12-m\n\n"
            "Date\tCBX\n"
            f"{label}\t54\n"
        )
        try:
            parse_tool_result(_envelope(text))
        except BoundaryCaptureError as error:
            assert error.codes == ["label_date_invalid"], (label, error.codes)
        else:  # pragma: no cover
            raise AssertionError(f"impossible calendar date must be refused: {label}")


def test_parser_refuses_an_unordered_series():
    """The documented rules describe an ascending series; unordered or
    duplicated labels are not covered, so they are refused (review D2)."""

    for rows in (
        "Oct 12 – 18, 2025\t54\nOct 5 – 11, 2025\t48\n",
        "Oct 12 – 18, 2025\t54\nOct 12 – 18, 2025\t48\n",
    ):
        text = (
            "Interest over time for: CBX\n"
            "Geo: JP | Timeframe: today 12-m\n\n"
            "Date\tCBX\n" + rows
        )
        try:
            parse_tool_result(_envelope(text))
        except BoundaryCaptureError as error:
            assert error.codes == ["labels_out_of_order"], error.codes
        else:  # pragma: no cover
            raise AssertionError("an unordered series must be refused")


def test_parser_refuses_a_row_with_extra_fields():
    """A single-term table with more value fields than terms is refused rather
    than silently truncated to its first value (review D3)."""

    text = (
        "Interest over time for: CBX\n"
        "Geo: JP | Timeframe: today 12-m\n\n"
        "Date\tCBX\n"
        "Oct 12 – 18, 2025\t54\t21\n"
    )
    try:
        parse_tool_result(_envelope(text))
    except BoundaryCaptureError as error:
        assert error.codes == ["row_shape_unknown"]
    else:  # pragma: no cover
        raise AssertionError("a row with extra value fields must be refused")


def test_parser_refuses_a_value_outside_the_relative_index():
    """The recorded convention is a relative index 0-100 (review D4)."""

    for value in ("101", "-5"):
        text = (
            "Interest over time for: CBX\n"
            "Geo: JP | Timeframe: today 12-m\n\n"
            "Date\tCBX\n"
            f"Oct 12 – 18, 2025\t{value}\n"
        )
        try:
            parse_tool_result(_envelope(text))
        except BoundaryCaptureError as error:
            assert error.codes == ["value_out_of_range"], (value, error.codes)
        else:  # pragma: no cover
            raise AssertionError(f"value outside 0-100 must be refused: {value}")


def test_verify_refuses_unconventional_manifest_content():
    cases = [
        (lambda m: m["captures"][0].__setitem__("run_id", "boundary-12m"), "run_id_unconventional"),
        (
            lambda m: m["captures"][0]["request"]["params"].__setitem__("timeframe", "today 10-y"),
            "request_invalid",
        ),
        (
            lambda m: m["captures"][0]["request"]["params"].__setitem__("terms", ["CBX", "CBD"]),
            "request_invalid",
        ),
        (
            lambda m: m["captures"][0].__setitem__("started_at", "2026-11-01"),
            "timestamp_invalid",
        ),
        (lambda m: m.__setitem__("capture_version", "2.0.0"), "manifest_version_unknown"),
    ]
    for mutate, expected in cases:
        manifest = _manifest(_capture())
        mutate(manifest)
        try:
            verify_capture_manifest(manifest)
        except BoundaryCaptureError as error:
            assert expected in error.codes, (expected, error.codes)
        else:  # pragma: no cover
            raise AssertionError(f"manifest must be refused for {expected}")

    duplicate = _manifest(_capture(), _capture())
    try:
        verify_capture_manifest(duplicate)
    except BoundaryCaptureError as error:
        assert "run_id_duplicate" in error.codes
    else:  # pragma: no cover
        raise AssertionError("duplicate run ids must be refused")


# ---------------------------------------------------------------------------
# staging / adoption (offline replay of the live procedure)
# ---------------------------------------------------------------------------


def test_staged_capture_is_adopted_and_strict_valid(tmp_path, registries):
    root = _workspace(tmp_path)
    capture = verify_capture_manifest(_manifest(_capture()))[0]
    capture.context = {
        "instrument": {"kind": "mcp_session", "server": "google-trends-mcp"},
        "manifest": "captures-pass1.json",
        "index": 0,
    }
    staged = stage_capture(
        capture,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert staged.action == "staged", [i.code for i in staged.issues]
    staged_dir = Path(staged.staging_dir)
    assert sorted(p.name for p in staged_dir.iterdir()) == [
        "artifact-manifest.json",
        RAW_ARTIFACT_NAME,
        "records_cbx.json",
        "run_metadata.json",
    ]

    # The verbatim tool result is preserved as received.
    stored = load_json(staged_dir / RAW_ARTIFACT_NAME)
    assert stored == _envelope(TEXT_12M)
    series = load_json(staged_dir / "records_cbx.json")
    assert series["keyword"] == "CBX"
    assert series["timeframe"] == "today 12-m"
    assert [point["date"] for point in series["data"]] == [
        "2025-11-02",
        "2025-11-09",
        "2025-12-28",
        "2026-10-25",
    ]

    document = load_json(staged_dir / "run_metadata.json")
    assert document["run_id"] == RUN_ID_12M
    temporal = document["temporal_provenance"]
    assert temporal["reference_time"] == "2026-11-01T03:00:00Z"
    assert temporal["observed_min_timestamp"] == "2025-11-02T00:00:00Z"
    assert temporal["observed_max_timestamp"] == "2026-10-25T00:00:00Z"
    assert temporal["exact_window_match"] is False
    assert temporal["boundary_semantics"]
    assert temporal["limitations"]
    assert temporal["submitted_parameters"]["timeframe"] == "today 12-m"
    # The relative request has no absolute form; the recorded bounds are the
    # nominal resolution, and the run says so.
    assert temporal["requested_start"].startswith("2025-11-01T03:00:00")
    assert any("not a study-requested absolute window" in text for text in temporal["limitations"])
    assert document["environment"]["measurement"]["protocol"] == MEASUREMENT_PROTOCOL_ID
    assert document["environment"]["measurement"]["capture_manifest"] == "captures-pass1.json"

    adopted = adopt_staged(
        staged_dir,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert adopted.action == "adopted", [i.code for i in adopted.issues]
    assert adopted.l1 is not None and adopted.l1.valid is True

    final_dir = Path(adopted.final_dir)
    outcome = validate_full(
        load_json(final_dir / "run_metadata.json"),
        schema_id="collection-run-v1",
        registries=registries,
        base_dir=final_dir,
        verify_artifacts=True,
    )
    assert outcome.valid is True, [i.to_dict() for i in outcome.issues]

    audit = audit_new_runs(root, root / "datasets", registries=registries)
    assert audit["new_run_count"] == 1
    assert audit["failure_count"] == 0
    assert audit["frozen_legacy_seen"] == 0

    report = load_json(final_dir / "artifact-manifest.json")
    raw_entry = next(a for a in report["artifacts"] if a["path"] == RAW_ARTIFACT_NAME)
    series_entry = next(a for a in report["artifacts"] if a["path"] == "records_cbx.json")
    assert series_entry["record_count"] == 4
    assert series_entry["derived_from"] == [raw_entry["artifact_id"]]


def test_environment_records_no_machine_local_paths(tmp_path, registries):
    root = _workspace(tmp_path)
    capture = verify_capture_manifest(_manifest(_capture()))[0]
    capture.context = {"instrument": {"kind": "mcp_session"}, "manifest": "captures-pass1.json", "index": 0}
    staged = stage_capture(
        capture,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    document = load_json(Path(staged.staging_dir) / "run_metadata.json")
    environment = json.dumps(document["environment"])
    assert str(root) not in environment
    assert "captures-pass1.json" in environment


def test_a_failed_capture_is_staged_as_failure_evidence(tmp_path, registries):
    root = _workspace(tmp_path)
    failure = _capture(
        result={"content": [{"type": "text", "text": "Error: HTTP 429"}], "isError": True}
    )
    capture = verify_capture_manifest(_manifest(failure))[0]
    staged = stage_capture(
        capture,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert staged.action == "staged", [i.code for i in staged.issues]
    staged_dir = Path(staged.staging_dir)
    assert sorted(p.name for p in staged_dir.iterdir()) == [
        "artifact-manifest.json",
        RAW_ARTIFACT_NAME,
        "run_metadata.json",
    ]
    document = load_json(staged_dir / "run_metadata.json")
    assert document["execution"]["status"] == "failed"
    assert document["execution"]["returned_count"] == 0
    assert document["execution"]["errors"][0]["code"] == "COLLECTION_FAILED"
    # No observation is recorded for a failed collection - missing is not zero.
    assert "observed_min_timestamp" not in document["temporal_provenance"]
    assert "observed_max_timestamp" not in document["temporal_provenance"]

    # L1 never adopts a failed execution: the raw error record is preserved in
    # quarantine instead of becoming an empty series in the catalog.
    adopted = adopt_staged(
        staged_dir,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert adopted.action == "quarantined"
    quarantine_dir = Path(adopted.final_dir)
    assert (quarantine_dir / "quarantine-reason.json").is_file()
    assert (quarantine_dir / RAW_ARTIFACT_NAME).is_file()


def test_staging_refuses_a_format_mismatch_before_writing(tmp_path, registries):
    root = _workspace(tmp_path)
    bad = _capture(
        result=_envelope(
            "Interest over time for: CBX\nGeo: JP | Timeframe: today 12-m\n\n"
            "Date\tCBX\nWeek of Oct 12\t54\n"
        )
    )
    capture = verify_capture_manifest(_manifest(bad))[0]
    try:
        stage_capture(
            capture,
            workspace_root=root,
            datasets_root=root / "datasets",
            registries=registries,
        )
    except BoundaryCaptureError as error:
        assert error.codes == ["label_format_unknown"]
    else:  # pragma: no cover
        raise AssertionError("a format mismatch must refuse staging")
    assert not (root / ".staging").exists()


def test_an_existing_run_id_is_never_overwritten(tmp_path, registries):
    root = _workspace(tmp_path)
    capture = verify_capture_manifest(_manifest(_capture()))[0]
    first = stage_capture(
        capture,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert first.action == "staged"
    second = stage_capture(
        capture,
        workspace_root=root,
        datasets_root=root / "datasets",
        registries=registries,
    )
    assert second.action == "stopped"
    assert [issue.code for issue in second.issues] == ["RUN_ID_ALREADY_EXISTS"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _write_manifest(tmp_path: Path, manifest: dict) -> Path:
    path = tmp_path / "captures.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return path


def test_cli_verify_reports_and_passes(tmp_path, capsys):
    manifest_path = _write_manifest(tmp_path, _manifest(_capture()))
    code = main(["verify", "--manifest", str(manifest_path), "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["format_verified"] is True
    assert report["captures"][0]["status"] == "parsed"
    assert report["captures"][0]["point_count"] == 4


def test_cli_verify_refuses_a_format_mismatch(tmp_path, capsys):
    bad = _capture(
        result=_envelope(
            "Interest over time for: CBX\nGeo: JP | Timeframe: today 12-m\n\n"
            "Date\tCBX\nWeek of Oct 12\t54\n"
        )
    )
    manifest_path = _write_manifest(tmp_path, _manifest(bad))
    code = main(["verify", "--manifest", str(manifest_path), "--format", "json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 1
    assert report["refused"] is True
    assert "stop the matrix" in captured.err


def test_cli_stage_writes_the_staged_run(tmp_path, capsys):
    root = _workspace(tmp_path)
    manifest_path = _write_manifest(tmp_path, _manifest(_capture()))
    code = main(
        [
            "stage",
            "--manifest",
            str(manifest_path),
            "--workspace",
            str(root),
            "--datasets-root",
            str(root / "datasets"),
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
    assert code == 0
    assert report["staged_count"] == 1
    assert (root / ".staging" / RUN_ID_12M / "run_metadata.json").is_file()


def test_cli_stage_refuses_a_bad_manifest_before_writing(tmp_path, capsys):
    root = _workspace(tmp_path)
    manifest = _manifest(_capture())
    manifest["captures"][0]["run_id"] = "not-a-protocol-run-id"
    manifest_path = _write_manifest(tmp_path, manifest)
    code = main(
        [
            "stage",
            "--manifest",
            str(manifest_path),
            "--workspace",
            str(root),
            "--datasets-root",
            str(root / "datasets"),
            "--config-dir",
            str(REPO_CONFIG),
            "--metadata-dir",
            str(REPO_METADATA),
        ]
    )
    assert code == 1
    assert not (root / ".staging").exists()
    assert "run_id_unconventional" in capsys.readouterr().err
