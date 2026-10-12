"""Contract tests for the G1 source / collector registry schemas (P3-3).

Covers a.md §6/§7/§7.2/§7.3/§14 samples and the structural side of the
"new source" contract test (a.md §15 items 1-3).
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.registries import (
    CAPABILITY_VALUES,
    COLLECTOR_REGISTRY_SCHEMA,
    COLLECTOR_STATUSES,
    SOURCE_REGISTRY_SCHEMA,
)

FIXTURES = Path(__file__).parent / "fixtures" / "registries"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_g1_schemas_are_registered_under_their_ids():
    assert get_schema("source-registry-v1") is SOURCE_REGISTRY_SCHEMA
    assert get_schema("collector-registry-v1") is COLLECTOR_REGISTRY_SCHEMA


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------


def test_source_registry_sample_passes():
    result = validate_document(_load("sources.json"), SOURCE_REGISTRY_SCHEMA)
    assert result.valid is True, result.errors


def test_source_registry_requires_schema_version():
    document = _load("sources.json")
    del document["schema_version"]
    assert not validate_document(document, SOURCE_REGISTRY_SCHEMA).valid


def test_source_item_requires_source_id_and_kind():
    document = _load("sources.json")
    del document["sources"][0]["source_id"]
    result = validate_document(document, SOURCE_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any("source_id" in str(entry) for entry in result.errors["sources"])


def test_source_registry_rejects_unknown_item_field():
    document = _load("sources.json")
    document["sources"][0]["api_key"] = "should-not-be-here"
    result = validate_document(document, SOURCE_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any("api_key" in str(entry) for entry in result.errors["sources"])


def test_source_registry_does_not_mutate():
    document = _load("sources.json")
    before = deepcopy(document)
    validate_document(document, SOURCE_REGISTRY_SCHEMA)
    assert document == before


# ---------------------------------------------------------------------------
# Collector registry
# ---------------------------------------------------------------------------


def test_collector_registry_sample_passes():
    result = validate_document(_load("collectors.json"), COLLECTOR_REGISTRY_SCHEMA)
    assert result.valid is True, result.errors


@pytest.mark.parametrize(
    "field",
    ["collector_id", "source_id", "adapter_id", "status", "capabilities"],
)
def test_collector_required_fields(field):
    """a.md §14: these five fields are the required minimum."""
    document = _load("collectors.json")
    del document["collectors"][0][field]
    result = validate_document(document, COLLECTOR_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any(field in str(entry) for entry in result.errors["collectors"])


def test_adapter_id_format_is_enforced():
    """P3-3: a malformed adapter_id is a structural failure."""
    document = _load("collectors.json")
    document["collectors"][0]["adapter_id"] = "bad adapter id!"
    result = validate_document(document, COLLECTOR_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any("adapter_id" in str(entry) for entry in result.errors["collectors"])


def test_adapter_id_accepts_version_suffix_and_plain_form():
    document = _load("collectors.json")
    assert document["collectors"][0]["adapter_id"] == "x-apify-example@1"
    document["collectors"][0]["adapter_id"] = "x-apify-example"
    assert validate_document(document, COLLECTOR_REGISTRY_SCHEMA).valid is True


def test_capability_values_are_three_valued():
    """a.md §7.2: unsupported / unknown must not be forced to supported."""
    assert CAPABILITY_VALUES == ["supported", "unsupported", "unknown"]
    document = _load("collectors.json")
    document["collectors"][0]["capabilities"]["pagination"] = "yes"
    result = validate_document(document, COLLECTOR_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any("pagination" in str(entry) for entry in result.errors["collectors"])


def test_collector_status_enum():
    assert COLLECTOR_STATUSES == [
        "active",
        "legacy",
        "deprecated",
        "unverified",
        "disabled",
    ]
    document = _load("collectors.json")
    document["collectors"][0]["status"] = "maybe"
    result = validate_document(document, COLLECTOR_REGISTRY_SCHEMA)
    assert result.valid is False


def test_verified_at_null_and_datetime_are_accepted():
    document = _load("collectors.json")
    assert validate_document(document, COLLECTOR_REGISTRY_SCHEMA).valid is True
    document["collectors"][0]["verified_at"] = "2026-10-13T00:00:00Z"
    assert validate_document(document, COLLECTOR_REGISTRY_SCHEMA).valid is True
    document["collectors"][0]["verified_at"] = "2026-10-13"
    assert validate_document(document, COLLECTOR_REGISTRY_SCHEMA).valid is False


def test_new_source_contract_structure():
    """a.md §15 item 1: a new source is described by registry data alone
    (here: a fictional source/collector pair validates structurally)."""
    document = {
        "schema_version": "1.0.0",
        "collectors": [
            {
                "collector_id": "test-social-example",
                "source_id": "test-social-platform",
                "adapter_id": "test-social-example@1",
                "status": "unverified",
                "capabilities": {"absolute_date_range": "unknown"},
            }
        ],
    }
    assert validate_document(document, COLLECTOR_REGISTRY_SCHEMA).valid is True
