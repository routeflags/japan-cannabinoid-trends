"""G4 artifact registry schema (d.md §7).

Contract sources
----------------
- G4 instruction §7 (artifact registry sample) and §8 (reader contract):
  ``docs/plans/20261013d.md``.

Scope
-----
Structural validation only.  Not covered here:

- duplicate reader / schema ids, unknown ``reader_id`` references and
  "active but unimplemented" readers ->
  ``validation.storage_contract.check_artifact_registry``
  (``validate-registries`` runs it);
- actual reader behaviour -> ``storage.readers`` contract tests.

Interpretations recorded for review
-----------------------------------
- ``readers[]`` entries are the *code* side of the contract; ``status`` is
  ``active`` (implemented and usable) or ``planned`` (declared for a future
  format - never resolved for validation).
- ``artifact_schemas[]`` entries are the *data* side: a ``schema_id`` (the
  same id an artifact manifest declares) with the format / artifact types it
  covers, the reader that reads it, and - when the contract defines it - the
  record-count semantics (``record_count_mode``).
- ``record_count_mode`` values: ``none`` (no file-level count is defined -
  summary, database), ``array_length`` (top-level JSON array),
  ``items_length`` (page ``items`` array), ``data_points`` (per-bucket
  series entries), ``data_rows`` (comparison rows).  The mode is what the
  S8 check compares against; ``none`` means "never compared" (d.md §6.2:
  a summary's ``data_points`` is not a record count).
- ``contains_full_timeseries`` mirrors the d.md §12 distinction on the
  schema side; the manifest-side flag must not contradict it.
"""

from __future__ import annotations

from validation.schemas.artifact import ARTIFACT_FORMATS, ARTIFACT_TYPES

READER_STATUSES = ["active", "planned"]

#: d.md §6.2 / §10 S8: record-count semantics defined per schema.
RECORD_COUNT_MODES = [
    "none",
    "array_length",
    "items_length",
    "data_points",
    "data_rows",
]

_READER_ITEM = {
    "reader_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "reader_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "status": {
        "type": "string",
        "required": True,
        "allowed": READER_STATUSES,
    },
    "formats": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "allowed": ARTIFACT_FORMATS,
        },
    },
    "artifact_types": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "allowed": ARTIFACT_TYPES,
        },
    },
    "read_modes": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "contains_full_timeseries": {
        "type": "boolean",
    },
    "implemented_by": {
        "type": "string",
        "empty": False,
    },
}

_SCHEMA_ITEM = {
    "schema_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "format": {
        "type": "string",
        "required": True,
        "allowed": ARTIFACT_FORMATS,
    },
    "artifact_types": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "allowed": ARTIFACT_TYPES,
        },
    },
    "reader_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "record_count_mode": {
        "type": "string",
        "allowed": RECORD_COUNT_MODES,
    },
    "contains_full_timeseries": {
        "type": "boolean",
    },
}

ARTIFACT_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "readers": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _READER_ITEM,
        },
    },
    "artifact_schemas": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _SCHEMA_ITEM,
        },
    },
}
