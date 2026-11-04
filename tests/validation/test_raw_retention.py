"""Raw retention is Repository Storage (Git tracking), not local raw presence.

Why this needs its own tests: the two-state vocabulary is the contract that
lets a checkout distinguish a missing repository run from a run that is
deliberately ``git_untracked`` because copyright or redistribution constraints
forbid committing the payload.  The tests pin the vocabulary, the required
decision basis, the policy default, and the actual Git index check.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from validation.raw_completeness import build_snapshot_scope
from validation.raw_retention import build_retention_report

RUN_ID = "20260101T000000Z-probe-a"
CLAIM = {"study_id": "probe", "source_id": "probe", "run_id": RUN_ID}


def _write_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _policy(
    root: Path,
    *,
    kind: str = "social",
    git_tracking: str = "ignored",
    policy_id: str = "raw-probe-social",
) -> None:
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
                    "policy_id": policy_id,
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


def _decision(
    root: Path,
    *,
    status: str = "git_untracked",
    reason: str | None = "copyright and redistribution constraints",
    reference: str | None = "docs/decisions/retention.md",
    publication: str = "requires_review",
    publication_reason: str | None = None,
    supersedes: list[str] | None = None,
    decision_id: str = "20260101-probe",
    filename: str = "20260101-probe.json",
    write_reference: bool = True,
) -> Path:
    if reference and write_reference:
        target = root / reference
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("recorded decision\n", encoding="utf-8")
    document = {
        "schema_version": "1.0.0",
        "record": "raw_retention_decision",
        "retention_decision_id": decision_id,
        "decided_at": "2026-01-01",
        "decided_by": "owner",
        "retention_status": status,
        "publication_status": publication,
        "runs": [dict(CLAIM)],
    }
    if reason is not None:
        document["reason"] = reason
    if reference is not None:
        document["decision_reference"] = reference
    if publication_reason is not None:
        document["publication_reason"] = publication_reason
    if supersedes is not None:
        document["supersedes"] = supersedes
    path = root / "metadata" / "provenance" / "retention" / filename
    _write_json(path, document)
    return path


def _report(root: Path, **kwargs):
    return build_retention_report(
        root,
        root / "metadata" / "provenance" / "retention",
        claims=[dict(CLAIM)],
        **kwargs,
    )


def _run(report: dict) -> dict:
    return report["runs"][0]


def _reasons(report: dict) -> set[str]:
    return {entry["reason"] for entry in report["violations"]}


def _catalog_claim(root: Path, source: str = "probe") -> None:
    _write_json(
        root / "datasets" / "probe" / "metadata" / "data-catalog.json",
        {
            "catalog_version": "1.0.0",
            "entries": [
                {
                    "run_id": RUN_ID,
                    "study_id": "probe",
                    "source_id": source,
                    "path": f"data/raw/{source}/{RUN_ID}/x.csv",
                }
            ],
        },
    )


def test_snapshot_scope_is_checkout_local_and_preserves_the_claim(
    tmp_path: Path,
) -> None:
    _policy(tmp_path, git_tracking="ignored")
    _catalog_claim(tmp_path)
    _decision(tmp_path)

    report = build_snapshot_scope(
        tmp_path / "datasets",
        tmp_path / "metadata" / "provenance" / "declarations",
        tmp_path,
        tmp_path / "metadata" / "provenance" / "retention",
    )

    assert report["audit_scope"] == "checkout_local"
    assert report["raw_visibility"] == "partial"
    assert report["raw_rows_generated"] is False
    assert report["raw_dependent_facts"] == "unavailable"
    assert report["not_repository_retained_run_ids"] == [RUN_ID]
    assert report["git_tracked_run_ids"] == []
    assert report["claim_count"] == 1
    run = report["runs"][0]
    assert run["availability"] == "not_repository_retained"
    assert run["raw_dependent_facts"] == "unavailable"
    assert run["record_count"] is None
    assert run["sha256"] is None
    assert report == build_snapshot_scope(
        tmp_path / "datasets",
        tmp_path / "metadata" / "provenance" / "declarations",
        tmp_path,
        tmp_path / "metadata" / "provenance" / "retention",
    )


def test_a_valid_git_untracked_decision_overrides_the_policy(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="tracked")
    _decision(tmp_path)

    report = _report(tmp_path)

    assert _run(report)["retention_status"] == "git_untracked"
    assert _run(report)["retention_source"] == "decision"
    assert _run(report)["retention_policy_status"] == "git_tracked"
    assert report["failure_count"] == 0


def test_untracked_decision_requires_a_reason_and_a_resolvable_reference(
    tmp_path: Path,
) -> None:
    _policy(tmp_path, git_tracking="tracked")
    _decision(tmp_path, reason=None, reference=None)

    report = _report(tmp_path)

    reasons = _reasons(report)
    assert "retention_reason_missing" in reasons
    assert "retention_decision_reference_missing" in reasons
    assert report["failure_count"] >= 2
    # The invalid decision must not excuse absence: it falls back to policy.
    assert _run(report)["retention_status"] == "git_tracked"
    assert _run(report)["retention_source"] == "storage_policy"


def test_an_unresolved_decision_reference_is_a_violation(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="tracked")
    _decision(
        tmp_path, reference="docs/decisions/absent.md", write_reference=False
    )

    report = _report(tmp_path)

    assert "retention_decision_reference_unresolved" in _reasons(report)


def test_policy_default_for_a_social_source_is_git_untracked(tmp_path: Path) -> None:
    _policy(tmp_path, kind="social", git_tracking="ignored")

    report = _report(tmp_path)

    assert _run(report)["retention_status"] == "git_untracked"
    assert _run(report)["retention_source"] == "storage_policy"
    assert report["failure_count"] == 0


def test_policy_default_for_a_search_source_is_git_tracked(tmp_path: Path) -> None:
    _policy(
        tmp_path,
        kind="search",
        git_tracking="tracked",
        policy_id="raw-probe-search",
    )

    report = _report(tmp_path)

    assert _run(report)["retention_status"] == "git_tracked"
    assert report["failure_count"] == 0


def test_publication_is_a_separate_axis_from_retention(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="ignored")
    _decision(
        tmp_path,
        status="git_untracked",
        publication="denied",
        publication_reason="row-level video data must not be published",
    )

    report = _report(tmp_path)

    assert _run(report)["retention_status"] == "git_untracked"
    assert _run(report)["publication_status"] == "denied"
    assert report["failure_count"] == 0


def test_publication_denied_requires_its_own_reason(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="ignored")
    _decision(tmp_path, publication="denied")

    report = _report(tmp_path)

    assert "publication_reason_missing" in _reasons(report)


def test_superseding_decision_replaces_an_earlier_one(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="tracked")
    _decision(
        tmp_path,
        status="git_untracked",
        decision_id="first",
        filename="first.json",
    )
    _decision(
        tmp_path,
        status="git_tracked",
        decision_id="second",
        filename="second.json",
        supersedes=["first"],
    )

    report = _report(tmp_path)

    assert _run(report)["retention_decision_id"] == "second"
    assert _run(report)["retention_status"] == "git_tracked"
    assert report["failure_count"] == 0


def test_two_active_decisions_for_one_run_conflict(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="ignored")
    _decision(tmp_path, decision_id="first", filename="first.json")
    _decision(tmp_path, decision_id="second", filename="second.json")

    report = _report(tmp_path)

    assert "retention_decision_conflict" in _reasons(report)
    assert report["failure_count"] == 1


def test_output_is_deterministic(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="ignored")
    _decision(tmp_path)

    assert _report(tmp_path) == _report(tmp_path)


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_a_git_untracked_run_must_not_have_tracked_raw(tmp_path: Path) -> None:
    _policy(tmp_path, git_tracking="ignored")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "tests@example.invalid")
    _git(tmp_path, "config", "user.name", "Contract Tests")
    run_dir = tmp_path / "datasets" / "probe" / "data" / "raw" / "probe" / RUN_ID
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "payload.csv").write_text("id\n1\n", encoding="utf-8")
    _git(tmp_path, "add", "-f", str(run_dir.relative_to(tmp_path)))

    report = _report(tmp_path, datasets_root=tmp_path / "datasets")

    assert "retention_git_untracked_but_tracked" in _reasons(report)


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_a_git_tracked_run_must_have_tracked_raw(tmp_path: Path) -> None:
    _policy(
        tmp_path,
        kind="search",
        git_tracking="tracked",
        policy_id="raw-probe-search",
    )
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "tests@example.invalid")
    _git(tmp_path, "config", "user.name", "Contract Tests")

    report = _report(tmp_path, datasets_root=tmp_path / "datasets")

    assert "retention_git_tracked_but_untracked" in _reasons(report)
