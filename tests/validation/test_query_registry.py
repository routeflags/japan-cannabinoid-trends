"""Contract tests for the G2 query registry / variants schemas (P3-4).

Covers b.md §5.2/§5.3 samples, the §10 minimum schema constraints and the
intent vocabulary (initial list, b.md §2 P2).
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.query import (
    QUERY_INTENTS,
    QUERY_REGISTRY_SCHEMA,
    QUERY_STATUSES,
    QUERY_VARIANTS_SCHEMA,
)

FIXTURES = Path(__file__).parent / "fixtures" / "registries"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_g2_schemas_are_registered_under_their_ids():
    assert get_schema("query-registry-v1") is QUERY_REGISTRY_SCHEMA
    assert get_schema("query-variants-v1") is QUERY_VARIANTS_SCHEMA


def test_query_registry_sample_passes():
    result = validate_document(_load("queries.json"), QUERY_REGISTRY_SCHEMA)
    assert result.valid is True, result.errors


@pytest.mark.parametrize(
    "field",
    ["query_id", "compound_id", "intent_id", "language", "canonical_text", "status"],
)
def test_query_required_fields(field):
    """b.md §10: these six fields are required for one query definition."""
    document = _load("queries.json")
    del document["queries"][0][field]
    result = validate_document(document, QUERY_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any(field in str(entry) for entry in result.errors["queries"])


def test_intent_vocabulary_is_enforced():
    """P3-4: an invalid intent value fails structurally."""
    assert "compound_general" in QUERY_INTENTS
    document = _load("queries.json")
    document["queries"][0]["intent_id"] = "unknown_intent"
    result = validate_document(document, QUERY_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any("intent_id" in str(entry) for entry in result.errors["queries"])


def test_query_status_enum():
    assert QUERY_STATUSES == ["active", "deprecated", "experimental"]
    document = _load("queries.json")
    document["queries"][0]["status"] = "draft"
    assert not validate_document(document, QUERY_REGISTRY_SCHEMA).valid


def test_language_minimum_length():
    """b.md §10: minLength 2 for the language code."""
    document = _load("queries.json")
    document["queries"][0]["language"] = "j"
    assert not validate_document(document, QUERY_REGISTRY_SCHEMA).valid


def test_query_registry_rejects_unknown_item_field():
    document = _load("queries.json")
    document["queries"][0]["platform_syntax"] = "x-operator"
    result = validate_document(document, QUERY_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any("platform_syntax" in str(entry) for entry in result.errors["queries"])


def test_query_registry_does_not_mutate():
    document = _load("queries.json")
    before = deepcopy(document)
    validate_document(document, QUERY_REGISTRY_SCHEMA)
    assert document == before


def test_query_variants_sample_passes():
    """b.md §5.3 sample."""
    document = {
        "query_id": "cbd-liquid-ja",
        "variants": [
            {"variant_id": "cbd-liquid-space", "text": "CBD リキッド", "status": "primary"},
            {"variant_id": "cbd-liquid-nospace", "text": "CBDリキッド", "status": "alternative"},
        ],
    }
    result = validate_document(document, QUERY_VARIANTS_SCHEMA)
    assert result.valid is True, result.errors


def test_query_variants_require_shape():
    document = {"query_id": "cbd-liquid-ja", "variants": [{"variant_id": "v1"}]}
    result = validate_document(document, QUERY_VARIANTS_SCHEMA)
    assert result.valid is False
    assert any("text" in str(entry) for entry in result.errors["variants"])
    document = {"query_id": "cbd-liquid-ja", "variants": [{"variant_id": "v1", "text": "x", "status": "first"}]}
    assert not validate_document(document, QUERY_VARIANTS_SCHEMA).valid
