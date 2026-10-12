"""Contract tests for the G6 storage policy / publication decision schemas
(P3-8).

Covers f.md §6.1 / §10.3 samples and the enum constraints (classification,
storage, git_tracking, publication, decision status).
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.storage_policy import (
    GIT_TRACKING_VALUES,
    PUBLICATION_DECISION_SCHEMA,
    PUBLICATION_STATES,
    STORAGE_CLASSIFICATIONS,
    STORAGE_POLICY_REGISTRY_SCHEMA,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_g6_schemas_are_registered_under_their_ids():
    assert get_schema("storage-policy-registry-v1") is STORAGE_POLICY_REGISTRY_SCHEMA
    assert get_schema("publication-decision-v1") is PUBLICATION_DECISION_SCHEMA


def test_storage_policy_sample_passes():
    result = validate_document(_load("storage_policies.json"), STORAGE_POLICY_REGISTRY_SCHEMA)
    assert result.valid is True, result.errors


def test_policy_required_fields():
    for field in (
        "policy_id",
        "artifact_layer",
        "source_kind",
        "classification",
        "storage",
        "git_tracking",
        "publication",
    ):
        document = _load("storage_policies.json")
        del document["policies"][0][field]
        assert not validate_document(document, STORAGE_POLICY_REGISTRY_SCHEMA).valid, field


def test_classification_enum():
    assert STORAGE_CLASSIFICATIONS == ["public", "internal", "restricted", "sensitive", "unknown"]
    document = _load("storage_policies.json")
    document["policies"][0]["classification"] = "confidential"
    assert not validate_document(document, STORAGE_POLICY_REGISTRY_SCHEMA).valid


def test_git_tracking_enum():
    assert GIT_TRACKING_VALUES == ["tracked", "ignored", "conditional"]
    document = _load("storage_policies.json")
    document["policies"][0]["git_tracking"] = "sometimes"
    assert not validate_document(document, STORAGE_POLICY_REGISTRY_SCHEMA).valid


def test_publication_axis_enum():
    assert PUBLICATION_STATES == ["approved", "denied", "requires_review", "unknown"]
    document = _load("storage_policies.json")
    document["policies"][0]["publication"] = "maybe"
    assert not validate_document(document, STORAGE_POLICY_REGISTRY_SCHEMA).valid


def test_storage_backend_enum():
    document = _load("storage_policies.json")
    document["policies"][0]["storage"] = "local-disk"
    assert not validate_document(document, STORAGE_POLICY_REGISTRY_SCHEMA).valid


def test_artifact_layer_enum_includes_metadata():
    document = _load("storage_policies.json")
    assert document["policies"][2]["artifact_layer"] == "metadata"
    document["policies"][0]["artifact_layer"] = "bronze"
    assert not validate_document(document, STORAGE_POLICY_REGISTRY_SCHEMA).valid


def test_publication_decision_sample_passes():
    result = validate_document(_load("publication_decision.json"), PUBLICATION_DECISION_SCHEMA)
    assert result.valid is True, result.errors


def test_publication_decision_required_fields():
    for field in ("decision_id", "artifact_id", "status", "criteria_version"):
        document = _load("publication_decision.json")
        del document[field]
        assert not validate_document(document, PUBLICATION_DECISION_SCHEMA).valid, field


def test_publication_decision_status_enum():
    document = _load("publication_decision.json")
    document["status"] = "pending"
    assert not validate_document(document, PUBLICATION_DECISION_SCHEMA).valid


def test_approved_decision_carries_hash_shape():
    """f.md §10.3: approval records the artifact hash; shape only here,
    the criteria completeness is enforced by the publication gate (P4-9)."""
    document = _load("publication_decision.json")
    document.update(
        {
            "status": "approved",
            "reviewed_at": "2026-10-13T00:00:00Z",
            "reviewer": "reviewer-id",
            "artifact_sha256": "a" * 64,
        }
    )
    assert validate_document(document, PUBLICATION_DECISION_SCHEMA).valid is True
    document["artifact_sha256"] = "not-a-hash"
    assert not validate_document(document, PUBLICATION_DECISION_SCHEMA).valid


def test_storage_policy_does_not_mutate():
    document = _load("storage_policies.json")
    before = deepcopy(document)
    validate_document(document, STORAGE_POLICY_REGISTRY_SCHEMA)
    assert document == before
