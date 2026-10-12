"""Schema Registry resolving stable schema IDs to schema documents.

Contract (docs/plans/20261013h.md §9):

- Every schema is addressable by a stable string ID (``collection-run-v1``;
  G1-G7 schemas will be added in Phase 3).
- Registering a new schema requires a matching Contract Test (§16).
- Unknown IDs raise ``ValueError`` so that CLI/config errors can be mapped to
  exit code 2 (schema / configuration error) in a later phase.
"""

from __future__ import annotations

from validation.schemas.collection_run import COLLECTION_RUN_SCHEMA

SCHEMA_REGISTRY: dict[str, dict] = {
    "collection-run-v1": COLLECTION_RUN_SCHEMA,
}


def get_schema(schema_id: str) -> dict:
    """Return the schema document registered under ``schema_id``.

    Raises ``ValueError`` for unknown IDs; the registry never falls back to
    a default schema.
    """
    try:
        return SCHEMA_REGISTRY[schema_id]
    except KeyError:
        raise ValueError(f"Unknown schema: {schema_id}") from None


def list_schema_ids() -> list[str]:
    """Return the registered schema IDs in sorted order."""
    return sorted(SCHEMA_REGISTRY)
