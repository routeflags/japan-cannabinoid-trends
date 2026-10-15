"""Catalog / lineage tests (d.md §14 / §15, G4-T13 / T16)."""

import hashlib
import json
from pathlib import Path

from storage.catalog import (
    build_catalog,
    build_study_catalog,
    catalog_path_for_study,
    dump_catalog,
    write_catalog,
)
from storage.cli import EXIT_CONFIG, EXIT_OK, EXIT_REFUSED, main as cli_main
from storage.lineage import check_catalog_lineage, trace_ancestors


def _write_json(path: Path, document) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _artifact(path: Path, base: Path, artifact_id: str, **overrides) -> dict:
    raw = path.read_bytes()
    artifact = {
        "artifact_id": artifact_id,
        "path": str(path.relative_to(base)),
        "artifact_type": "raw_records",
        "format": "json",
        "schema_id": "x-tweet-result-list-v1",
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "layer": "raw",
        "completeness": "complete",
    }
    artifact.update(overrides)
    return artifact


def _workspace(tmp_path) -> Path:
    root = tmp_path / "datasets"
    run_dir = root / "study-a" / "data" / "raw" / "run-1"
    payload = _write_json(run_dir / "payload.json", [{"id": 1}])
    derived = _write_json(run_dir / "monthly.json", {"count": 1})
    manifest = {
        "schema_version": "1.0.0",
        "run_id": "run-1",
        "artifacts": [
            _artifact(payload, run_dir, "artifact-raw"),
            _artifact(
                derived,
                run_dir,
                "monthly-counts-001",
                artifact_type="aggregate",
                layer="processed",
                schema_id="monthly-count-v1",
                derived_from=["artifact-raw"],
                transformation={"name": "monthly_post_count", "version": "1.0.0"},
            ),
        ],
    }
    _write_json(run_dir / "artifact-manifest.json", manifest)
    _write_json(
        run_dir / "run_metadata.json",
        {
            "schema_version": "1.0.0",
            "run_id": "run-1",
            "study_id": "study-a",
            "source_id": "x",
            "query_provenance": {"query_id": "cbx-general-ja", "compound_id": "compound_cbx"},
            "temporal_provenance": {"window_id": "2026-09-jst"},
        },
    )
    return root


def test_catalog_entries_join_manifest_and_run_metadata(tmp_path):
    root = _workspace(tmp_path)
    catalog = build_catalog(root)
    assert catalog["manifest_count"] == 1
    assert catalog["count"] == 2
    assert catalog["errors"] == []
    entry = next(item for item in catalog["entries"] if item["artifact_id"] == "artifact-raw")
    assert entry["study_id"] == "study-a"
    assert entry["run_id"] == "run-1"
    assert entry["source_id"] == "x"
    assert entry["query_id"] == "cbx-general-ja"
    assert entry["compound_id"] == "compound_cbx"
    assert entry["window_id"] == "2026-09-jst"
    assert entry["layer"] == "raw"


def test_catalog_rebuild_is_deterministic(tmp_path):
    root = _workspace(tmp_path)
    first = build_catalog(root)
    second = build_catalog(root)
    assert first == second
    assert json.dumps(first, ensure_ascii=False) == json.dumps(second, ensure_ascii=False)


def test_catalog_ignores_legacy_directories_without_manifests(tmp_path):
    root = _workspace(tmp_path)
    legacy = root / "study-a" / "data" / "raw" / "legacy-run"
    _write_json(legacy / "records.json", [{"id": 1}])
    catalog = build_catalog(root)
    assert catalog["manifest_count"] == 1  # the legacy run is not indexed (P8)
    assert all("legacy-run" not in entry["path"] for entry in catalog["entries"])


def test_catalog_lineage_resolves_and_traces_ancestors(tmp_path):
    root = _workspace(tmp_path)
    catalog = build_catalog(root)
    assert check_catalog_lineage(catalog) == []
    assert trace_ancestors(catalog, "monthly-counts-001") == ["artifact-raw"]


def test_dangling_lineage_reference_is_reported(tmp_path):
    root = _workspace(tmp_path)
    manifest_path = root / "study-a" / "data" / "raw" / "run-1" / "artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][1]["derived_from"] = ["artifact-does-not-exist"]
    _write_json(manifest_path, manifest)
    catalog = build_catalog(root)
    problems = check_catalog_lineage(catalog)
    assert [problem["code"] for problem in problems] == ["LINEAGE_REFERENCE_MISSING"]


def test_unreadable_manifest_is_reported_not_crashed(tmp_path):
    root = _workspace(tmp_path)
    bad = root / "study-a" / "data" / "raw" / "run-2"
    bad.mkdir(parents=True)
    (bad / "artifact-manifest.json").write_text("{broken", encoding="utf-8")
    catalog = build_catalog(root)
    assert catalog["manifest_count"] == 2
    assert catalog["errors"] and catalog["errors"][0]["reason"] == "manifest_unreadable"
    assert catalog["count"] == 2


# --- Per-study persistence (ISS-20261015-ART-008, d.md §17.1) ----------------

NO_REGISTRY = "nonexistent-metadata-dir"  # missing registry file loads as None


def _study_workspace(tmp_path):
    """A study-dir layout: <tmp>/datasets/study-a/{data,metadata}."""
    root = _workspace(tmp_path)
    return root / "study-a"


def _persist(study, *extra, metadata_dir=NO_REGISTRY):
    return cli_main(
        [
            "catalog",
            "--study-dir",
            str(study),
            "--persist",
            *extra,
            "--metadata-dir",
            str(metadata_dir),
        ]
    )


def _raw_snapshot(study):
    data_dir = study / "data"
    return {
        path.relative_to(study).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(data_dir.rglob("*"))
        if path.is_file()
    }


def test_catalog_path_for_study_is_canonical(tmp_path):
    study = tmp_path / "datasets" / "study-a"
    assert catalog_path_for_study(study) == study / "metadata" / "data-catalog.json"


def test_build_study_catalog_reuses_build_catalog(tmp_path):
    study = _study_workspace(tmp_path)
    assert build_study_catalog(study) == build_catalog(study / "data")


def test_persist_writes_canonical_catalog(tmp_path, capsys):
    study = _study_workspace(tmp_path)
    assert _persist(study) == EXIT_OK
    capsys.readouterr()  # stderr note only; the document goes to the file
    target = study / "metadata" / "data-catalog.json"
    persisted = json.loads(target.read_text(encoding="utf-8"))
    assert persisted == build_study_catalog(study)
    assert persisted["manifest_count"] == 1
    assert persisted["count"] == 2


def test_persist_is_byte_identical_and_portable(tmp_path, capsys):
    study = _study_workspace(tmp_path)
    assert _persist(study) == EXIT_OK
    target = study / "metadata" / "data-catalog.json"
    first = target.read_bytes()
    assert first.endswith(b"\n")
    assert first == (dump_catalog(build_study_catalog(study))).encode("utf-8")
    target.unlink()
    capsys.readouterr()
    assert _persist(study) == EXIT_OK
    assert target.read_bytes() == first
    # No timestamps and no absolute paths: identical input regenerates
    # byte-identical output on any machine.
    assert str(study).encode() not in first
    assert str(tmp_path).encode() not in first
    assert b"timestamp" not in first.lower()
    leftovers = list(study.joinpath("metadata").glob("*.tmp"))
    assert leftovers == []


def test_persist_does_not_touch_raw(tmp_path, capsys):
    study = _study_workspace(tmp_path)
    before = _raw_snapshot(study)
    assert before  # the fixture really has raw payloads
    assert _persist(study) == EXIT_OK
    capsys.readouterr()
    assert _raw_snapshot(study) == before
    metadata_files = sorted(
        path.relative_to(study).as_posix()
        for path in (study / "metadata").rglob("*")
        if path.is_file()
    )
    assert metadata_files == ["metadata/data-catalog.json"]


def test_write_catalog_leaves_no_partial_file_on_failure(tmp_path):
    target = tmp_path / "study" / "metadata" / "data-catalog.json"
    try:
        write_catalog({"unserializable": {object()}}, target)
    except TypeError:
        pass
    else:  # pragma: no cover - json always rejects sets
        raise AssertionError("expected TypeError")
    assert not target.exists()
    assert list(target.parent.glob("*.tmp")) == []


def _break_lineage(study):
    manifest_path = study / "data" / "raw" / "run-1" / "artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][1]["derived_from"] = ["artifact-does-not-exist"]
    _write_json(manifest_path, manifest)


def test_persist_lineage_failure_creates_nothing(tmp_path, capsys):
    study = _study_workspace(tmp_path)
    _break_lineage(study)
    target = study / "metadata" / "data-catalog.json"
    assert _persist(study, "--check-lineage") == EXIT_REFUSED
    assert "LINEAGE_REFERENCE_MISSING" in capsys.readouterr().err
    assert not target.exists()
    assert list(study.joinpath("metadata").glob("*.tmp")) == []


def test_persist_lineage_failure_keeps_previous_catalog(tmp_path, capsys):
    study = _study_workspace(tmp_path)
    assert _persist(study) == EXIT_OK
    target = study / "metadata" / "data-catalog.json"
    good_bytes = target.read_bytes()
    capsys.readouterr()
    _break_lineage(study)
    assert _persist(study, "--check-lineage") == EXIT_REFUSED
    capsys.readouterr()
    assert target.read_bytes() == good_bytes


def test_persist_without_lineage_flag_writes_despite_dangling_ref(tmp_path):
    """Lineage gating is opt-in: without --check-lineage the (honest)
    catalog - which lists the dangling reference in its entries - is stored."""
    study = _study_workspace(tmp_path)
    _break_lineage(study)
    assert _persist(study) == EXIT_OK
    target = study / "metadata" / "data-catalog.json"
    assert json.loads(target.read_text(encoding="utf-8")) == build_study_catalog(study)


def test_persist_manifest_less_study_writes_stable_empty_catalog(tmp_path, capsys):
    """Fixed rule (d.md §17.1): no manifests -> empty catalog, not a refusal."""
    study = tmp_path / "datasets" / "study-empty"
    (study / "data" / "raw").mkdir(parents=True)
    (study / "data" / "raw" / "notes.txt").write_text("no manifests here", encoding="utf-8")
    assert _persist(study) == EXIT_OK
    capsys.readouterr()
    target = study / "metadata" / "data-catalog.json"
    persisted = json.loads(target.read_text(encoding="utf-8"))
    assert persisted["count"] == 0
    assert persisted["manifest_count"] == 0
    assert persisted["entries"] == []
    assert target.read_bytes() == (dump_catalog(build_study_catalog(study))).encode("utf-8")


def test_persist_requires_study_dir_and_rejects_output(tmp_path, capsys):
    assert (
        cli_main(["catalog", "--persist", "--metadata-dir", str(tmp_path / "meta")])
        == EXIT_CONFIG
    )
    capsys.readouterr()
    study = _study_workspace(tmp_path)
    assert (
        cli_main(
            [
                "catalog",
                "--study-dir",
                str(study),
                "--persist",
                "--output",
                str(tmp_path / "catalog.json"),
                "--metadata-dir",
                str(tmp_path / "meta"),
            ]
        )
        == EXIT_CONFIG
    )
    capsys.readouterr()
    assert not (study / "metadata" / "data-catalog.json").exists()


def test_persist_missing_study_dir_is_config_error(tmp_path, capsys):
    ghost = tmp_path / "datasets" / "no-such-study"
    assert _persist(ghost) == EXIT_CONFIG
    assert "not found" in capsys.readouterr().err
    assert not ghost.exists()  # nothing is created for a missing study


def test_legacy_datasets_root_output_is_unchanged(tmp_path, capsys):
    """Existing `catalog --datasets-root --output` behavior stays compatible."""
    root = _workspace(tmp_path)
    output = tmp_path / "catalog.json"
    code = cli_main(
        [
            "catalog",
            "--datasets-root",
            str(root),
            "--output",
            str(output),
            "--metadata-dir",
            str(tmp_path / "meta"),
        ]
    )
    assert code == EXIT_OK
    capsys.readouterr()
    assert output.read_bytes() == (dump_catalog(build_catalog(root))).encode("utf-8")
