"""G1 L1-06/L1-07/L1-09 tests: raw evidence, hash, missingness, completeness.

Covers ``validation.semantic.check_missingness_consistency`` and the
``validation.gates.post_collection_gate`` L1 additions.
"""

import hashlib
import json
from pathlib import Path

from validation.gates import post_collection_gate
from validation.semantic import check_missingness_consistency

FIXTURES = Path(__file__).parent / "fixtures"
RUN_ID = "20261013T000000Z-x-cbx-001"


def _document(**execution_overrides) -> dict:
    document = json.loads(
        (FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8")
    )
    document["execution"].update(execution_overrides)
    return document


def _manifest(
    *,
    completeness: str = "complete",
    record_count=None,
    layer: str = "raw",
    run_id: str = RUN_ID,
) -> dict:
    artifact = {
        "artifact_id": "artifact-001",
        "path": "payload.json",
        "artifact_type": "raw_response",
        "format": "json",
        "schema_id": "raw-response-v1",
        "byte_length": 1,
        "sha256": "0" * 64,
        "layer": layer,
        "completeness": completeness,
    }
    if record_count is not None:
        artifact["record_count"] = record_count
    return {"schema_version": "1.0.0", "run_id": run_id, "artifacts": [artifact]}


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


# ---------------------------------------------------------------------------
# check_missingness_consistency
# ---------------------------------------------------------------------------


def test_running_runs_are_not_graded():
    document = _document(status="running")
    assert check_missingness_consistency(document, None) == []


def test_terminal_run_without_manifest_has_no_evidence():
    document = _document(status="success", returned_count=52)
    codes = _codes(check_missingness_consistency(document, None))
    assert codes == ["MISSINGNESS_RAW_EVIDENCE_MISSING"]


def test_manifest_without_raw_artifacts_has_no_evidence():
    document = _document(status="success", returned_count=52)
    manifest = _manifest(layer="processed")
    codes = _codes(check_missingness_consistency(document, manifest))
    assert codes == ["MISSINGNESS_RAW_EVIDENCE_MISSING"]


def test_success_with_complete_artifacts_is_accepted():
    document = _document(status="success", returned_count=52)
    assert check_missingness_consistency(document, _manifest()) == []


def test_zero_observations_require_record_count_evidence():
    document = _document(status="success", returned_count=0)
    codes = _codes(check_missingness_consistency(document, _manifest()))
    assert codes == ["MISSINGNESS_ZERO_WITHOUT_EVIDENCE"]


def test_zero_observations_with_record_count_zero_are_accepted():
    document = _document(status="success", returned_count=0)
    manifest = _manifest(record_count=0)
    assert check_missingness_consistency(document, manifest) == []


def test_success_with_partial_raw_artifact_is_inconsistent():
    document = _document(status="success", returned_count=52)
    codes = _codes(check_missingness_consistency(document, _manifest(completeness="partial")))
    assert codes == ["COMPLETENESS_INCONSISTENT_WITH_SUCCESS"]


def test_partial_run_may_carry_partial_artifacts():
    document = _document(status="partial")
    manifest = _manifest(completeness="partial")
    assert check_missingness_consistency(document, manifest) == []


def test_failed_run_requires_error_evidence():
    document = _document(status="failed", returned_count=0, errors=[])
    codes = _codes(check_missingness_consistency(document, _manifest(completeness="missing")))
    assert codes == ["COLLECTION_FAILED_WITHOUT_ERROR_EVIDENCE"]


def test_failed_run_with_errors_is_recorded_honestly():
    document = _document(status="failed", returned_count=0, errors=[{"code": "X"}])
    assert check_missingness_consistency(document, _manifest(completeness="missing")) == []


# ---------------------------------------------------------------------------
# post_collection_gate (L1 adoption decision)
# ---------------------------------------------------------------------------


def _write_run(tmp_path: Path, document: dict, *, payload=b'{"records": []}', manifest=None):
    (tmp_path / "payload.json").write_bytes(payload)
    if manifest is None:
        manifest = _manifest()
    # Keep the manifest honest towards the written payload; tests that want a
    # hash mismatch pass a prepared payload/manifest pair explicitly.
    manifest["artifacts"][0]["byte_length"] = len(payload)
    manifest["artifacts"][0]["sha256"] = hashlib.sha256(payload).hexdigest()
    (tmp_path / "artifact-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    document["artifact_manifest"] = "artifact-manifest.json"
    return document


def test_gate_quarantines_terminal_run_without_artifact_evidence(tmp_path):
    document = json.loads(
        (FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8")
    )
    document.pop("artifact_manifest", None)
    result = post_collection_gate(document, base_dir=tmp_path)
    assert result.passed is False
    assert result.action == "quarantine"
    assert "MISSINGNESS_RAW_EVIDENCE_MISSING" in _codes(result.issues)


def test_gate_catalogs_zero_run_with_evidence(tmp_path):
    document = _document(
        status="success", returned_count=0, errors=[], pagination_exhausted=True
    )
    document = _write_run(
        tmp_path, document, payload=b'{"data": []}', manifest=_manifest(record_count=0)
    )
    result = post_collection_gate(document, base_dir=tmp_path)
    assert result.passed is True, [i.to_dict() for i in result.issues]
    assert result.action == "catalog"


def test_gate_quarantines_zero_run_without_evidence(tmp_path):
    document = _document(
        status="success", returned_count=0, errors=[], pagination_exhausted=True
    )
    document = _write_run(tmp_path, document, payload=b'{"data": []}')
    result = post_collection_gate(document, base_dir=tmp_path)
    assert result.action == "quarantine"
    assert "MISSINGNESS_ZERO_WITHOUT_EVIDENCE" in _codes(result.issues)


def test_gate_quarantines_a_failed_run(tmp_path):
    document = _document(
        status="failed", returned_count=0, errors=[{"code": "X"}]
    )
    document = _write_run(
        tmp_path, document, payload=b'{"error": {}}', manifest=_manifest(completeness="missing", run_id=RUN_ID)
    )
    result = post_collection_gate(document, base_dir=tmp_path)
    assert result.action == "quarantine"
    assert "COLLECTION_FAILED_NOT_ADOPTED" in _codes(result.issues)


def test_gate_quarantines_a_manifest_from_another_run(tmp_path):
    document = _document(status="partial")
    manifest = _manifest(run_id="20261014T000000Z-x-other")
    document = _write_run(tmp_path, document, manifest=manifest)
    result = post_collection_gate(document, base_dir=tmp_path)
    assert result.action == "quarantine"
    assert "MANIFEST_RUN_ID_MISMATCH" in _codes(result.issues)


def test_gate_ignores_manifest_comparisons_without_base_dir():
    """Without a base directory nothing can be verified: fail closed for
    terminal runs (the caller must provide the run directory).
    """
    document = _document(status="success", returned_count=52)
    result = post_collection_gate(document)
    assert result.action == "quarantine"
    assert "MISSINGNESS_RAW_EVIDENCE_MISSING" in _codes(result.issues)
