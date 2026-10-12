"""Contract tests for schema version management (P3-2 / CV-20).

- every registered schema has a contract version;
- a document whose ``schema_version`` differs from the registered contract
  version is detected as a data validation failure (CV-20);
- absence of the field is the structural layer's concern (required check),
  not the semantic version check.
"""

import json
from pathlib import Path

from validation.schema_registry import (
    SCHEMA_REGISTRY,
    SCHEMA_VERSIONS,
    get_schema_version,
)
from validation.semantic import check_schema_version

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "collection_run_valid.json"


def test_every_schema_has_a_version():
    assert set(SCHEMA_VERSIONS) == set(SCHEMA_REGISTRY)
    for schema_id, version in SCHEMA_VERSIONS.items():
        assert isinstance(version, str) and version, schema_id


def test_get_schema_version_rejects_unknown_ids():
    import pytest

    with pytest.raises(ValueError, match="^Unknown schema: no-such-schema$"):
        get_schema_version("no-such-schema")


def test_matching_version_produces_no_issue():
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert document["schema_version"] == get_schema_version("collection-run-v1")
    assert check_schema_version(document, "collection-run-v1") == []


def test_cv20_version_mismatch_is_detected():
    """CV-20: a newer document schema_version must not silently pass."""
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    document["schema_version"] = "2.0.0"

    issues = check_schema_version(document, "collection-run-v1")

    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == "SCHEMA_VERSION_MISMATCH"
    assert issue.path == "/schema_version"
    assert issue.severity == "error"
    assert "1.0.0" in issue.message
    assert "2.0.0" not in issue.message  # value itself stays out of reports


def test_missing_version_is_not_reported_by_semantic_check():
    """The required-field rule belongs to the structural schema."""
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    document.pop("schema_version")
    assert check_schema_version(document, "collection-run-v1") == []


def test_version_check_covers_every_schema_family():
    for schema_id in SCHEMA_REGISTRY:
        document = {"schema_version": "9.9.9"}
        issues = check_schema_version(document, schema_id)
        assert [issue.code for issue in issues] == ["SCHEMA_VERSION_MISMATCH"], schema_id
