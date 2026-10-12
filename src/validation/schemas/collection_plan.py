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

G1 alignment (2026-10-13, collection core): ``query`` (adapter-specific
request parameters; extension area like ``temporal_provenance.
submitted_parameters``) and ``window.granularity`` / ``window.timezone`` /
``window.window_id`` were added as *optional* fields so that a plan carries
everything the adapter and the run-provenance builder need.  Adding optional
fields keeps every previous plan document valid (P6 backward compatibility);
the schema ID and contract version are unchanged.

Scope: structural only.  Registration, collector status (``active`` only),
capability support and temporal ordering are semantic checks in
``validation.semantic`` / ``validation.gates``.
"""

from __future__ import annotations

from validation.schemas.temporal import GRANULARITIES

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
    # Adapter-specific request parameters (non-secret only). This is a
    # documented extension area: the core is source-agnostic and must not
    # hard-code vendor parameter names.
    "query": {
        "type": "dict",
        "allow_unknown": True,
        "schema": {
            "text": {
                "type": "string",
                "empty": False,
            },
            "geo": {
                "type": "string",
            },
            "timeframe": {
                "type": "string",
            },
            "compound_id": {
                "type": "string",
            },
            "language": {
                "type": "string",
            },
        },
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
            "window_id": {
                "type": "string",
                "empty": False,
            },
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
            "granularity": {
                "type": "string",
                "allowed": GRANULARITIES,
            },
            "week_start": {
                "type": "string",
            },
            "timezone": {
                "type": "string",
                "empty": False,
            },
            # G3: a study may require an exact absolute window.  When true,
            # a collector whose compiled window is inexact (e.g. rolling
            # relative timeframes with unverified boundaries) must not run
            # (c.md §6.2 "exact=false の状態では、厳密な期間指定が必要な収集を
            # 実行しない").  Optional and untouched by previous documents.
            "exact_required": {
                "type": "boolean",
            },
        },
    },
    "purpose": {
        "type": "string",
    },
}
