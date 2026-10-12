"""G3 temporal window schema and shared temporal constants.

Contract sources
----------------
- G3 instruction §4 (Temporal Contract: fields and required list) and §13
  (``schemas/temporal-window.schema.json``): ``docs/plans/20261013c.md``.

Scope
-----
Structural validation only: required fields, types, allowed values and
unknown-field rejection for a standalone window document. Everything the G3
contract places in the Semantic Validator (c.md §13) is intentionally *not*
here:

- ``start`` must be earlier than ``end_exclusive`` -> ``validation.semantic``;
- timezone validity -> ``validation.semantic``;
- ``granularity`` / ``week_start`` consistency -> ``validation.semantic``;
- coverage, bucket generation, missingness -> later phases.

Role separation between this schema and ``temporal_provenance``
----------------------------------------------------------------
``temporal-window-v1`` validates a *standalone* window document (G3 §4.1
shape: ``window_id`` / ``start`` / ``end_exclusive`` / ...).  A collection
run embeds the resolved window inside ``run_metadata.json`` as
``temporal_provenance`` (G5, ``collection-run-v1``).  The two structures
describe the same concept at different layers and are validated by their own
schemas; the semantic checks in ``validation.semantic`` accept both shapes.

Documented divergence from the c.md example
-------------------------------------------
``c.md`` §4.2 lists ``calendar`` and ``temporal_contract_version`` among the
required fields, while the §13 JSON Schema omits them (and sets
``additionalProperties: false``).  This schema follows the §13 required list
(``window_id`` / ``timezone`` / ``start`` / ``end_exclusive`` /
``granularity``) and accepts ``calendar``, ``week_start`` and
``temporal_contract_version`` as optional fields, so that the §4.1 sample
validates in full.  The inconsistency is recorded in the rollout plan; the
strict semantic rule "week granularity requires week_start" lives in
``validation.semantic``.
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

TEMPORAL_WINDOW_SCHEMA = {
    "window_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "timezone": {
        "type": "string",
        "required": True,
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
        "required": True,
        "allowed": GRANULARITIES,
    },
    "calendar": {
        "type": "string",
    },
    "week_start": {
        "type": "string",
        "nullable": True,
    },
    "temporal_contract_version": {
        "type": "string",
    },
}
