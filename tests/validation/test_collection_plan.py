"""Structural tests for the collection plan schema (P6-1 input contract)."""

import json
from pathlib import Path

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.collection_plan import COLLECTION_PLAN_SCHEMA

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "collection_plan.json"


def _load() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_collection_plan_schema_is_registered_under_its_id():
    assert get_schema("collection-plan-v1") is COLLECTION_PLAN_SCHEMA


def test_collection_plan_sample_passes():
    result = validate_document(_load(), COLLECTION_PLAN_SCHEMA)
    assert result.valid is True, result.errors


def test_plan_requires_source_query_and_capabilities():
    for field in ("source_id", "query_id", "required_capabilities"):
        document = _load()
        del document[field]
        assert not validate_document(document, COLLECTION_PLAN_SCHEMA).valid, field


def test_plan_window_requires_iso_datetimes():
    document = _load()
    document["window"]["start"] = "2026-09-01"
    assert not validate_document(document, COLLECTION_PLAN_SCHEMA).valid


def test_plan_window_is_optional():
    document = _load()
    del document["window"]
    assert validate_document(document, COLLECTION_PLAN_SCHEMA).valid is True


def test_plan_rejects_unknown_fields():
    document = _load()
    document["api_key"] = "must-not-be-stored"
    result = validate_document(document, COLLECTION_PLAN_SCHEMA)
    assert result.valid is False
    assert result.errors.get("api_key") == ["unknown field"]
