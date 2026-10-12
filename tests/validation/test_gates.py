"""Collection gate tests (Phase 6: P6-1 / P6-2).
"""

import hashlib
import json
from pathlib import Path

from validation.gates import post_collection_gate, pre_collection_gate
from validation.semantic import Registries

FIXTURES = Path(__file__).parent / "fixtures"
REGISTRIES = FIXTURES / "registries"


def _load(name: str, base: Path = FIXTURES) -> dict:
    return json.loads((base / name).read_text(encoding="utf-8"))


def _registries() -> Registries:
    return Registries.from_documents(
        source_registry=_load("sources.json", REGISTRIES),
        collector_registry=_load("collectors.json", REGISTRIES),
        query_registry=_load("queries.json", REGISTRIES),
        study_registry=_load("study-registry.json", REGISTRIES),
    )


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


# ---------------------------------------------------------------------------
# P6-1: pre-collection gate
# ---------------------------------------------------------------------------


def test_plan_gate_passes_for_eligible_plan():
    result = pre_collection_gate(_load("collection_plan.json"), registries=_registries())
    assert result.passed is True
    assert result.action == "proceed"
    assert result.issues == []


def test_plan_gate_fail_closed_for_unknown_capability():
    plan = _load("collection_plan.json")
    plan["collector_id"] = "x-apify-example"  # all capabilities unverified
    result = pre_collection_gate(plan, registries=_registries())
    assert result.passed is False
    assert result.action == "stop"
    assert "GATE_CAPABILITY_UNKNOWN" in _codes(result.issues)


def test_plan_gate_refuses_unregistered_collector():
    plan = _load("collection_plan.json")
    plan["collector_id"] = "ghost-collector"
    result = pre_collection_gate(plan, registries=_registries())
    assert result.passed is False
    assert "GATE_COLLECTOR_UNREGISTERED" in _codes(result.issues)


def test_plan_gate_refuses_unregistered_query():
    plan = _load("collection_plan.json")
    plan["query_id"] = "not-registered"
    result = pre_collection_gate(plan, registries=_registries())
    assert result.passed is False
    assert "REFERENCE_QUERY_UNREGISTERED" in _codes(result.issues)


def test_plan_gate_checks_window_ordering():
    plan = _load("collection_plan.json")
    plan["window"]["end_exclusive"] = plan["window"]["start"]
    result = pre_collection_gate(plan, registries=_registries())
    assert result.passed is False
    assert "TEMPORAL_ORDER_INVALID" in _codes(result.issues)


def test_plan_gate_rejects_non_mapping():
    result = pre_collection_gate([], registries=_registries())
    assert result.passed is False
    assert result.action == "stop"


def test_plan_gate_without_registries_still_checks_structure_less_rules():
    """With no registries available there is no collector to refuse on; the
    gate must not invent failures."""
    result = pre_collection_gate(_load("collection_plan.json"), registries=Registries())
    assert result.passed is True


# ---------------------------------------------------------------------------
# P6-2: post-collection gate
# ---------------------------------------------------------------------------


def test_post_gate_catalogs_valid_run(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_bytes(b'{"records": []}')
    manifest = {
        "schema_version": "1.0.0",
        "run_id": "20261013T000000Z-x-cbx-001",
        "artifacts": [
            {
                "artifact_id": "artifact-001",
                "path": "payload.json",
                "artifact_type": "raw_records",
                "format": "json",
                "schema_id": "social-post-v1",
                "byte_length": payload.stat().st_size,
                "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
                "layer": "raw",
                "completeness": "complete",
            }
        ],
    }
    (tmp_path / "artifact-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    document = _load("collection_run_valid.json")
    document["artifact_manifest"] = "artifact-manifest.json"

    result = post_collection_gate(
        document, registries=_registries(), base_dir=tmp_path
    )
    assert result.passed is True
    assert result.action == "catalog"


def test_post_gate_quarantines_on_integrity_failure(tmp_path):
    document = _load("collection_run_valid.json")
    document["artifact_manifest"] = "missing-manifest.json"
    result = post_collection_gate(
        document, registries=_registries(), base_dir=tmp_path
    )
    assert result.passed is False
    assert result.action == "quarantine"
    assert "ARTIFACT_MANIFEST_MISSING" in _codes(result.issues)


def test_post_gate_quarantines_on_semantic_failure(tmp_path):
    document = _load("collection_run_valid.json")
    document["execution"]["returned_count"] = -1  # structural would catch
    document["execution"]["status"] = "success"
    document["execution"]["errors"] = ["boom"]
    result = post_collection_gate(document, registries=_registries(), base_dir=tmp_path)
    assert result.passed is False
    assert result.action == "quarantine"


def test_gate_result_serializes():
    result = pre_collection_gate(_load("collection_plan.json"), registries=_registries())
    data = result.to_dict()
    assert data == {"passed": True, "action": "proceed", "issues": []}
