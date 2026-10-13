"""Snapshot drift test for the committed G4 storage inventory.

Like the G3 temporal inventory test: the committed audit
(``docs/audits/g4-storage-inventory.json``) must be reproducible from the
repository data (29 legacy runs, unchanged hashes) so a change in the raw
files or the classifier shows up as a test failure, never as a silent
snapshot drift.
"""

import json
from pathlib import Path

from storage.inventory import build_artifact_inventory
from storage.registry import ArtifactRegistry

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = REPO_ROOT / "docs" / "audits" / "g4-storage-inventory.json"
REGISTRY_PATH = REPO_ROOT / "metadata" / "artifacts" / "artifact-registry.json"


def _committed() -> dict:
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def _recompute() -> dict:
    registry = ArtifactRegistry.load(REGISTRY_PATH)
    return build_artifact_inventory(REPO_ROOT / "datasets", artifact_registry=registry)


def test_committed_inventory_is_reproducible():
    assert _recompute() == _committed()


def test_inventory_covers_the_legacy_runs_and_is_non_destructive():
    inventory = _committed()
    assert inventory["run_count"] == 29
    assert inventory["raw_modified"] is False
    assert inventory["count"] > 0


def test_legacy_artifacts_are_recorded_without_manifests():
    inventory = _committed()
    assert inventory["manifest_summary"] == {"missing": inventory["count"]}
    for run in inventory["runs"]:
        assert run["manifest_state"] == "missing"
        assert run["verification"] == "unverifiable_no_manifest"
        assert run["lineage_note"].startswith("unknown")
    # every legacy artifact is explicitly unverifiable (no fabricated hashes)
    assert all(
        entry["verification"] == "unverifiable_no_manifest"
        for entry in inventory["files"]
    )


def test_summary_and_timeseries_are_not_conflated():
    inventory = _committed()
    summaries = [f for f in inventory["files"] if f["artifact_type"] == "summary"]
    timeseries = [f for f in inventory["files"] if f["artifact_type"] == "timeseries"]
    assert summaries and timeseries
    for entry in summaries:
        assert entry["contains_full_timeseries"] is False
        assert entry["record_count"] is None
    for entry in timeseries:
        assert entry["contains_full_timeseries"] is True
        assert isinstance(entry["record_count"], int)
    # The baseline summaries declare a point count; it is recorded as a
    # declared aggregate, never as a record count.
    declared = [f for f in summaries if f["declared_data_points"] == 261]
    assert declared
    # File names do not decide the type: `records_*_5y.json` files that only
    # carry a summary block are classified as summaries by content (P3).
    misnamed = [f for f in summaries if f["path"].endswith("records_crdh_5y.json")]
    assert misnamed and all(
        any("summary:first_value" in note for note in entry["notes"])
        for entry in misnamed
    )


def test_sqlite_absence_is_recorded_not_fabricated():
    inventory = _committed()
    assert inventory["sqlite_present"] is False
    assert "not-present" in inventory["sqlite_note"]
    assert all(entry["format"] != "sqlite" for entry in inventory["files"])


def test_no_private_directories_are_scanned():
    inventory = _committed()
    assert inventory["exclusions"]["directories"] == ["private"]
    assert all("private" not in entry["path"].split("/") for entry in inventory["files"])
