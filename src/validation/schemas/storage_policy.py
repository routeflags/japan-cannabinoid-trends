"""G6 storage policy registry and publication decision schemas.

Contract sources
----------------
- G6 instruction §5 (storage classification), §6.1 (``config/storage-
  policies.json`` sample), §8.3 (git tracking expectations) and §10.3
  (publication decision sample): ``docs/plans/20261013f.md``.

Scope
-----
Structural validation only.  Not covered here:

- actual git tracking state -> ``validation.storage_policy.check_git_tracking``
  (Phase 4, read-only git commands);
- publication approval logic -> ``validation.storage_policy.check_publication``
  (Phase 4);
- release manifest / Zenodo checks -> G6 §12 (future work).

Interpretations recorded for review
-----------------------------------
- The three policy axes use the values shown in the §6.1 sample
  (``storage``: private/managed/repository, ``git_tracking``:
  tracked/ignored/conditional, ``publication``:
  approved/denied/requires_review/unknown).  ``classification`` uses the
  §5 vocabulary.  The §4 axis examples ("Local / Object Storage") describe
  deployment types, not this enum, and are not used here.
- ``artifact_layer`` accepts ``raw`` / ``interim`` / ``processed`` /
  ``metadata``: the §6.1 sample uses raw/processed/metadata, and ``interim``
  exists in the AGENTS.md pipeline.
- ``source_kind`` is a free string; the sample uses ``social`` and the
  wildcard ``any``.
- ``publication-decision-v1``: ``artifact_sha256`` is optional structurally;
  the publication gate requires it for ``approved`` decisions ("承認時には、
  承認者、日時、対象Artifactのハッシュ、審査基準の版を記録する", f.md §10.3).
"""

from __future__ import annotations

ARTIFACT_LAYERS = ["raw", "interim", "processed", "metadata"]

STORAGE_CLASSIFICATIONS = [
    "public",
    "internal",
    "restricted",
    "sensitive",
    "unknown",
]

STORAGE_BACKENDS = ["private", "managed", "repository"]

GIT_TRACKING_VALUES = ["tracked", "ignored", "conditional"]

PUBLICATION_STATES = ["approved", "denied", "requires_review", "unknown"]

_POLICY_ITEM = {
    "policy_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "artifact_layer": {
        "type": "string",
        "required": True,
        "allowed": ARTIFACT_LAYERS,
    },
    "source_kind": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "classification": {
        "type": "string",
        "required": True,
        "allowed": STORAGE_CLASSIFICATIONS,
    },
    "storage": {
        "type": "string",
        "required": True,
        "allowed": STORAGE_BACKENDS,
    },
    "git_tracking": {
        "type": "string",
        "required": True,
        "allowed": GIT_TRACKING_VALUES,
    },
    "publication": {
        "type": "string",
        "required": True,
        "allowed": PUBLICATION_STATES,
    },
}

STORAGE_POLICY_REGISTRY_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "policies": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": _POLICY_ITEM,
        },
    },
}

PUBLICATION_DECISION_SCHEMA = {
    "decision_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "artifact_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "status": {
        "type": "string",
        "required": True,
        "allowed": PUBLICATION_STATES,
    },
    "reviewed_at": {
        "type": "string",
        "nullable": True,
        "iso_datetime": True,
    },
    "reviewer": {
        "type": "string",
        "nullable": True,
    },
    "criteria_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "evidence": {
        "type": "list",
    },
    "notes": {
        "type": "string",
    },
    "artifact_sha256": {
        "type": "string",
        "regex": r"^[0-9a-f]{64}$",
    },
}
