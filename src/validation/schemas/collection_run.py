"""G5 run metadata schema (collection run provenance contract).

Contract sources
----------------
- G5 instruction §4.2 (new-run ``run_metadata.json`` sample) and §13 (JSON
  Schema): ``docs/plans/20261013e.md``.
- G1 instruction §10 (Run Metadata Contract) and §11 (L1 integrity items):
  ``docs/plans/20261013a.md``.
- Cerberus rollout instruction §7 (initial structural example):
  ``docs/plans/20261013h.md``.

Scope
-----
Structural validation only (Cerberus scope, rollout instruction §2):
required fields, types, ranges, allowed values, nested structures and
unknown-field rejection.

Explicitly *not* covered here (separate validators later):
- datetime ordering (``collection_started_at`` < ``collection_finished_at``,
  requested window start < end) -> Temporal / Semantic Validator;
- ``compound_id`` / ``query_id`` / ``source_id`` existence in registries ->
  Registry Validator;
- artifact manifest existence, SHA-256 match, lineage -> Integrity / Lineage
  Validator;
- secret leakage in recorded parameters -> Semantic Validator (§8.2 P16).

Deviation from rollout instruction §8
-------------------------------------
The §8 example document contains no ``temporal_provenance`` and expects
``True``. That example belongs to the initial schema of §7; the G5 contract
(20261013e.md §4.2 / §13 and §8.3) requires temporal provenance, so it is
required here. A contract test documents this intentional divergence.

Extensible areas
----------------
``environment`` and ``temporal_provenance.submitted_parameters`` carry
runtime/collector-specific detail and intentionally allow unknown keys. All
other objects are strict.
"""

from __future__ import annotations

GRANULARITIES = ["hour", "day", "week", "month"]

COLLECTOR_WINDOW_TYPES = [
    "absolute_datetime",
    "absolute_date",
    "relative_duration",
    "calendar_period",
    "unbounded",
    "unsupported",
]

EXECUTION_STATUSES = ["running", "success", "partial", "failed"]

COLLECTION_RUN_SCHEMA = {
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
    "study_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "source_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "purpose": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "collector": {
        "type": "dict",
        "required": True,
        "schema": {
            "collector_id": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "adapter_id": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "provider": {
                "type": "string",
            },
            "transport": {
                "type": "string",
            },
            "external_id": {
                "type": "string",
            },
            "version": {
                "type": "string",
            },
        },
    },
    "collection_started_at": {
        "type": "string",
        "required": True,
        "empty": False,
        "iso_datetime": True,
    },
    "collection_finished_at": {
        "type": "string",
        "empty": False,
        "iso_datetime": True,
    },
    "query_provenance": {
        "type": "dict",
        "required": True,
        "schema": {
            "query_id": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "submitted_query": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "compound_id": {
                "type": "string",
            },
            "intent_id": {
                "type": "string",
            },
            "query_registry_version": {
                "type": "string",
            },
        },
    },
    "temporal_provenance": {
        "type": "dict",
        "required": True,
        "schema": {
            "window_id": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "requested_start": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
            "requested_end_exclusive": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
            "granularity": {
                "type": "string",
                "required": True,
                "allowed": GRANULARITIES,
            },
            "timezone": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "collector_window_type": {
                "type": "string",
                "allowed": COLLECTOR_WINDOW_TYPES,
            },
            # Collector-specific request parameters (non-secret only). This
            # is a documented extension area.
            "submitted_parameters": {
                "type": "dict",
                "allow_unknown": True,
            },
            "boundary_semantics": {
                "type": "string",
            },
            "exact_window_match": {
                "type": "boolean",
            },
            "observed_min_timestamp": {
                "type": "string",
                "nullable": True,
                "iso_datetime": True,
            },
            "observed_max_timestamp": {
                "type": "string",
                "nullable": True,
                "iso_datetime": True,
            },
            "temporal_contract_version": {
                "type": "string",
            },
            "calendar": {
                "type": "string",
            },
            "week_start": {
                "type": "string",
                "nullable": True,
            },
        },
    },
    "execution": {
        "type": "dict",
        "required": True,
        "schema": {
            "status": {
                "type": "string",
                "required": True,
                "allowed": EXECUTION_STATUSES,
            },
            "returned_count": {
                "type": "integer",
                "required": True,
                "min": 0,
            },
            "errors": {
                "type": "list",
                "required": True,
            },
            "pagination_exhausted": {
                "type": "boolean",
            },
        },
    },
    "artifact_manifest": {
        "type": "string",
        "empty": False,
    },
    # Runtime fingerprint. This is a documented extension area so that future
    # evidence references and environment fields can be recorded without a
    # schema bump.
    "environment": {
        "type": "dict",
        "allow_unknown": True,
        "schema": {
            "code_commit": {
                "type": "string",
            },
            "runtime_version": {
                "type": "string",
            },
        },
    },
}
