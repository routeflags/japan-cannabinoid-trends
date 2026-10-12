"""Contract tests for the G5 transformation provenance schema (P3-7).

Covers e.md §6 sample, the required list from rollout plan P3-7, and G5-T17's
structural part (input/output id lists must exist and be non-empty).
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.provenance import TRANSFORMATION_SCHEMA, TRANSFORMATION_STATUSES

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "transformation.json"


def _load() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_g5_transformation_schema_is_registered_under_its_id():
    assert get_schema("transformation-v1") is TRANSFORMATION_SCHEMA


def test_transformation_sample_passes():
    result = validate_document(_load(), TRANSFORMATION_SCHEMA)
    assert result.valid is True, result.errors


@pytest.mark.parametrize(
    "field",
    [
        "transformation_id",
        "executed_at",
        "status",
        "input_artifact_ids",
        "output_artifact_ids",
    ],
)
def test_required_fields(field):
    """P3-7: these five fields are required."""
    document = _load()
    del document[field]
    result = validate_document(document, TRANSFORMATION_SCHEMA)
    assert result.valid is False
    assert field in result.errors


def test_input_and_output_lists_must_not_be_empty():
    for field in ("input_artifact_ids", "output_artifact_ids"):
        document = _load()
        document[field] = []
        assert not validate_document(document, TRANSFORMATION_SCHEMA).valid, field


def test_executed_at_requires_timezone():
    document = _load()
    document["executed_at"] = "2026-10-13T01:00:00"
    assert not validate_document(document, TRANSFORMATION_SCHEMA).valid


def test_status_enum():
    assert TRANSFORMATION_STATUSES == ["success", "partial", "failed"]
    document = _load()
    document["status"] = "done"
    assert not validate_document(document, TRANSFORMATION_SCHEMA).valid


def test_parameters_is_an_extension_area():
    document = _load()
    document["parameters"]["collector_specific"] = {"nested": True}
    assert validate_document(document, TRANSFORMATION_SCHEMA).valid is True


def test_transformation_rejects_unknown_top_level_field():
    document = _load()
    document["raw_artifact_overwrite"] = True
    result = validate_document(document, TRANSFORMATION_SCHEMA)
    assert result.valid is False
    assert result.errors.get("raw_artifact_overwrite") == ["unknown field"]


def test_transformation_does_not_mutate():
    document = _load()
    before = deepcopy(document)
    validate_document(document, TRANSFORMATION_SCHEMA)
    assert document == before
