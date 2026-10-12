"""Contract tests for the G4 artifact manifest schema (P3-6).

The normal case uses a *real* file: SHA-256 and byte_length are computed from
bytes written in the test (P3-6 acceptance), never from a placeholder.
"""

import hashlib
import json
from copy import deepcopy

import pytest

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.artifact import ARTIFACT_MANIFEST_SCHEMA


def test_g4_schema_is_registered_under_its_id():
    assert get_schema("artifact-manifest-v1") is ARTIFACT_MANIFEST_SCHEMA


def _manifest_for(tmp_path, payload: bytes = b'{"records": []}') -> dict:
    target = tmp_path / "payload.json"
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    return {
        "schema_version": "1.0.0",
        "run_id": "20261013T000000Z-x-cbx-001",
        "artifacts": [
            {
                "artifact_id": "artifact-001",
                "path": "payload.json",
                "artifact_type": "raw_records",
                "format": "json",
                "media_type": "application/json",
                "schema_id": "social-post-v1",
                "record_count": 100,
                "byte_length": len(payload),
                "sha256": digest,
                "layer": "raw",
                "completeness": "partial",
            }
        ],
    }


def test_manifest_with_real_hash_passes(tmp_path):
    result = validate_document(_manifest_for(tmp_path), ARTIFACT_MANIFEST_SCHEMA)
    assert result.valid is True, result.errors


@pytest.mark.parametrize(
    "field",
    [
        "artifact_id",
        "path",
        "artifact_type",
        "format",
        "schema_id",
        "byte_length",
        "sha256",
        "layer",
        "completeness",
    ],
)
def test_artifact_required_fields(tmp_path, field):
    """d.md §6.2 required list (run_id is envelope-level per §6.1)."""
    document = _manifest_for(tmp_path)
    del document["artifacts"][0][field]
    result = validate_document(document, ARTIFACT_MANIFEST_SCHEMA)
    assert result.valid is False
    assert any(field in str(entry) for entry in result.errors["artifacts"])


def test_sha256_format_is_enforced(tmp_path):
    """P3-6: a tampered sha256 shape fails structurally."""
    document = _manifest_for(tmp_path)
    document["artifacts"][0]["sha256"] = "ACTUAL_SHA256"
    result = validate_document(document, ARTIFACT_MANIFEST_SCHEMA)
    assert result.valid is False
    assert any("sha256" in str(entry) for entry in result.errors["artifacts"])


def test_uppercase_sha256_is_rejected(tmp_path):
    document = _manifest_for(tmp_path)
    document["artifacts"][0]["sha256"] = document["artifacts"][0]["sha256"].upper()
    assert not validate_document(document, ARTIFACT_MANIFEST_SCHEMA).valid


def test_byte_length_must_be_non_negative(tmp_path):
    document = _manifest_for(tmp_path)
    document["artifacts"][0]["byte_length"] = -1
    assert not validate_document(document, ARTIFACT_MANIFEST_SCHEMA).valid


def test_artifact_type_enum(tmp_path):
    document = _manifest_for(tmp_path)
    document["artifacts"][0]["artifact_type"] = "blob"
    assert not validate_document(document, ARTIFACT_MANIFEST_SCHEMA).valid


def test_format_and_layer_and_completeness_enums(tmp_path):
    for field, value in (
        ("format", "excel"),
        ("layer", "published"),
        ("completeness", "done"),
    ):
        document = _manifest_for(tmp_path)
        document["artifacts"][0][field] = value
        assert not validate_document(document, ARTIFACT_MANIFEST_SCHEMA).valid, field


def test_derived_artifact_lineage_shape(tmp_path):
    """d.md §15: derived artifacts carry derived_from references."""
    document = _manifest_for(tmp_path)
    document["artifacts"].append(
        {
            "artifact_id": "monthly-counts-001",
            "path": "monthly.json",
            "artifact_type": "aggregate",
            "format": "json",
            "schema_id": "monthly-count-v1",
            "byte_length": 10,
            "sha256": "0" * 64,
            "layer": "processed",
            "completeness": "complete",
            "derived_from": ["artifact-001", "artifact-002"],
            "transformation": {"name": "monthly_post_count", "version": "1.0.0"},
        }
    )
    assert validate_document(document, ARTIFACT_MANIFEST_SCHEMA).valid is True


def test_manifest_does_not_mutate(tmp_path):
    document = _manifest_for(tmp_path)
    before = deepcopy(document)
    validate_document(document, ARTIFACT_MANIFEST_SCHEMA)
    assert document == before


def test_record_count_optional_and_non_negative(tmp_path):
    document = _manifest_for(tmp_path)
    del document["artifacts"][0]["record_count"]
    assert validate_document(document, ARTIFACT_MANIFEST_SCHEMA).valid is True
    document["artifacts"][0]["record_count"] = -1
    assert not validate_document(document, ARTIFACT_MANIFEST_SCHEMA).valid


def test_unknown_artifact_field_fails(tmp_path):
    document = _manifest_for(tmp_path)
    document["artifacts"][0]["checksum"] = "md5:abc"
    result = validate_document(document, ARTIFACT_MANIFEST_SCHEMA)
    assert result.valid is False
    assert any("checksum" in str(entry) for entry in result.errors["artifacts"])
