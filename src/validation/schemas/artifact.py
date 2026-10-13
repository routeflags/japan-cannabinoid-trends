"""G4 artifact manifest schema.

Contract sources
----------------
- G4 instruction §4.1 (artifact types), §4.2 (storage formats), §6.1
  (manifest sample) and §6.2 (required fields): ``docs/plans/20261013d.md``.
- G4 §11 (paginated collections: ``artifact_groups``), §12
  (``contains_full_timeseries``), §13 (SQLite lineage block) and §15
  (lineage: derived artifacts reference source artifacts).

Scope
-----
Structural validation only.  Not covered here:

- file existence, byte length, SHA-256 recomputation ->
  ``validation.integrity`` (Phase 4);
- lineage resolution (``derived_from`` targets exist) ->
  ``validation.integrity.check_manifest_lineage`` (Phase 4);
- content / format / reader consistency, record-count semantics, pagination
  completeness and SQLite lineage requirements ->
  ``validation.storage_contract`` (G4 vertical slice).

Interpretations recorded for review
-----------------------------------
- ``artifact_type`` uses the initial ten-value set of d.md §4.1.  The
  contract calls it preliminary ("実際の既存ファイルを調査し、重複や不足があれば
  整理する"); extensions are schema changes under §19.
- ``completeness`` uses ``complete`` / ``partial`` / ``missing`` / ``unknown``
  (d.md G4-T09/T10, AGENTS.md missing-data vocabulary).
- ``derived_from`` / ``transformation`` are optional: they are required for
  derived artifacts only, which the semantic layer will enforce when it knows
  the artifact layer semantics; the structural rule here is shape only.
- ``sha256`` is validated as 64 lowercase hex characters (d.md example uses
  lowercase); uppercase digests fail and must be normalized by the producer.
- G4 vertical-slice additions (backward compatible; existing manifests stay
  valid and the contract version stays 1.0.0, following the G2/G3 precedent):

  - ``contains_full_timeseries``: d.md §12 distinguishes a summary from a
    full timeseries.  A summary must never claim ``true`` (checked
    semantically by ``validation.storage_contract``); structural only here.
  - ``page_index`` / ``artifact_group_id``: d.md §11 page members.
  - ``database``: d.md §13 lineage block (tables + source run/artifact ids +
    dedup rule + transformation version).  Shape only; the semantic layer
    requires the block for ``artifact_type: database``.
  - ``artifact_groups``: d.md §11 group record (``expected_pages`` may be
    null - the total is unknown; ``pagination_exhausted: false`` forbids a
    ``complete`` claim, checked semantically).
"""

from __future__ import annotations

ARTIFACT_LAYERS = ["raw", "interim", "processed"]

ARTIFACT_TYPES = [
    "raw_response",
    "raw_records",
    "timeseries",
    "summary",
    "comparison",
    "page",
    "checkpoint",
    "database",
    "normalized_records",
    "aggregate",
]

ARTIFACT_FORMATS = [
    "json",
    "jsonl",
    "csv",
    "sqlite",
    "parquet",
    "text",
    "binary",
    "other",
]

COMPLETENESS_VALUES = ["complete", "partial", "missing", "unknown"]

SHA256_PATTERN = r"^[0-9a-f]{64}$"

#: d.md §11 group types (``paginated_collection`` is the documented value;
#: the field stays a free string so future group kinds need no schema change).
ARTIFACT_GROUP_TYPES = ["paginated_collection"]

_DATABASE_TABLE_ITEM = {
    "table_name": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "record_count": {
        "type": "integer",
        "min": 0,
    },
    "source_run_ids": {
        "type": "list",
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "source_artifact_ids": {
        "type": "list",
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "deduplication_rule": {
        "type": "string",
    },
    "transformation_version": {
        "type": "string",
    },
}

_DATABASE_BLOCK = {
    "db_schema_version": {
        "type": "string",
        "empty": False,
    },
    "tables": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "dict",
            "schema": _DATABASE_TABLE_ITEM,
        },
    },
}

_ARTIFACT_GROUP_ITEM = {
    "artifact_group_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "group_type": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "expected_pages": {
        "type": "integer",
        "nullable": True,
        "min": 0,
    },
    "collected_pages": {
        "type": "integer",
        "required": True,
        "min": 0,
    },
    "pagination_exhausted": {
        "type": "boolean",
        "required": True,
    },
    "completeness": {
        "type": "string",
        "allowed": COMPLETENESS_VALUES,
    },
    "artifacts": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "artifact_id": {
                    "type": "string",
                    "required": True,
                    "empty": False,
                },
                "page_index": {
                    "type": "integer",
                    "required": True,
                    "min": 1,
                },
                "path": {
                    "type": "string",
                    "empty": False,
                },
            },
        },
    },
}

_ARTIFACT_ITEM = {
    "artifact_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "path": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "artifact_type": {
        "type": "string",
        "required": True,
        "allowed": ARTIFACT_TYPES,
    },
    "format": {
        "type": "string",
        "required": True,
        "allowed": ARTIFACT_FORMATS,
    },
    "schema_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "byte_length": {
        "type": "integer",
        "required": True,
        "min": 0,
    },
    "sha256": {
        "type": "string",
        "required": True,
        "regex": SHA256_PATTERN,
    },
    "layer": {
        "type": "string",
        "required": True,
        "allowed": ARTIFACT_LAYERS,
    },
    "completeness": {
        "type": "string",
        "required": True,
        "allowed": COMPLETENESS_VALUES,
    },
    "media_type": {
        "type": "string",
    },
    "record_count": {
        "type": "integer",
        "min": 0,
    },
    "contains_full_timeseries": {
        "type": "boolean",
    },
    "page_index": {
        "type": "integer",
        "min": 1,
    },
    "artifact_group_id": {
        "type": "string",
        "empty": False,
    },
    "database": {
        "type": "dict",
        "schema": _DATABASE_BLOCK,
    },
    "derived_from": {
        "type": "list",
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "transformation": {
        "type": "dict",
        "schema": {
            "name": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "version": {
                "type": "string",
                "required": True,
                "empty": False,
            },
        },
    },
}

ARTIFACT_MANIFEST_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "run_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "artifacts": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _ARTIFACT_ITEM,
        },
    },
    "artifact_groups": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": _ARTIFACT_GROUP_ITEM,
        },
    },
}
