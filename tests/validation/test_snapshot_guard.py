"""The audit-snapshot guard refuses a partial raw checkout.

Why this needs its own tests: the target overwrites eleven tracked reports.
The guard has to fail before the first write when a committed claim or an
existing snapshot names a run this checkout cannot show, and it has to notice
a run id that disappeared after the writes.  A guard that only passes is not a
guard, so both directions are tested.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from validation.snapshot_guard import postflight, preflight, snapshot_run_ids


def _write_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _catalog(root: Path, run_ids: list[str]) -> None:
    _write_json(
        root / "datasets" / "probe" / "metadata" / "data-catalog.json",
        {
            "catalog_version": "1.0.0",
            "entries": [
                {
                    "run_id": run_id,
                    "study_id": "probe",
                    "source_id": "youtube",
                    "path": f"data/raw/youtube/{run_id}/x.csv",
                }
                for run_id in run_ids
            ],
        },
    )


def _run(root: Path, run_id: str, metadata=True) -> Path:
    directory = root / "datasets" / "probe" / "data" / "raw" / "youtube" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "payload.csv").write_text("id,title\n1,x\n", encoding="utf-8")
    if metadata:
        _write_json(directory / "run_metadata.json", {"run_id": run_id})
    return directory


def _audits(root: Path, run_ids: list[str]) -> Path:
    audits = root / "docs" / "audits"
    _write_json(
        audits / "g4-storage-inventory.json",
        {"runs": [{"run_id": run_id} for run_id in run_ids]},
    )
    return audits


def _preflight(root: Path, audits: Path, state: Path, **kwargs):
    return preflight(
        root / "datasets",
        audits,
        root / "metadata" / "provenance" / "declarations",
        state_file=state,
        **kwargs,
    )


def _policy(root: Path) -> None:
    _write_json(
        root / "config" / "sources.json",
        {"sources": [{"source_id": "youtube", "kind": "social"}]},
    )
    _write_json(
        root / "config" / "storage-policies.json",
        {
            "policies": [
                {
                    "policy_id": "raw-social-default",
                    "artifact_layer": "raw",
                    "source_kind": "social",
                    "classification": "restricted",
                    "storage": "private",
                    "git_tracking": "ignored",
                    "publication": "requires_review",
                }
            ]
        },
    )


def _decision(
    root: Path,
    run_id: str,
    *,
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
        "retention_status": "git_untracked",
        "publication_status": "requires_review",
        "runs": [
            {"study_id": "probe", "source_id": "youtube", "run_id": run_id}
        ],
    }
    if reason is not None:
        document["reason"] = reason
    if reference is not None:
        document["decision_reference"] = reference
    _write_json(
        root
        / "metadata"
        / "provenance"
        / "retention"
        / "20260101-probe.json",
        document,
    )


def test_preflight_refuses_when_an_expected_raw_run_is_missing(tmp_path: Path) -> None:
    root = tmp_path
    _catalog(root, ["20260101T000000Z-probe-a"])
    audits = _audits(root, [])

    report = _preflight(root, audits, root / ".staging" / "state.json")

    assert report["refused"] is True
    assert report["adopted_missing_raw_count"] == 1
    assert report["missing_run_ids"] == ["20260101T000000Z-probe-a"]


def test_preflight_passes_and_writes_state_when_raw_is_complete(tmp_path: Path) -> None:
    root = tmp_path
    _catalog(root, ["20260101T000000Z-probe-a"])
    _run(root, "20260101T000000Z-probe-a")
    audits = _audits(root, ["20260101T000000Z-probe-a"])
    state = root / ".staging" / "state.json"

    report = _preflight(root, audits, state)

    assert report["refused"] is False
    assert report["missing_run_ids"] == []
    assert json.loads(state.read_text(encoding="utf-8"))["phase"] == "preflight"


def test_preflight_accepts_an_explicit_expected_run_file(tmp_path: Path) -> None:
    root = tmp_path
    _catalog(root, [])
    audits = _audits(root, [])
    expected = root / "expected.json"
    _write_json(expected, {"run_ids": ["20260101T000000Z-probe-b"]})

    report = _preflight(
        root, audits, root / "state.json", expected_run_ids=expected
    )

    assert report["refused"] is True
    assert report["missing_run_ids"] == ["20260101T000000Z-probe-b"]


def test_postflight_detects_a_run_id_that_disappeared(tmp_path: Path) -> None:
    root = tmp_path
    _catalog(root, ["20260101T000000Z-probe-a"])
    _run(root, "20260101T000000Z-probe-a")
    audits = _audits(root, ["20260101T000000Z-probe-a"])
    state = root / "state.json"
    assert _preflight(root, audits, state)["refused"] is False

    # The regeneration loses the row even though the raw run is still present.
    _audits(root, [])

    report = postflight(state, audits)

    assert report["refused"] is True
    assert report["lost_run_ids"] == ["20260101T000000Z-probe-a"]


def test_postflight_reports_an_addition_without_failing(tmp_path: Path) -> None:
    root = tmp_path
    _catalog(root, ["20260101T000000Z-probe-a"])
    _run(root, "20260101T000000Z-probe-a")
    audits = _audits(root, ["20260101T000000Z-probe-a"])
    state = root / "state.json"
    _preflight(root, audits, state)

    _run(root, "20260101T000000Z-probe-b")
    _audits(root, ["20260101T000000Z-probe-a", "20260101T000000Z-probe-b"])

    report = postflight(state, audits)

    assert report["refused"] is False
    assert report["added_run_ids"] == ["20260101T000000Z-probe-b"]


def test_snapshot_labels_that_are_not_run_ids_are_ignored(tmp_path: Path) -> None:
    root = tmp_path
    audits = root / "docs" / "audits"
    _write_json(
        audits / "g2-query-inventory.json",
        {"queries": [{"run_id": "observed"}, {"run_id": "20260101T000000Z-probe-a"}]},
    )

    report = snapshot_run_ids(audits)

    assert report["union"] == ["20260101T000000Z-probe-a"]


def test_scope_sidecar_run_ids_are_not_snapshot_rows(tmp_path: Path) -> None:
    """The sidecar preserves claims; it must not mask a raw-derived row loss."""

    audits = tmp_path / "docs" / "audits"
    _write_json(
        audits / "snapshot-scope.json",
        {"runs": [{"run_id": "20260101T000000Z-probe-a"}]},
    )

    report = snapshot_run_ids(audits)

    assert report["per_file"]["snapshot-scope.json"] == []
    assert report["union"] == []


# ---------------------------------------------------------------------------
# Raw retention: git_untracked is not missing
# ---------------------------------------------------------------------------


def test_preflight_does_not_refuse_an_intentionally_untracked_run(
    tmp_path: Path,
) -> None:
    root = tmp_path
    run_id = "20260101T000000Z-probe-a"
    _policy(root)
    _catalog(root, [run_id])
    _decision(root, run_id)
    audits = _audits(root, [])
    state = root / "state.json"

    report = _preflight(root, audits, state)

    assert report["refused"] is False
    assert report["audit_scope"] == "checkout_local"
    assert report["raw_visibility"] == "partial"
    assert report["missing_run_ids"] == []
    assert report["not_repository_retained_run_ids"] == [run_id]
    assert report["retention_violation_count"] == 0
    assert json.loads(state.read_text(encoding="utf-8"))[
        "not_repository_retained_run_ids"
    ] == [run_id]


def test_preflight_refuses_an_untracked_run_without_a_retention_basis(
    tmp_path: Path,
) -> None:
    root = tmp_path
    run_id = "20260101T000000Z-probe-a"
    _policy(root)
    _catalog(root, [run_id])
    _decision(root, run_id, reason=None, reference=None)
    audits = _audits(root, [])

    report = _preflight(root, audits, root / "state.json")

    assert report["refused"] is True
    # The policy alone already says git_untracked, so absence is not missing;
    # the refusal is the unproven decision, not a missing run.
    assert report["missing_run_ids"] == []
    assert report["retention_violation_count"] >= 2


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_preflight_reports_tracked_raw_for_an_untracked_run_as_warning(
    tmp_path: Path,
) -> None:
    root = tmp_path
    run_id = "20260101T000000Z-probe-a"
    _policy(root)
    _catalog(root, [run_id])
    _decision(root, run_id)
    directory = _run(root, run_id)
    _git(root, "init", "-q")
    _git(root, "add", "-f", str(directory.relative_to(root)))
    audits = _audits(root, [])

    report = _preflight(root, audits, root / "state.json")

    # The hard failure is audit-raw-retention; the snapshot guard only blocks
    # git_tracked loss/inconsistency per the owner decision.
    assert report["refused"] is False
    assert report["retention_violation_count"] == 0
    reasons = {entry["reason"] for entry in report["retention_warnings"]}
    assert "retention_git_untracked_but_tracked" in reasons


def test_postflight_allows_dropping_an_intentionally_untracked_run(
    tmp_path: Path,
) -> None:
    root = tmp_path
    run_id = "20260101T000000Z-probe-a"
    _policy(root)
    _catalog(root, [run_id])
    _decision(root, run_id)
    audits = _audits(root, [run_id])
    state = root / "state.json"
    assert _preflight(root, audits, state)["refused"] is False

    _audits(root, [])

    report = postflight(state, audits)

    assert report["refused"] is False
    assert report["lost_run_ids"] == []
    assert report["intentionally_dropped_run_ids"] == [run_id]
