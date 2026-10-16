"""G6 vertical slice contract tests (§16/§17/§18, P1-P8).

Covers the slice actually shipped (not the full §19 list):

- ``config/storage-policies.json`` exists, validates against
  ``storage-policy-registry-v1`` and carries no dangerous blanket file
  patterns (G6-T01/T02 + §6 scope guard);
- git tracking inventory is non-destructive and classifies tracked /
  ignored / untracked_unignored / absent without reading private values
  (G6-T04/T05/T06/T14/T15 + P8);
- publication eligibility maps §10.2 PUB-01..PUB-10 to
  SUPPORTED / CONDITIONAL / BLOCKED record-only verdicts, reusing the §11
  minimal rule (G6-T03/T07/T08/T09/T11);
- secret scan refuses publication without emitting values (G6-T10);
- private catalog records existence only (G6-T17);
- local filesystem backend refuses overwrites (G6-T18).

Release manifest / Zenodo checks (G6-T12/T13/T19/T20) and new-source
coverage (G6-T16) are explicitly out of this slice (see module docstring
and ``docs/specs/validation-framework.md`` §19).
"""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from validation.core import validate_document
from validation.g6_inventory import (
    KNOWN_LOCAL_ONLY_PATHS,
    build_git_tracking_inventory,
    classify_path,
)
from validation.private_catalog import build_private_catalog
from validation.publication_eligibility import evaluate_eligibility
from validation.schema_registry import get_schema
from validation.storage_policy import (
    can_publish,
    check_git_tracking,
    check_publication,
    select_policy,
)
from storage.backend import BackendOverwriteRefused, LocalFilesystemBackend

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / "config" / "storage-policies.json"


def _registry() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Storage Policy Registry (§6)
# ---------------------------------------------------------------------------


def test_storage_policy_registry_file_validates():
    document = _registry()
    schema = get_schema("storage-policy-registry-v1")
    result = validate_document(document, schema)
    assert result.valid is True, result.errors


def test_storage_policy_ids_unique_and_scoped():
    document = _registry()
    ids = [policy["policy_id"] for policy in document["policies"]]
    assert len(ids) == len(set(ids))  # G6-T02
    layers = {policy["artifact_layer"] for policy in document["policies"]}
    assert {"raw", "interim", "processed", "metadata"} <= layers
    # No policy carries file globs: the registry declares layer/kind axes
    # only, so a blanket "*.csv" exclusion cannot hide here.
    blob = json.dumps(document)
    for pattern in ("*.csv", "*.json", "**"):
        assert pattern not in blob


def test_storage_policy_select_covers_each_layer():
    registry = _registry()
    assert select_policy(registry, artifact_layer="raw", source_kind="social") is not None  # G6-T01 negative
    assert select_policy(registry, artifact_layer="interim", source_kind="any") is not None
    assert select_policy(registry, artifact_layer="processed", source_kind="search") is not None
    assert select_policy(registry, artifact_layer="metadata", source_kind="tiktok") is not None  # wildcard covers new kinds
    assert select_policy(registry, artifact_layer="bronze", source_kind="any") is None  # G6-T01: unknown layer FAILs


def test_new_source_kind_resolves_through_wildcard_g6_t16():
    """A future source kind (e.g. LinkedIn/social) resolves via ``any``."""
    registry = _registry()
    policy = select_policy(registry, artifact_layer="processed", source_kind="linkedin")
    assert policy is not None and policy["source_kind"] == "any"


# ---------------------------------------------------------------------------
# Git tracking inventory (§15; read-only)
# ---------------------------------------------------------------------------


def test_git_inventory_is_non_destructive_and_classifies():
    before = {path: sha256(path.read_bytes()).hexdigest() for path in REPO_ROOT.rglob("datasets/**/run_metadata.json")}
    inventory = build_git_tracking_inventory(REPO_ROOT)
    assert inventory["raw_modified"] is False  # G6-T15: legacy raw unchanged
    after = {path: sha256(path.read_bytes()).hexdigest() for path in REPO_ROOT.rglob("datasets/**/run_metadata.json")}
    assert before == after
    assert inventory["count"] > 0
    assert "tracked" in inventory["state_summary"]
    # google-trends raw stays tracked (the .gitignore exception): the
    # inventory reports reality, it does not change tracking.
    tracked = [entry["path"] for entry in inventory["entries"] if entry["state"] == "tracked"]
    assert any("google_trends" in path for path in tracked)


def test_git_inventory_absent_is_not_zero_p8():
    inventory = build_git_tracking_inventory(REPO_ROOT)
    states = {extra["path"]: extra["state"] for extra in inventory["extras"]}
    # Paths that do not exist in this checkout are "absent", never a zero
    # count or a fabricated hash.
    for relative in KNOWN_LOCAL_ONLY_PATHS:
        if not (REPO_ROOT / relative).exists():
            assert states[relative] == "absent"
            record = next(extra for extra in inventory["extras"] if extra["path"] == relative)
            assert "sha256" not in record


def test_git_inventory_private_contents_never_read():
    inventory = build_git_tracking_inventory(REPO_ROOT)
    for entry in inventory["entries"]:
        assert "private" not in Path(entry["path"]).parts
    for extra in inventory["extras"]:
        if extra.get("kind") == "private_marker":
            assert set(extra) <= {"path", "exists", "state", "tracked", "ignored", "kind"}


def test_gitignore_has_no_blanket_file_pattern():
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    scoped = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("!")]
    for pattern in ("*.csv", "*.json"):
        assert pattern not in scoped


def test_classify_path_read_only_smoke():
    record = classify_path(REPO_ROOT, "pyproject.toml")
    assert record == {"path": "pyproject.toml", "exists": True, "state": "tracked", "tracked": True, "ignored": False}


# ---------------------------------------------------------------------------
# Publication eligibility gate (§10; record-only)
# ---------------------------------------------------------------------------


def _artifact(sha: str = "a" * 64) -> dict:
    return {"artifact_id": "artifact-001", "sha256": sha}


def _approved(sha: str = "a" * 64) -> dict:
    return {
        "decision_id": "review-001",
        "artifact_id": "artifact-001",
        "status": "approved",
        "reviewed_at": "2026-10-13T00:00:00Z",
        "reviewer": "reviewer-001",
        "criteria_version": "1.0.0",
        "evidence": [],
        "notes": "ok",
        "artifact_sha256": sha,
    }


def _full_evidence() -> dict:
    return {
        "provenance_present": True,
        "integrity": "verified",
        "schema_valid": True,
        "personal_data_reviewed": True,
        "source_terms_confirmed": True,
        "redistribution_confirmed": True,
        "copyright_confirmed": True,
        "anonymization_applied": True,
    }


def test_unknown_publication_is_refused_g6_t03():
    result = evaluate_eligibility(_artifact(), None, evidence=_full_evidence())
    assert result["verdict"] == "BLOCKED"
    assert "PUB-10" in result["failed"]
    assert can_publish(_artifact(), None) is False


def test_missing_decision_is_blocked_g6_t07():
    result = evaluate_eligibility(_artifact(), None, evidence={})
    assert result["verdict"] == "BLOCKED"
    assert check_publication(_artifact(), None)[0].code == "PUBLICATION_DECISION_MISSING"


def test_unapproved_decision_is_blocked_g6_t08():
    decision = _approved()
    decision["status"] = "requires_review"
    result = evaluate_eligibility(_artifact(), decision, evidence=_full_evidence())
    assert result["verdict"] == "BLOCKED"
    assert "PUB-10" in result["failed"]


def test_changed_hash_invalidates_approval_g6_t09():
    artifact = _artifact("b" * 64)
    result = evaluate_eligibility(artifact, _approved("a" * 64), evidence=_full_evidence())
    assert result["verdict"] == "BLOCKED"
    assert "PUB-10" in result["failed"]


def test_unreviewed_personal_data_blocks_g6_t11():
    evidence = _full_evidence()
    evidence["personal_data_reviewed"] = False
    result = evaluate_eligibility(_artifact(), _approved(), evidence=evidence)
    assert result["verdict"] == "BLOCKED"
    assert "PUB-04" in result["failed"]


def test_warnings_only_yield_conditional():
    evidence = _full_evidence()
    evidence.update({"source_terms_confirmed": None, "redistribution_confirmed": None, "copyright_confirmed": None})
    result = evaluate_eligibility(_artifact(), _approved(), evidence=evidence)
    assert result["verdict"] == "CONDITIONAL"
    assert result["failed"] == []
    assert set(result["warnings"]) == {"PUB-06", "PUB-07", "PUB-08"}


def test_full_approval_yields_supported():
    result = evaluate_eligibility(_artifact(), _approved(), evidence=_full_evidence())
    assert result["verdict"] == "SUPPORTED"
    assert result["failed"] == [] and result["warnings"] == []


def test_secret_values_are_never_emitted_g6_t10():
    evidence = _full_evidence()
    evidence["notes"] = "token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
    result = evaluate_eligibility(_artifact(), _approved(), evidence=evidence)
    assert result["verdict"] == "BLOCKED"
    assert "PUB-05" in result["failed"]
    assert "ghp_" not in json.dumps(result)


def test_eligibility_is_non_destructive():
    artifact, decision, evidence = _artifact(), _approved(), _full_evidence()
    before = (deepcopy(artifact), deepcopy(decision), deepcopy(evidence))
    evaluate_eligibility(artifact, decision, evidence=evidence)
    assert (artifact, decision, evidence) == before


# ---------------------------------------------------------------------------
# Private catalog (§13; existence only)
# ---------------------------------------------------------------------------


def test_private_catalog_default_is_committed_safe_g6_t17(tmp_path):
    """Default output must not leak this checkout's disk state (ISS-20261016-MNT-002).

    ``datasets/*/data/private`` is gitignored, so one checkout has it and a
    clean clone does not.  The committed snapshot must be identical either
    way: ``exists`` / ``present`` / ``absent`` stay ``None`` and only
    repository facts are recorded.
    """
    empty = build_private_catalog(tmp_path)
    marker = tmp_path / "datasets" / "cbx-social-trends" / "data" / "private"
    marker.mkdir(parents=True)
    with_marker = build_private_catalog(tmp_path)
    assert empty == with_marker
    assert empty["count"] == 9
    assert empty["include_local_state"] is False
    assert empty["present"] is None
    assert empty["absent"] is None
    for entry in empty["entries"]:
        assert entry["exists"] is None
        assert entry["classification"] == "restricted"
        assert entry["availability"] == "private"
        assert entry["publication_status"] == "not_approved"
        assert set(entry) <= {"path", "exists", "tracked", "ignored", "classification", "availability", "publication_status", "note"}


def test_private_catalog_local_mode_inspects_this_checkout_only_g6_t17(tmp_path):
    """Opt-in local mode reports real disk facts (never commit this output)."""
    marker = tmp_path / "datasets" / "cbx-social-trends" / "data" / "private"
    marker.mkdir(parents=True)
    catalog = build_private_catalog(tmp_path, include_local_state=True)
    assert catalog["include_local_state"] is True
    assert catalog["count"] == 9
    assert catalog["present"] == 1
    assert catalog["absent"] == 8
    by_path = {entry["path"]: entry for entry in catalog["entries"]}
    assert by_path["datasets/cbx-social-trends/data/private"]["exists"] is True
    assert all(
        entry["exists"] is False
        for path, entry in by_path.items()
        if path != "datasets/cbx-social-trends/data/private"
    )


# ---------------------------------------------------------------------------
# Storage backend (§14; local filesystem only)
# ---------------------------------------------------------------------------


def test_backend_put_immutable_refuses_overwrite_g6_t18(tmp_path):
    backend = LocalFilesystemBackend(tmp_path)
    digest = backend.put_immutable("artifact-001", b"bytes")
    assert backend.verify("artifact-001", digest) is True
    with pytest.raises(BackendOverwriteRefused):
        backend.put_immutable("artifact-001", b"other bytes")
    assert backend.get("artifact-001") == b"bytes"


def test_backend_missing_is_not_zero(tmp_path):
    backend = LocalFilesystemBackend(tmp_path)
    assert backend.exists("absent") is False
    assert backend.verify("absent", "a" * 64) is False


def test_backend_rejects_escaping_ids(tmp_path):
    backend = LocalFilesystemBackend(tmp_path)
    with pytest.raises(ValueError):
        backend.put_immutable("../escape", b"x")
