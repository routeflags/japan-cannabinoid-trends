"""Contract tests for the running-run profile (P3-1).

Verifies that ``collection-run-v1-running``

- accepts a running document without ``collection_finished_at``;
- refuses a document that carries ``collection_finished_at`` (bypass
  detection: a finished run cannot be re-labelled as running);
- keeps the finalized profile behaviour untouched.
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.schemas.collection_run import (
    COLLECTION_RUN_RUNNING_SCHEMA,
    COLLECTION_RUN_SCHEMA,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "collection_run_valid.json"


def _running_document() -> dict:
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    document.pop("collection_finished_at", None)
    document["execution"]["status"] = "running"
    return document


def test_running_document_passes_running_profile():
    result = validate_document(_running_document(), COLLECTION_RUN_RUNNING_SCHEMA)
    assert result.valid is True, result.errors


def test_running_profile_detects_finished_at_bypass():
    """A finished run must not validate under the running profile."""
    document = _running_document()
    document["collection_finished_at"] = "2026-10-13T00:03:00Z"

    result = validate_document(document, COLLECTION_RUN_RUNNING_SCHEMA)

    assert result.valid is False
    assert result.errors.get("collection_finished_at") == ["unknown field"]


@pytest.mark.parametrize("status", ["success", "partial", "failed"])
def test_running_profile_refuses_terminal_status(status):
    document = _running_document()
    document["execution"]["status"] = status

    result = validate_document(document, COLLECTION_RUN_RUNNING_SCHEMA)

    assert result.valid is False
    nested = result.errors["execution"]
    assert any("status" in entry for entry in nested), nested


def test_finalized_profile_still_accepts_running_status():
    """The finalized schema keeps the full G5 §7 enum; the running-only
    restriction is a property of the running profile."""
    result = validate_document(_running_document(), COLLECTION_RUN_SCHEMA)
    assert result.valid is True, result.errors


def test_running_profile_inherits_finalized_required_fields():
    document = _running_document()
    del document["query_provenance"]

    result = validate_document(document, COLLECTION_RUN_RUNNING_SCHEMA)

    assert result.valid is False
    assert result.errors.get("query_provenance") == ["required field"]


def test_running_profile_is_derived_not_key_modified():
    """The running profile must not mutate the finalized schema."""
    assert "collection_finished_at" in COLLECTION_RUN_SCHEMA
    assert COLLECTION_RUN_SCHEMA["execution"]["schema"]["status"]["allowed"] == [
        "running",
        "success",
        "partial",
        "failed",
    ]
    # and the running schema is a distinct object
    assert COLLECTION_RUN_RUNNING_SCHEMA is not COLLECTION_RUN_SCHEMA
    assert COLLECTION_RUN_RUNNING_SCHEMA != COLLECTION_RUN_SCHEMA


def test_running_profile_rejects_unknown_top_level_fields():
    document = _running_document()
    document["legacy_field"] = 1

    result = validate_document(document, COLLECTION_RUN_RUNNING_SCHEMA)

    assert result.valid is False
    assert result.errors.get("legacy_field") == ["unknown field"]


def test_running_document_is_not_mutated_by_validation():
    document = _running_document()
    before = deepcopy(document)
    validate_document(document, COLLECTION_RUN_RUNNING_SCHEMA)
    assert document == before
