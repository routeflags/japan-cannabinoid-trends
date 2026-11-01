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
from pathlib import Path

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
