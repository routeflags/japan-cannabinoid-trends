"""G4 artifact manifest schema.

Contract sources
----------------
- G4 instruction §4.1 (artifact types), §4.2 (storage formats), §6.1
  (manifest sample) and §6.2 (required fields): ``docs/plans/20261013d.md``.
- G4 §15 (lineage: derived artifacts reference source artifacts).

Scope
-----
Structural validation only.  Not covered here:

- file existence, byte length and SHA-256 recomputation ->
  ``validation.integrity`` (Phase 4);
- lineage resolution (``derived_from`` targets exist) ->
  ``validation.integrity.check_manifest_lineage`` (Phase 4);
- completeness / pagination semantics beyond the enum -> G4 §11 (future).

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
}
