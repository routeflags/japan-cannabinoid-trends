"""Catalog / lineage tests (d.md §14 / §15, G4-T13 / T16)."""

import hashlib
import json
from pathlib import Path

from storage.catalog import build_catalog
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
