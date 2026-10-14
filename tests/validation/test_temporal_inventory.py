"""G3 §15 legacy temporal inventory tests (non-destructive, recompute-checked).

The stored audit (``docs/audits/g3-temporal-inventory.json``) is a
snapshot: this module recomputes it from the live datasets and fails when
they drift, so the audit can never silently disagree with the repository.
"""

import json
from pathlib import Path

from validation.cli import EXIT_OK
from validation.cli import main as validation_main
from validation.coverage import build_temporal_inventory
from validation.integrity import sha256_file

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = REPO_ROOT / "datasets"
AUDIT_PATH = REPO_ROOT / "docs" / "audits" / "g3-temporal-inventory.json"
NODATA_METADATA = (
    DATASETS_ROOT
    / "cannabinoid-multi-trends"
    / "data"
    / "raw"
    / "google_trends"
    / "20261002T064135Z-google-trends-nodata"
    / "run_metadata.json"
)


def test_stored_inventory_matches_a_fresh_recomputation():
    stored = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    fresh = build_temporal_inventory(DATASETS_ROOT)
    assert fresh == stored


def test_inventory_is_complete_and_non_destructive():
    inventory = build_temporal_inventory(DATASETS_ROOT)
    assert inventory["count"] == len(list(DATASETS_ROOT.rglob("run_metadata.json")))
    assert inventory["raw_modified"] is False
    summary = inventory["classification_summary"]
    # Contract runs (collected through the pipeline) carry temporal provenance,
    # so they are *verified*; the legacy runs stay *inferred*.
    assert summary["unknown"] == 0
    assert summary["ambiguous"] == 0
    assert summary["verified"] > 0
    assert summary["verified"] + summary["inferred"] == inventory["count"]


def test_inventory_never_converts_relative_periods_into_absolute_windows():
    """P1 / §15: legacy relative periods are not to be converted
    retroactively (the conversion would be a guess)."""

    inventory = build_temporal_inventory(DATASETS_ROOT)
    for record in inventory["runs"]:
        assert record["resolved_absolute_window"] is None
        assert "not derived" in record["resolution_note"]


def test_audit_does_not_modify_the_legacy_run_metadata():
    before = sha256_file(NODATA_METADATA)
    build_temporal_inventory(DATASETS_ROOT)
    assert sha256_file(NODATA_METADATA) == before


def test_example_runs_are_extracted_with_evidence():
    inventory = build_temporal_inventory(DATASETS_ROOT)
    records = {record["run_id"]: record for record in inventory["runs"]}

    nodata = records["20261002T064135Z-google-trends-nodata"]
    assert nodata["reference"]["value"] == "2026-10-02T06:41:35Z"
    assert {item["value"] for item in nodata["timeframes"]} == {"today 12-m"}
    assert nodata["observed_bounds"] is None
    assert any(
        item["field"].startswith("no_data_keywords")
        for item in nodata["completeness_evidence"]
    )

    common = records["common-scale-missing-20261009"]
    assert common["classification"] == "inferred"
    assert common["observed_bounds"]["start"] == "2025-10-05T00:00:00Z"
    assert common["observed_bounds"]["end_exclusive"] == "2026-10-11T00:00:00Z"


def test_audit_cli_writes_the_inventory(tmp_path):
    output = tmp_path / "inventory.json"
    code = validation_main(
        [
            "audit-temporal",
            "--datasets-root",
            str(DATASETS_ROOT),
            "--output",
            str(output),
        ]
    )
    assert code == EXIT_OK
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["count"] == len(list(DATASETS_ROOT.rglob("run_metadata.json")))
    assert written["raw_modified"] is False
