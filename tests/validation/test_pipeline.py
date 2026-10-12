"""Pipeline-layer tests (P4-11 / CV-20 integration).

Focus: layer order, legacy branch, artifact verification wiring and the
stability of the outcome -> report conversion.
"""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.pipeline import validate_full

FIXTURES = Path(__file__).parent / "fixtures"


def _run_document() -> dict:
    return json.loads((FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8"))


def test_valid_document_produces_valid_outcome():
    outcome = validate_full(_run_document(), schema_id="collection-run-v1", target="t")
    assert outcome.valid is True
    assert outcome.issues == []
    assert outcome.profile == "strict"


def test_schema_version_mismatch_fails_through_pipeline():
    document = _run_document()
    document["schema_version"] = "3.0.0"
    outcome = validate_full(document, schema_id="collection-run-v1")
    assert outcome.valid is False
    assert "SCHEMA_VERSION_MISMATCH" in [issue.code for issue in outcome.issues]


def test_unknown_schema_id_raises_value_error():
    with pytest.raises(ValueError, match="^Unknown schema: nope$"):
        validate_full({}, schema_id="nope")


def test_legacy_profile_returns_audit_record():
    legacy = {
        "run_id": "20261001T115959Z-google-trends-cbx-rikiddo",
        "study_id": "cbx-search-trends",
        "source": "google-trends",
    }
    outcome = validate_full(legacy, schema_id="collection-run-v1", profile="legacy")
    assert outcome.valid is True  # missing fields never fail the audit
    assert outcome.issues == []
    assert outcome.legacy is not None
    assert outcome.legacy.status == "incomplete"
    assert "temporal_provenance" in outcome.legacy.missing_fields
    assert outcome.to_report().to_dict()["profile"] == "legacy_audit"


def test_artifact_verification_only_when_requested(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_bytes(b'{"records": []}')
    manifest = {
        "schema_version": "1.0.0",
        "run_id": "20261013T000000Z-x-cbx-001",
        "artifacts": [
            {
                "artifact_id": "artifact-001",
                "path": "payload.json",
                "artifact_type": "raw_records",
                "format": "json",
                "schema_id": "social-post-v1",
                "byte_length": payload.stat().st_size,
                "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
                "layer": "raw",
                "completeness": "complete",
            }
        ],
    }
    (tmp_path / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    document = _run_document()
    document["artifact_manifest"] = "artifact-manifest.json"

    without = validate_full(document, schema_id="collection-run-v1", base_dir=tmp_path)
    assert without.valid is True

    with_artifacts = validate_full(
        document, schema_id="collection-run-v1", base_dir=tmp_path, verify_artifacts=True
    )
    assert with_artifacts.valid is True

    # tamper -> hash mismatch surfaces as a failure
    payload.write_bytes(b'{"records": [1]}')
    tampered = validate_full(
        document, schema_id="collection-run-v1", base_dir=tmp_path, verify_artifacts=True
    )
    assert tampered.valid is False
    assert "ARTIFACT_HASH_MISMATCH" in [issue.code for issue in tampered.issues]


def test_missing_manifest_reports_io_class_issue(tmp_path):
    document = _run_document()
    document["artifact_manifest"] = "not-there.json"
    outcome = validate_full(
        document, schema_id="collection-run-v1", base_dir=tmp_path, verify_artifacts=True
    )
    codes = [issue.code for issue in outcome.issues]
    assert "ARTIFACT_MANIFEST_MISSING" in codes


def test_outcome_does_not_mutate_document():
    document = _run_document()
    before = deepcopy(document)
    validate_full(document, schema_id="collection-run-v1")
    assert document == before


def test_report_conversion_is_stable():
    document = _run_document()
    first = validate_full(document, schema_id="collection-run-v1", target="x").to_report()
    second = validate_full(document, schema_id="collection-run-v1", target="x").to_report()
    assert first.to_dict() == second.to_dict()
