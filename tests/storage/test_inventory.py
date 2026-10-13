"""Inventory tests (d.md §16): non-destructive walk, judgments, page
groups with missing (取得失敗) vs observed zero, private exclusion."""

import hashlib
import json
from pathlib import Path

from storage.inventory import build_artifact_inventory
from storage.registry import ArtifactRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "metadata" / "artifacts" / "artifact-registry.json"


def _write_json(path: Path, document) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _run(tmp_path, run_id="run-1", **metadata) -> Path:
    run_dir = tmp_path / "datasets" / "study-a" / "data" / "raw" / run_id
    document = {"run_id": run_id, "study_id": "study-a", "source_id": "youtube"}
    document.update(metadata)
    _write_json(run_dir / "run_metadata.json", document)
    return run_dir


def _registry() -> ArtifactRegistry:
    return ArtifactRegistry.load(REGISTRY_PATH)


def _entry(inventory, name):
    return next(entry for entry in inventory["files"] if entry["path"].endswith(name))


def test_monthly_page_gap_is_missing_not_zero(tmp_path):
    run_dir = _run(
        tmp_path,
        start_date="2026-01-01",
        end_date="2026-03-31",
    )
    _write_json(run_dir / "records_2026-01.json", {"items": [1, 2]})
    _write_json(run_dir / "records_2026-02.json", {"items": []})
    # 2026-03 page is absent although the run period covers it.
    inventory = build_artifact_inventory(tmp_path / "datasets", artifact_registry=_registry())
    (group,) = inventory["groups"]
    assert group["expected_pages"] == 3
    assert group["expected_basis"] == "run_metadata_period"
    assert group["missing_pages"] == ["2026-03"]
    assert group["observed_zero_pages"] == ["2026-02"]
    assert group["completeness_state"] == "partial"
    # a present but empty page is observed_zero, never 'missing'
    zero = next(page for page in group["pages"] if page["index"] == "2026-02")
    assert zero["state"] == "observed_zero"
    assert "missing pages are absent-but-expected" in group["note"]


def test_observed_range_groups_are_never_complete(tmp_path):
    run_dir = _run(tmp_path)
    _write_json(run_dir / "page_0001.json", [{"id": 1}])
    _write_json(run_dir / "page_0002.json", [])
    inventory = build_artifact_inventory(tmp_path / "datasets")
    (group,) = inventory["groups"]
    assert group["expected_pages"] == 2
    assert group["expected_basis"] == "observed_range"
    assert group["missing_pages"] == []
    assert group["observed_zero_pages"] == [2]
    assert group["completeness_state"] == "unverified"


def test_duplicate_page_indexes_are_reported(tmp_path):
    run_dir = _run(tmp_path)
    _write_json(run_dir / "page_0001.json", [{"id": 1}])
    _write_json(run_dir / "page_0001_extra.json", [{"id": 2}])
    # page_0001_extra does not match the numbered pattern; use a second
    # numbered file by pointing the same index through a weekly family.
    _write_json(run_dir / "W01_2026-01-01.json", [{"id": 1}])
    _write_json(run_dir / "W01_2026-01-08.json", [{"id": 2}])
    inventory = build_artifact_inventory(tmp_path / "datasets")
    weekly = next(g for g in inventory["groups"] if g["family"] == "weekly_pages")
    assert weekly["duplicate_pages"] == [1]
    assert weekly["completeness_state"] == "partial"


def test_year_pages_are_grouped_with_sub_pages(tmp_path):
    run_dir = _run(tmp_path)
    _write_json(run_dir / "records_2016.json", {"items": [1]})
    _write_json(run_dir / "records_2016_page2.json", {"items": [1]})
    # page 3 is missing: pages 1,2,4 exist
    _write_json(run_dir / "records_2016_page4.json", {"items": []})
    inventory = build_artifact_inventory(tmp_path / "datasets")
    yearly = next(g for g in inventory["groups"] if g["family"] == "yearly_pages")
    assert yearly["expected_pages"] == 4
    assert yearly["missing_pages"] == ["2016-003"]
    assert yearly["observed_zero_pages"] == ["2016-004"]
    assert yearly["completeness_state"] == "partial"


def test_manifest_and_metadata_states_are_recorded(tmp_path):
    run_dir = _run(tmp_path)
    _write_json(run_dir / "payload.json", [{"id": 1}])
    _write_json(
        run_dir / "artifact-manifest.json",
        {"schema_version": "1.0.0", "run_id": "run-1", "artifacts": []},
    )
    derived = tmp_path / "datasets" / "study-a" / "data" / "processed"
    _write_json(derived / "summary.json", {"compound": "CBD", "avg_5y": 1})
    inventory = build_artifact_inventory(tmp_path / "datasets")
    payload = _entry(inventory, "payload.json")
    assert payload["manifest_state"] == "present"
    assert payload["metadata_state"] == "present"
    orphan = _entry(inventory, "summary.json")
    assert (orphan["manifest_state"], orphan["metadata_state"]) == ("missing", "missing")
    assert orphan["judgment"] == "missing_metadata"
    run = next(item for item in inventory["runs"] if item["run_id"] == "run-1")
    assert run["manifest_state"] == "present"
    assert run["lineage_note"] is None


def test_legacy_runs_are_recorded_as_missing_manifest(tmp_path):
    run_dir = _run(tmp_path, run_id="legacy-run")
    _write_json(run_dir / "records.json", {"keyword": "A", "data": [{"date": "2026-01-04", "value": 1}]})
    inventory = build_artifact_inventory(tmp_path / "datasets", artifact_registry=_registry())
    entry = _entry(inventory, "records.json")
    assert entry["manifest_state"] == "missing"
    assert "legacy:no-manifest" in entry["notes"]
    assert "lineage:unknown" in entry["notes"]
    run = next(item for item in inventory["runs"] if item["run_id"] == "legacy-run")
    assert run["lineage_note"].startswith("unknown")


def test_private_directories_are_excluded_by_default(tmp_path):
    private_dir = tmp_path / "datasets" / "study-a" / "data" / "private"
    _write_json(private_dir / "mapping.json", {"secret": "mapping"})
    default = build_artifact_inventory(tmp_path / "datasets")
    assert default["count"] == 0
    assert default["exclusions"]["directories"] == ["private"]
    included = build_artifact_inventory(tmp_path / "datasets", include_private=True)
    assert included["count"] == 1


def test_inventory_never_changes_files(tmp_path):
    run_dir = _run(tmp_path)
    payload = _write_json(run_dir / "payload.json", [{"id": 1}])
    before = hashlib.sha256(payload.read_bytes()).hexdigest()
    inventory = build_artifact_inventory(tmp_path / "datasets")
    assert inventory["raw_modified"] is False
    assert hashlib.sha256(payload.read_bytes()).hexdigest() == before


def test_summary_and_timeseries_are_not_conflated_in_the_inventory(tmp_path):
    run_dir = _run(tmp_path)
    _write_json(
        run_dir / "series.json",
        {"keyword": "A", "data": [{"date": "2026-01-04", "value": 1}]},
    )
    _write_json(
        run_dir / "summary.json",
        {"compound": "A", "data_points": 261, "avg_5y": 1},
    )
    inventory = build_artifact_inventory(tmp_path / "datasets", artifact_registry=_registry())
    series = _entry(inventory, "series.json")
    summary = _entry(inventory, "summary.json")
    assert series["contains_full_timeseries"] is True
    assert series["record_count"] == 1
    assert summary["contains_full_timeseries"] is False
    assert summary["record_count"] is None
    assert summary["declared_data_points"] == 261
    assert any("never reconstructed" in note for note in summary["notes"])
