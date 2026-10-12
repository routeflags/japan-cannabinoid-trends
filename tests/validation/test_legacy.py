"""Legacy audit profile tests (P8-1 / P8-3) and frozen-list integrity.
"""

import json
from pathlib import Path

import pytest

from validation.legacy import (
    LEGACY_RUN_IDS,
    LegacyProfileNotAllowed,
    audit_record,
    missing_required_paths,
    resolve_profile,
)
from validation.schemas.collection_run import COLLECTION_RUN_SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = REPO_ROOT / "docs" / "audits" / "g5-legacy-runs.json"

LEGACY_SAMPLE = {
    "run_id": "20261001T115959Z-google-trends-cbx-rikiddo",
    "study_id": "cbx-search-trends",
    "source": "google-trends",
    "mcp_server": "google-trends-mcp",
    "collection_timestamp": "2026-10-01T11:59:59Z",
    "queries": [{"term": "CBX", "geo": "JP"}],
}


def test_missing_required_paths_top_level():
    missing = missing_required_paths(LEGACY_SAMPLE, COLLECTION_RUN_SCHEMA)
    assert missing == [
        "schema_version",
        "source_id",
        "purpose",
        "collector",
        "collection_started_at",
        "query_provenance",
        "temporal_provenance",
        "execution",
    ]


def test_missing_required_paths_descends_nested_dicts():
    document = {
        "collector": {"collector_id": "x"},  # adapter_id missing
        "query_provenance": {},
    }
    missing = missing_required_paths(document, COLLECTION_RUN_SCHEMA)
    assert "collector.adapter_id" in missing
    assert "query_provenance.query_id" in missing
    assert "query_provenance.submitted_query" in missing


def test_audit_record_matches_h_md_section_18_shape():
    record = audit_record(LEGACY_SAMPLE)
    assert record.to_dict() == {
        "profile": "legacy_audit",
        "run_id": "20261001T115959Z-google-trends-cbx-rikiddo",
        "status": "incomplete",
        "missing_fields": [
            "schema_version",
            "source_id",
            "purpose",
            "collector",
            "collection_started_at",
            "query_provenance",
            "temporal_provenance",
            "execution",
        ],
    }


def test_audit_record_complete_when_requirements_present():
    document = json.loads(
        (Path(__file__).parent / "fixtures" / "collection_run_valid.json").read_text(
            encoding="utf-8"
        )
    )
    record = audit_record(document)
    assert record.status == "complete"
    assert record.missing_fields == []


def test_audit_never_fails_for_missing_fields():
    """P8-1: legacy profile reports, it does not FAIL."""
    record = audit_record(LEGACY_SAMPLE)
    assert record.status == "incomplete"


def test_resolve_profile_strict_passthrough():
    assert resolve_profile("strict", LEGACY_SAMPLE) == "strict"


def test_resolve_profile_legacy_for_frozen_ids():
    assert resolve_profile("legacy", LEGACY_SAMPLE) == "legacy_audit"


def test_p8_3_bypass_attempt_is_refused():
    """A new run cannot use the legacy profile to avoid strict validation."""
    new_run = {"run_id": "20261013T000000Z-x-cbx-001"}
    assert new_run["run_id"] not in LEGACY_RUN_IDS
    with pytest.raises(LegacyProfileNotAllowed):
        resolve_profile("legacy", new_run)


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="^Unknown profile: loose$"):
        resolve_profile("loose", LEGACY_SAMPLE)


def test_frozen_list_matches_the_audit_artifact():
    """The frozen list and the non-destructive audit snapshot must agree.

    Adding a legacy run requires a fresh audit (P8-2) and a review; the test
    fails when someone edits only one of the two artifacts.
    """
    assert AUDIT_PATH.is_file(), "run `python -m validation.cli audit-legacy` first"
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    audited = {entry["run_id"] for entry in audit["runs"]}
    assert audited == set(LEGACY_RUN_IDS)


def test_audit_artifact_records_raw_immutability():
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    assert audit["raw_modified"] is False
    for entry in audit["runs"]:
        if entry["status"] == "unreadable":
            continue
        assert entry["sha256"] == entry["sha256_after"]
        assert entry["unchanged"] is True


def test_audit_artifact_records_missing_field_reports():
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    assert audit["count"] == len(audit["runs"])
    for entry in audit["runs"]:
        assert entry["profile"] == "legacy_audit"
        assert entry["status"] in ("complete", "incomplete", "unreadable")
        assert isinstance(entry["missing_fields"], list)
