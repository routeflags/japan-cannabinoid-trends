"""Contract tests for the G5 provenance slice (e.md §7-§11, §15 G5-T01-T20).

Covers the canonical assessment module (``validation.provenance``), the
``evidence-registry-v1`` schema and its registry wiring, P01 run_id
uniqueness, P17 registry-version traceability, and the G5-T01..T20 mapping
(where a case is owned by an earlier slice's test module, the mapping test
names that owner instead of duplicating it).
"""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.integrity import check_transformation_lineage
from validation.pipeline import validate_full
from validation.provenance import (
    ASSESSMENT_VERSION,
    ESSENTIAL_PROVENANCE_PATHS,
    EVIDENCE_LEVELS,
    READINESS_LEVELS,
    REQUIRED_PROVENANCE_PATHS,
    assess_completeness,
    assess_confidence,
    assess_integrity,
    assess_readiness,
    build_provenance_assessment,
    check_evidence_registry,
    find_duplicate_run_ids,
    get_path,
)
from validation.schema_registry import SCHEMA_REGISTRY, get_schema
from validation.semantic import Registries, check_query_registry_version

FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_document() -> dict:
    return json.loads((FIXTURES / "collection_run_valid.json").read_text(encoding="utf-8"))


def _registries(**overrides):
    base = {
        "query_registry_version": "1.0.0",
    }
    base.update(overrides)
    return Registries(**base)


# ---------------------------------------------------------------------------
# Canonical split (T1): one contract, one builder, one assessor
# ---------------------------------------------------------------------------


def test_evidence_registry_schema_is_registered():
    assert get_schema("evidence-registry-v1") is SCHEMA_REGISTRY["evidence-registry-v1"]
    assert SCHEMA_REGISTRY["evidence-registry-v1"]["schema_version"]["required"] is True


def test_required_paths_cover_the_required_nine_essentials():
    # e.md §4.1 required-9 mapping; canonical table: collection.core.provenance.
    assert len(ESSENTIAL_PROVENANCE_PATHS) == 9
    assert set(ESSENTIAL_PROVENANCE_PATHS) <= set(REQUIRED_PROVENANCE_PATHS)
    assert len(REQUIRED_PROVENANCE_PATHS) == 22


def test_builder_mapping_and_assessor_paths_agree():
    # The assessor mirrors the builder's required-9 table (T1: no fork).
    import collection.core.provenance as builder

    table = builder.__doc__
    for token in ("run_id", "study_id", "source_id", "returned_count", "purpose"):
        assert token in table
    for path in ESSENTIAL_PROVENANCE_PATHS:
        assert get_path(_run_document(), path) is not None


# ---------------------------------------------------------------------------
# §9.1 completeness
# ---------------------------------------------------------------------------


def test_complete_run_scores_full_marks():
    result = assess_completeness(_run_document())
    assert result["total"] == 22
    assert result["verified"] == 22
    assert result["score"] == 1.0
    assert result["missing"] == []
    assert result["essential_missing"] == []


def test_legacy_shape_scores_zero_essentials():
    legacy = {
        "run_id": "20261002T063821Z-google-trends-cbd",
        "study_id": "cannabinoid-multi-trends",
        "source": "google-trends",
    }
    result = assess_completeness(legacy)
    assert result["verified"] == 2  # run_id + study_id only
    assert set(result["essential_missing"]) == set(ESSENTIAL_PROVENANCE_PATHS) - {
        "run_id",
        "study_id",
    }


def test_high_score_never_excuses_missing_essentials():
    document = _run_document()
    del document["purpose"]
    result = assess_completeness(document)
    assert result["score"] > 0.9
    assert result["essential_missing"] == ["purpose"]
    readiness = assess_readiness(
        completeness=result, strict_valid=True, registry_resolvable=True,
        integrity_verified=True,
    )
    assert readiness["readiness"] == "not_ready"


def test_explicit_null_counts_as_unknown():
    document = _run_document()
    document["purpose"] = None
    result = assess_completeness(document)
    assert "purpose" in result["missing"]


# ---------------------------------------------------------------------------
# §9.2 confidence: observed vs unknown, inferred never auto-emitted (P2/P5)
# ---------------------------------------------------------------------------


def test_confidence_levels_are_observed_or_unknown_only():
    for document in (_run_document(), {}, None, []):
        confidence = assess_confidence(document)
        assert set(confidence["fields"].values()) <= {"observed", "unknown"}
        assert set(confidence["fields"]) == set(REQUIRED_PROVENANCE_PATHS)


def test_confidence_vocabulary_reserves_inferred_and_ambiguous():
    assert set(EVIDENCE_LEVELS) == {"observed", "inferred", "unknown", "ambiguous"}
    confidence = assess_confidence({})
    assert "inferred" not in confidence["fields"].values()
    assert "ambiguous" not in confidence["fields"].values()


def test_inferred_is_never_invented_for_legacy_runs():
    # G5-T16: 推定値をobserved扱いにしない (owner: this module).
    legacy = json.loads(
        (
            REPO_ROOT
            / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
            / "20261002T063821Z-google-trends-cbd/run_metadata.json"
        ).read_text(encoding="utf-8")
    )
    confidence = assess_confidence(legacy)
    assert confidence["fields"]["collection_started_at"] == "unknown"
    assert confidence["fields"]["query_provenance.query_id"] == "unknown"


# ---------------------------------------------------------------------------
# §9.3 integrity
# ---------------------------------------------------------------------------


def test_integrity_without_manifest_is_unknown_not_a_pass():
    integrity = assess_integrity({"run_id": "x"})
    assert integrity["verified"] is None
    assert integrity["manifest_present"] is None


def test_integrity_verifies_a_real_manifest(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_bytes(b'{"records": []}')
    manifest = {
        "schema_version": "1.0.0",
        "run_id": "r",
        "artifacts": [
            {
                "artifact_id": "a-1",
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
    (tmp_path / "artifact-manifest.json").write_text(json.dumps(manifest))
    integrity = assess_integrity(
        {"artifact_manifest": "artifact-manifest.json"}, base_dir=tmp_path
    )
    assert integrity["manifest_present"] is True
    assert integrity["manifest_valid"] is True
    assert integrity["verified"] is True

    payload.write_bytes(b'tampered')
    tampered = assess_integrity(
        {"artifact_manifest": "artifact-manifest.json"}, base_dir=tmp_path
    )
    assert tampered["verified"] is False
    assert "ARTIFACT_HASH_MISMATCH" in tampered["artifact_issues"]


# ---------------------------------------------------------------------------
# §9.4 readiness
# ---------------------------------------------------------------------------


def test_readiness_vocabulary():
    assert set(READINESS_LEVELS) == {"ready", "partial", "not_ready", "unknown"}


def test_readiness_ready_requires_all_three_verdicts():
    complete = assess_completeness(_run_document())
    ready = assess_readiness(
        completeness=complete, strict_valid=True,
        registry_resolvable=True, integrity_verified=True,
    )
    assert ready["readiness"] == "ready"


@pytest.mark.parametrize("kwargs", [
    {"registry_resolvable": None, "integrity_verified": True},
    {"registry_resolvable": True, "integrity_verified": None},
    {"registry_resolvable": None, "integrity_verified": None},
])
def test_readiness_unknown_inputs_degrade_to_partial(kwargs):
    complete = assess_completeness(_run_document())
    result = assess_readiness(completeness=complete, strict_valid=True, **kwargs)
    assert result["readiness"] == "partial"
    assert result["reasons"]


def test_readiness_failed_gate_is_not_ready():
    complete = assess_completeness(_run_document())
    result = assess_readiness(
        completeness=complete, strict_valid=False,
        strict_error_codes=["EXECUTION_ERRORS_ON_SUCCESS"],
        registry_resolvable=True, integrity_verified=True,
    )
    assert result["readiness"] == "not_ready"


def test_readiness_without_strict_run_is_unknown():
    complete = assess_completeness(_run_document())
    result = assess_readiness(completeness=complete, strict_valid=None)
    assert result["readiness"] == "unknown"


# ---------------------------------------------------------------------------
# P01 run_id uniqueness
# ---------------------------------------------------------------------------


def test_duplicate_run_ids_are_found():
    duplicates = find_duplicate_run_ids([
        ("a/run_metadata.json", "run-1"),
        ("b/run_metadata.json", "run-2"),
        ("c/run_metadata.json", "run-1"),
        ("d/run_metadata.json", None),
        ("e/run_metadata.json", ""),
    ])
    assert duplicates == {"run-1": ["a/run_metadata.json", "c/run_metadata.json"]}


def test_unique_run_ids_yield_no_duplicates():
    assert find_duplicate_run_ids([("a", "run-1"), ("b", "run-2")]) == {}


def test_validate_study_flags_duplicate_strict_run_ids(tmp_path):
    from validation.cli import main

    for run_dir in ("run-a", "run-b"):
        target = tmp_path / "datasets" / "study-dup" / run_dir
        target.mkdir(parents=True)
        document = _run_document()
        document["run_id"] = "duplicated-run-id"
        # No manifest file in this synthetic study: drop the reference so the
        # duplicate gate (P01) is observed without I/O noise.
        document.pop("artifact_manifest", None)
        (target / "run_metadata.json").write_text(
            json.dumps(document), encoding="utf-8"
        )
    code = main(
        [
            "validate-study",
            "--study", "study-dup",
            "--datasets-root", str(tmp_path / "datasets"),
            "--config-dir", str(REPO_ROOT / "config"),
            "--metadata-dir", str(REPO_ROOT / "metadata"),
            "--format", "json",
            "--output", str(tmp_path / "report.json"),
        ]
    )
    bundle = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert code == 1
    for report in bundle["reports"]:
        assert report["valid"] is False
        assert "RUN_ID_DUPLICATE" in [i["code"] for i in report["issues"]]


# ---------------------------------------------------------------------------
# P17 registry-version traceability (G5-T13)
# ---------------------------------------------------------------------------


def test_matching_registry_version_is_silent():
    assert check_query_registry_version(_run_document(), _registries()) == []


def test_missing_registry_version_is_warning_not_failure():
    document = _run_document()
    del document["query_provenance"]["query_registry_version"]
    issues = check_query_registry_version(document, _registries())
    assert [i.code for i in issues] == ["REGISTRY_VERSION_UNTRACEABLE"]
    assert all(i.severity == "warning" for i in issues)
    outcome = validate_full(
        document, schema_id="collection-run-v1", target="t",
        registries=_registries(),
    )
    assert outcome.valid is True  # 判定不能 never fails the run (G5-T13)
    assert "REGISTRY_VERSION_UNTRACEABLE" in [i.code for i in outcome.issues]


def test_historical_registry_version_is_info():
    document = _run_document()
    document["query_provenance"]["query_registry_version"] = "0.9.0"
    issues = check_query_registry_version(document, _registries())
    assert [i.code for i in issues] == ["REGISTRY_VERSION_HISTORICAL"]
    assert all(i.severity == "info" for i in issues)


def test_absent_query_registry_disables_the_check():
    document = _run_document()
    del document["query_provenance"]["query_registry_version"]
    assert check_query_registry_version(document, Registries()) == []


# ---------------------------------------------------------------------------
# Evidence registry (§11)
# ---------------------------------------------------------------------------


def _evidence_document(tmp_path, *, sha256=None, reference="present.txt") -> dict:
    (tmp_path / "present.txt").write_bytes(b"evidence")
    entry = {
        "evidence_id": "ev-001",
        "evidence_type": "collection_log",
        "reference": reference,
        "observed_at": "2026-10-13T00:00:00Z",
    }
    if sha256 is not None:
        entry["sha256"] = sha256
    return {"schema_version": "1.0.0", "evidence": [entry]}


def test_evidence_registry_seed_is_structurally_valid():
    document = json.loads(
        (REPO_ROOT / "metadata/provenance/evidence-registry.json").read_text(
            encoding="utf-8"
        )
    )
    result = validate_document(document, get_schema("evidence-registry-v1"))
    assert result.valid is True, result.errors


def test_evidence_registry_seed_references_resolve():
    from validation.provenance import check_evidence_registry as check

    document = json.loads(
        (REPO_ROOT / "metadata/provenance/evidence-registry.json").read_text(
            encoding="utf-8"
        )
    )
    issues = check(document, repo_root=REPO_ROOT)
    assert [i.code for i in issues if i.severity == "error"] == []


def test_missing_local_reference_is_an_error(tmp_path):
    document = _evidence_document(tmp_path, reference="absent.txt")
    issues = check_evidence_registry(document, repo_root=tmp_path)
    assert [i.code for i in issues] == ["EVIDENCE_REFERENCE_MISSING"]


def test_hash_mismatch_is_an_error(tmp_path):
    document = _evidence_document(tmp_path, sha256="0" * 64)
    issues = check_evidence_registry(document, repo_root=tmp_path)
    assert [i.code for i in issues] == ["EVIDENCE_HASH_MISMATCH"]


def test_matching_hash_is_silent(tmp_path):
    digest = hashlib.sha256(b"evidence").hexdigest()
    document = _evidence_document(tmp_path, sha256=digest)
    assert check_evidence_registry(document, repo_root=tmp_path) == []


def test_unrecorded_hash_is_info_not_failure(tmp_path):
    document = _evidence_document(tmp_path)
    issues = check_evidence_registry(document, repo_root=tmp_path)
    assert [i.code for i in issues] == ["EVIDENCE_HASH_UNRECORDED"]
    assert all(i.severity == "info" for i in issues)


def test_external_reference_is_info_not_failure(tmp_path):
    document = _evidence_document(
        tmp_path, reference="https://cloud.example/actor-runs/abc123"
    )
    issues = check_evidence_registry(document, repo_root=tmp_path)
    assert [i.code for i in issues] == ["EVIDENCE_REFERENCE_EXTERNAL"]
    assert all(i.severity == "info" for i in issues)


def test_duplicate_evidence_ids_fail(tmp_path):
    document = _evidence_document(tmp_path)
    document["evidence"].append(deepcopy(document["evidence"][0]))
    issues = check_evidence_registry(document, repo_root=tmp_path)
    assert "EVIDENCE_ID_DUPLICATE" in [i.code for i in issues]


def test_evidence_registry_rejects_unknown_types(tmp_path):
    document = _evidence_document(tmp_path)
    document["evidence"][0]["evidence_type"] = "platform-x-export"
    result = validate_document(document, get_schema("evidence-registry-v1"))
    assert result.valid is False  # source-specific types need a schema bump (§19)


def test_evidence_registry_allows_null_hash_but_not_bad_hash(tmp_path):
    document = _evidence_document(tmp_path)
    document["evidence"][0]["sha256"] = None
    assert validate_document(
        document, get_schema("evidence-registry-v1")
    ).valid is True
    document["evidence"][0]["sha256"] = "not-a-hash"
    assert validate_document(
        document, get_schema("evidence-registry-v1")
    ).valid is False


# ---------------------------------------------------------------------------
# Transformation lineage wiring (G5-T17)
# ---------------------------------------------------------------------------


def test_transformation_lineage_failure_codes_are_stable():
    transformation = json.loads(
        (FIXTURES / "transformation.json").read_text(encoding="utf-8")
    )
    issues = check_transformation_lineage(
        transformation, known_artifact_ids=frozenset()
    )
    assert "LINEAGE_REFERENCE_MISSING" in [i.code for i in issues]
    resolved = check_transformation_lineage(
        transformation, known_artifact_ids=frozenset({"artifact-001", "monthly-counts-001"})
    )
    assert resolved == []


# ---------------------------------------------------------------------------
# audit-provenance command (non-destructive, §10)
# ---------------------------------------------------------------------------


def test_audit_provenance_is_non_destructive(tmp_path):
    from validation.cli import main

    run_dir = tmp_path / "datasets" / "study-p" / "run-a"
    run_dir.mkdir(parents=True)
    before_doc = _run_document()
    (run_dir / "run_metadata.json").write_text(
        json.dumps(before_doc), encoding="utf-8"
    )
    before_hash = hashlib.sha256(
        (run_dir / "run_metadata.json").read_bytes()
    ).hexdigest()
    output = tmp_path / "assessment.json"
    code = main(
        [
            "audit-provenance",
            "--datasets-root", str(tmp_path / "datasets"),
            "--config-dir", str(REPO_ROOT / "config"),
            "--metadata-dir", str(REPO_ROOT / "metadata"),
            "--output", str(output),
        ]
    )
    assert code == 0
    assessment = json.loads(output.read_text(encoding="utf-8"))
    assert assessment["assessment_version"] == ASSESSMENT_VERSION
    assert assessment["count"] == 1
    assert assessment["raw_modified"] is False
    entry = assessment["runs"][0]
    assert entry["sha256"] == before_hash
    assert entry["sha256_after"] == before_hash
    assert entry["unchanged"] is True
    assert entry["completeness"]["score"] == 1.0
    assert (run_dir / "run_metadata.json").read_text(encoding="utf-8") == json.dumps(
        before_doc
    )


def test_audit_provenance_marks_legacy_unknowns(tmp_path):
    run_dir = tmp_path / "datasets" / "study-p" / "run-old"
    run_dir.mkdir(parents=True)
    (run_dir / "run_metadata.json").write_text(
        json.dumps({"run_id": "old", "study_id": "s", "source": "x"}),
        encoding="utf-8",
    )
    assessment = build_provenance_assessment(tmp_path / "datasets", registries=None)
    assert assessment["count"] == 1
    assert assessment["raw_modified"] is False
    entry = assessment["runs"][0]
    assert entry["readiness"] == "not_ready"
    assert entry["strict_valid"] is False
    assert entry["confidence"]["fields"]["collector.collector_id"] == "unknown"
    assert "inferred" not in set(entry["confidence"]["fields"].values())


def test_audit_provenance_reports_unreadable_as_unknown(tmp_path):
    run_dir = tmp_path / "datasets" / "study-p" / "run-broken"
    run_dir.mkdir(parents=True)
    (run_dir / "run_metadata.json").write_text("{broken", encoding="utf-8")
    assessment = build_provenance_assessment(tmp_path / "datasets", registries=None)
    entry = assessment["runs"][0]
    assert entry["readiness"] == "unknown"
    assert entry["strict_valid"] is None
    assert assessment["raw_modified"] is False


# ---------------------------------------------------------------------------
# G5-T01..T20 mapping (unreached cases name their owner or defer explicitly)
# ---------------------------------------------------------------------------


def test_g5_t_mapping_table():
    """Each §15 case resolves to a test or a documented deferral.

    Owner modules hold the behavior; this table guards the mapping itself.
    G5-T13/T16/T17-critical paths are asserted above in this module.
    """
    mapping = {
        "G5-T01": "tests/validation/test_collection_run.py (run_id missing → FAIL)",
        "G5-T02": "tests/validation/test_collection_run.py (study_id missing → FAIL)",
        "G5-T03": "tests/validation/test_references.py (source unregistered → FAIL)",
        "G5-T04": "tests/validation/test_references.py (collector unregistered → FAIL)",
        "G5-T05": "tests/validation/test_references.py (query unregistered → FAIL)",
        "G5-T06": "tests/validation/test_collection_run.py (submitted_query missing → FAIL)",
        "G5-T07": "tests/validation/test_semantic.py (bad collection datetime → FAIL)",
        "G5-T08": "tests/validation/test_semantic.py (finish before start → FAIL)",
        "G5-T09": "tests/validation/test_collection_run.py (negative count → FAIL)",
        "G5-T10": "tests/validation/test_semantic.py (error-state inconsistency → FAIL)",
        "G5-T11": "tests/validation/test_gates.py (manifest missing → quarantine)",
        "G5-T12": "tests/validation/test_pipeline.py + test_provenance.py (hash mismatch → FAIL)",
        "G5-T13": "test_provenance.py::test_missing_registry_version_is_warning_not_failure (判定不能)",
        "G5-T14": "tests/validation/test_semantic.py (secret scan) + test_provenance.py (registry scan)",
        "G5-T15": "test_provenance.py::test_audit_provenance_marks_legacy_unknowns (unknown)",
        "G5-T16": "test_provenance.py::test_inferred_is_never_invented_for_legacy_runs (FAIL if observed)",
        "G5-T17": "test_provenance.py::test_transformation_lineage_failure_codes_are_stable (FAIL)",
        "G5-T18": "test_provenance.py::test_audit_provenance_is_non_destructive (変更なし)",
        "G5-T19": "deferred: no new source in this slice (contract is source-agnostic by construction)",
        "G5-T20": "test_provenance.py lineage edges (参照欠落 → LINEAGE_REFERENCE_MISSING)",
    }
    assert len(mapping) == 20
    import re

    for case, owner in mapping.items():
        assert re.match(r"G5-T\d{2}", case)
        assert owner, case
    # deferred cases stay explicit and countable
    deferred = [c for c, o in mapping.items() if o.startswith("deferred")]
    assert deferred == ["G5-T19"]
