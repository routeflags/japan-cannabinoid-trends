"""G3 coverage manifest schema (ISS-20261015-COV-004).

Contract sources
----------------
- G3 §9 (coverage types / status / manifest §9.3): ``docs/plans/20261013c.md``.
- G3 §11 (missingness contract: missing stays missing, never an observed
  zero) and §15 (legacy runs are not retroactively converted).
- Persistence rule: ``docs/specs/validation-framework.md`` §16 (the canonical
  persisted manifest is ``<run-dir>/coverage-manifest.json``, written only via
  the explicit ``coverage-run --persist`` opt-in; existing runs are never
  backfilled).

Scope
-----
Structural validation only.  Not covered here:

- bucket generation and window matching -> ``validation.coverage``
  (``evaluate_coverage``) and ``validation.windows``;
- coverage status semantics (``complete`` / ``partial`` / ``missing`` /
  ``unknown`` and the per-term missingness states) -> ``validation.coverage``
  (the state machine; ``tests/validation/test_coverage.py`` pins it);
- collector resolution, pagination and verification evidence -> the evaluator.

Interpretations recorded for review
-------------------------------------
- The manifest carries its schema identity inline (``schema_id`` /
  ``schema_version``), set by ``validation.coverage.evaluate_coverage`` from
  the constants below.  ``schema_version`` must match
  ``validation.schema_registry.SCHEMA_VERSIONS`` (CV-20).
- ``run_id`` / ``window_id`` are nullable: a run without readable
  ``run_metadata.json`` still yields a manifest (status ``unknown``,
  reason ``run_metadata_missing``).
- ``verified`` stays null: verification evidence does not exist yet, and the
  manifest never fabricates it (G3 §9).  ``truncated`` is reserved null.
- ``observed.end_exclusive`` is nullable: a single-label observation has no
  span to close.
- ``states`` is keyed by observed term with ``valuesrules`` (the same Cerberus
  pattern as ``validation.schemas.registries`` capabilities): term names are
  data, not contract.
- ``label_gap_days`` is optional: it appears only when a consecutive label gap
  longer than the evaluator threshold is observed.
"""

from __future__ import annotations

__all__ = [
    "COVERAGE_MANIFEST_SCHEMA",
    "COVERAGE_MANIFEST_SCHEMA_ID",
    "COVERAGE_MANIFEST_SCHEMA_VERSION",
    "COVERAGE_STATUSES",
    "EXPECTED_GRANULARITIES",
    "TERM_STATES",
]

#: Stable schema ID of the coverage manifest document.
COVERAGE_MANIFEST_SCHEMA_ID = "coverage-manifest-v1"

#: Contract version of the coverage manifest schema (CV-20).
COVERAGE_MANIFEST_SCHEMA_VERSION = "1.0.0"

#: Coverage statuses emitted by ``validation.coverage.evaluate_coverage``
#: (G3 §9.3; a Google Trends zero point is never ``observed_zero`` — §11).
COVERAGE_STATUSES = ["complete", "partial", "missing", "unknown"]

#: Per-term missingness states (§11).  ``below_threshold`` is missing evidence,
#: never an observed zero.
TERM_STATES = [
    "observed_nonzero",
    "below_threshold",
    "collection_failed",
    "unknown",
]

#: Granularities with a deterministic calendar bucket rule
#: (``validation.coverage._BUCKET_GRANULARITIES``).
EXPECTED_GRANULARITIES = ["day", "week", "month"]

_INTERVAL = {
    "start": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "end_exclusive": {
        "type": "string",
        "required": True,
        "empty": False,
    },
}

_INTERVAL_LIST = {
    "type": "list",
    "required": True,
    "schema": {
        "type": "dict",
        "schema": _INTERVAL,
    },
}

_TERM_STATE = {
    "state": {
        "type": "string",
        "required": True,
        "allowed": TERM_STATES,
    },
    "point_count": {
        "type": "integer",
        "required": True,
        "min": 0,
    },
    "zero_count": {
        "type": "integer",
        "required": True,
        "min": 0,
    },
    "observed_min": {
        "type": "string",
        "nullable": True,
    },
    "observed_max": {
        "type": "string",
        "nullable": True,
    },
    "sources": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "string",
        },
    },
    "platform_no_data": {
        "type": "dict",
        "schema": {
            "status": {
                "type": "string",
            },
            "note": {
                "type": "string",
            },
            "source": {
                "type": "string",
            },
        },
    },
}

_COVERAGE = {
    "requested": {
        "type": "dict",
        "required": True,
        "nullable": True,
        "schema": _INTERVAL,
    },
    "requested_relative": {
        "type": "dict",
        "required": True,
        "nullable": True,
        "schema": {
            "timeframes": {
                "type": "list",
                "required": True,
                "schema": {
                    "type": "string",
                },
            },
            "sources": {
                "type": "list",
                "required": True,
                "schema": {
                    "type": "string",
                },
            },
            "reference": {
                "type": "string",
                "nullable": True,
            },
            "reference_source": {
                "type": "string",
                "nullable": True,
            },
            "resolved_absolute_window": {
                "nullable": True,
            },
            "resolution_note": {
                "type": "string",
                "required": True,
            },
        },
    },
    "collector": {
        "type": "dict",
        "required": True,
        "nullable": True,
        "schema": {
            "start": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "end_exclusive": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "basis": {
                "type": "string",
                "required": True,
            },
            "timeframe": {
                "type": "string",
                "required": True,
            },
        },
    },
    "observed": {
        "type": "dict",
        "required": True,
        "nullable": True,
        "schema": {
            "start": {
                "type": "string",
                "required": True,
                "empty": False,
            },
            "end_exclusive": {
                "type": "string",
                "required": True,
                "nullable": True,
            },
            "basis": {
                "type": "string",
                "required": True,
            },
        },
    },
    "verified": {
        "nullable": True,
    },
    "status": {
        "type": "string",
        "required": True,
        "allowed": COVERAGE_STATUSES,
    },
    "pagination_exhausted": {
        "type": "boolean",
        "required": True,
        "nullable": True,
    },
    "truncated": {
        "nullable": True,
    },
    "verified_intervals": _INTERVAL_LIST,
    "missing_intervals": _INTERVAL_LIST,
    "unknown_intervals": _INTERVAL_LIST,
    "expected_granularity": {
        "type": "string",
        "required": True,
        "nullable": True,
        "allowed": EXPECTED_GRANULARITIES,
    },
    "expected_intervals": _INTERVAL_LIST,
    "missing_expected_intervals": _INTERVAL_LIST,
    "states": {
        "type": "dict",
        "required": True,
        "valuesrules": {
            "type": "dict",
            "schema": _TERM_STATE,
        },
    },
    "reasons": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "evidence": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "label_gap_days": {
        "type": "integer",
        "min": 0,
    },
}

COVERAGE_MANIFEST_SCHEMA = {
    "schema_id": {
        "type": "string",
        "required": True,
        "allowed": [COVERAGE_MANIFEST_SCHEMA_ID],
        "empty": False,
    },
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "coverage_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "profile": {
        "type": "string",
        "required": True,
        "allowed": ["g3_coverage"],
        "empty": False,
    },
    "run_id": {
        "type": "string",
        "required": True,
        "nullable": True,
    },
    "target": {
        "type": "string",
        "required": True,
    },
    "window_id": {
        "type": "string",
        "required": True,
        "nullable": True,
    },
    "coverage": {
        "type": "dict",
        "required": True,
        "schema": _COVERAGE,
    },
}
