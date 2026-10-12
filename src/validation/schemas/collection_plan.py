"""Collection plan schema (pre-collection gate input, Phase 6 / P6-1).

Contract sources
----------------
- The validation pipeline of the rollout instruction §12 starts at
  "Collection Plan"; G1 §9 (Capability Gate) defines what must be checked
  before a collection starts.

This is an *initial* contract introduced for the pre-collection gate: it
covers the fields the gate consumes (source / collector / query / required
capabilities / requested window).  The full Collection Plan shape belongs to
the G1 adapter contract (separate development line) and must be aligned when
that lands; until then this schema is the machine-checkable minimum and is
documented as such in ``docs/specs/validation-framework.md``.

Scope: structural only.  Registration, collector status (``active`` only),
capability support and temporal ordering are semantic checks in
``validation.semantic`` / ``validation.gates``.
"""

from __future__ import annotations

COLLECTION_PLAN_SCHEMA = {
    "plan_id": {
        "type": "string",
    },
    "study_id": {
        "type": "string",
    },
    "source_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "collector_id": {
        "type": "string",
    },
    "query_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "required_capabilities": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "window": {
        "type": "dict",
        "schema": {
            "start": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
            "end_exclusive": {
                "type": "string",
                "required": True,
                "empty": False,
                "iso_datetime": True,
            },
        },
    },
    "purpose": {
        "type": "string",
    },
}
