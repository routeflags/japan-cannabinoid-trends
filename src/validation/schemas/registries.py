"""G1 source and collector registry schemas.

Contract sources
----------------
- G1 instruction §6 (Source Registry sample, ``config/sources.json``) and
  §7 (Collector Registry sample, ``config/collectors.json``):
  ``docs/plans/20261013a.md``.
- G1 §7.2 capability values (three-valued) and §7.3 collector statuses.
- G1 §14 minimum collector JSON Schema is *mapped* to Cerberus here; the JSON
  Schema file itself is never passed to Cerberus (rollout instruction §2).

Scope
-----
Structural validation only: required fields, types, enumerations (capability
values, collector status) and unknown-field rejection.  Not covered here:

- registry *references* from run metadata (source_id / collector_id
  existence) -> ``validation.semantic.check_registry_references`` (Phase 4);
- collector status used for collection eligibility (``active`` only) ->
  capability gate in ``validation.semantic`` (Phase 4 / Phase 6);
- capability semantics beyond the three-valued vocabulary -> adapter contract
  work (G1 §8, separate development line).

Interpretations recorded for review
-----------------------------------
- ``adapter_id`` format is not defined explicitly in a.md §5/§7 beyond the
  sample ``x-apify-example@1``.  This schema requires ``^[A-Za-z0-9]`` start,
  alphanumerics plus ``. _ -`` and an optional ``@<digits>`` version suffix.
- ``kind`` is required (sample shows it for every source) but its vocabulary
  is not enumerated in the contract, so it stays a free non-empty string.
- ``measurement_types`` / ``publication_review_required`` are optional because
  a.md §6.1 shows them on every sample row without stating a required list.
"""

from __future__ import annotations

CAPABILITY_VALUES = ["supported", "unsupported", "unknown"]

COLLECTOR_STATUSES = [
    "active",
    "legacy",
    "deprecated",
    "unverified",
    "disabled",
]

ADAPTER_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]*(@[0-9]+)?$"

_SOURCE_ITEM = {
    "source_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "kind": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "measurement_types": {
        "type": "list",
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "publication_review_required": {
        "type": "boolean",
    },
}

SOURCE_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "sources": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _SOURCE_ITEM,
        },
    },
}

_COLLECTOR_ITEM = {
    "collector_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "source_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "adapter_id": {
        "type": "string",
        "required": True,
        "empty": False,
        "regex": ADAPTER_ID_PATTERN,
    },
    "status": {
        "type": "string",
        "required": True,
        "allowed": COLLECTOR_STATUSES,
    },
    "capabilities": {
        "type": "dict",
        "required": True,
        "valuesrules": {
            "type": "string",
            "allowed": CAPABILITY_VALUES,
        },
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
    "verified_at": {
        "type": "string",
        "nullable": True,
        "iso_datetime": True,
    },
    "evidence": {
        "type": "list",
    },
}

COLLECTOR_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "collectors": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _COLLECTOR_ITEM,
        },
    },
}
