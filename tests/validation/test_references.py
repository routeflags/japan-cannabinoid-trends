"""Registry reference and capability gate tests (P4-2 / P4-3).

Fixtures mirror the a.md/b.md registry samples; the run document comes from
the G5 sample fixture.
"""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.semantic import (
    Registries,
    check_capability_gate,
    check_registry_references,
    eligible_collectors,
)

REGISTRIES = Path(__file__).parent / "fixtures" / "registries"
FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((REGISTRIES / name).read_text(encoding="utf-8"))


def _run_document() -> dict:
    return json.loads((FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8"))


def _registries() -> Registries:
    return Registries.from_documents(
        source_registry=_load("sources.json"),
        collector_registry=_load("collectors.json"),
        query_registry=_load("queries.json"),
        study_registry=_load("study-registry.json"),
    )


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


# ---------------------------------------------------------------------------
# P4-2 / CV-05 / CV-06
# ---------------------------------------------------------------------------


def test_registered_references_produce_no_errors():
    issues = check_registry_references(_run_document(), _registries())
    assert [issue for issue in issues if issue.severity == "error"] == []
    # unverified collector is reported as informational only
    assert _codes(issues) == ["COLLECTOR_LEGACY_REFERENCE"]


def test_cv05_unregistered_source_fails():
    document = _run_document()
    document["source_id"] = "mastodon"
    issues = check_registry_references(document, _registries())
    assert "REFERENCE_SOURCE_UNREGISTERED" in _codes(issues)


def test_unregistered_collector_fails():
    document = _run_document()
    document["collector"]["collector_id"] = "x-apify-unknown"
    issues = check_registry_references(document, _registries())
    assert "REFERENCE_COLLECTOR_UNREGISTERED" in _codes(issues)


def test_collector_source_mismatch_fails_p05():
    document = _run_document()
    document["collector"]["collector_id"] = "google-trends-mcp"
    issues = check_registry_references(document, _registries())
    assert "REFERENCE_COLLECTOR_SOURCE_MISMATCH" in _codes(issues)


def test_adapter_mismatch_fails():
    document = _run_document()
    document["collector"]["adapter_id"] = "x-apify-example@999"
    issues = check_registry_references(document, _registries())
    assert "REFERENCE_ADAPTER_MISMATCH" in _codes(issues)


def test_cv06_unregistered_query_fails():
    document = _run_document()
    document["query_provenance"]["query_id"] = "thc-o-acetate-ja"
    issues = check_registry_references(document, _registries())
    assert "REFERENCE_QUERY_UNREGISTERED" in _codes(issues)


def test_compound_mismatch_fails():
    document = _run_document()
    document["query_provenance"]["compound_id"] = "compound_thc"
    issues = check_registry_references(document, _registries())
    assert "REFERENCE_COMPOUND_MISMATCH" in _codes(issues)


def test_deprecated_query_is_informational():
    """Registered-but-deprecated differs from unregistered."""
    document = _run_document()
    document["query_provenance"]["query_id"] = "cbd-liquid-ja"
    document["query_provenance"]["compound_id"] = "compound_cbd"
    issues = check_registry_references(document, _registries())
    by_code = {issue.code: issue for issue in issues}
    assert by_code["QUERY_DEPRECATED_REFERENCE"].severity == "info"
    assert not [issue for issue in issues if issue.severity == "error"]


def test_unregistered_study_fails_when_registry_present():
    document = _run_document()
    document["study_id"] = "does-not-exist"
    issues = check_registry_references(document, _registries())
    assert "REFERENCE_STUDY_UNREGISTERED" in _codes(issues)


def test_empty_registries_skip_reference_checks():
    document = _run_document()
    document["source_id"] = "anything"
    assert check_registry_references(document, Registries()) == []


def test_reference_check_does_not_mutate():
    document = _run_document()
    before = deepcopy(document)
    check_registry_references(document, _registries())
    assert document == before


# ---------------------------------------------------------------------------
# P4-3: capability gate (a.md §9)
# ---------------------------------------------------------------------------


def test_eligible_collectors_only_returns_active_supported():
    eligible = eligible_collectors(
        "x", ["absolute_date_range", "language_filter"], _registries()
    )
    assert [collector["collector_id"] for collector in eligible] == ["x-apify-active"]


def test_eligible_collectors_empty_when_capability_unknown():
    """unknown is not support: automatic selection is not allowed."""
    eligible = eligible_collectors("x", ["stable_item_id"], _registries())
    assert eligible == []


def test_gate_passes_for_active_supported_collector():
    issues = check_capability_gate(
        "x",
        ["absolute_date_range", "language_filter"],
        _registries(),
        requested_collector_id="x-apify-active",
    )
    assert issues == []


def test_gate_refuses_unknown_capability():
    issues = check_capability_gate(
        "x", ["relative_date_range"], _registries(), requested_collector_id="x-apify-active"
    )
    assert _codes(issues) == ["GATE_CAPABILITY_UNKNOWN"]


def test_gate_treats_missing_capability_as_unknown():
    """An absent capability entry must not be read as unsupported (no
    invented capability state)."""
    issues = check_capability_gate(
        "x",
        ["not_recorded_anywhere"],
        _registries(),
        requested_collector_id="x-apify-active",
    )
    assert _codes(issues) == ["GATE_CAPABILITY_UNKNOWN"]


def test_gate_refuses_unsupported_capability():
    issues = check_capability_gate(
        "x", ["stable_item_id"], _registries(), requested_collector_id="x-apify-active"
    )
    assert _codes(issues) == ["GATE_CAPABILITY_UNSUPPORTED"]


def test_gate_refuses_non_active_collector():
    issues = check_capability_gate(
        "x", ["absolute_date_range"], _registries(), requested_collector_id="x-apify-legacy"
    )
    assert _codes(issues) == ["GATE_COLLECTOR_NOT_ACTIVE"]


def test_gate_refuses_when_no_eligible_collector_exists():
    issues = check_capability_gate("x", ["stable_item_id"], _registries())
    assert _codes(issues) == ["GATE_NO_ELIGIBLE_COLLECTOR"]


def test_gate_refuses_unregistered_source():
    issues = check_capability_gate("mastodon", [], _registries())
    assert _codes(issues) == ["GATE_NO_COLLECTOR_FOR_SOURCE"]


def test_gate_accepts_dict_requirements():
    """a.md §9 says implementers may pass requirements as a mapping."""
    issues = check_capability_gate(
        "x",
        {"absolute_date_range": "supported"},
        _registries(),
        requested_collector_id="x-apify-active",
    )
    assert issues == []


# ---------------------------------------------------------------------------
# CV-14 / CV-15: new sources and studies reuse the same contract
# ---------------------------------------------------------------------------


def test_cv14_new_source_is_accepted_once_registered():
    """A fictional source only needs registry entries to be validated by the
    common contract (a.md §15 item 1; CV-14)."""
    base = _registries()
    fictional_source = {
        "source_id": "test-social-platform",
        "kind": "social",
        "measurement_types": ["post_count"],
        "publication_review_required": True,
    }
    fictional_collector = {
        "collector_id": "test-social-example",
        "source_id": "test-social-platform",
        "adapter_id": "test-social-example@1",
        "status": "unverified",
        "capabilities": {"absolute_date_range": "unknown"},
    }
    registries = Registries(
        sources=base.sources + (fictional_source,),
        collectors=base.collectors + (fictional_collector,),
        queries=base.queries,
        studies=base.studies,
    )
    document = _run_document()
    document["source_id"] = "test-social-platform"
    document["collector"] = {
        "collector_id": "test-social-example",
        "adapter_id": "test-social-example@1",
    }
    issues = check_registry_references(document, registries)
    assert [issue for issue in issues if issue.severity == "error"] == []


def test_cv15_new_study_is_accepted_once_registered():
    """A new study passes reference checks after its registry entry exists
    (g.md G7-T19; CV-15)."""
    registries = Registries.from_documents(
        study_registry={
            "schema_version": "1.0.0",
            "studies": [
                {
                    "study_id": "new-study-2026",
                    "title": "New Study",
                    "research_questions": ["q"],
                    "sources": ["x"],
                    "status": "active",
                }
            ],
        }
    )
    document = _run_document()
    document["study_id"] = "new-study-2026"
    assert check_registry_references(document, registries) == []
