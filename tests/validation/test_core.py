"""Contract tests for the common validator interface (validation.core).

Covers the rollout instruction §16 items that belong to the Phase 2 scope:
CV-02 (type mismatch), CV-03 (unknown fields), CV-07 (invalid datetime,
structural part) and CV-19 (no implicit value changes).
"""

from copy import deepcopy

import pytest

from validation.core import (
    ResearchValidator,
    ValidationResult,
    validate_document,
)

ISO_SCHEMA = {
    "started_at": {
        "type": "string",
        "required": True,
        "empty": False,
        "iso_datetime": True,
    },
}


def test_iso_datetime_accepts_utc_and_offset_formats():
    """CV-07 (negative): valid ISO 8601 datetimes pass structural checks."""
    validator = ResearchValidator(ISO_SCHEMA)
    assert validator.validate({"started_at": "2026-10-13T00:00:00Z"})
    assert validator.validate({"started_at": "2026-10-13T09:00:00+09:00"})


def test_iso_datetime_rejects_naive_datetime():
    """CV-07: a datetime without timezone must fail."""
    validator = ResearchValidator(ISO_SCHEMA)
    assert not validator.validate({"started_at": "2026-10-13T00:00:00"})
    assert "Timezone is required" in validator.errors["started_at"]


def test_iso_datetime_rejects_invalid_datetime():
    """CV-07: unparsable / impossible datetimes must fail."""
    for bad in ("2026-13-45T99:00:00Z", "not-a-date"):
        validator = ResearchValidator(ISO_SCHEMA)
        assert not validator.validate({"started_at": bad}), bad
        assert "Invalid ISO datetime" in validator.errors["started_at"], bad


def test_iso_datetime_rejects_date_only_value():
    """CV-07: a date-only value parses as naive midnight, so it is rejected
    for the same reason as any other value without a timezone."""
    validator = ResearchValidator(ISO_SCHEMA)
    assert not validator.validate({"started_at": "2026-10-13"})
    assert "Timezone is required" in validator.errors["started_at"]


def test_iso_datetime_rule_can_be_disabled():
    """The iso_datetime rule itself is opt-in via the schema."""
    validator = ResearchValidator(
        {"note": {"type": "string", "iso_datetime": False}}
    )
    assert validator.validate({"note": "not-a-date"})


def test_iso_datetime_allows_null_for_nullable_fields():
    """Nullable timestamps such as observed_min_timestamp may be null."""
    validator = ResearchValidator(
        {
            "observed_min_timestamp": {
                "type": "string",
                "nullable": True,
                "iso_datetime": True,
            }
        }
    )
    assert validator.validate({"observed_min_timestamp": None})


def test_validate_document_returns_validation_result():
    """The shared interface returns a ValidationResult, not a raw Validator."""
    result = validate_document({"started_at": "2026-10-13T00:00:00Z"}, ISO_SCHEMA)
    assert isinstance(result, ValidationResult)
    assert result.valid is True
    assert result.errors == {}


def test_validate_document_rejects_missing_required_field():
    """CV-01: a missing required field must fail."""
    result = validate_document({}, ISO_SCHEMA)
    assert result.valid is False
    assert result.errors == {"started_at": ["required field"]}


def test_validate_document_rejects_type_mismatch():
    """CV-02: wrong types must fail, and ``normalize=False`` must prevent
    coercion (a numeric-looking string must not become an integer)."""
    schema = {"count": {"type": "integer", "required": True}}
    result = validate_document({"count": "100"}, schema)
    assert result.valid is False
    assert result.errors == {"count": ["must be of integer type"]}


def test_validate_document_rejects_unknown_field():
    """CV-03: unknown fields must fail (``allow_unknown=False``)."""
    result = validate_document(
        {"started_at": "2026-10-13T00:00:00Z", "unexpected": 1}, ISO_SCHEMA
    )
    assert result.valid is False
    assert result.errors == {"unexpected": ["unknown field"]}


def test_validate_document_does_not_mutate_document():
    """CV-19: validation must not modify the validated document, even when it
    fails (``purge_unknown=False`` forbids removing unknown fields)."""
    document = {"started_at": "2026-10-13T00:00:00", "unexpected": {"a": 1}}
    before = deepcopy(document)

    result = validate_document(document, ISO_SCHEMA)

    assert result.valid is False
    assert document == before
    assert "unexpected" in document


def test_validate_document_is_pure_for_valid_documents():
    """CV-19: repeated validation of a valid document yields identical results
    and leaves the document byte-identical."""
    document = {"started_at": "2026-10-13T00:00:00Z"}
    before = deepcopy(document)

    first = validate_document(document, ISO_SCHEMA)
    second = validate_document(document, ISO_SCHEMA)

    assert first == second == ValidationResult(valid=True, errors={})
    assert document == before


@pytest.mark.parametrize("value", [None, ""], ids=["null", "empty-string"])
def test_empty_false_rejects_null_and_empty(value):
    """CV-01: ``empty: False`` rejects null and empty strings alike."""
    result = validate_document({"started_at": value}, ISO_SCHEMA)
    assert result.valid is False


@pytest.mark.parametrize(
    "document", [[1, 2, 3], "text", 7, None], ids=["list", "string", "int", "null"]
)
def test_non_mapping_document_is_a_validation_failure(document):
    """A document that is not a mapping fails validation instead of raising.

    Cerberus raises ``DocumentError`` for these inputs, which used to crash
    every caller that reads a file before validating it.
    """
    result = validate_document(document, ISO_SCHEMA)

    assert result.valid is False
    assert result.errors == {"": ["document is not a JSON object"]}
