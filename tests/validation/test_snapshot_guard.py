"""The audit-snapshot guard refuses a partial raw checkout.

Why this needs its own tests: the target overwrites eleven tracked reports.
The guard has to fail before the first write when a committed claim or an
existing snapshot names a run this checkout cannot show, and it has to notice
a run id that disappeared after the writes.  A guard that only passes is not a
guard, so both directions are tested.
"""

from __future__ import annotations

import json
from pathlib import Path

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


def _run(root: Path, run_id: str, metadata=True) -> None:
    directory = root / "datasets" / "probe" / "data" / "raw" / "youtube" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "payload.csv").write_text("id,title\n1,x\n", encoding="utf-8")
    if metadata:
        _write_json(directory / "run_metadata.json", {"run_id": run_id})


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
