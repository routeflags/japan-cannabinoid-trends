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


# ---------------------------------------------------------------------------
# G1 adapter-contract alignment (optional fields added 2026-10-13)
# ---------------------------------------------------------------------------


def _extended_plan() -> dict:
    document = _load()
    document["query"] = {
        "text": "CBX リキッド",
        "geo": "JP",
        "timeframe": "today 12-m",
        "compound_id": "CBX",
    }
    document["window"].update(
        {
            "window_id": "2025-10-12_2026-10-12",
            "granularity": "week",
            "week_start": "sunday",
            "timezone": "Asia/Tokyo",
        }
    )
    return document


def test_plan_accepts_the_adapter_contract_fields():
    result = validate_document(_extended_plan(), COLLECTION_PLAN_SCHEMA)
    assert result.valid is True, result.errors


def test_plan_query_is_an_extension_area_for_adapter_parameters():
    """Adapter-specific request keys are allowed inside ``query`` (the core is
    source-agnostic), while the top level stays strict."""
    document = _extended_plan()
    document["query"]["section"] = "latest"
    assert validate_document(document, COLLECTION_PLAN_SCHEMA).valid is True
    document["section"] = "latest"
    assert validate_document(document, COLLECTION_PLAN_SCHEMA).valid is False


def test_plan_window_granularity_is_enum_checked():
    document = _extended_plan()
    document["window"]["granularity"] = "fortnight"
    assert validate_document(document, COLLECTION_PLAN_SCHEMA).valid is False


def test_plan_previous_documents_remain_valid():
    """P6 backward compatibility: adding optional fields did not change the
    verdict for documents written against the initial contract."""
    assert validate_document(_load(), COLLECTION_PLAN_SCHEMA).valid is True
