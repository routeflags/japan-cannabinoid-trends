"""Reconciliation-pass tests (ISS-20261015-PRV-011).

Contract sources: ``docs/specs/validation-framework.md`` §18.3 (the missing
pass), ``docs/provenance/evidence-hash-policy.md`` (the hash policy),
``validation.provenance`` (unknowns are never promoted there; they are not
promoted here either).

The decisive tests are :func:`test_reconciliation_never_promotes` (the output
vocabulary contains no ``observed`` / ``inferred`` / ``ambiguous`` and the
inputs are unmutated) and :func:`test_real_registry_disposition_is_explicit`
(the 7 info-level ``EVIDENCE_HASH_UNRECORDED`` entries are each classified
with their owner action instead of being resolved by fabrication).
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from validation.evidence_reconciliation import (
    RECONCILIATION_VERSION,
    classify_hash_status,
    covered_paths,
    reconcile_evidence,
    unknowns_from_assessment,
)
from validation.provenance import check_evidence_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "metadata/provenance/evidence-registry.json"


def _entry(evidence_id, evidence_type, reference, sha256=None):
    entry = {
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "reference": reference,
        "observed_at": "2026-10-15T00:00:00Z",
    }
    if sha256 is not None:
        entry["sha256"] = sha256
    return entry


def _registry(*entries):
    return {"schema_version": "1.0.0", "evidence": list(entries)}


# ---------------------------------------------------------------------------
# coverage mapping: narrow by construction
# ---------------------------------------------------------------------------


def test_only_mapped_registry_definitions_cover(tmp_path):
    (tmp_path / "sources.json").write_text("{}", encoding="utf-8")
    assert covered_paths(
        _entry("a", "registry_definition", "config/sources.json")
    ) == ("source_id",)
    # Same reference shape, wrong type: context, not coverage.
    assert covered_paths(
        _entry("b", "audit_report", "config/sources.json")
    ) == ()
    # Taxonomy / fixtures / audit reports never cover a required run path.
    assert covered_paths(
        _entry("c", "taxonomy", "metadata/taxonomy/x.json")
    ) == ()
    assert covered_paths(
        _entry("d", "test_fixture", "tests/fixture.json")
    ) == ()
    # External references are recorded but never covering (unverifiable).
    assert covered_paths(
        _entry("e", "actor_run", "https://cloud.example/runs/1")
    ) == ()
    assert covered_paths(
        _entry("f", "registry_definition", "config/sources.json")
    ) == ("source_id",)  # type-gated, not reference-gated


def test_window_documents_cover_temporal_paths():
    paths = covered_paths(
        _entry("w", "registry_definition", "metadata/windows/2025-10-12_2026-10-12.json")
    )
    assert "temporal_provenance.window_id" in paths
    assert "temporal_provenance.timezone" in paths


# ---------------------------------------------------------------------------
# the pass itself: candidates only, never promotions
# ---------------------------------------------------------------------------


def test_reconciliation_never_promotes(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "sources.json").write_text("{}", encoding="utf-8")
    registry = _registry(
        _entry("ev-src", "registry_definition", "config/sources.json"),
    )
    unknowns = [
        {
            "run_id": "run-1",
            "run_path": "datasets/s/run-1/run_metadata.json",
            "unknown_paths": ["source_id", "purpose"],
        }
    ]
    before_registry, before_unknowns = deepcopy(registry), deepcopy(unknowns)
    report = reconcile_evidence(registry, unknowns, repo_root=tmp_path)

    assert registry == before_registry and unknowns == before_unknowns
    assert report["reconciliation_version"] == RECONCILIATION_VERSION
    assert report["candidate_count"] == 1
    (candidate,) = report["candidates"]
    assert candidate["unknown_path"] == "source_id"
    assert candidate["evidence_id"] == "ev-src"
    assert candidate["verdict"] == "candidate"
    assert "do not auto-apply" in candidate["action"]
    assert report["uncovered_count"] == 1
    assert report["uncovered"][0]["unknown_path"] == "purpose"
    assert report["uncovered"][0]["verdict"] == "no_covering_evidence"
    # The forbidden vocabulary appears nowhere as a verdict or level:
    # every finding is a candidate or an explicit non-match.
    verdicts = {item["verdict"] for item in report["candidates"] + report["uncovered"]}
    assert verdicts <= {"candidate", "no_covering_evidence"}


def test_missing_reference_cannot_evidence(tmp_path):
    registry = _registry(
        _entry("ev-src", "registry_definition", "config/sources.json"),
    )
    unknowns = [{"run_id": "r", "run_path": "p", "unknown_paths": ["source_id"]}]
    report = reconcile_evidence(registry, unknowns, repo_root=tmp_path)
    assert report["candidate_count"] == 0
    assert report["uncovered"][0]["verdict"] == "no_covering_evidence"


def test_unrecorded_hash_is_a_caveat_not_a_blocker(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "collectors.json").write_text("{}", encoding="utf-8")
    registry = _registry(
        _entry("ev-col", "registry_definition", "config/collectors.json"),
    )
    unknowns = [
        {"run_id": "r", "run_path": "p", "unknown_paths": ["collector.collector_id"]}
    ]
    (candidate,) = reconcile_evidence(
        registry, unknowns, repo_root=tmp_path
    )["candidates"]
    assert candidate["hash_status"] == "needs_witnessed_observation"
    assert "Integrity unverified" in candidate["action"]
    assert candidate["verdict"] == "candidate"  # still a candidate, not a promotion


def test_unknowns_extracted_from_assessment_shape():
    assessment = {
        "runs": [
            {
                "run_id": "r1",
                "path": "p1",
                "confidence": {"fields": {"source_id": "observed", "purpose": "unknown"}},
            },
            {"run_id": "r2", "path": "p2", "confidence": {"fields": {}}},
        ]
    }
    assert unknowns_from_assessment(assessment) == [
        {"run_id": "r1", "run_path": "p1", "unknown_paths": ["purpose"]}
    ]
    assert unknowns_from_assessment({}) == []
    assert unknowns_from_assessment({"runs": None}) == []


# ---------------------------------------------------------------------------
# the real registry: 7 unrecorded entries stay explicit, not fabricated
# ---------------------------------------------------------------------------


def _load_real_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_real_registry_disposition_is_explicit():
    """1 pinned, 1 regenerated, 6 awaiting witnessed observation."""

    registry = _load_real_registry()
    statuses = {
        entry["evidence_id"]: classify_hash_status(entry, repo_root=REPO_ROOT)
        for entry in registry["evidence"]
    }
    assert statuses["ev-replay-fixture-12m"] == "pinned"
    assert statuses["ev-legacy-audit-20261013"] == "regenerated_output"
    assert [key for key, value in statuses.items() if value == "needs_witnessed_observation"] == [
        "ev-source-registry",
        "ev-collector-registry",
        "ev-query-registry",
        "ev-compound-taxonomy",
        "ev-window-2025-2026",
        "ev-artifact-registry",
    ]
    # The disposition agrees with the checker: info only, no error.
    codes = [issue.code for issue in check_evidence_registry(registry, repo_root=REPO_ROOT)]
    assert codes.count("EVIDENCE_HASH_UNRECORDED") == 7
    assert all(
        issue.severity != "error"
        for issue in check_evidence_registry(registry, repo_root=REPO_ROOT)
    )


def test_real_registry_reconciliation_names_owner_actions():
    registry = _load_real_registry()
    before_hash = hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest()
    unknowns = [
        {
            "run_id": "legacy-run",
            "run_path": "datasets/legacy/run/run_metadata.json",
            "unknown_paths": [
                "source_id",
                "collector.collector_id",
                "query_provenance.query_id",
                "temporal_provenance.window_id",
                "purpose",
            ],
        }
    ]
    report = reconcile_evidence(registry, unknowns, repo_root=REPO_ROOT)
    by_path = {item["unknown_path"]: item for item in report["candidates"]}
    assert by_path["source_id"]["evidence_id"] == "ev-source-registry"
    assert by_path["collector.collector_id"]["evidence_id"] == "ev-collector-registry"
    assert by_path["query_provenance.query_id"]["evidence_id"] == "ev-query-registry"
    assert by_path["temporal_provenance.window_id"]["evidence_id"] == "ev-window-2025-2026"
    for item in report["candidates"]:
        assert item["hash_status"] == "needs_witnessed_observation"
        assert item["verdict"] == "candidate"
    assert [item["unknown_path"] for item in report["uncovered"]] == ["purpose"]
    # Read-only: the registry file is byte-identical afterwards.
    assert hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest() == before_hash
