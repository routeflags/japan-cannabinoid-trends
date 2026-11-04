"""Committed catalog/declaration claims versus the raw layer.

Why this needs its own tests: the raw layer is machine-local, so a missing
run directory is a normal state on a clone.  The audit has to report it
without pretending the claim is false, resolve the study rename and the
Google Trends directory spelling, and keep post-staging corrections pinned
to the declaration bytes they claim to correct.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from validation.raw_completeness import build_raw_completeness


def _write_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _study_registry(root: Path, current: str, previous: list[str]) -> None:
    _write_json(
        root / "metadata" / "studies" / "study-registry.json",
        {
            "schema_version": "1.0.0",
            "studies": [
                {
                    "study_id": current,
                    "title": current,
                    "research_questions": ["q"],
                    "sources": ["google-trends"],
                    "status": "active",
                    "previous_study_ids": previous,
                }
            ],
        },
    )


def _catalog(root: Path, study: str, entries: list[dict]) -> None:
    _write_json(
        root / "datasets" / study / "metadata" / "data-catalog.json",
        {
            "catalog_version": "1.0.0",
            "datasets_root": "data",
            "manifest_count": 1,
            "count": len(entries),
            "errors": [],
            "entries": entries,
        },
    )


def _run(root: Path, study: str, source: str, run_id: str, metadata=True) -> Path:
    directory = root / "datasets" / study / "data" / "raw" / source / run_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "payload.csv").write_text("id,title\n1,x\n", encoding="utf-8")
    if metadata:
        _write_json(directory / "run_metadata.json", {"run_id": run_id})
    return directory


def _declaration(path: Path, study: str, source: str, run_id: str) -> None:
    _write_json(
        path,
        {
            "declaration_version": "staging-declaration-v1",
            "runs": [
                {
                    "run_id": run_id,
                    "study_id": study,
                    "source_id": source,
                    "query": {"keyword": "x", "query_id": "x"},
                }
            ],
        },
    )


def test_present_catalog_run_is_not_a_finding(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _catalog(
        root,
        "probe",
        [
            {
                "run_id": "20260101T000000Z-probe-a",
                "study_id": "probe",
                "source_id": "youtube",
                "path": "data/raw/youtube/20260101T000000Z-probe-a/x.csv",
            }
        ],
    )
    _run(root, "probe", "youtube", "20260101T000000Z-probe-a")

    report = build_raw_completeness(
        root / "datasets",
        root / "metadata" / "provenance" / "declarations",
        None,
        root,
    )

    assert report["present_count"] == 1
    assert report["missing_count"] == 0
    assert report["failure_count"] == 0
    assert report["runs"][0]["state"] == "present"


def test_missing_directory_and_missing_metadata_are_distinct(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _catalog(
        root,
        "probe",
        [
            {"run_id": "20260101T000000Z-probe-a", "study_id": "probe", "source_id": "youtube", "path": "a"},
            {"run_id": "20260101T000000Z-probe-b", "study_id": "probe", "source_id": "youtube", "path": "b"},
        ],
    )
    _run(root, "probe", "youtube", "20260101T000000Z-probe-a", metadata=False)

    report = build_raw_completeness(
        root / "datasets",
        root / "metadata" / "provenance" / "declarations",
        None,
        root,
    )
    states = {run["run_id"]: run["state"] for run in report["runs"]}
    assert states["20260101T000000Z-probe-a"] == "missing_run_metadata"
    assert states["20260101T000000Z-probe-b"] == "missing_directory"
    assert report["missing_run_metadata_count"] == 1
    assert report["missing_directory_count"] == 1


def test_previous_study_id_resolves_to_the_current_directory(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "current", ["old"])
    _catalog(
        root,
        "current",
        [{"run_id": "20260101T000000Z-probe-a", "study_id": "old", "source_id": "youtube", "path": "a"}],
    )
    _run(root, "current", "youtube", "20260101T000000Z-probe-a")

    report = build_raw_completeness(
        root / "datasets",
        root / "metadata" / "provenance" / "declarations",
        None,
        root,
    )

    assert report["missing_count"] == 0
    assert report["runs"][0]["resolved_study_id"] == "current"


def test_google_trends_directory_spelling_is_normalized(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _catalog(
        root,
        "probe",
        [{"run_id": "20260101T000000Z-probe-a", "study_id": "probe", "source_id": "google-trends", "path": "a"}],
    )
    _run(root, "probe", "google_trends", "20260101T000000Z-probe-a")

    report = build_raw_completeness(
        root / "datasets",
        root / "metadata" / "provenance" / "declarations",
        None,
        root,
    )

    assert report["missing_count"] == 0


def test_declaration_run_without_catalog_is_reported(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "current", [])
    declarations = root / "metadata" / "provenance" / "declarations"
    _declaration(
        declarations / "d.json",
        "other-study",
        "youtube",
        "20260101T000000Z-probe-a",
    )

    report = build_raw_completeness(
        root / "datasets", declarations, None, root
    )

    assert report["declaration_run_count"] == 1
    assert report["missing_count"] == 1
    assert report["declaration_studies_without_catalog"] == ["other-study"]


def test_correction_record_pins_the_declaration_bytes(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    declarations = root / "metadata" / "provenance" / "declarations"
    original = declarations / "original.json"
    _declaration(original, "probe", "youtube", "20260101T000000Z-probe-a")
    digest = hashlib.sha256(original.read_bytes()).hexdigest()
    corrections = root / "metadata" / "provenance" / "corrections"
    _write_json(
        corrections / "c.json",
        {
            "record": "declaration_correction",
            "correction_id": "c",
            "original_declarations": [
                {
                    "path": "metadata/provenance/declarations/original.json",
                    "sha256": digest,
                }
            ],
            "corrections": [
                {"run_id": "20260101T000000Z-probe-a", "field": "x"}
            ],
        },
    )

    report = build_raw_completeness(
        root / "datasets", declarations, corrections, root
    )

    assert report["correction_violation_count"] == 0
    assert report["corrections"][0]["correction_id"] == "c"


def test_correction_sha_mismatch_and_unknown_run_are_violations(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    declarations = root / "metadata" / "provenance" / "declarations"
    original = declarations / "original.json"
    _declaration(original, "probe", "youtube", "20260101T000000Z-probe-a")
    corrections = root / "metadata" / "provenance" / "corrections"
    _write_json(
        corrections / "c.json",
        {
            "record": "declaration_correction",
            "correction_id": "c",
            "original_declarations": [
                {
                    "path": "metadata/provenance/declarations/original.json",
                    "sha256": "0" * 64,
                }
            ],
            "corrections": [
                {"run_id": "20260101T000000Z-probe-unknown", "field": "x"}
            ],
        },
    )

    report = build_raw_completeness(
        root / "datasets", declarations, corrections, root
    )

    reasons = {entry["reason"] for entry in report["correction_violations"]}
    assert "original_declarations_sha256_mismatch" in reasons
    assert "corrected_run_id_not_in_original_declaration" in reasons


# ---------------------------------------------------------------------------
# Raw retention: Repository Storage (Git tracking), not local raw existence
# ---------------------------------------------------------------------------


def _policy(root: Path, *, kind: str = "social", git_tracking: str = "ignored") -> None:
    _write_json(
        root / "config" / "sources.json",
        {"schema_version": "1.0.0", "sources": [{"source_id": "probe", "kind": kind}]},
    )
    _write_json(
        root / "config" / "storage-policies.json",
        {
            "schema_version": "1.0.0",
            "policies": [
                {
                    "policy_id": f"raw-probe-{kind}",
                    "artifact_layer": "raw",
                    "source_kind": kind,
                    "classification": "restricted",
                    "storage": "private",
                    "git_tracking": git_tracking,
                    "publication": "requires_review",
                }
            ],
        },
    )


def _retention_decision(
    root: Path,
    *,
    status: str = "git_untracked",
    reason: str | None = "copyright and redistribution constraints",
    reference: str | None = "docs/decisions/retention.md",
) -> None:
    if reference:
        target = root / reference
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("recorded decision\n", encoding="utf-8")
    document = {
        "schema_version": "1.0.0",
        "record": "raw_retention_decision",
        "retention_decision_id": "20260101-probe",
        "decided_at": "2026-01-01",
        "decided_by": "owner",
        "retention_status": status,
        "publication_status": "requires_review",
        "runs": [
            {
                "study_id": "probe",
                "source_id": "probe",
                "run_id": "20260101T000000Z-probe-a",
            }
        ],
    }
    if reason is not None:
        document["reason"] = reason
    if reference is not None:
        document["decision_reference"] = reference
    _write_json(
        root / "metadata" / "provenance" / "retention" / "20260101-probe.json",
        document,
    )


def _completeness(root: Path) -> dict:
    return build_raw_completeness(
        root / "datasets",
        root / "metadata" / "provenance" / "declarations",
        None,
        repo_root=root,
        retention_dir=root / "metadata" / "provenance" / "retention",
    )


def _catalog_claim(root: Path, source: str = "probe") -> None:
    _catalog(
        root,
        "probe",
        [
            {
                "run_id": "20260101T000000Z-probe-a",
                "study_id": "probe",
                "source_id": source,
                "path": f"data/raw/{source}/20260101T000000Z-probe-a/x.csv",
            }
        ],
    )


def test_a_git_tracked_claim_without_raw_is_still_a_failure(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _policy(root, kind="search", git_tracking="tracked")
    _catalog_claim(root)

    report = _completeness(root)

    run = report["runs"][0]
    assert run["retention_status"] == "git_tracked"
    assert run["state"] == "missing_directory"
    assert report["missing_count"] == 1
    assert report["failure_count"] == 1


def test_a_git_untracked_run_with_a_valid_decision_is_not_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    # The policy says tracked; the explicit decision overrides it.
    _policy(root, kind="social", git_tracking="tracked")
    _catalog_claim(root)
    _retention_decision(root)

    report = _completeness(root)

    run = report["runs"][0]
    assert run["retention_status"] == "git_untracked"
    assert run["retention_source"] == "decision"
    assert run["state"] == "not_repository_retained"
    assert report["missing_count"] == 0
    assert report["not_repository_retained_count"] == 1
    assert report["failure_count"] == 0


def test_a_git_untracked_decision_without_a_basis_fails(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _policy(root, kind="social", git_tracking="ignored")
    _catalog_claim(root)
    _retention_decision(root, reason=None, reference=None)

    report = _completeness(root)

    reasons = {entry["reason"] for entry in report["retention_violations"]}
    assert "retention_reason_missing" in reasons
    assert "retention_decision_reference_missing" in reasons
    assert report["failure_count"] >= 2


def test_policy_default_for_an_untracked_source_is_not_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _policy(root, kind="social", git_tracking="ignored")
    _catalog_claim(root)

    report = _completeness(root)

    run = report["runs"][0]
    assert run["retention_status"] == "git_untracked"
    assert run["retention_source"] == "storage_policy"
    assert run["state"] == "not_repository_retained"
    assert report["failure_count"] == 0


def test_local_raw_of_an_untracked_run_is_reported_separately(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _policy(root, kind="social", git_tracking="ignored")
    _catalog_claim(root)
    _run(root, "probe", "probe", "20260101T000000Z-probe-a")

    report = _completeness(root)

    run = report["runs"][0]
    assert run["state"] == "local_only_present"
    assert report["present_count"] == 0
    assert report["local_only_present_count"] == 1
    assert report["failure_count"] == 0


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_untracked_run_with_tracked_raw_is_a_violation(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _policy(root, kind="social", git_tracking="ignored")
    _catalog_claim(root)
    directory = _run(root, "probe", "probe", "20260101T000000Z-probe-a")
    _git(root, "init", "-q")
    _git(root, "add", "-f", str(directory.relative_to(root)))

    report = _completeness(root)

    run = report["runs"][0]
    assert run["state"] == "git_untracked_but_tracked"
    assert report["retention_violation_count"] == 1
    assert report["failure_count"] == 1


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_git_tracked_run_present_only_locally_is_a_failure(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _policy(root, kind="search", git_tracking="tracked")
    _catalog_claim(root)
    _run(root, "probe", "probe", "20260101T000000Z-probe-a")
    _git(root, "init", "-q")

    report = _completeness(root)

    run = report["runs"][0]
    assert run["state"] == "present_not_git_tracked"
    assert report["retention_violation_count"] == 1
    assert report["failure_count"] == 1


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_a_tracked_run_not_checked_out_is_not_missing(tmp_path: Path) -> None:
    root = tmp_path
    _study_registry(root, "probe", [])
    _policy(root, kind="search", git_tracking="tracked")
    _catalog_claim(root)
    directory = _run(root, "probe", "probe", "20260101T000000Z-probe-a")
    _git(root, "init", "-q")
    _git(root, "add", "-f", str(directory.relative_to(root)))
    shutil.rmtree(directory)

    report = _completeness(root)

    run = report["runs"][0]
    assert run["state"] == "tracked_not_checked_out"
    assert report["missing_count"] == 0
    assert report["failure_count"] == 0
