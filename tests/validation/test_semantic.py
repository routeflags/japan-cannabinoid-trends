"""Semantic validator tests (Phase 4): P4-1 temporal, P4-4 execution,
P4-10 secret scan, plus P4-11's layer-order guarantee through the pipeline.

Each function is exercised on the documents it is documented to accept
(standalone windows, temporal_provenance blocks, full run documents).
"""

import json
from copy import deepcopy
from pathlib import Path

from validation.pipeline import validate_full
from validation.semantic import (
    check_execution_consistency,
    check_temporal_semantics,
    scan_for_secrets,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _run_document() -> dict:
    return json.loads((FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8"))


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


# ---------------------------------------------------------------------------
# P4-1 / CV-08: temporal semantics
# ---------------------------------------------------------------------------


def test_valid_window_has_no_issues():
    window = json.loads((FIXTURES / "temporal_window.json").read_text(encoding="utf-8"))
    assert check_temporal_semantics(window) == []


def test_reversed_window_fails_cv08():
    window = {
        "start": "2026-10-01T00:00:00+09:00",
        "end_exclusive": "2026-09-01T00:00:00+09:00",
    }
    issues = check_temporal_semantics(window)
    assert _codes(issues) == ["TEMPORAL_ORDER_INVALID"]
    assert issues[0].path == "/start"


def test_equal_boundaries_fail_cv08():
    """G3-T01: start must be *earlier* than end (half-open interval)."""
    window = {
        "start": "2026-09-01T00:00:00Z",
        "end_exclusive": "2026-09-01T00:00:00Z",
    }
    assert _codes(check_temporal_semantics(window)) == ["TEMPORAL_ORDER_INVALID"]


def test_invalid_timezone_fails_g3_t02():
    issues = check_temporal_semantics({"timezone": "Not/AZone"})
    assert _codes(issues) == ["TIMEZONE_UNKNOWN"]
    assert issues[0].path == "/timezone"


def test_iana_timezone_accepted():
    assert check_temporal_semantics({"timezone": "Asia/Tokyo"}) == []


def test_week_granularity_requires_week_start():
    issues = check_temporal_semantics({"granularity": "week", "week_start": None})
    assert _codes(issues) == ["WEEK_START_REQUIRED"]
    assert check_temporal_semantics({"granularity": "week", "week_start": "monday"}) == []


def test_week_start_on_non_weekly_granularity_warns():
    issues = check_temporal_semantics({"granularity": "day", "week_start": "monday"})
    assert _codes(issues) == ["WEEK_START_UNEXPECTED"]
    assert issues[0].severity == "warning"


def test_temporal_provenance_block_is_checked():
    document = _run_document()
    document["temporal_provenance"]["requested_end_exclusive"] = (
        document["temporal_provenance"]["requested_start"]
    )
    issues = check_temporal_semantics(document)
    assert _codes(issues) == ["TEMPORAL_ORDER_INVALID"]
    assert issues[0].path == "/temporal_provenance/requested_start"


def test_run_finished_before_start_fails_g5_t08():
    document = _run_document()
    document["collection_finished_at"] = "2026-10-12T23:00:00Z"
    issues = check_temporal_semantics(document)
    assert _codes(issues) == ["COLLECTION_FINISHED_BEFORE_START"]


def test_run_finished_equal_to_start_is_allowed():
    document = _run_document()
    document["collection_finished_at"] = document["collection_started_at"]
    assert check_temporal_semantics(document) == []


def test_temporal_boundary_missing_when_null():
    issues = check_temporal_semantics({"start": None, "end_exclusive": "2026-01-01T00:00:00Z"})
    assert _codes(issues) == ["TEMPORAL_BOUNDARY_MISSING"]


def test_temporal_semantics_does_not_mutate():
    document = _run_document()
    before = deepcopy(document)
    check_temporal_semantics(document)
    assert document == before


# ---------------------------------------------------------------------------
# P4-4: execution consistency
# ---------------------------------------------------------------------------


def test_valid_execution_has_no_issues():
    assert check_execution_consistency(_run_document()) == []


def test_success_with_errors_fails():
    document = _run_document()
    document["execution"] = {
        "status": "success",
        "returned_count": 10,
        "errors": ["page 2 timeout"],
        "pagination_exhausted": True,
    }
    issues = check_execution_consistency(document)
    assert _codes(issues) == ["EXECUTION_ERRORS_ON_SUCCESS"]


def test_failed_with_positive_count_fails():
    document = _run_document()
    document["execution"] = {
        "status": "failed",
        "returned_count": 3,
        "errors": ["api error"],
    }
    issues = check_execution_consistency(document)
    assert _codes(issues) == ["EXECUTION_COUNT_ON_FAILURE"]


def test_success_with_unexhausted_pagination_fails():
    document = _run_document()
    document["execution"] = {
        "status": "success",
        "returned_count": 10,
        "errors": [],
        "pagination_exhausted": False,
    }
    issues = check_execution_consistency(document)
    assert _codes(issues) == ["EXECUTION_PAGINATION_INCOMPLETE"]


def test_terminal_status_requires_completion_evidence():
    """P3-1: the finalized profile requires completion information."""
    document = _run_document()
    document.pop("collection_finished_at")
    for status in ("success", "partial", "failed"):
        document["execution"]["status"] = status
        document["execution"]["errors"] = ["e"] if status == "failed" else []
        document["execution"]["returned_count"] = 0 if status == "failed" else 1
        issues = check_execution_consistency(document)
        assert "COMPLETION_EVIDENCE_MISSING" in _codes(issues), status


def test_running_status_does_not_require_completion_evidence():
    document = _run_document()
    document.pop("collection_finished_at")
    document["execution"]["status"] = "running"
    assert check_execution_consistency(document) == []


def test_explicitly_complete_partial_is_allowed():
    """partial + pagination exhausted + no errors: allowed (e.g. window cut)."""
    document = _run_document()
    document["execution"]["pagination_exhausted"] = True
    assert check_execution_consistency(document) == []


# ---------------------------------------------------------------------------
# P4-10: secret scan
# ---------------------------------------------------------------------------


def test_secret_key_with_value_is_detected():
    document = {"environment": {"api_key": "not-a-placeholder-value"}}
    issues = scan_for_secrets(document)
    assert _codes(issues) == ["SECRET_DETECTED"]
    assert issues[0].path == "/environment/api_key"
    # the value must not leak into the message (h.md §14)
    assert "not-a-placeholder-value" not in issues[0].message


def test_secret_value_patterns_are_detected():
    document = {
        "notes": "rotate ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 now",
        "nested": ["sk-abcdefghijklmnopqrstuvwx"],
    }
    issues = scan_for_secrets(document)
    assert set(_codes(issues)) == {"SECRET_DETECTED"}
    assert {issue.path for issue in issues} == {"/notes", "/nested/0"}


def test_normal_notes_do_not_trigger_false_positives():
    """Documented false-positive boundary: prose about tokens is not a
    credential; empty placeholders are not leaks."""
    document = {
        "notes": "sanitize the token before commit; tokenization is unrelated",
        "environment": {"api_key": "", "token": None, "evidence_refs": []},
        "query_provenance": {"submitted_query": "CBX"},
    }
    assert scan_for_secrets(document) == []


def test_secret_scan_does_not_modify_or_remove():
    document = {"token": "secret-value"}
    before = deepcopy(document)
    scan_for_secrets(document)
    assert document == before


# ---------------------------------------------------------------------------
# P4-11: layer order (structural failure short-circuits semantics)
# ---------------------------------------------------------------------------


def test_structural_failure_skips_semantic_layer():
    calls = []

    def spy(document):
        calls.append(document)
        return []

    document = _run_document()
    document["execution"]["returned_count"] = "100"  # type mismatch
    outcome = validate_full(
        document, schema_id="collection-run-v1", extra_checks=[spy]
    )
    assert outcome.valid is False
    assert calls == []
    assert _codes(outcome.issues) == ["TYPE_MISMATCH"]


def test_semantic_layer_runs_after_successful_structure():
    calls = []

    def spy(document):
        calls.append(document)
        return []

    outcome = validate_full(
        _run_document(), schema_id="collection-run-v1", extra_checks=[spy]
    )
    assert outcome.valid is True
    assert len(calls) == 1


def test_semantic_issue_is_covered_after_structure():
    document = _run_document()
    document["temporal_provenance"]["requested_end_exclusive"] = (
        document["temporal_provenance"]["requested_start"]
    )
    outcome = validate_full(document, schema_id="collection-run-v1")
    assert outcome.valid is False
    assert "TEMPORAL_ORDER_INVALID" in _codes(outcome.issues)


def test_issue_carries_schema_version_stamp():
    document = _run_document()
    document["execution"]["returned_count"] = "100"
    outcome = validate_full(document, schema_id="collection-run-v1")
    assert all(issue.schema_version == "1.0.0" for issue in outcome.issues)
