"""YouTube Apify CSV handover adapter/driver tests (COL-016 MVP, COL-033 pattern).

Offline only: every payload is a synthetic CSV written to ``tmp_path`` (a real
dataset export cannot be committed - third-party video metadata).  The wrapper
is exercised end to end through the existing adoption path
(``stage_csv`` -> ``adopt_staged``); no live Apify call is ever issued and no
real raw run is ever touched.
"""

import csv
from pathlib import Path

import pytest

from collection.adapters import get_window_compiler, registered_sources
from collection.adapters.youtube import apify_csv
from collection.adapters.youtube.apify_csv import (
    DATE_FILTERS,
    YouTubeApifyCsvAdapter,
    YouTubeApifyCsvError,
    build_adapter,
    build_csv_run,
    collector_identity,
    stage_csv,
)
from collection.core.contracts import SUPPORT_VALUES, check_adapter_contract
from collection.core.pipeline import (
    ARTIFACT_MANIFEST_NAME,
    RUN_METADATA_NAME,
    adopt_staged,
)
from collection.core.staging import DeclarationError
from validation.pipeline import validate_full

from conftest import load_json, make_workspace

STUDY_ID = "youtube-consistency"
RUN_ID = "20261011T191900Z-youtube-youtube-consistency"
QUERY_ID = "cbd-liquid-ja"
KEYWORD = "CBD リキッド"

HEADER = ["id", "url", "title", "date", "channelName", "input", "hashtags/0"]


def _write_csv(path: Path, *, input_value: str = KEYWORD, rows=None) -> Path:
    default_rows = [
        [
            "synthetic-0001",
            "https://example.invalid/watch?v=s1",
            "Synthetic record one",
            "2026-10-01T00:00:00Z",
            "Synthetic channel",
            input_value,
            "tag1",
        ],
        [
            "synthetic-0002",
            "https://example.invalid/watch?v=s2",
            'Title with, comma and "quotes"\nplus a second line',
            "2026-10-03T00:00:00Z",
            "Synthetic channel",
            input_value,
            "tag2",
        ],
        [
            "synthetic-0003",
            "https://example.invalid/watch?v=s3",
            "Synthetic record three",
            "2026-10-09T00:00:00Z",
            "Synthetic channel",
            input_value,
            "",
        ],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(default_rows if rows is None else rows)
    return path


def _run_kwargs(csv_path, **overrides) -> dict:
    kwargs = {
        "csv_path": csv_path,
        "run_id": RUN_ID,
        "study_id": STUDY_ID,
        "query_keyword": KEYWORD,
        "query_id": QUERY_ID,
        "date_filter": "year",
        "reference_time": "2026-10-11T19:19:02Z",
        "window_start": "2025-10-11T00:00:00Z",
        "window_end_exclusive": "2026-10-10T00:00:00Z",
        "started_at": "2026-10-11T19:09:08Z",
        "finished_at": "2026-10-11T19:19:02Z",
        "timestamp_basis": "synthetic fixture: no payload timestamp exists",
        "purpose": "COL-016 MVP contract test (synthetic payload)",
        "collector_window_type": "relative_duration",
    }
    kwargs.update(overrides)
    return kwargs


def _stage(tmp_path, registries, run, name="handover"):
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    declarations = tmp_path / "declarations"
    report = stage_csv(
        run,
        declarations_dir=declarations,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
        description=f"synthetic {name} test",
    )
    return workspace, report


# ---------------------------------------------------------------------------
# A7: registry identity / capability stays evidence-based
# ---------------------------------------------------------------------------


def test_adapter_identity_matches_the_registry_entry(registries):
    adapter = build_adapter(registries)
    entry = next(
        collector
        for collector in registries.collectors
        if collector.get("collector_id") == "youtube-apify-scraper"
    )
    assert adapter.collector_id == entry["collector_id"] == "youtube-apify-scraper"
    assert adapter.source_id == entry["source_id"] == "youtube"
    assert adapter.adapter_id == entry["adapter_id"]
    assert adapter.version == entry["version"] == "unknown"


def test_adapter_satisfies_the_common_contract(registries):
    assert check_adapter_contract(build_adapter(registries)) == []


def test_capabilities_are_reported_from_the_registry_and_stay_unknown(registries):
    adapter = build_adapter(registries)
    capabilities = adapter.capabilities()
    assert capabilities == {
        "absolute_date_range": "unknown",
        "relative_date_range": "unknown",
        "language_filter": "unknown",
        "geo_filter": "unknown",
        "pagination": "unknown",
        "stable_item_id": "unknown",
    }
    for value in capabilities.values():
        assert value in SUPPORT_VALUES
    # Live measurement has not happened: nothing may be upgraded to supported.
    assert "supported" not in capabilities.values()
    assert collector_identity(registries)["status"] == "unverified"
    # The adapter hands out a copy - callers cannot mutate its state.
    capabilities["pagination"] = "supported"
    assert adapter.capabilities()["pagination"] == "unknown"


def test_unknown_collector_is_refused_before_anything_is_built(registries):
    adapter = YouTubeApifyCsvAdapter(
        adapter_id="youtube-apify-scraper@1", version="unknown", capabilities={}
    )
    assert isinstance(adapter, YouTubeApifyCsvAdapter)
    with pytest.raises(YouTubeApifyCsvError):
        collector_identity(type("R", (), {"collectors": ()})())


def test_youtube_has_no_live_dispatch_or_window_compiler():
    """The MVP is handover-only: registering a source that cannot collect
    would imply an unevidenced capability, so dispatch stays closed."""
    assert "youtube" not in registered_sources()
    assert get_window_compiler("youtube-apify-scraper") is None


def test_collect_fails_closed_without_a_live_transport(registries):
    adapter = build_adapter(registries)
    result = adapter.collect({})
    assert result.status == "failed"
    assert result.errors and result.errors[0]["code"] == "LIVE_TRANSPORT_UNIMPLEMENTED"
    assert result.completeness == "missing"
    assert result.observations == []
    assert result.pagination_exhausted is None
    assert adapter.extract_observations({"rows": [1, 2, 3]}) == []
    description = adapter.describe_execution()
    assert description["collection_mode"] == "external_staged"
    assert description["collector_id"] == "youtube-apify-scraper"


def test_validate_plan_rejects_empty_query_and_window(registries):
    adapter = build_adapter(registries)
    assert any(
        "query.text" in violation
        for violation in adapter.validate_plan({"query": {"text": ""}})
    )
    assert any(
        "window.start" in violation
        for violation in adapter.validate_plan({"query": {"text": KEYWORD}})
    )


# ---------------------------------------------------------------------------
# A1: a valid handover stages byte-for-byte and adopts through the existing path
# ---------------------------------------------------------------------------


def test_valid_handover_stages_byte_for_byte_and_adopts(tmp_path, registries):
    csv_path = _write_csv(tmp_path / "records.csv")
    workspace, report = _stage(tmp_path, registries, build_csv_run(**_run_kwargs(csv_path)))

    assert report["staged"] == 1 and report["stopped"] == 0
    result = report["results"][0]
    assert result["action"] == "staged" and result["run_id"] == RUN_ID
    staged = Path(result["staging_dir"])
    assert (staged / "records.csv").read_bytes() == csv_path.read_bytes()

    manifest = load_json(staged / ARTIFACT_MANIFEST_NAME)
    artifact = manifest["artifacts"][0]
    assert artifact["byte_length"] == csv_path.stat().st_size
    assert artifact["format"] == "csv" and artifact["layer"] == "raw"
    assert artifact["record_count"] == 3  # CSV records, not physical lines

    adopted = adopt_staged(
        staged,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert adopted.action == "adopted", [issue.code for issue in adopted.l1.issues]
    final = Path(adopted.final_dir)
    assert final == workspace / "datasets" / STUDY_ID / "data" / "raw" / "youtube" / RUN_ID
    assert (final / "records.csv").read_bytes() == csv_path.read_bytes()

    document = load_json(final / RUN_METADATA_NAME)
    outcome = validate_full(
        document,
        schema_id="collection-run-v1",
        target=str(final),
        registries=registries,
        base_dir=final,
        verify_artifacts=True,
    )
    assert outcome.valid is True, [issue.to_dict() for issue in outcome.issues]
    assert not [
        issue for issue in outcome.issues if issue.severity in ("error", "warning")
    ]


def test_quoted_newlines_count_as_records_not_lines(tmp_path, registries):
    """Embedded newlines/commas/quotes are one record each: the count comes
    from the ``csv`` module reader, never from a line count."""
    csv_path = _write_csv(tmp_path / "records.csv")
    assert len(csv_path.read_bytes().splitlines()) == 5  # 1 header + 4 physical lines
    _, report = _stage(tmp_path, registries, build_csv_run(**_run_kwargs(csv_path)))
    manifest = load_json(Path(report["results"][0]["staging_dir"]) / ARTIFACT_MANIFEST_NAME)
    assert manifest["artifacts"][0]["record_count"] == 3


# ---------------------------------------------------------------------------
# A2: request facts are declared, never inferred from the payload
# ---------------------------------------------------------------------------


def test_payload_columns_never_decide_the_query(tmp_path, registries):
    csv_path = _write_csv(tmp_path / "records.csv", input_value="HHBD リキッド")
    _, report = _stage(tmp_path, registries, build_csv_run(**_run_kwargs(csv_path)))
    document = load_json(
        Path(report["results"][0]["staging_dir"]) / RUN_METADATA_NAME
    )
    assert document["query_provenance"]["submitted_query"] == KEYWORD
    assert document["query_provenance"]["query_id"] == QUERY_ID


@pytest.mark.parametrize(
    "drop", ["query_id", "query_keyword", "date_filter", "reference_time"]
)
def test_missing_request_facts_fail_closed_without_staging(tmp_path, registries, drop):
    csv_path = _write_csv(tmp_path / "records.csv")
    kwargs = _run_kwargs(csv_path)
    kwargs[drop] = ""
    with pytest.raises(YouTubeApifyCsvError):
        build_csv_run(**kwargs)
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    assert not (workspace / ".staging").exists()


def test_unknown_date_filter_fails_closed(tmp_path, registries):
    csv_path = _write_csv(tmp_path / "records.csv")
    assert "day" not in DATE_FILTERS  # the actor has no `day` value (skill evidence)
    with pytest.raises(YouTubeApifyCsvError) as excinfo:
        build_csv_run(**_run_kwargs(csv_path, date_filter="day"))
    assert "date_filter" in str(excinfo.value)


# ---------------------------------------------------------------------------
# A3: a declared count mismatch quarantines deterministically before adoption
# ---------------------------------------------------------------------------


def test_declared_record_count_mismatch_quarantines_before_adoption(tmp_path, registries):
    csv_path = _write_csv(tmp_path / "records.csv")
    workspace, report = _stage(
        tmp_path, registries, build_csv_run(**_run_kwargs(csv_path, record_count=4))
    )
    staged = Path(report["results"][0]["staging_dir"])
    assert load_json(staged / ARTIFACT_MANIFEST_NAME)["artifacts"][0]["record_count"] == 4

    adopted = adopt_staged(
        staged,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert adopted.action == "quarantined"
    assert "ARTIFACT_RECORD_COUNT_MISMATCH" in [issue.code for issue in adopted.l1.issues]
    quarantined_csv = Path(adopted.final_dir) / "records.csv"
    assert quarantined_csv.is_file()  # raw preserved, not deleted or overwritten
    assert quarantined_csv.read_bytes() == csv_path.read_bytes()


# ---------------------------------------------------------------------------
# A4: dateFilter (request) and the observed range stay separate
# ---------------------------------------------------------------------------


def test_date_filter_and_observed_range_stay_separate(tmp_path, registries):
    csv_path = _write_csv(tmp_path / "records.csv")
    _, report = _stage(tmp_path, registries, build_csv_run(**_run_kwargs(csv_path)))
    document = load_json(
        Path(report["results"][0]["staging_dir"]) / RUN_METADATA_NAME
    )
    temporal = document["temporal_provenance"]
    assert temporal["submitted_parameters"] == {
        "date_filter": "year",
        "reference_time": "2026-10-11T19:19:02Z",
    }
    assert temporal["requested_start"] == "2025-10-11T00:00:00Z"
    assert temporal["requested_end_exclusive"] == "2026-10-10T00:00:00Z"
    assert any(
        "must not be treated as the API search condition" in limitation
        for limitation in temporal["limitations"]
    )


# ---------------------------------------------------------------------------
# A5: an existing run id is never overwritten
# ---------------------------------------------------------------------------


def test_restaging_the_same_run_id_stops_without_touching_raw(tmp_path, registries):
    csv_path = _write_csv(tmp_path / "records.csv")
    workspace, first = _stage(tmp_path, registries, build_csv_run(**_run_kwargs(csv_path)))
    assert first["staged"] == 1
    before = (Path(first["results"][0]["staging_dir"]) / "records.csv").read_bytes()

    second = stage_csv(
        build_csv_run(**_run_kwargs(csv_path)),
        declarations_dir=tmp_path / "declarations",
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert second["stopped"] == 1
    assert "RUN_ID_ALREADY_EXISTS" in [
        issue["code"] for issue in second["results"][0]["issues"]
    ]
    assert (Path(first["results"][0]["staging_dir"]) / "records.csv").read_bytes() == before


def test_preexisting_catalog_run_id_stops_without_touching_raw(tmp_path, registries):
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    catalog_dir = workspace / "datasets" / STUDY_ID / "data" / "raw" / "youtube" / RUN_ID
    catalog_dir.mkdir(parents=True)
    marker = catalog_dir / "records.csv"
    marker.write_bytes(b"pre-existing raw; must not be overwritten\n")

    csv_path = _write_csv(tmp_path / "records.csv")
    report = stage_csv(
        build_csv_run(**_run_kwargs(csv_path)),
        declarations_dir=tmp_path / "declarations",
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert report["stopped"] == 1
    assert "RUN_ID_ALREADY_EXISTS" in [
        issue["code"] for issue in report["results"][0]["issues"]
    ]
    assert marker.read_bytes() == b"pre-existing raw; must not be overwritten\n"


# ---------------------------------------------------------------------------
# A6: missing / failed collections are never converted to count = 0
# ---------------------------------------------------------------------------


def test_missing_csv_source_is_a_configuration_error(tmp_path, registries):
    with pytest.raises(YouTubeApifyCsvError) as excinfo:
        build_csv_run(**_run_kwargs(tmp_path / "absent.csv"))
    assert "never recorded as returned_count=0" in str(excinfo.value)
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    assert not (workspace / ".staging").exists()


def test_uncountable_csv_without_declared_count_stages_nothing(tmp_path, registries):
    ragged = tmp_path / "ragged.csv"
    ragged.write_text("id,title\nthree,fields,here\n", encoding="utf-8")
    with pytest.raises(DeclarationError) as excinfo:
        _stage(tmp_path, registries, build_csv_run(**_run_kwargs(ragged)))
    assert "record_count cannot be determined" in str(excinfo.value)
    assert not (tmp_path / "workspace" / ".staging").exists()
