"""Staging driver contract tests (ISS-20261015-COL-017).

A declaration (``staging-declaration-v1``) is assembled into a plan, artifact
claims and execution facts, then run through ``stage_run`` -> ``adopt_staged``.
The payload is the **synthetic** CSV under ``tests/storage/fixtures`` (a real
dataset export cannot be committed - third-party video metadata); the driver
never consults the payload's own columns to decide what a file is, so the
synthetic rows exercise exactly the same code paths as the real download.
"""

import json
from pathlib import Path

import pytest

from validation.integrity import sha256_file
from validation.pipeline import validate_full

from collection.core.pipeline import ARTIFACT_MANIFEST_NAME, RUN_METADATA_NAME, adopt_staged
from collection.core.staging import (
    DeclarationError,
    load_declaration,
    stage_declaration,
)

from conftest import load_json, make_workspace

STUDY_ID = "youtube-consistency"
COLLECTOR_ID = "youtube-apify-scraper"
SCHEMA_ID = "youtube-dataset-csv-v1"
RUN_ID = "20261010T135024Z-youtube-youtube-consistency"
SYNTHETIC = (
    Path(__file__).resolve().parents[1]
    / "storage"
    / "fixtures"
    / "dataset_export_synthetic.csv"
)


def _run(**overrides) -> dict:
    run = {
        "run_id": RUN_ID,
        "study_id": STUDY_ID,
        "source_id": "youtube",
        "collector_id": COLLECTOR_ID,
        "purpose": "ISS-20261015-COL-017 contract test (synthetic payload)",
        # Declared, never inferred: the payload's own `input` column is not
        # consulted for this mapping.
        "query": {"keyword": "CBD リキッド", "query_id": "cbd-liquid-ja"},
        "window": {
            "start": "2026-01-01T00:00:00Z",
            "end_exclusive": "2026-01-10T00:00:00Z",
            "granularity": "month",
            "timezone": "UTC",
        },
        "collection_request": {
            "date_filter": "month",
            "reference_time": "2026-01-06T00:00:00Z",
        },
        "temporal": {
            "collector_window_type": "relative_duration",
            "boundary_semantics": "synthetic test: relative filter resolved by the collector",
            "exact_window_match": False,
            "limitations": [
                "synthetic test: the absolute window is declared, not collector-enforced",
            ],
        },
        "timestamps": {
            "started_at": "2026-01-06T00:00:00Z",
            "finished_at": "2026-01-06T00:00:00Z",
            "basis": "synthetic fixture: no payload timestamp exists",
        },
        "execution": {"status": "success", "returned_count": None, "errors": []},
        "artifacts": [
            {
                "source": str(SYNTHETIC),
                "path": "records.csv",
                "artifact_type": "raw_records",
                "format": "csv",
                "schema_id": SCHEMA_ID,
                "completeness": "complete",
            }
        ],
    }
    run.update(overrides)
    return run


def _declaration(*runs, **overrides) -> dict:
    document = {
        "declaration_version": "staging-declaration-v1",
        "description": "synthetic contract test",
        "runs": list(runs) or [_run()],
    }
    document.update(overrides)
    return document


def _write(tmp_path: Path, document: dict, name: str = "declaration.json") -> Path:
    path = tmp_path / name
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _stage(tmp_path, registries, document=None, name="declaration.json"):
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    declaration = load_declaration(_write(tmp_path, document or _declaration(), name))
    report = stage_declaration(
        declaration,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    return workspace, declaration, report


# ---------------------------------------------------------------------------
# happy path: declare -> stage -> adopt -> strict validation
# ---------------------------------------------------------------------------


def test_declared_run_is_staged_then_cataloged_strictly_valid(tmp_path, registries):
    workspace, declaration, report = _stage(tmp_path, registries)

    assert report["staged"] == 1 and report["stopped"] == 0
    result = report["results"][0]
    assert result["action"] == "staged"
    assert result["run_id"] == RUN_ID
    staged = Path(result["staging_dir"])
    assert sorted(path.name for path in staged.iterdir()) == [
        ARTIFACT_MANIFEST_NAME,
        "records.csv",
        RUN_METADATA_NAME,
    ]

    adopted = adopt_staged(
        staged,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert adopted.action == "adopted", [issue.code for issue in adopted.issues]
    final = Path(adopted.final_dir)
    assert final == workspace / "datasets" / STUDY_ID / "data" / "raw" / "youtube" / RUN_ID

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
    assert not [issue for issue in outcome.issues if issue.severity in ("error", "warning")]
    # The collector is registered as `unverified`; that stays visible (info).
    assert "COLLECTOR_LEGACY_REFERENCE" in [issue.code for issue in outcome.issues]


def test_payload_is_the_declared_file_byte_for_byte(tmp_path, registries):
    workspace, _, report = _stage(tmp_path, registries)
    staged = Path(report["results"][0]["staging_dir"])
    assert (staged / "records.csv").read_bytes() == SYNTHETIC.read_bytes()

    manifest = load_json(staged / ARTIFACT_MANIFEST_NAME)
    artifact = manifest["artifacts"][0]
    assert artifact["sha256"] == sha256_file(SYNTHETIC)
    assert artifact["byte_length"] == SYNTHETIC.stat().st_size
    assert artifact["record_count"] == 3  # CSV records, not physical lines
    assert artifact["format"] == "csv"
    assert artifact["layer"] == "raw"


def test_metadata_records_declared_and_derived_facts(tmp_path, registries):
    workspace, declaration, report = _stage(tmp_path, registries)
    document = load_json(Path(report["results"][0]["staging_dir"]) / RUN_METADATA_NAME)

    assert document["run_id"] == RUN_ID
    assert document["source_id"] == "youtube"
    assert document["study_id"] == STUDY_ID
    assert document["collector"] == {
        "collector_id": COLLECTOR_ID,
        "adapter_id": "youtube-apify-scraper@1",
        "version": "unknown",
        "provider": "apify",
        "transport": "actor",
        "external_id": "h7sDV53CddomktSi5",
    }
    assert document["query_provenance"] == {
        "query_id": "cbd-liquid-ja",
        "submitted_query": "CBD リキッド",
        "compound_id": "compound_cbd",
        "intent_id": "product_liquid",
        "query_registry_version": "1.0.0",
    }
    # returned_count is derived from the artifact (the payload is the count's
    # only evidence); pagination was not observed, so it is not recorded.
    assert document["execution"] == {
        "status": "success",
        "returned_count": 3,
        "errors": [],
    }

    temporal = document["temporal_provenance"]
    assert temporal["window_id"] == "2026-01-01T00:00:00Z_2026-01-10T00:00:00Z"
    assert temporal["requested_start"] == "2026-01-01T00:00:00Z"
    assert temporal["requested_end_exclusive"] == "2026-01-10T00:00:00Z"
    assert temporal["granularity"] == "month"
    assert temporal["timezone"] == "UTC"
    assert temporal["collector_window_type"] == "relative_duration"
    assert temporal["exact_window_match"] is False
    assert temporal["reference_time"] == "2026-01-06T00:00:00Z"
    assert temporal["limitations"] == [
        "synthetic test: the absolute window is declared, not collector-enforced"
    ]
    assert temporal["submitted_parameters"] == {
        "date_filter": "month",
        "reference_time": "2026-01-06T00:00:00Z",
    }

    assert document["collection_started_at"] == "2026-01-06T00:00:00Z"
    assert document["collection_finished_at"] == "2026-01-06T00:00:00Z"

    environment = document["environment"]
    assert environment["adapter"] == {
        "collection_mode": "external_staged",
        "collector_version": "unknown",
    }
    handover = environment["handover"]
    assert handover["declaration_name"] == "declaration.json"
    assert handover["declaration_sha256"] == sha256_file(declaration.path)
    assert handover["timestamp_basis"] == "synthetic fixture: no payload timestamp exists"
    assert handover["record_counts"] == {"records.csv": "derived:csv-record-reader"}
    assert handover["returned_count"] == "derived:sum(artifacts)"


def test_declared_keyword_is_never_inferred_from_the_payload(tmp_path, registries):
    """A declaration whose keyword disagrees with the CSV's own `input`
    column is staged with the declared keyword - proof that the driver does
    not infer the search from the payload."""
    other = tmp_path / "other.csv"
    other.write_bytes(
        ("id,title,input\nsynthetic-9001,other record,NOT-THE-DECLARED-KEYWORD\n").encode(
            "utf-8"
        )
    )
    run = _run()
    run["artifacts"][0]["source"] = str(other)
    workspace, _, report = _stage(tmp_path, registries, _declaration(run))

    assert report["staged"] == 1, report["results"]
    document = load_json(Path(report["results"][0]["staging_dir"]) / RUN_METADATA_NAME)
    assert document["query_provenance"]["submitted_query"] == "CBD リキッド"


def test_declared_record_count_is_passed_through_and_verified_by_l1(tmp_path, registries):
    """A declared count is not recomputed by the driver; L1 has to catch an
    incorrect one (S8 is not vacuous through this path either)."""
    run = _run()
    run["artifacts"][0]["record_count"] = 4  # the synthetic file has 3
    workspace, _, report = _stage(tmp_path, registries, _declaration(run))
    staged = Path(report["results"][0]["staging_dir"])
    manifest = load_json(staged / ARTIFACT_MANIFEST_NAME)
    assert manifest["artifacts"][0]["record_count"] == 4

    adopted = adopt_staged(
        staged,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert adopted.action == "quarantined"
    assert "ARTIFACT_RECORD_COUNT_MISMATCH" in [
        issue.code for issue in adopted.l1.issues
    ]
    assert (Path(adopted.final_dir) / "records.csv").is_file()  # raw preserved


def test_two_runs_of_the_same_query_stage_under_distinct_ids(tmp_path, registries):
    second = _run(
        run_id="20261011T191900Z-youtube-youtube-consistency",
        timestamps={
            "started_at": "2026-01-07T00:00:00Z",
            "finished_at": "2026-01-07T00:00:00Z",
            "basis": "synthetic fixture",
        },
        window={
            "start": "2025-01-01T00:00:00Z",
            "end_exclusive": "2026-01-07T00:00:00Z",
            "granularity": "month",
            "timezone": "UTC",
        },
    )
    first = _run(run_id=None)  # stage_run derives it from started_at
    _, _, report = _stage(tmp_path, registries, _declaration(first, second))

    assert report["staged"] == 2
    ids = [entry["run_id"] for entry in report["results"]]
    assert ids == [
        "20260106T000000Z-youtube-youtube-consistency",
        "20261011T191900Z-youtube-youtube-consistency",
    ]


# ---------------------------------------------------------------------------
# declaration-level refusals (configuration errors, nothing staged)
# ---------------------------------------------------------------------------


def test_unknown_query_id_is_refused_before_anything_is_staged(tmp_path, registries):
    run = _run()
    run["query"]["query_id"] = "no-such-query"
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    declaration = load_declaration(_write(tmp_path, _declaration(run)))

    with pytest.raises(DeclarationError) as excinfo:
        stage_declaration(
            declaration,
            workspace_root=workspace,
            datasets_root=workspace / "datasets",
            registries=registries,
        )

    assert "no-such-query" in str(excinfo.value)
    assert "not registered" in str(excinfo.value)
    assert not (workspace / ".staging").exists()


def test_structural_problem_names_the_declaration_path(tmp_path, registries):
    run = _run()
    del run["window"]["granularity"]
    with pytest.raises(DeclarationError) as excinfo:
        load_declaration(_write(tmp_path, _declaration(run)))
    assert any(
        "granularity" in issue.path or "granularity" in issue.message
        for issue in excinfo.value.issues
    )


def test_unknown_declaration_key_is_refused(tmp_path):
    document = _declaration()
    document["descriptoin"] = "typo"
    with pytest.raises(DeclarationError) as excinfo:
        load_declaration(_write(tmp_path, document))
    assert any(
        "descriptoin" in issue.path or "descriptoin" in issue.message
        for issue in excinfo.value.issues
    )


def test_empty_runs_list_is_refused(tmp_path):
    document = _declaration()
    document["runs"] = []
    with pytest.raises(DeclarationError):
        load_declaration(_write(tmp_path, document))


def test_uncountable_source_is_a_declaration_error(tmp_path, registries):
    run = _run()
    run["artifacts"][0]["source"] = str(tmp_path / "absent.csv")
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    declaration = load_declaration(_write(tmp_path, _declaration(run)))

    with pytest.raises(DeclarationError) as excinfo:
        stage_declaration(
            declaration,
            workspace_root=workspace,
            datasets_root=workspace / "datasets",
            registries=registries,
        )
    assert "record_count cannot be determined" in str(excinfo.value)


# ---------------------------------------------------------------------------
# pipeline-level refusals (per run, batch continues)
# ---------------------------------------------------------------------------


def test_unregistered_collector_stops_only_that_run(tmp_path, registries):
    bad = _run(run_id="20261010T140000Z-youtube-youtube-consistency")
    bad["collector_id"] = "no-such-collector"
    _, _, report = _stage(tmp_path, registries, _declaration(bad, _run()))

    assert report["stopped"] == 1 and report["staged"] == 1
    stopped, staged = report["results"]
    assert stopped["action"] == "stopped"
    assert "STAGING_COLLECTOR_UNKNOWN" in [issue["code"] for issue in stopped["issues"]]
    assert staged["action"] == "staged"


def test_unsafe_artifact_path_is_refused_by_stage_run(tmp_path, registries):
    run = _run()
    run["artifacts"][0]["path"] = "../escaped.csv"
    _, _, report = _stage(tmp_path, registries, _declaration(run))
    assert report["stopped"] == 1
    assert "STAGING_ARTIFACT_PATH_UNSAFE" in [
        issue["code"] for issue in report["results"][0]["issues"]
    ]
    assert not (tmp_path / "escaped.csv").exists()


def test_restaging_reports_the_existing_run(tmp_path, registries):
    workspace = make_workspace(tmp_path, studies=(STUDY_ID,))
    document = _declaration()
    declaration = load_declaration(_write(tmp_path, document))
    first = stage_declaration(
        declaration,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert first["staged"] == 1
    second = stage_declaration(
        declaration,
        workspace_root=workspace,
        datasets_root=workspace / "datasets",
        registries=registries,
    )
    assert second["stopped"] == 1
    assert "RUN_ID_ALREADY_EXISTS" in [
        issue["code"] for issue in second["results"][0]["issues"]
    ]
