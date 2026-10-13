"""Storage contract tests (d.md §10 / §11 / §12 / §13).

Covers the §17 expectations that live at the manifest level:
G4-T01 (duplicate ids), T06 (format), T07 (unregistered reader),
T08 (JSON array shape), T09 (missing page -> partial), T10
(pagination not exhausted -> complete forbidden), T11 (summary vs
timeseries), T12 (SQLite lineage), T14 (raw overwrite detected), T17
(new format via reader registration), T18 (new source, same contract).
"""

import hashlib
import json
import sqlite3
from copy import deepcopy
from pathlib import Path

from validation.integrity import verify_artifact_manifest
from validation.storage_contract import check_manifest_storage_contract

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "metadata" / "artifacts" / "artifact-registry.json"


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _write(path: Path, document) -> Path:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


def _artifact(path: Path, *, base: Path | None = None, **overrides) -> dict:
    raw = path.read_bytes()
    relative = str(path.relative_to(base)) if base is not None else path.name
    artifact = {
        "artifact_id": f"artifact-{path.name}",
        "path": relative,
        "artifact_type": "raw_records",
        "format": "json",
        "schema_id": "x-tweet-result-list-v1",
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "layer": "raw",
        "completeness": "complete",
    }
    artifact.update(overrides)
    return artifact


def _manifest(artifacts, **extra) -> dict:
    document = {
        "schema_version": "1.0.0",
        "run_id": "run-storage-contract",
        "artifacts": artifacts,
    }
    document.update(extra)
    return document


# ---------------------------------------------------------------------------
# T01 / S11
# ---------------------------------------------------------------------------


def test_duplicate_artifact_id_fails(tmp_path):
    payload = _write(tmp_path / "a.json", [{"id": 1}])
    artifact = _artifact(payload, base=tmp_path)
    duplicate = dict(artifact, path=_write(tmp_path / "b.json", [{"id": 2}]).name, byte_length=len(b'[{"id": 2}]'))
    duplicate["sha256"] = hashlib.sha256((tmp_path / "b.json").read_bytes()).hexdigest()
    manifest = _manifest([artifact, duplicate])
    issues = check_manifest_storage_contract(manifest, base_dir=tmp_path, artifact_registry=_registry())
    assert "ARTIFACT_ID_DUPLICATE" in _codes(issues)


def test_unsafe_artifact_paths_fail(tmp_path):
    payload = _write(tmp_path / "a.json", [])
    for unsafe in ("/etc/passwd", "../outside.json"):
        artifact = _artifact(payload, base=tmp_path)
        artifact["path"] = unsafe
        issues = check_manifest_storage_contract(
            _manifest([artifact]), base_dir=tmp_path, artifact_registry=None
        )
        assert "ARTIFACT_PATH_UNSAFE" in _codes(issues), unsafe


# ---------------------------------------------------------------------------
# S6 / S7 / S8 / S9 -> T06 / T07 / T08
# ---------------------------------------------------------------------------


def test_format_mismatch_fails(tmp_path):
    payload = _write(tmp_path / "a.json", [{"id": 1}])
    artifact = _artifact(payload, base=tmp_path, format="csv")
    issues = check_manifest_storage_contract(_manifest([artifact]), base_dir=tmp_path)
    assert "ARTIFACT_FORMAT_MISMATCH" in _codes(issues)


def test_unregistered_schema_fails_when_registry_present(tmp_path):
    payload = _write(tmp_path / "a.json", [{"id": 1}])
    artifact = _artifact(payload, base=tmp_path, schema_id="no-such-schema-v1")
    issues = check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=_registry()
    )
    assert "ARTIFACT_READER_UNREGISTERED" in _codes(issues)
    # Without a registry the reader-dependent check is disabled (repository
    # convention: missing registries never produce false failures).
    assert check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=None
    ) == []


def test_json_array_shape_is_validated(tmp_path):
    payload = _write(tmp_path / "object.json", {"not": "an array"})
    artifact = _artifact(payload, base=tmp_path)  # x-tweet-result-list-v1: array
    issues = check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=_registry()
    )
    assert "ARTIFACT_SCHEMA_INVALID" in _codes(issues)


def test_record_count_mismatch_fails(tmp_path):
    series = _write(
        tmp_path / "series.json",
        {"keyword": "CBD", "data": [{"date": "2026-01-04", "value": 1}]},
    )
    artifact = _artifact(
        series,
        base=tmp_path,
        artifact_type="raw_response",
        schema_id="google-trends-interest-over-time-v1",
        record_count=2,  # the file has one point
    )
    issues = check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=_registry()
    )
    assert "ARTIFACT_RECORD_COUNT_MISMATCH" in _codes(issues)


def test_record_count_is_not_compared_for_summaries(tmp_path):
    summary = _write(
        tmp_path / "summary.json",
        {"compound": "CBD", "data_points": 261, "avg_5y": 32.5},
    )
    artifact = _artifact(
        summary,
        base=tmp_path,
        artifact_type="summary",
        schema_id="google-trends-summary-v1",
        contains_full_timeseries=False,
        record_count=261,  # a declared data_points is not a record count
    )
    assert check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=_registry()
    ) == []


# ---------------------------------------------------------------------------
# T11: summary vs timeseries
# ---------------------------------------------------------------------------


def test_summary_claiming_full_timeseries_fails(tmp_path):
    summary = _write(tmp_path / "summary.json", {"compound": "CBD", "avg_5y": 1})
    artifact = _artifact(
        summary,
        base=tmp_path,
        artifact_type="summary",
        schema_id="google-trends-summary-v1",
        contains_full_timeseries=True,
    )
    issues = check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=_registry()
    )
    assert "ARTIFACT_SUMMARY_TIMESERIES_CONFLICT" in _codes(issues)


def test_registry_side_summary_flag_is_cross_checked(tmp_path):
    series = _write(
        tmp_path / "series.json",
        {"keyword": "CBD", "data": [{"date": "2026-01-04", "value": 1}]},
    )
    registry = _registry()
    for entry in registry["artifact_schemas"]:
        if entry["schema_id"] == "google-trends-interest-over-time-v1":
            entry["contains_full_timeseries"] = False
    artifact = _artifact(
        series,
        base=tmp_path,
        artifact_type="raw_response",
        schema_id="google-trends-interest-over-time-v1",
        contains_full_timeseries=True,
    )
    issues = check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=registry
    )
    assert "ARTIFACT_SUMMARY_TIMESERIES_CONFLICT" in _codes(issues)


# ---------------------------------------------------------------------------
# T09 / T10: pagination groups
# ---------------------------------------------------------------------------

def _page_group(tmp_path, *, expected, pages, exhausted, completeness=None) -> dict:
    artifacts = []
    references = []
    for index, present in pages.items():
        path = tmp_path / f"page-{index:03d}.json"
        document = {"items": list(range(present))}
        if present == 0:
            document = {"items": []}
        _write(path, document)
        artifact = _artifact(path, base=tmp_path, artifact_type="page", schema_id="youtube-search-list-response-v1")
        artifact["artifact_type"] = "page"
        artifact["page_index"] = index
        artifact["artifact_group_id"] = "group-1"
        artifacts.append(artifact)
        references.append({"artifact_id": artifact["artifact_id"], "page_index": index, "path": path.name})
    group = {
        "artifact_group_id": "group-1",
        "group_type": "paginated_collection",
        "expected_pages": expected,
        "collected_pages": len(references),
        "pagination_exhausted": exhausted,
        "artifacts": references,
    }
    if completeness is not None:
        group["completeness"] = completeness
    return _manifest(artifacts, artifact_groups=[group])


def test_complete_page_group_passes(tmp_path):
    manifest = _page_group(tmp_path, expected=3, pages={1: 2, 2: 0, 3: 5}, exhausted=True, completeness="complete")
    issues = check_manifest_storage_contract(
        manifest, base_dir=tmp_path, artifact_registry=_registry()
    )
    assert issues == []


def test_missing_page_is_partial_not_zero(tmp_path):
    """T09: an expected page that is absent is missing (not observed zero)."""
    manifest = _page_group(tmp_path, expected=3, pages={1: 2, 3: 5}, exhausted=False)
    issues = check_manifest_storage_contract(manifest, base_dir=tmp_path)
    missing = [issue for issue in issues if issue.code == "ARTIFACT_PAGE_MISSING"]
    assert missing and all(issue.severity == "warning" for issue in missing)


def test_missing_page_with_exhausted_claim_is_an_error(tmp_path):
    manifest = _page_group(tmp_path, expected=3, pages={1: 2, 3: 5}, exhausted=True)
    issues = check_manifest_storage_contract(manifest, base_dir=tmp_path)
    missing = [issue for issue in issues if issue.code == "ARTIFACT_PAGE_MISSING"]
    assert missing and all(issue.severity == "error" for issue in missing)


def test_not_exhausted_group_must_not_claim_complete(tmp_path):
    """T10: pagination_exhausted=false forbids a complete claim."""
    manifest = _page_group(
        tmp_path, expected=2, pages={1: 1, 2: 1}, exhausted=False, completeness="complete"
    )
    issues = check_manifest_storage_contract(manifest, base_dir=tmp_path)
    assert "ARTIFACT_PAGINATION_INCOMPLETE" in _codes(issues)
    # the same group without the completeness claim is only "partial"
    manifest = _page_group(tmp_path, expected=2, pages={1: 1, 2: 1}, exhausted=False)
    assert check_manifest_storage_contract(manifest, base_dir=tmp_path) == []


def test_group_bookkeeping_mismatches_fail(tmp_path):
    manifest = _page_group(tmp_path, expected=2, pages={1: 1, 2: 1}, exhausted=True)
    manifest["artifact_groups"][0]["collected_pages"] = 5
    assert "ARTIFACT_GROUP_COUNT_MISMATCH" in _codes(
        check_manifest_storage_contract(manifest, base_dir=tmp_path)
    )

    manifest = _page_group(tmp_path, expected=2, pages={1: 1, 2: 1}, exhausted=True)
    manifest["artifact_groups"][0]["artifacts"].append(
        {"artifact_id": "ghost-page", "page_index": 3, "path": "ghost.json"}
    )
    issues = check_manifest_storage_contract(manifest, base_dir=tmp_path)
    assert "ARTIFACT_PAGE_REFERENCE_MISSING" in _codes(issues)
    assert "ARTIFACT_PAGE_INDEX_UNEXPECTED" in _codes(issues)


def test_duplicate_page_index_fails(tmp_path):
    manifest = _page_group(tmp_path, expected=2, pages={1: 1, 2: 1}, exhausted=True)
    manifest["artifact_groups"][0]["artifacts"][1]["page_index"] = 1
    assert "ARTIFACT_PAGE_INDEX_DUPLICATE" in _codes(
        check_manifest_storage_contract(manifest, base_dir=tmp_path)
    )


# ---------------------------------------------------------------------------
# T12: SQLite lineage
# ---------------------------------------------------------------------------

def _sqlite_artifact(tmp_path, *, database=None, **overrides) -> dict:
    db_path = tmp_path / "trends.db"
    if not db_path.exists():
        connection = sqlite3.connect(db_path)
        connection.execute("CREATE TABLE runs (run_id TEXT PRIMARY KEY)")
        connection.execute("CREATE TABLE videos (video_id TEXT PRIMARY KEY)")
        connection.commit()
        connection.close()
    artifact = _artifact(db_path, base=tmp_path, artifact_type="database", format="sqlite", schema_id="sqlite-trends-db-v1")
    if database is not None:
        artifact["database"] = database
    artifact.update(overrides)
    return artifact


def test_database_without_lineage_block_fails(tmp_path):
    artifact = _sqlite_artifact(tmp_path)
    issues = check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=_registry()
    )
    assert "ARTIFACT_DATABASE_LINEAGE_MISSING" in _codes(issues)


def test_database_lineage_block_requires_sources(tmp_path):
    artifact = _sqlite_artifact(
        tmp_path,
        database={
            "db_schema_version": "1.0.0",
            "tables": [
                {
                    "table_name": "runs",
                    "source_run_ids": [],  # empty -> provenance assumed
                    "source_artifact_ids": ["artifact-1"],
                    "deduplication_rule": "primary key on runs.run_id",
                    "transformation_version": "1.0.0",
                }
            ],
        },
    )
    issues = check_manifest_storage_contract(_manifest([artifact]), base_dir=tmp_path)
    assert "ARTIFACT_DATABASE_LINEAGE_MISSING" in _codes(issues)


def test_database_with_complete_lineage_passes(tmp_path):
    artifact = _sqlite_artifact(
        tmp_path,
        database={
            "db_schema_version": "1.0.0",
            "tables": [
                {
                    "table_name": "runs",
                    "record_count": 3,
                    "source_run_ids": ["run-1", "run-2"],
                    "source_artifact_ids": ["artifact-1", "artifact-2"],
                    "deduplication_rule": "primary key on runs.run_id",
                    "transformation_version": "1.0.0",
                }
            ],
        },
    )
    assert check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=_registry()
    ) == []


def test_declared_table_must_exist_in_the_database(tmp_path):
    artifact = _sqlite_artifact(
        tmp_path,
        database={
            "db_schema_version": "1.0.0",
            "tables": [
                {
                    "table_name": "ghost_table",
                    "source_run_ids": ["run-1"],
                    "source_artifact_ids": ["artifact-1"],
                    "deduplication_rule": "primary key",
                    "transformation_version": "1.0.0",
                }
            ],
        },
    )
    issues = check_manifest_storage_contract(_manifest([artifact]), base_dir=tmp_path)
    assert "ARTIFACT_DATABASE_TABLE_MISSING" in _codes(issues)


# ---------------------------------------------------------------------------
# T14: raw overwrite detection (read-only verification)
# ---------------------------------------------------------------------------


def test_raw_overwrite_is_detected_and_refused(tmp_path):
    payload = _write(tmp_path / "payload.json", [{"id": 1}])
    artifact = _artifact(payload, base=tmp_path)
    manifest = _manifest([artifact])
    manifest_path = tmp_path / "artifact-manifest.json"
    _write(manifest_path, manifest)
    assert verify_artifact_manifest(
        manifest_path, base_dir=tmp_path, artifact_registry=_registry()
    ) == []

    payload.write_bytes(b'[{"id": 2}]')
    issues = verify_artifact_manifest(
        manifest_path, base_dir=tmp_path, artifact_registry=_registry()
    )
    assert "ARTIFACT_HASH_MISMATCH" in _codes(issues)
    # verifying never rewrites the tampered file: the evidence stays as found
    assert payload.read_bytes() == b'[{"id": 2}]'


# ---------------------------------------------------------------------------
# T17 / T18: new format, new source - the same contract applies
# ---------------------------------------------------------------------------


def test_new_format_is_adopted_by_registering_a_reader(tmp_path):
    """T17: an unregistered schema fails; a registry entry resolves it."""
    payload = _write(tmp_path / "a.json", [{"id": 1}])
    artifact = _artifact(payload, base=tmp_path, schema_id="tiktok-post-list-v1")
    registry = _registry()
    issues = check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=registry
    )
    assert "ARTIFACT_READER_UNREGISTERED" in _codes(issues)

    registry["artifact_schemas"].append(
        {
            "schema_id": "tiktok-post-list-v1",
            "format": "json",
            "artifact_types": ["raw_records"],
            "reader_id": "json-record-reader",
            "record_count_mode": "array_length",
        }
    )
    assert check_manifest_storage_contract(
        _manifest([artifact]), base_dir=tmp_path, artifact_registry=registry
    ) == []


def test_new_source_uses_the_same_storage_contract(tmp_path):
    """T18: a new source adds no storage code - only registry entries."""
    payload = _write(tmp_path / "a.json", [{"id": 1}, {"id": 2}])
    artifact = _artifact(payload, base=tmp_path, schema_id="tiktok-post-list-v1")
    registry = _registry()
    registry["artifact_schemas"].append(
        {
            "schema_id": "tiktok-post-list-v1",
            "format": "json",
            "artifact_types": ["raw_records"],
            "reader_id": "json-record-reader",
            "record_count_mode": "array_length",
        }
    )
    document = _manifest([artifact])
    assert check_manifest_storage_contract(
        document, base_dir=tmp_path, artifact_registry=registry
    ) == []
    # record_count semantics apply to the new source too
    artifact["record_count"] = 3
    assert "ARTIFACT_RECORD_COUNT_MISMATCH" in _codes(
        check_manifest_storage_contract(
            document, base_dir=tmp_path, artifact_registry=registry
        )
    )


# ---------------------------------------------------------------------------
# read-only / no mutation
# ---------------------------------------------------------------------------


def test_checks_do_not_mutate_the_manifest(tmp_path):
    payload = _write(tmp_path / "a.json", [{"id": 1}])
    document = _manifest([_artifact(payload, base=tmp_path)])
    before = deepcopy(document)
    check_manifest_storage_contract(
        document, base_dir=tmp_path, artifact_registry=_registry()
    )
    assert document == before
