"""C3 content review is a gate of its own (ISS-20261105-PUB-037).

The regression this pins: ``research_thcnm`` had an approved decision and passed
PUB-01..PUB-10, and the gate returned ``SUPPORTED`` - although no human had
recorded a content review.  The mechanical checks say the artifact is
well-formed and approved; they say nothing about its content.

The repository has no committed C1..C45 publication checklist yet (the only
C1/C2/C3 in the tree are the comparability checks in
``docs/specs/collection-pipeline.md``), so the production gate fails closed with
``CONTENT_REVIEW_CHECKLIST_UNDEFINED``.  The tests below build a synthetic
45-item checklist to prove both directions of the rule.
"""

import hashlib
import json
from pathlib import Path

from validation.publication_content_review import check_content_review
from validation.publication_eligibility import evaluate_eligibility

SHA = hashlib.sha256(b"artifact").hexdigest()
CHECKLIST_ID = "publication-content-review-c1-c45"


def _checklist(items=45) -> dict:
    return {
        "schema_version": "1.0.0",
        "record": "publication_content_review_checklist",
        "checklist_id": CHECKLIST_ID,
        "version": "1.0.0",
        "items": [{"id": f"C{index}", "title": f"item {index}"} for index in range(1, items + 1)],
    }


def _write_checklist(root: Path, document: dict | None = None) -> None:
    path = root / "metadata" / "publication" / "content-review-checklist.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document or _checklist(), ensure_ascii=False), encoding="utf-8")


def _review(items=45, **overrides) -> dict:
    review = {
        "checklist_id": CHECKLIST_ID,
        "checklist_version": "1.0.0",
        "artifact_sha256": SHA,
        "reviewer": "reviewer-001",
        "reviewed_at": "2026-11-05",
        "items": [
            {"id": f"C{index}", "verdict": "pass", "basis": f"checked item {index}"}
            for index in range(1, items + 1)
        ],
    }
    review.update(overrides)
    return review


def _evidence(review=None) -> dict:
    evidence = {
        "provenance_present": True,
        "integrity": "verified",
        "schema_valid": True,
        "personal_data_reviewed": True,
        "source_terms_confirmed": True,
        "redistribution_confirmed": True,
        "copyright_confirmed": True,
        "anonymization_applied": True,
    }
    if review is not None:
        evidence["content_review"] = review
    return evidence


def _artifact() -> dict:
    return {"artifact_id": "research-thcnm", "sha256": SHA}


def _decision(status="approved") -> dict:
    return {
        "decision_id": "publication-review-research-thcnm",
        "artifact_id": "research-thcnm",
        "artifact_sha256": SHA,
        "status": status,
        "reviewed_at": "2026-11-05",
        "reviewer": "owner",
        "criteria_version": "1.0.0",
    }


def _codes(root: Path, review) -> list[str]:
    return [issue["code"] for issue in check_content_review(root, _evidence(review), artifact_sha256=SHA)]


def test_the_old_thcnm_state_is_blocked_even_though_pub_01_10_pass(tmp_path):
    """The regression: approved + mechanically complete + no C3 record."""

    _write_checklist(tmp_path)

    result = evaluate_eligibility(
        _artifact(),
        _decision(),
        evidence=_evidence(),
        content_review=check_content_review(tmp_path, _evidence(), artifact_sha256=SHA),
    )

    assert result["verdict"] == "BLOCKED"
    assert result["failed"] == ["PUB-11"]
    detail = next(check for check in result["checks"] if check["id"] == "PUB-11")["detail"]
    assert "content_review" in detail


def test_a_complete_c1_to_c45_record_is_supported(tmp_path):
    _write_checklist(tmp_path)
    evidence = _evidence(_review())

    result = evaluate_eligibility(
        _artifact(),
        _decision(),
        evidence=evidence,
        content_review=check_content_review(tmp_path, evidence, artifact_sha256=SHA),
    )

    assert result["verdict"] == "SUPPORTED"
    assert result["failed"] == []


def test_an_incomplete_record_is_blocked(tmp_path):
    _write_checklist(tmp_path)
    evidence = _evidence(_review(items=44))

    assert "CONTENT_REVIEW_INCOMPLETE" in _codes(tmp_path, evidence["content_review"])


def test_a_failed_item_is_blocked(tmp_path):
    _write_checklist(tmp_path)
    review = _review()
    review["items"][0]["verdict"] = "fail"

    assert "CONTENT_REVIEW_ITEM_FAILED" in _codes(tmp_path, review)


def test_every_item_needs_a_basis(tmp_path):
    _write_checklist(tmp_path)
    review = _review()
    review["items"][3]["basis"] = ""

    assert "CONTENT_REVIEW_INVALID" in _codes(tmp_path, review)


def test_the_review_must_pin_the_current_artifact_hash(tmp_path):
    _write_checklist(tmp_path)
    review = _review(artifact_sha256="b" * 64)

    assert "CONTENT_REVIEW_HASH_MISMATCH" in _codes(tmp_path, review)


def test_the_reviewer_and_date_are_required(tmp_path):
    _write_checklist(tmp_path)
    for key in ("reviewer", "reviewed_at"):
        review = _review()
        review.pop(key)
        assert "CONTENT_REVIEW_INVALID" in _codes(tmp_path, review)


def test_the_checklist_id_and_version_must_match(tmp_path):
    _write_checklist(tmp_path)
    assert "CONTENT_REVIEW_CHECKLIST_MISMATCH" in _codes(
        tmp_path, _review(checklist_id="other")
    )
    assert "CONTENT_REVIEW_CHECKLIST_MISMATCH" in _codes(
        tmp_path, _review(checklist_version="9.9.9")
    )


def test_an_item_outside_the_checklist_is_reported(tmp_path):
    _write_checklist(tmp_path)
    review = _review()
    review["items"].append({"id": "C99", "verdict": "pass", "basis": "extra"})

    assert "CONTENT_REVIEW_ITEM_UNKNOWN" in _codes(tmp_path, review)


def test_no_checklist_fails_closed(tmp_path):
    """The repository state: the formal checklist is not committed yet."""

    assert _codes(tmp_path, _review()) == ["CONTENT_REVIEW_CHECKLIST_UNDEFINED"]


def test_the_gate_cannot_claim_supported_without_a_check(tmp_path):
    result = evaluate_eligibility(
        _artifact(), _decision(), evidence=_evidence(_review()), content_review=None
    )

    assert result["verdict"] == "BLOCKED"
    assert result["failed"] == ["PUB-11"]
