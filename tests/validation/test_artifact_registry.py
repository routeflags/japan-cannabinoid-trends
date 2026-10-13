"""Contract tests for the G4 artifact registry (d.md §7).

The registry document (``metadata/artifacts/artifact-registry.json``) is
validated by ``validate-registries`` in two layers: the structural schema
(``artifact-registry-v1``) and ``validation.storage_contract.check_artifact_registry``
(duplicate ids, unknown reader references, active-but-unimplemented readers,
reader format coverage).
"""

import json
from copy import deepcopy
from pathlib import Path

from validation.cli import load_registries
from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.artifact_registry import ARTIFACT_REGISTRY_SCHEMA
from validation.storage_contract import check_artifact_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "metadata" / "artifacts" / "artifact-registry.json"


def _document() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


def test_artifact_registry_schema_is_registered():
    assert get_schema("artifact-registry-v1") is ARTIFACT_REGISTRY_SCHEMA


def test_repository_registry_satisfies_the_schema():
    result = validate_document(_document(), ARTIFACT_REGISTRY_SCHEMA)
    assert result.valid is True, result.errors


def test_repository_registry_is_internally_consistent():
    assert check_artifact_registry(_document()) == []


def test_every_registered_schema_resolves_to_an_implemented_reader():
    from storage.readers import get_reader

    document = _document()
    readers = {item["reader_id"]: item for item in document["readers"]}
    for schema in document["artifact_schemas"]:
        entry = readers[schema["reader_id"]]
        assert entry["status"] == "active", schema["schema_id"]
        assert get_reader(schema["reader_id"]) is not None, schema["schema_id"]
        assert schema["format"] in entry["formats"], schema["schema_id"]


def test_g1_payload_schema_is_registered():
    """The G1 Google Trends payload schema must resolve (L1 depends on it)."""
    entry = next(
        item
        for item in _document()["artifact_schemas"]
        if item["schema_id"] == "google-trends-interest-over-time-v1"
    )
    assert entry["reader_id"] == "json-timeseries-reader"
    assert entry["record_count_mode"] == "data_points"
    assert entry["contains_full_timeseries"] is True


def test_duplicate_reader_id_fails():
    document = _document()
    document["readers"].append(deepcopy(document["readers"][0]))
    assert "ARTIFACT_REGISTRY_DUPLICATE_ID" in _codes(check_artifact_registry(document))


def test_duplicate_schema_id_fails():
    document = _document()
    document["artifact_schemas"].append(deepcopy(document["artifact_schemas"][0]))
    assert "ARTIFACT_REGISTRY_DUPLICATE_ID" in _codes(check_artifact_registry(document))


def test_unknown_reader_reference_fails():
    document = _document()
    document["artifact_schemas"][0]["reader_id"] = "not-a-reader"
    assert "ARTIFACT_REGISTRY_UNKNOWN_READER" in _codes(
        check_artifact_registry(document)
    )


def test_active_reader_without_implementation_fails():
    document = _document()
    document["readers"][0]["reader_id"] = "imaginary-reader"
    assert "ARTIFACT_REGISTRY_UNIMPLEMENTED" in _codes(
        check_artifact_registry(document)
    )


def test_reader_format_coverage_is_checked():
    document = _document()
    document["readers"][0]["formats"] = ["csv"]
    assert "ARTIFACT_REGISTRY_FORMAT_MISMATCH" in _codes(
        check_artifact_registry(document)
    )


def test_planned_reader_reference_is_a_warning():
    document = _document()
    document["readers"][0]["status"] = "planned"
    issues = check_artifact_registry(document)
    warnings = [issue for issue in issues if issue.code == "ARTIFACT_REGISTRY_PLANNED_REFERENCE"]
    assert warnings and all(issue.severity == "warning" for issue in warnings)


def test_validate_registries_covers_the_artifact_registry(tmp_path):
    """The CLI target set includes the new registry (7 targets today)."""
    from validation.cli import EXIT_OK, main

    report_path = tmp_path / "report.json"
    code = main(
        [
            "validate-registries",
            "--config-dir",
            str(REPO_ROOT / "config"),
            "--metadata-dir",
            str(REPO_ROOT / "metadata"),
            "--format",
            "json",
            "--output",
            str(report_path),
        ]
    )
    assert code == EXIT_OK
    bundle = json.loads(report_path.read_text(encoding="utf-8"))
    targets = {report["schema_id"] for report in bundle["reports"]}
    assert "artifact-registry-v1" in targets
    assert bundle["valid"] is True


def test_load_registries_carries_the_artifact_registry():
    registries = load_registries(REPO_ROOT / "config", REPO_ROOT / "metadata")
    assert isinstance(registries.artifact_registry, dict)
    assert registries.artifact_registry["schema_version"] == "1.0.0"
