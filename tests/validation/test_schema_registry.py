"""Contract tests for the Schema Registry (rollout instruction §9 / §16).

Covers CV-04 (unregistered schema -> FAIL) and the registry invariants that
new schemas must satisfy.
"""

import pytest

from validation.schema_registry import (
    SCHEMA_REGISTRY,
    get_schema,
    list_schema_ids,
)
from validation.schemas.collection_run import COLLECTION_RUN_SCHEMA


# ---------------------------------------------------------------------------
# Normal cases
# ---------------------------------------------------------------------------


def test_collection_run_v1_resolves_to_the_g5_schema():
    assert get_schema("collection-run-v1") is COLLECTION_RUN_SCHEMA


def test_list_schema_ids_reports_registered_ids():
    assert "collection-run-v1" in list_schema_ids()
    assert list_schema_ids() == sorted(SCHEMA_REGISTRY)


def test_registered_schemas_are_nonempty_dicts():
    for schema_id in list_schema_ids():
        schema = get_schema(schema_id)
        assert isinstance(schema, dict)
        assert schema, f"schema {schema_id} must not be empty"


# ---------------------------------------------------------------------------
# CV-04: unregistered schema
# ---------------------------------------------------------------------------


def test_unknown_schema_raises_value_error():
    """CV-04: an unknown schema ID must be a schema/config error, not a
    validation failure of some default schema."""
    with pytest.raises(ValueError, match="^Unknown schema: no-such-schema$"):
        get_schema("no-such-schema")


def test_empty_schema_id_raises_value_error():
    with pytest.raises(ValueError):
        get_schema("")
