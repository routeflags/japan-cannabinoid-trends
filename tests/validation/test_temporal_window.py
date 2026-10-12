"""Contract tests for the G3 temporal window schema (P3-5).

Structural scope only: ordering / timezone / week_start consistency live in
tests/validation/test_semantic.py (P4-1).
"""

import json
from pathlib import Path

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.schemas.temporal import TEMPORAL_WINDOW_SCHEMA

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "temporal_window.json"


def _load() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_g3_schema_is_registered_under_its_id():
    assert get_schema("temporal-window-v1") is TEMPORAL_WINDOW_SCHEMA


def test_temporal_window_sample_passes():
    """c.md §4.1 sample (calendar / temporal_contract_version included)."""
    result = validate_document(_load(), TEMPORAL_WINDOW_SCHEMA)
    assert result.valid is True, result.errors


def test_required_fields():
    for field in ("window_id", "timezone", "start", "end_exclusive", "granularity"):
        document = _load()
        del document[field]
        assert not validate_document(document, TEMPORAL_WINDOW_SCHEMA).valid, field


def test_granularity_enum():
    document = _load()
    document["granularity"] = "fortnight"
    assert not validate_document(document, TEMPORAL_WINDOW_SCHEMA).valid


def test_datetime_fields_require_timezone():
    document = _load()
    document["start"] = "2026-09-01T00:00:00"  # naive
    result = validate_document(document, TEMPORAL_WINDOW_SCHEMA)
    assert result.valid is False
    assert result.errors["start"]


def test_week_start_nullable():
    document = _load()
    assert document["week_start"] is None
    assert validate_document(document, TEMPORAL_WINDOW_SCHEMA).valid is True
    document["week_start"] = "monday"
    assert validate_document(document, TEMPORAL_WINDOW_SCHEMA).valid is True


def test_schema_does_not_include_ordering_or_timezone_validity():
    """The semantic layer owns these checks (c.md §13 last paragraph); the
    structure must stay innocent of them so the two layers stay separate."""
    document = _load()
    document["start"] = "2026-10-01T00:00:00+09:00"
    document["end_exclusive"] = "2026-09-01T00:00:00+09:00"  # reversed
    document["timezone"] = "Not/AZone"
    assert validate_document(document, TEMPORAL_WINDOW_SCHEMA).valid is True


def test_unknown_window_field_fails():
    document = _load()
    document["submitted_parameters"] = {"timeSince": "2026-09-01"}
    result = validate_document(document, TEMPORAL_WINDOW_SCHEMA)
    assert result.valid is False
    assert result.errors.get("submitted_parameters") == ["unknown field"]
