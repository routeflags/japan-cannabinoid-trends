"""G5 transformation provenance schema.

Contract sources
----------------
- G5 instruction §5.3 (transformation provenance fields) and §6 (sample):
  ``docs/plans/20261013e.md``.
- G5 §15 / G5-T17 (transformation inputs must exist).

Scope
-----
Structural validation only.  Not covered here:

- input/output artifact existence -> ``validation.integrity.
  check_transformation_lineage`` (Phase 4);
- ``status`` / error-state consistency -> Semantic Validator when
  transformation records grow error fields (not in the §6 sample).

Required fields (G5 rollout plan P3-7): ``transformation_id``,
``executed_at``, ``status``, ``input_artifact_ids``, ``output_artifact_ids``.
``input_artifact_ids`` / ``output_artifact_ids`` must be non-empty: a derived
artifact without references cannot satisfy the lineage contract (d.md §15,
e.md §5.3).

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

TRANSFORMATION_STATUSES = ["success", "partial", "failed"]

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
