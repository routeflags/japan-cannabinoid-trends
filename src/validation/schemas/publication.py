"""Publication content-review schemas (ISS-20261105-PUB-037).

Two different things are recorded for a publication artifact:

- the **mechanical** checks (PC-1..PC-10, PUB-01..PUB-10): hash, schema,
  provenance, secrets, terms, approval pinning.  These can be computed from
  the repository;
- the **content review** (C3): a human reads the page and records a verdict and
  a basis for every item of the publication checklist.  This cannot be computed,
  and a mechanical pass says nothing about it.

The gate reported ``SUPPORTED`` on mechanical checks alone, so a page whose
content had never been reviewed looked releasable.  These schemas make the
content review a recorded document instead of an assumption.
"""

from __future__ import annotations

CONTENT_REVIEW_CHECKLIST_SCHEMA = {
    "schema_version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "record": {
        "type": "string",
        "required": True,
        "allowed": ["publication_content_review_checklist"],
    },
    "checklist_id": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "version": {
        "type": "string",
        "required": True,
        "empty": False,
    },
    "items": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "dict",
            "schema": {
                "id": {"type": "string", "required": True, "empty": False},
                "title": {"type": "string", "required": True, "empty": False},
            },
        },
    },
}

CONTENT_REVIEW_SCHEMA = {
    "checklist_id": {"type": "string", "required": True, "empty": False},
    "checklist_version": {"type": "string", "required": True, "empty": False},
    "artifact_sha256": {
        "type": "string",
        "required": True,
        "regex": "^[0-9a-f]{64}$",
    },
    "reviewer": {"type": "string", "required": True, "empty": False},
    "reviewed_at": {
        "type": "string",
        "required": True,
        "regex": r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
    },
    "items": {
        "type": "list",
        "required": True,
        "minlength": 1,
        "schema": {
            "type": "dict",
            "schema": {
                "id": {"type": "string", "required": True, "empty": False},
                "verdict": {
                    "type": "string",
                    "required": True,
                    "allowed": ["pass", "fail", "not_applicable"],
                },
                "basis": {"type": "string", "required": True, "empty": False},
            },
        },
    },
}
