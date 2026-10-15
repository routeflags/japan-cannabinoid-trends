from pathlib import Path

from processing.gt_legacy_label_corrections import (
    BAD_LABEL_DATE,
    CORRECTED_LABEL_DATE,
    build_manifest,
    correct_record,
    dump_manifest,
    write_manifest,
)
import json


ROOT = Path(__file__).resolve().parents[2]


def test_manifest_records_all_affected_phase_a_files():
    manifest = build_manifest(ROOT)

    assert manifest["schema_id"] == "gt-legacy-label-correction-v1"
    assert manifest["layer"] == "interim"
    assert manifest["summary"] == {
        "affected_file_count": 8,
        "raw_files_modified": False,
        "correction_action": "downstream_date_label_correction",
    }
    assert {entry["recorded_date"] for entry in manifest["files"]} == {BAD_LABEL_DATE}
    assert {entry["corrected_date"] for entry in manifest["files"]} == {
        CORRECTED_LABEL_DATE
    }
    assert all(entry["raw_modified"] is False for entry in manifest["files"])


def test_manifest_uses_raw_text_label_as_evidence():
    manifest = build_manifest(ROOT)

    labels = {entry["raw_text_evidence"]["label"] for entry in manifest["files"]}
    assert labels == {"Dec 28, 2025 – Jan 3, 2026"}
    assert {
        entry["raw_text_evidence"]["parsed_start_date"] for entry in manifest["files"]
    } == {CORRECTED_LABEL_DATE}
    assert any(
        entry["raw_text_evidence"]["path"].endswith("/comparison_ja1.json")
        for entry in manifest["files"]
    )
    assert any(
        entry["raw_text_evidence"]["path"].endswith("/records_cbd-rikiddo.json")
        for entry in manifest["files"]
    )


def test_correct_record_changes_only_the_bad_label_date():
    path = (
        ROOT
        / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
        / "20261012T060517Z-google-trends-ja-rikiddo-phase-a-repeat-12m"
        / "records_cbd-rikiddo.json"
    )
    record = json.loads(path.read_text(encoding="utf-8"))

    corrected = correct_record(record)

    original_dates = [point["date"] for point in record["data"]]
    corrected_dates = [point["date"] for point in corrected["data"]]
    assert BAD_LABEL_DATE in original_dates
    assert BAD_LABEL_DATE not in corrected_dates
    assert corrected_dates[11] == CORRECTED_LABEL_DATE
    assert corrected_dates == sorted(corrected_dates)
    assert [point["value"] for point in corrected["data"]] == [
        point["value"] for point in record["data"]
    ]
    assert record["data"][11]["date"] == BAD_LABEL_DATE


def test_manifest_dump_and_write_are_deterministic(tmp_path):
    first = build_manifest(ROOT)
    second = build_manifest(ROOT)

    assert dump_manifest(first) == dump_manifest(second)

    out = tmp_path / "manifest.json"
    written = write_manifest(ROOT, out)
    assert out.read_text(encoding="utf-8") == dump_manifest(written)
