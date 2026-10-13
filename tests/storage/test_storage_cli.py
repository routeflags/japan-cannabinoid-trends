"""Storage CLI tests (read / inspect / catalog): read-only surfaces."""

import json
from pathlib import Path

from storage.cli import EXIT_CONFIG, EXIT_IO, EXIT_OK, EXIT_REFUSED, main

REPO_ROOT = Path(__file__).resolve().parents[2]
SERIES = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261012T064246Z-google-trends-ja-rikiddo-5y-main5/records_cbd-rikiddo-5y.json"
)
SUMMARY = (
    REPO_ROOT
    / "datasets/cannabinoid-multi-trends/data/raw/google_trends"
    / "20261008T093228Z-google-trends-5y-baseline/cbd_5y_summary.json"
)
METADATA = REPO_ROOT / "metadata"


def _run(argv):
    return main(argv)


def test_read_series_points(capsys):
    code = _run(
        [
            "read",
            "--path",
            str(SERIES),
            "--mode",
            "points",
            "--limit",
            "2",
            "--metadata-dir",
            str(METADATA),
        ]
    )
    assert code == EXIT_OK
    document = json.loads(capsys.readouterr().out)
    assert document["reader_id"] == "json-timeseries-reader"
    assert document["count"] == 2
    assert document["contains_full_timeseries"] is True


def test_summary_cannot_be_read_as_timeseries(capsys):
    """d.md §12 / P8: the refusal is an error, never a reconstruction."""
    code = _run(
        ["read", "--path", str(SUMMARY), "--mode", "points", "--metadata-dir", str(METADATA)]
    )
    assert code == EXIT_REFUSED
    captured = capsys.readouterr()
    assert "does not implement read mode" in captured.err


def test_summary_reads_its_fields(capsys):
    code = _run(["read", "--path", str(SUMMARY), "--metadata-dir", str(METADATA)])
    assert code == EXIT_OK
    document = json.loads(capsys.readouterr().out)
    assert document["mode"] == "summary_fields"
    assert document["contains_full_timeseries"] is False


def test_unknown_artifact_is_refused(tmp_path, capsys):
    blob = tmp_path / "blob.bin"
    blob.write_bytes(b"\x00\x01\x02")
    code = _run(["read", "--path", str(blob), "--metadata-dir", str(METADATA)])
    assert code == EXIT_REFUSED
    assert "no registered reader" in capsys.readouterr().err


def test_missing_file_is_an_io_error(tmp_path):
    assert (
        _run(["read", "--path", str(tmp_path / "ghost.json"), "--metadata-dir", str(METADATA)])
        == EXIT_IO
    )


def test_inspect_reports_the_schema_resolution(capsys):
    code = _run(["inspect", "--path", str(SUMMARY), "--metadata-dir", str(METADATA)])
    assert code == EXIT_OK
    document = json.loads(capsys.readouterr().out)
    assert document["schema_id"] == "google-trends-summary-v1"
    assert document["reader_registered"] is True


def test_malformed_registry_is_a_config_error(tmp_path):
    metadata = tmp_path / "metadata" / "artifacts"
    metadata.mkdir(parents=True)
    (metadata / "artifact-registry.json").write_text("{broken", encoding="utf-8")
    code = _run(["inspect", "--path", str(SUMMARY), "--metadata-dir", str(tmp_path / "metadata")])
    assert code == EXIT_CONFIG


def test_catalog_check_lineage_on_an_empty_root(tmp_path, capsys):
    code = _run(["catalog", "--datasets-root", str(tmp_path), "--check-lineage", "--metadata-dir", str(METADATA)])
    assert code == EXIT_OK
    document = json.loads(capsys.readouterr().out)
    assert document["count"] == 0


def test_catalog_reports_dangling_lineage(tmp_path, capsys):
    run_dir = tmp_path / "datasets" / "study" / "data" / "raw" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "artifact-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "run_id": "run-1",
                "artifacts": [
                    {
                        "artifact_id": "derived-1",
                        "path": "derived.json",
                        "artifact_type": "aggregate",
                        "format": "json",
                        "schema_id": "aggregate-v1",
                        "byte_length": 2,
                        "sha256": "0" * 64,
                        "layer": "processed",
                        "completeness": "complete",
                        "derived_from": ["raw-missing"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    code = _run(["catalog", "--datasets-root", str(tmp_path / "datasets"), "--check-lineage", "--output", str(tmp_path / "catalog.json"), "--metadata-dir", str(METADATA)])
    assert code == EXIT_REFUSED
    captured = capsys.readouterr()
    assert "LINEAGE_REFERENCE_MISSING" in captured.err
