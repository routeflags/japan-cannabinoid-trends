"""Publication gate tests (P4-9 / CV-11, f.md §10/§11).
"""

import json
from copy import deepcopy
from pathlib import Path

from validation.storage_policy import can_publish, check_publication

FIXTURES = Path(__file__).parent / "fixtures"


def _artifact():
    return {
        "artifact_id": "artifact-001",
        "sha256": "a" * 64,
    }


def _approved_decision():
    decision = json.loads(
        (FIXTURES / "publication_decision.json").read_text(encoding="utf-8")
    )
    decision.update(
        {
            "status": "approved",
            "reviewed_at": "2026-10-13T00:00:00Z",
            "reviewer": "reviewer-001",
            "artifact_sha256": "a" * 64,
        }
    )
    return decision


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


def test_missing_decision_refuses_publication_g6_t07():
    issues = check_publication(_artifact(), None)
    assert _codes(issues) == ["PUBLICATION_DECISION_MISSING"]
    assert can_publish(_artifact(), None) is False


def test_requires_review_refuses_publication_g6_t08():
    decision = json.loads(
        (FIXTURES / "publication_decision.json").read_text(encoding="utf-8")
    )
    assert decision["status"] == "requires_review"
    issues = check_publication(_artifact(), decision)
    assert "PUBLICATION_NOT_APPROVED" in _codes(issues)
    assert can_publish(_artifact(), decision) is False


def test_unknown_status_refuses_publication():
    decision = _approved_decision()
    decision["status"] = "unknown"
    assert "PUBLICATION_NOT_APPROVED" in _codes(check_publication(_artifact(), decision))


def test_approved_matching_decision_passes_all_criteria():
    issues = check_publication(_artifact(), _approved_decision())
    assert issues == []
    assert can_publish(_artifact(), _approved_decision()) is True


def test_approved_decision_without_criteria_fails():
    decision = _approved_decision()
    decision.update({"reviewed_at": None, "reviewer": None, "artifact_sha256": None})
    issues = check_publication(_artifact(), decision)
    assert "PUBLICATION_CRITERIA_MISSING" in _codes(issues)
    assert "PUBLICATION_HASH_MISMATCH" in _codes(issues)
    assert can_publish(_artifact(), decision) is False


def test_changed_artifact_hash_invalidates_approval_g6_t09():
    artifact = _artifact()
    artifact["sha256"] = "b" * 64
    decision = _approved_decision()
    issues = check_publication(artifact, decision)
    assert "PUBLICATION_HASH_MISMATCH" in _codes(issues)
    assert can_publish(artifact, decision) is False


def test_decision_for_other_artifact_is_refused():
    decision = _approved_decision()
    decision["artifact_id"] = "artifact-999"
    issues = check_publication(_artifact(), decision)
    assert "PUBLICATION_ARTIFACT_MISMATCH" in _codes(issues)


def test_publication_check_is_non_destructive():
    artifact = _artifact()
    decision = _approved_decision()
    artifact_before = deepcopy(artifact)
    decision_before = deepcopy(decision)
    check_publication(artifact, decision)
    assert artifact == artifact_before
    assert decision == decision_before
