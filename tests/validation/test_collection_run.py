"""Contract tests for the G5 collection-run schema (``collection-run-v1``).

Covers the Phase 2 scope of rollout instruction §16: CV-01 (missing required
fields), CV-02 (type mismatch), CV-03 (unknown fields), CV-07 (invalid
datetime, structural part) and CV-19 (no implicit value changes).

Items intentionally left to later phases are listed in the rollout plan:
CV-04 (registry), CV-05/CV-06 (registry references), CV-08 (temporal
ordering), CV-09/CV-10 (integrity/lineage), CV-11..CV-20 beyond the above.
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.schemas.collection_run import COLLECTION_RUN_SCHEMA

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "collection_run_valid.json"

REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "run_id",
    "study_id",
    "source_id",
    "purpose",
    "collector",
    "collection_started_at",
    "query_provenance",
    "temporal_provenance",
    "execution",
]


def load_valid_document() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Normal case
# ---------------------------------------------------------------------------


def test_valid_fixture_passes():
    """A complete G5 run_metadata document passes strict validation."""
    result = validate_document(load_valid_document(), COLLECTION_RUN_SCHEMA)
    assert result.valid is True, result.errors
    assert result.errors == {}


def test_fixture_contains_every_required_top_level_field():
    """Guard against fixture drift when the schema grows."""
    document = load_valid_document()
    missing = [key for key in REQUIRED_TOP_LEVEL_FIELDS if key not in document]
    assert missing == []


def test_minimal_document_passes():
    """Required fields only: optional blocks (finished_at, manifest,
    environment, extension details) may be absent."""
    document = load_valid_document()
    for optional in (
        "collection_finished_at",
        "artifact_manifest",
        "environment",
    ):
        document.pop(optional)
    document["temporal_provenance"] = {
        "window_id": "2026-09-jst",
        "requested_start": "2026-08-31T15:00:00Z",
        "requested_end_exclusive": "2026-09-30T15:00:00Z",
        "granularity": "day",
        "timezone": "Asia/Tokyo",
    }

    result = validate_document(document, COLLECTION_RUN_SCHEMA)
    assert result.valid is True, result.errors


# ---------------------------------------------------------------------------
# CV-01: required fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", REQUIRED_TOP_LEVEL_FIELDS)
def test_missing_required_top_level_field_fails(field):
    document = load_valid_document()
    del document[field]

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    assert field in result.errors


@pytest.mark.parametrize(
    "parent,child",
    [
        ("collector", "collector_id"),
        ("collector", "adapter_id"),
        ("query_provenance", "query_id"),
        ("query_provenance", "submitted_query"),
        ("temporal_provenance", "window_id"),
        ("temporal_provenance", "requested_start"),
        ("temporal_provenance", "requested_end_exclusive"),
        ("temporal_provenance", "granularity"),
        ("temporal_provenance", "timezone"),
        ("execution", "status"),
        ("execution", "returned_count"),
        ("execution", "errors"),
    ],
)
def test_missing_required_nested_field_fails(parent, child):
    document = load_valid_document()
    del document[parent][child]

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    nested_errors = result.errors[parent]
    assert any(child in entry for entry in nested_errors), nested_errors


@pytest.mark.parametrize(
    "field,empty_value",
    [
        ("schema_version", ""),
        ("run_id", ""),
        ("study_id", ""),
        ("source_id", ""),
        ("purpose", ""),
        ("collection_started_at", ""),
    ],
)
def test_empty_required_string_fails(field, empty_value):
    """``empty: False`` rejects empty strings for identity fields."""
    document = load_valid_document()
    document[field] = empty_value

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    assert field in result.errors


# ---------------------------------------------------------------------------
# CV-02: type mismatch
# ---------------------------------------------------------------------------


def test_returned_count_as_string_fails():
    """normalize=False: numeric-looking strings are not coerced."""
    document = load_valid_document()
    document["execution"]["returned_count"] = "100"

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    assert document["execution"]["returned_count"] == "100"


def test_collector_as_string_fails():
    document = load_valid_document()
    document["collector"] = "x-apify-example"

    assert not validate_document(document, COLLECTION_RUN_SCHEMA).valid


def test_errors_as_dict_fails():
    document = load_valid_document()
    document["execution"]["errors"] = {}

    assert not validate_document(document, COLLECTION_RUN_SCHEMA).valid


def test_negative_returned_count_fails():
    document = load_valid_document()
    document["execution"]["returned_count"] = -1

    assert not validate_document(document, COLLECTION_RUN_SCHEMA).valid


# ---------------------------------------------------------------------------
# CV-03: unknown fields
# ---------------------------------------------------------------------------


def test_unknown_top_level_field_fails():
    document = load_valid_document()
    document["legacy_source"] = "google-trends"

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    assert result.errors.get("legacy_source") == ["unknown field"]


def test_unknown_nested_field_fails():
    document = load_valid_document()
    document["collector"]["token"] = "do-not-record-secrets"

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    nested_errors = result.errors["collector"]
    assert any("token" in entry for entry in nested_errors), nested_errors


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["running", "success", "partial", "failed"])
def test_execution_status_allowed_values(status):
    document = load_valid_document()
    document["execution"]["status"] = status

    assert validate_document(document, COLLECTION_RUN_SCHEMA).valid


def test_execution_status_rejects_unknown_value():
    document = load_valid_document()
    document["execution"]["status"] = "done"

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    nested_errors = result.errors["execution"]
    assert any("status" in entry for entry in nested_errors), nested_errors


@pytest.mark.parametrize("granularity", ["hour", "day", "week", "month"])
def test_temporal_granularity_allowed_values(granularity):
    document = load_valid_document()
    document["temporal_provenance"]["granularity"] = granularity

    assert validate_document(document, COLLECTION_RUN_SCHEMA).valid


def test_temporal_granularity_rejects_unknown_value():
    document = load_valid_document()
    document["temporal_provenance"]["granularity"] = "fortnight"

    assert not validate_document(document, COLLECTION_RUN_SCHEMA).valid


# ---------------------------------------------------------------------------
# CV-07: datetime formats (ordering is a semantic concern, Phase 4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "2026-13-45T99:00:00Z",
        "not-a-date",
        "2026-10-13T00:00:00",  # naive datetime: timezone required
    ],
)
def test_invalid_collection_started_at_fails(value):
    document = load_valid_document()
    document["collection_started_at"] = value

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    assert result.errors.get("collection_started_at")


def test_nullable_observed_timestamps_accept_null_and_valid_values():
    document = load_valid_document()
    document["temporal_provenance"]["observed_min_timestamp"] = None
    document["temporal_provenance"]["observed_max_timestamp"] = (
        "2026-09-15T12:00:00Z"
    )

    assert validate_document(document, COLLECTION_RUN_SCHEMA).valid


def test_observed_timestamp_rejects_invalid_value():
    document = load_valid_document()
    document["temporal_provenance"]["observed_min_timestamp"] = "yesterday"

    assert not validate_document(document, COLLECTION_RUN_SCHEMA).valid


# ---------------------------------------------------------------------------
# Documented extension areas (rollout instruction §6)
# ---------------------------------------------------------------------------


def test_extension_areas_accept_extra_keys():
    """``environment`` and ``submitted_parameters`` are intentionally
    extensible; collector-specific request parameters are recorded there."""
    document = load_valid_document()
    document["environment"]["evidence_refs"] = ["registry-hash-001"]
    document["temporal_provenance"]["submitted_parameters"] = {
        "timeSince": "2026-09-01",
        "timeUntil": "2026-10-01",
    }
    document["temporal_provenance"]["collector_window_type"] = "absolute_date"

    result = validate_document(document, COLLECTION_RUN_SCHEMA)
    assert result.valid is True, result.errors


def test_extension_area_does_not_hide_unknown_top_level_fields():
    """A documented extension area must not weaken top-level strictness."""
    document = load_valid_document()
    document["environment"]["note"] = "ok"
    document["unexpected_top_level"] = "not ok"

    result = validate_document(document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    assert result.errors.get("unexpected_top_level") == ["unknown field"]


# ---------------------------------------------------------------------------
# CV-19: validation is non-destructive
# ---------------------------------------------------------------------------


def test_validation_does_not_mutate_documents():
    document = load_valid_document()
    document["execution"]["extra_legacy_key"] = "kept"
    before = deepcopy(document)

    validate_document(document, COLLECTION_RUN_SCHEMA)

    assert document == before
    assert document["execution"]["extra_legacy_key"] == "kept"


# ---------------------------------------------------------------------------
# Strict profile vs. legacy metadata (rollout instruction §18, Phase 8)
# ---------------------------------------------------------------------------


def test_legacy_run_metadata_shape_fails_strict_validation():
    """The existing run_metadata.json files (datasets/.../raw/...) predate the
    G5 contract; the strict profile must reject them so that the legacy audit
    profile is required for old runs (and cannot be bypassed with the strict
    schema).
    """
    legacy_document = {
        "run_id": "20261001T115959Z-google-trends-cbx-rikiddo",
        "study_id": "cbx-search-trends",
        "source": "google-trends",
        "mcp_server": "google-trends-mcp",
        "collection_timestamp": "2026-10-01T11:59:59Z",
        "queries": [{"term": "CBX", "geo": "JP"}],
    }

    result = validate_document(legacy_document, COLLECTION_RUN_SCHEMA)

    assert result.valid is False
    assert result.errors.get("schema_version") == ["required field"]
    assert result.errors.get("source") == ["unknown field"]


def test_rollout_instruction_section_8_example_divergence():
    """Documents an intentional divergence (see the schema module docstring).

    §8 of the rollout instruction shows an example without
    ``temporal_provenance`` and expects True, but the G5 contract
    (20261013e.md §4.2 / §13) requires temporal provenance. The strict
    schema follows the G5 contract.
    """
    section_8_document = {
        "schema_version": "1.0.0",
        "run_id": "run-001",
        "study_id": "study-001",
        "source_id": "x",
        "purpose": "trend observation",
        "collector": {
            "collector_id": "collector-001",
            "adapter_id": "adapter-001",
        },
        "collection_started_at": "2026-10-13T00:00:00Z",
        "query_provenance": {
            "query_id": "cbx-general-ja",
            "submitted_query": "CBX",
        },
        "execution": {
            "status": "success",
            "returned_count": 100,
            "errors": [],
        },
    }

    result = validate_document(section_8_document, COLLECTION_RUN_SCHEMA)
    assert result.valid is False
    assert result.errors.get("temporal_provenance") == ["required field"]

    # ... and passes once the G5 temporal provenance block is added.
    section_8_document["temporal_provenance"] = {
        "window_id": "2026-10-13-utc",
        "requested_start": "2026-10-13T00:00:00Z",
        "requested_end_exclusive": "2026-10-14T00:00:00Z",
        "granularity": "day",
        "timezone": "Asia/Tokyo",
    }
    extended = validate_document(section_8_document, COLLECTION_RUN_SCHEMA)
    assert extended.valid is True, extended.errors
