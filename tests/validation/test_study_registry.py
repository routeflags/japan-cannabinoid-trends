"""Contract tests for the G7 study / measurement / research view schemas
(P3-9).

Covers g.md §4.2 / §6.2 / §10.1 samples.  Comparability semantics live in
tests/validation/test_comparability.py (P4-8).
"""

import json
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.study import (
    MEASUREMENT_AGGREGATIONS,
    MEASUREMENT_REGISTRY_SCHEMA,
    RESEARCH_VIEW_SCHEMA,
    STUDY_REGISTRY_SCHEMA,
)

FIXTURES = Path(__file__).parent / "fixtures"
REGISTRIES = FIXTURES / "registries"


def _load(name: str, base: Path = FIXTURES) -> dict:
    return json.loads((base / name).read_text(encoding="utf-8"))


def test_g7_schemas_are_registered_under_their_ids():
    assert get_schema("study-registry-v1") is STUDY_REGISTRY_SCHEMA
    assert get_schema("measurement-registry-v1") is MEASUREMENT_REGISTRY_SCHEMA
    assert get_schema("research-view-v1") is RESEARCH_VIEW_SCHEMA


def test_study_registry_sample_passes():
    result = validate_document(
        _load("study-registry.json", REGISTRIES), STUDY_REGISTRY_SCHEMA
    )
    assert result.valid is True, result.errors


def test_study_required_fields():
    for field in ("study_id", "title", "research_questions", "sources", "status"):
        document = _load("study-registry.json", REGISTRIES)
        del document["studies"][0][field]
        assert not validate_document(document, STUDY_REGISTRY_SCHEMA).valid, field


def test_study_rejects_unknown_field():
    document = _load("study-registry.json", REGISTRIES)
    document["studies"][0]["doi"] = "10.0000/example"
    result = validate_document(document, STUDY_REGISTRY_SCHEMA)
    assert result.valid is False
    assert any("doi" in str(entry) for entry in result.errors["studies"])


def test_study_registry_keeps_actual_ids_unchanged():
    """g.md §4.2: the sample IDs are illustrative; the repository's own IDs
    must pass structurally without being rewritten (P3-9 data example uses the
    existing study_id)."""
    document = _load("study-registry.json", REGISTRIES)
    assert document["studies"][0]["study_id"] == "cannabinoid-social-trends"
    assert validate_document(document, STUDY_REGISTRY_SCHEMA).valid is True


def test_measurement_registry_sample_passes():
    result = validate_document(
        _load("measurement-registry.json", REGISTRIES), MEASUREMENT_REGISTRY_SCHEMA
    )
    assert result.valid is True, result.errors


def test_measurement_required_fields():
    for field in (
        "measurement_id",
        "unit",
        "observation_entity",
        "aggregation",
        "normalization_required",
    ):
        document = _load("measurement-registry.json", REGISTRIES)
        del document["measurements"][0][field]
        assert not validate_document(document, MEASUREMENT_REGISTRY_SCHEMA).valid, field


def test_measurement_aggregation_enum():
    assert MEASUREMENT_AGGREGATIONS == ["count", "sum", "mean", "source_defined"]
    document = _load("measurement-registry.json", REGISTRIES)
    document["measurements"][0]["aggregation"] = "median"
    assert not validate_document(document, MEASUREMENT_REGISTRY_SCHEMA).valid


def test_normalization_required_is_boolean():
    document = _load("measurement-registry.json", REGISTRIES)
    document["measurements"][0]["normalization_required"] = "yes"
    assert not validate_document(document, MEASUREMENT_REGISTRY_SCHEMA).valid


def test_research_view_sample_passes():
    result = validate_document(_load("research_view.json"), RESEARCH_VIEW_SCHEMA)
    assert result.valid is True, result.errors


def test_research_view_required_fields():
    for field in (
        "view_id",
        "view_version",
        "compound_id",
        "granularity",
        "timezone",
        "sources",
        "measurements",
        "comparison_mode",
        "require_comparability_gate",
    ):
        document = _load("research_view.json")
        del document[field]
        assert not validate_document(document, RESEARCH_VIEW_SCHEMA).valid, field


def test_research_view_rejects_sum_mode():
    """g.md §10.1: parallel_timeseries must not sum measurements; a sum-like
    mode is not an allowed value."""
    document = _load("research_view.json")
    document["comparison_mode"] = "summed_index"
    assert not validate_document(document, RESEARCH_VIEW_SCHEMA).valid


def test_research_view_requires_non_empty_sources_and_measurements():
    document = _load("research_view.json")
    document["sources"] = []
    assert not validate_document(document, RESEARCH_VIEW_SCHEMA).valid
    document = _load("research_view.json")
    document["measurements"] = []
    assert not validate_document(document, RESEARCH_VIEW_SCHEMA).valid


def test_research_view_granularity_enum():
    document = _load("research_view.json")
    document["granularity"] = "quarter"
    assert not validate_document(document, RESEARCH_VIEW_SCHEMA).valid


def test_g7_schemas_do_not_mutate():
    for name, schema, base in (
        ("study-registry.json", STUDY_REGISTRY_SCHEMA, REGISTRIES),
        ("measurement-registry.json", MEASUREMENT_REGISTRY_SCHEMA, REGISTRIES),
        ("research_view.json", RESEARCH_VIEW_SCHEMA, FIXTURES),
    ):
        document = _load(name, base)
        before = json.loads(json.dumps(document))
        validate_document(document, schema)
        assert document == before, name
