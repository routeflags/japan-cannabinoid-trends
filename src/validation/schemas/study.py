"""G7 study, measurement and research view schemas.

Contract sources
----------------
- G7 instruction §4.2 (``metadata/studies/study-registry.json`` sample),
  §6.2 (``metadata/measurements/measurement-registry.json`` sample) and
  §10.1 (research view definition): ``docs/plans/20261013g.md``.

Scope
-----
Structural validation only.  Not covered here:

- study / measurement / compound *references* from runs ->
  ``validation.semantic.check_registry_references`` (Phase 4);
- cross-study comparability -> ``validation.comparability`` (Phase 4);
- research catalog generation and deduplication -> G7 §5/§12 (future work).

Interpretations recorded for review
-----------------------------------
- Study IDs in this schema are free strings: the g.md sample explicitly says
  the shown IDs are illustrative and that existing repository study IDs must
  be confirmed before use ("Study IDは説明用であり、既存リポジトリの実際のIDを
  確認してから設定する").  No enumeration is added here.
- ``status`` is a free non-empty string: no vocabulary for study status is
  defined in g.md, and inventing one would be a contract change.
- ``aggregation`` uses the g.md §7 examples (count / sum / mean) plus the
  §6.2 sample value ``source_defined``.
- ``comparison_mode`` currently allows only ``parallel_timeseries``: g.md
  §10.1 defines that mode explicitly and states that it must not sum
  measurements ("測定値を合算するモードではない").  Additional modes require a
  documented contract change.
- ``normalization_required`` is kept exactly as defined in g.md §6.2
  ("測定値が正規化済みかどうかを表すものではない" -> it means "the measurement
  needs normalization"); the normalization method fields listed under
  "本番実装では、以下の情報を追加する" are future additions and are not yet in
  this schema.
"""

from __future__ import annotations

from validation.schemas.temporal import GRANULARITIES

_STUDY_ITEM = {
    "study_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "title": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "research_questions": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "sources": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "status": {
        "type": "string",
        "required": True,
        "empty": False,
    },
}

STUDY_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "studies": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _STUDY_ITEM,
        },
    },
}

MEASUREMENT_AGGREGATIONS = ["count", "sum", "mean", "source_defined"]

_MEASUREMENT_ITEM = {
    "measurement_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "unit": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "observation_entity": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "aggregation": {
        "type": "string",
        "required": True,
        "allowed": MEASUREMENT_AGGREGATIONS,
    },
    "normalization_required": {
        "type": "boolean",
        "required": True,
    },
}

MEASUREMENT_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "measurements": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _MEASUREMENT_ITEM,
        },
    },
}

COMPARISON_MODES = ["parallel_timeseries"]

RESEARCH_VIEW_SCHEMA = {
    "view_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "view_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "compound_id": {
        "type": "string",
        "required": True,
        "empty": False,
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
    "sources": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "measurements": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "comparison_mode": {
        "type": "string",
        "required": True,
        "allowed": COMPARISON_MODES,
    },
    "require_comparability_gate": {
        "type": "boolean",
        "required": True,
    },
}
