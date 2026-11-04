"""C3 content review: a human review record, checked apart from the machine (ISS-20261105-PUB-037).

The publication gate had ten checks and every one of them was mechanical: hash,
schema, provenance, secrets, terms, anonymization, approval pinning.  A page
whose *content* had never been read by a reviewer passed all ten and came back
``SUPPORTED``.  That is the failure this module exists to stop: the mechanical
result says the artifact is well-formed and approved, not that its content was
reviewed.

Two gates, one verdict
----------------------
- **mechanical** (``PUB-01..PUB-10``): computed from the repository.
- **content review / C3** (``PUB-11``): read from a recorded review in
  ``evidence.json``, against a committed checklist.

Neither implies the other.  ``SUPPORTED`` requires both; an approved decision
with no C3 record is ``BLOCKED``, not approved-with-a-warning.

Where the checklist comes from
------------------------------
``metadata/publication/content-review-checklist.json`` declares the item ids and
titles the repository requires.  The repository does not currently contain a
C1..C45 publication checklist (the only C1/C2/C3 in the tree are the
comparability checks in ``docs/specs/collection-pipeline.md``), so the file is
absent and this check fails closed with ``CONTENT_REVIEW_CHECKLIST_UNDEFINED``.
Creating the checklist is a contract decision, not something this module may
invent; the shape is in ``validation.schemas.publication``.
"""

from __future__ import annotations

import json
from pathlib import Path

from validation.core import validate_document
from validation.schemas.publication import (
    CONTENT_REVIEW_CHECKLIST_SCHEMA,
    CONTENT_REVIEW_SCHEMA,
)

__all__ = [
    "CHECKLIST_PATH",
    "check_content_review",
    "load_checklist",
]

#: Committed checklist definition (ids + titles).  Absence is a finding, not a
#: pass: without it nobody can say what "complete" means.
CHECKLIST_PATH = Path("metadata") / "publication" / "content-review-checklist.json"


def _issue(code: str, pointer: str, detail: str) -> dict:
    return {"code": code, "pointer": pointer, "detail": detail}


def load_checklist(repo_root: Path) -> tuple[dict | None, list[dict]]:
    """Read and validate the checklist definition; ``(None, issues)`` if absent."""

    path = repo_root / CHECKLIST_PATH
    if not path.is_file():
        return None, [
            _issue(
                "CONTENT_REVIEW_CHECKLIST_UNDEFINED",
                str(CHECKLIST_PATH),
                "no publication content-review checklist is committed; the C3 "
                "review cannot be verified and the artifact cannot be SUPPORTED",
            )
        ]
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [
            _issue(
                "CONTENT_REVIEW_CHECKLIST_INVALID",
                str(CHECKLIST_PATH),
                f"cannot read the checklist: {error.__class__.__name__}",
            )
        ]
    result = validate_document(document, CONTENT_REVIEW_CHECKLIST_SCHEMA)
    if not result.valid:
        return None, [
            _issue("CONTENT_REVIEW_CHECKLIST_INVALID", pointer, detail)
            for pointer, messages in sorted(result.errors.items())
            for detail in messages
        ]
    return document, []


def check_content_review(
    repo_root: Path,
    evidence: dict | None,
    *,
    artifact_sha256: str,
) -> list[dict]:
    """Every reason the recorded C3 review does not cover this artifact."""

    checklist, issues = load_checklist(repo_root)
    if checklist is None:
        return issues
    evidence = evidence if isinstance(evidence, dict) else {}
    review = evidence.get("content_review")
    if not isinstance(review, dict):
        return [
            _issue(
                "CONTENT_REVIEW_MISSING",
                "/content_review",
                "evidence.json has no content_review record; the C3 review was "
                "not performed (a mechanical pass is not a content review)",
            )
        ]

    result = validate_document(review, CONTENT_REVIEW_SCHEMA)
    if not result.valid:
        return [
            _issue("CONTENT_REVIEW_INVALID", pointer, detail)
            for pointer, messages in sorted(result.errors.items())
            for detail in messages
        ]

    if review["checklist_id"] != checklist["checklist_id"]:
        issues.append(
            _issue(
                "CONTENT_REVIEW_CHECKLIST_MISMATCH",
                "/content_review/checklist_id",
                f"review cites {review['checklist_id']!r}, the committed "
                f"checklist is {checklist['checklist_id']!r}",
            )
        )
    if review["checklist_version"] != checklist["version"]:
        issues.append(
            _issue(
                "CONTENT_REVIEW_CHECKLIST_MISMATCH",
                "/content_review/checklist_version",
                f"review cites version {review['checklist_version']!r}, the "
                f"committed checklist is {checklist['version']!r}",
            )
        )
    if review["artifact_sha256"] != artifact_sha256:
        issues.append(
            _issue(
                "CONTENT_REVIEW_HASH_MISMATCH",
                "/content_review/artifact_sha256",
                "the review pins a different artifact hash; a content change "
                "voids the review",
            )
        )

    required = [item["id"] for item in checklist["items"]]
    recorded: dict[str, dict] = {}
    for index, item in enumerate(review["items"]):
        item_id = item["id"]
        if item_id in recorded:
            issues.append(
                _issue("CONTENT_REVIEW_ITEM_DUPLICATE", f"/content_review/items/{index}", item_id)
            )
        recorded[item_id] = item
        if item_id not in required:
            issues.append(
                _issue(
                    "CONTENT_REVIEW_ITEM_UNKNOWN",
                    f"/content_review/items/{index}",
                    f"{item_id} is not in the committed checklist",
                )
            )
        if item["verdict"] == "fail":
            issues.append(
                _issue(
                    "CONTENT_REVIEW_ITEM_FAILED",
                    f"/content_review/items/{index}",
                    f"{item_id} was reviewed and failed: {item['basis']}",
                )
            )

    missing = [item_id for item_id in required if item_id not in recorded]
    if missing:
        issues.append(
            _issue(
                "CONTENT_REVIEW_INCOMPLETE",
                "/content_review/items",
                f"{len(recorded)} of {len(required)} checklist items recorded; "
                f"missing: {', '.join(missing[:10])}"
                + ("..." if len(missing) > 10 else ""),
            )
        )
    return issues
