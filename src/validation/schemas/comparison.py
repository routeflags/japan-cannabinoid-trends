"""Shared comparison declaration fragment (plan and run contracts).

Why this exists
---------------
A Google Trends single-term series is normalized to its own peak, so it can
never be compared with another compound's series.  A ``compare_terms``
request is the only common-scale measurement, and it is comparable across
compounds only when the study's declared anchors are in the request (for this
study: CBD and THC).  The declaration therefore belongs to both the
pre-collection plan and the adopted run, and both schemas use one fragment so
the two cannot drift.

The block is optional (legacy plans and runs carry none; AGENTS.md: do not
rewrite historical records).  A multi-term plan that declares nothing is
refused by the pre-collection gate instead of being treated as comparable.

This is a schema *fragment*, not a registered schema: there is no document
identified by ``comparison-v1`` and therefore no entry in
``SCHEMA_REGISTRY`` / the contract ledger.
"""

from __future__ import annotations

__all__ = [
    "COMMON_SCALE",
    "COMPARISON_BLOCK_SCHEMA",
    "COMPARISON_SCALES",
    "SINGLE_SERIES",
    "run_comparison_schema",
]

#: ``common_scale``: one ``compare_terms`` request measured every term on one
#: shared 0-100 scale; ``single_series``: one term normalized to its own peak.
COMMON_SCALE = "common_scale"
SINGLE_SERIES = "single_series"
COMPARISON_SCALES = (COMMON_SCALE, SINGLE_SERIES)

#: Fields a plan or a run may declare.  ``anchor_query_ids`` / ``anchor_terms``
#: are required only for ``common_scale``; the semantic layer enforces that
#: (Cerberus cannot express a conditional requirement without a custom rule,
#: and the repository keeps custom rules in the semantic layer).
COMPARISON_BLOCK_SCHEMA = {
    "comparison_scale": {
        "type": "string",
        "required": True,
        "allowed": list(COMPARISON_SCALES),
    },
    "policy_id": {
        "type": "string",
        "empty": False,
    },
    "anchor_query_ids": {
        "type": "list",
        "schema": {"type": "string", "empty": False},
    },
    "anchor_terms": {
        "type": "list",
        "schema": {"type": "string", "empty": False},
    },
    "locale": {
        "type": "string",
        "empty": False,
    },
    "geo": {
        "type": "string",
        "empty": False,
    },
    "timeframe": {
        "type": "string",
        "empty": False,
    },
    "tool": {
        "type": "string",
        "empty": False,
    },
}


def run_comparison_schema() -> dict:
    """The run-record block: the plan declaration plus the derived marker.

    ``cross_compound_comparable`` is written by the provenance builder (it is
    derived from ``comparison_scale``), never declared by a plan.  It records
    eligibility, not a statistical comparability verdict: the post-collection
    gate still verifies the anchors and the request metadata.
    """

    schema = dict(COMPARISON_BLOCK_SCHEMA)
    schema["cross_compound_comparable"] = {
        "type": "boolean",
        "required": True,
    }
    return schema
