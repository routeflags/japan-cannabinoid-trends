"""G2 query registry and query variant schemas.

Contract sources
----------------
- G2 instruction §5.2 (``query-registry.json`` sample), §5.3 (query variant
  sample) and §10 (minimum JSON Schema for one query definition):
  ``docs/plans/20261013b.md``.

Scope
-----
Structural validation only.  Not covered here:

- compound / intent / variant registry *references* -> Semantic Validator
  (Phase 3/4 tests combine structure and reference checks);
- query uniqueness (G2-T02 duplicate query_id) -> reference-level check;
- platform compiler syntax -> ``src/collection/query`` (G2 §6, separate
  development line);
- semantic filter classification -> G2 §8, explicitly out of the current
  scope (requires labelled evaluation data).

Interpretations recorded for review
-----------------------------------
- ``intent_id`` uses the *initial* intent vocabulary of b.md §2 P2
  (``compound_general`` ... ``unknown``).  The contract calls this list
  preliminary ("実際の研究クエリーを棚卸しして確定する"); changing it later is a
  schema change and must follow the §19 update procedure (version bump,
  regression tests, compatibility review).
- variant ``status`` uses the two values shown in §5.3 (``primary`` /
  ``alternative``); ``deprecated`` from §10 belongs to the *query* status
  enum, not the variant one.
- ``language`` requires at least two characters (b.md §10 JSON Schema
  ``minLength: 2``).
- ``compound_id`` references the compound taxonomy's ``skos:notation``
  (e.g. ``compound_cbx``).  b.md §4 makes the existing SKOS taxonomy the
  canonical source for compound concepts and §5.2 asks the registry to
  reference its identifiers; the repository standard (AGENTS.md) names the
  notation as the portable Concept ID, keeping the compound concept separate
  from any search text (P1).
- ``query-variants-registry-v1`` (added with the G2 vertical slice) is the
  *file* schema for ``metadata/queries/query-variants.json``; the block shape
  stays ``query-variants-v1`` (b.md §5.1/§5.3) and is reused unchanged as the
  item schema of ``variant_sets``.
"""

from __future__ import annotations

__all__ = [
    "QUERY_INTENTS",
    "QUERY_REGISTRY_SCHEMA",
    "QUERY_STATUSES",
    "QUERY_VARIANT_ITEM",
    "QUERY_VARIANTS_REGISTRY_SCHEMA",
    "QUERY_VARIANTS_SCHEMA",
    "VARIANT_STATUSES",
]

QUERY_STATUSES = ["active", "deprecated", "experimental"]

QUERY_INTENTS = [
    "compound_general",
    "product_liquid",
    "product_oil",
    "product_other",
    "regulation",
    "research",
    "other",
    "unknown",
]

VARIANT_STATUSES = ["primary", "alternative"]

_QUERY_ITEM = {
    "query_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "compound_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "intent_id": {
        "type": "string",
        "required": True,
        "allowed": QUERY_INTENTS,
    },
    "language": {
        "type": "string",
        "required": True,
        "minlength": 2,
    },
    "canonical_text": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "status": {
        "type": "string",
        "required": True,
        "allowed": QUERY_STATUSES,
    },
}

QUERY_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "queries": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _QUERY_ITEM,
        },
    },
}

QUERY_VARIANT_ITEM = {
    "variant_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "text": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "status": {
        "type": "string",
        "required": True,
        "allowed": VARIANT_STATUSES,
    },
}

QUERY_VARIANTS_SCHEMA = {
    "query_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "variants": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": QUERY_VARIANT_ITEM,
        },
    },
}

#: ``metadata/queries/query-variants.json`` - a bundle of ``query-variants-v1``
#: blocks, one per query concept (b.md §5.1 recommends the file; the block
#: schema is kept as-is for backward compatibility).
QUERY_VARIANTS_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "variant_sets": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": QUERY_VARIANTS_SCHEMA,
        },
    },
}
