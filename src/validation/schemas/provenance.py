"""G5 provenance schemas: transformation records and the evidence registry.

Contract sources
----------------
- G5 instruction §5.3 (transformation provenance fields) and §6 (sample):
  ``docs/plans/20261013e.md``.
- G5 §11 (evidence registry) and §10 (legacy audit evidence levels):
  ``docs/plans/20261013e.md``.
- G5 §15 / G5-T17 (transformation inputs must exist).

Scope
-----
Structural validation only.  Not covered here:

- input/output artifact existence -> ``validation.integrity.
  check_transformation_lineage`` (Phase 4);
- ``status`` / error-state consistency -> Semantic Validator when
  transformation records grow error fields (not in the §6 sample);
- evidence reference existence and hash match -> ``validation.provenance.
  check_evidence_registry`` (G5 vertical slice; needs filesystem access).

Required fields (G5 rollout plan P3-7): ``transformation_id``,
``executed_at``, ``status``, ``input_artifact_ids``, ``output_artifact_ids``.
``input_artifact_ids`` / ``output_artifact_ids`` must be non-empty: a derived
artifact without references cannot satisfy the lineage contract (d.md §15,
e.md §5.3).

Module naming note (G5 duplicate整理 T1)
-----------------------------------------
This module is named ``provenance`` but holds the *transformation* and
*evidence* schemas, while the collection-run provenance contract lives in
``validation.schemas.collection_run`` (``collection-run-v1``) and its builder
in ``collection.core.provenance``.  The name is kept for backward
compatibility (``validation.schema_registry`` and
``tests/validation/test_transformation.py`` import from it); renaming would
churn the registry and the P3-11 coverage map for no behavioral gain.

Interpretations recorded for review
-----------------------------------
- ``status`` vocabulary is ``success`` / ``partial`` / ``failed``: a stored
  transformation record describes an execution that happened (``executed_at``
  is required), so ``running`` is not part of it.  If the G5 implementation
  later records in-flight transformations, this is a schema change under §19.
- ``parameters`` is an extension area (``allow_unknown=True``): the fields in
  it are transformation-specific.  Only non-secret parameters may be stored
  (G5 P7 / §4.2 "秘密情報"); ``validation.semantic.scan_for_secrets`` checks
  this at validation time.
"""

from __future__ import annotations

__all__ = [
    "EVIDENCE_REGISTRY_SCHEMA",
    "EVIDENCE_TYPES",
    "TRANSFORMATION_SCHEMA",
    "TRANSFORMATION_STATUSES",
]

TRANSFORMATION_STATUSES = ["success", "partial", "failed"]

#: Evidence kinds accepted by the G5 evidence registry (e.md §11).
#: Source-agnostic (G5 P8): no platform or provider names appear here.
#: ``registry_definition`` covers sources/collectors/queries/windows/artifact
#: registry files; ``taxonomy`` covers SKOS compound taxonomies and mappings.
EVIDENCE_TYPES = [
    "collection_log",
    "run_metadata",
    "actor_run",
    "git_commit",
    "source_config",
    "raw_artifact",
    "database_record",
    "registry_definition",
    "taxonomy",
    "audit_report",
    "test_fixture",
]

TRANSFORMATION_SCHEMA = {
    "transformation_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "transformation_name": {
        "type": "string",
    },
    "transformation_version": {
        "type": "string",
    },
    "executed_at": {
        "type": "string",
        "required": True,
        "empty": False,
        "iso_datetime": True,
    },
    "code_commit": {
        "type": "string",
    },
    "input_artifact_ids": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "output_artifact_ids": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "string",
            "empty": False,
        },
    },
    "parameters": {
        "type": "dict",
        "allow_unknown": True,
    },
    "status": {
        "type": "string",
        "required": True,
        "allowed": TRANSFORMATION_STATUSES,
    },
}

#: G5 evidence registry document (e.md §11).  Each entry cites one piece of
#: evidence an audit can re-examine: local ``reference`` values are
#: repository-relative paths and must exist; external references (URIs such
#: as cloud actor-run URLs) are recorded but reported as unverifiable, never
#: failed (G5 P2/P5: no guessing, explicit unknown).
#:
#: ``sha256`` is optional: omitted (null) means "hash not recorded" and is
#: reported as info, never invented.  When present it must match the file.
#: ``observed_at`` records when the evidence was observed by the registrar —
#: a genuine observation timestamp, never back-filled (G5 P2).
EVIDENCE_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "evidence": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "evidence_id": {
                    "type": "string",
                    "required": True,
                    "empty": False,
                },
                "evidence_type": {
                    "type": "string",
                    "required": True,
                    "allowed": EVIDENCE_TYPES,
                },
                "reference": {
                    "type": "string",
                    "required": True,
                    "empty": False,
                },
                "sha256": {
                    "type": "string",
                    "nullable": True,
                    "regex": "^[0-9a-f]{64}$",
                },
                "observed_at": {
                    "type": "string",
                    "required": True,
                    "empty": False,
                    "iso_datetime": True,
                },
                "note": {
                    "type": "string",
                },
            },
        },
    },
}
