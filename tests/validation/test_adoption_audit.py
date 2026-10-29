"""The adoption backlog enumerates raw run directories, not metadata files.

Why this needs its own tests: ``audit-new-runs`` discovers runs by
``rglob("run_metadata.json")``, so a run directory without that file is absent
from it.  The property this module has to keep is the opposite one - every
directory under ``data/raw/<source>/`` appears exactly once, whatever its
metadata looks like - otherwise the backlog it reports is not the backlog.

Contract sources: AGENTS.md ("Raw Data Rule", "Run Identity"),
``docs/specs/collection-pipeline.md`` (staging declaration), and
``src/collection/core/staging.py`` (the fields a declaration must state).
"""

import json
from pathlib import Path

from validation.adoption import (
    RUN_METADATA_NAME,
    SKIPPED_DIRECTORY_NAMES,
    build_adoption_backlog,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _raw_root(datasets: Path, study: str = "probe-study", source: str = "probe") -> Path:
    root = datasets / study / "data" / "raw" / source
    root.mkdir(parents=True, exist_ok=True)
    return root


def _run(root: Path, name: str, metadata=None, files: int = 1) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    for index in range(files):
        (run_dir / f"payload_{index}.json").write_text("{}", encoding="utf-8")
    if metadata is not None:
        (run_dir / RUN_METADATA_NAME).write_text(
            metadata if isinstance(metadata, str) else json.dumps(metadata),
            encoding="utf-8",
        )
    return run_dir


def _one(report: dict) -> dict:
    assert report["run_count"] == 1
    return report["runs"][0]


# ---------------------------------------------------------------------------
# every generation of run metadata on disk is "a run is recorded"
# ---------------------------------------------------------------------------


def test_current_framework_metadata_records_run_request_and_window(
    tmp_path: Path,
) -> None:
    root = _raw_root(tmp_path / "datasets")
    _run(
        root,
        "20261013T000000Z-probe-cbd",
        {
            "run_id": "20261013T000000Z-probe-cbd",
            "source_id": "probe",
            "query": {"keyword": "CBD"},
            "window": {"start": "2025-10-13T00:00:00Z", "end": "2026-10-13"},
        },
    )
    run = _one(build_adoption_backlog(tmp_path / "datasets"))
    assert run["state"] == "run_metadata"
    assert run["request_recorded"] is True
    assert run["window_recorded"] is True
    assert run["run_id_matches_directory"] is True


def test_pipeline_metadata_records_request_and_window_when_nested(
    tmp_path: Path,
) -> None:
    """The framework nests both facts under ``*_provenance``; a flat scan
    would report a fully declared run as undeclared."""

    root = _raw_root(tmp_path / "datasets")
    _run(
        root,
        "20261023T171700Z-probe-setA",
        {
            "run_id": "20261023T171700Z-probe-setA",
            "source_id": "probe",
            "query_provenance": {"query_id": "comparison-5y-setA"},
            "temporal_provenance": {
                "requested_start": "2021-10-17T00:00:00Z",
                "requested_end_exclusive": "2026-10-18T00:00:00Z",
            },
        },
    )
    run = _one(build_adoption_backlog(tmp_path / "datasets"))
    assert run["state"] == "run_metadata"
    assert run["request_recorded"] is True
    assert run["window_recorded"] is True


def test_legacy_google_trends_metadata_counts_as_run_metadata(tmp_path: Path) -> None:
    """The legacy shape records the request as ``queries`` and the time as a
    relative ``timeframe``.  Reading it as "unrecognized" would hide 25 real
    runs behind a vocabulary difference."""

    root = _raw_root(tmp_path / "datasets")
    _run(
        root,
        "20261002T063821Z-probe-cbd",
        {
            "run_id": "20261002T063821Z-probe-cbd",
            "source": "google-trends",
            "queries": [{"term": "CBD", "timeframe": "today 12-m"}],
        },
    )
    run = _one(build_adoption_backlog(tmp_path / "datasets"))
    assert run["state"] == "run_metadata"
    assert run["request_recorded"] is True
    # A relative timeframe is not an absolute window: a declaration still has
    # to state the window it was resolved to.
    assert run["window_recorded"] is False


def test_apify_style_metadata_keeps_its_run_id_mismatch_visible(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    _run(
        root,
        "20261002T064739Z-probe-cbd",
        {
            "run_id": "ZU6YwuNB053SWv7sz",
            "source": "probe",
            "search_term": "CBD",
            "max_videos": 100,
        },
    )
    run = _one(build_adoption_backlog(tmp_path / "datasets"))
    assert run["state"] == "run_metadata"
    assert run["request_recorded"] is True
    assert run["window_recorded"] is False
    assert run["run_id_matches_directory"] is False


# ---------------------------------------------------------------------------
# the states that a declaration cannot be built from at all
# ---------------------------------------------------------------------------


def test_vendor_envelope_is_not_a_collection_record(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    _run(
        root,
        "20261001T074851Z-probe-cbd",
        {"id": "cIAc3Ii2oIeLYN0vF", "status": "SUCCEEDED"},
    )
    report = build_adoption_backlog(tmp_path / "datasets")
    run = _one(report)
    assert run["state"] == "vendor_envelope"
    assert run["request_recorded"] is False
    assert report["no_run_metadata_count"] == 1


def test_missing_metadata_is_reported_with_the_directory_shape(
    tmp_path: Path,
) -> None:
    root = _raw_root(tmp_path / "datasets")
    _run(root, "20261013T000000Z-probe-cbd")
    _run(root, "probe-archive", files=3)
    report = build_adoption_backlog(tmp_path / "datasets")
    by_name = {run["run_dir"]: run for run in report["runs"]}
    assert by_name["20261013T000000Z-probe-cbd"]["state"] == "metadata_missing"
    assert by_name["20261013T000000Z-probe-cbd"]["run_id_form"] is True
    # Not run-shaped is a layout divergence, still reported, never skipped.
    assert by_name["probe-archive"]["run_id_form"] is False
    assert report["no_run_metadata_count"] == 2


def test_unrecognized_metadata_is_neither_run_nor_vendor(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    _run(root, "20261013T000000Z-probe-cbd", {"collection_date": "2026-10-06"})
    run = _one(build_adoption_backlog(tmp_path / "datasets"))
    assert run["state"] == "metadata_unrecognized"


def test_unreadable_metadata_is_a_violation(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    _run(root, "20261013T000000Z-probe-cbd", "{ not json")
    report = build_adoption_backlog(tmp_path / "datasets")
    assert report["runs"][0]["state"] == "metadata_unreadable"
    assert [v["run_dir"] for v in report["violations"]] == [
        "20261013T000000Z-probe-cbd"
    ]


def test_empty_run_directory_is_a_violation(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    _run(root, "20261013T000000Z-probe-cbd", files=0)
    report = build_adoption_backlog(tmp_path / "datasets")
    assert report["empty_run_count"] == 1
    assert len(report["violations"]) == 1


# ---------------------------------------------------------------------------
# payload that is not in a run directory at all
# ---------------------------------------------------------------------------


def test_loose_payload_files_are_counted_separately(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    (root / "export.csv").write_text("a\n", encoding="utf-8")
    (root / ".gitkeep").write_text("", encoding="utf-8")
    report = build_adoption_backlog(tmp_path / "datasets")
    assert report["run_count"] == 0
    assert report["loose_file_count"] == 1
    assert report["loose_files"][0]["name"] == "export.csv"


# ---------------------------------------------------------------------------
# exclusions, catalog membership, and read-only behaviour
# ---------------------------------------------------------------------------


def test_private_and_quarantine_are_skipped_unless_requested(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    for name in sorted(SKIPPED_DIRECTORY_NAMES):
        _run(root, name)
    assert build_adoption_backlog(tmp_path / "datasets")["run_count"] == 0
    assert (
        build_adoption_backlog(tmp_path / "datasets", include_private=True)["run_count"]
        == len(SKIPPED_DIRECTORY_NAMES)
    )


def test_catalog_membership_is_reported_not_decided(tmp_path: Path) -> None:
    datasets = tmp_path / "datasets"
    root = _raw_root(datasets)
    _run(root, "20261013T000000Z-probe-cbd", {"run_id": "x"})
    _run(root, "20261013T000000Z-probe-thc", {"run_id": "y"})
    catalog = datasets / "probe-study" / "metadata" / "data-catalog.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "path": (
                            "raw/probe/20261013T000000Z-probe-cbd/payload_0.json"
                        )
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report = build_adoption_backlog(datasets)
    by_name = {run["run_dir"]: run for run in report["runs"]}
    assert by_name["20261013T000000Z-probe-cbd"]["catalogued"] is True
    assert by_name["20261013T000000Z-probe-thc"]["catalogued"] is False
    assert report["uncatalogued_count"] == 1


def test_audit_reads_metadata_and_writes_nothing(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    run_dir = _run(root, "20261013T000000Z-probe-cbd", {"run_id": "x"})
    before = {path.name: path.read_bytes() for path in run_dir.iterdir()}
    build_adoption_backlog(tmp_path / "datasets")
    after = {path.name: path.read_bytes() for path in run_dir.iterdir()}
    assert after == before


def test_absent_datasets_root_is_an_empty_backlog(tmp_path: Path) -> None:
    report = build_adoption_backlog(tmp_path / "datasets")
    assert report["run_count"] == 0
    assert report["violations"] == []


# ---------------------------------------------------------------------------
# the rule itself: nothing under raw/<source>/ can be invisible
# ---------------------------------------------------------------------------


def test_every_raw_directory_appears_exactly_once(tmp_path: Path) -> None:
    root = _raw_root(tmp_path / "datasets")
    shapes = {
        "20261013T000000Z-probe-a": {"run_id": "20261013T000000Z-probe-a"},
        "20261013T000000Z-probe-b": {"id": "vendor", "status": "ok"},
        "20261013T000000Z-probe-c": {"note": "no identity"},
        "20261013T000000Z-probe-d": None,
        "probe-archive": None,
    }
    for name, metadata in shapes.items():
        _run(root, name, metadata)
    report = build_adoption_backlog(tmp_path / "datasets")
    seen = [run["run_dir"] for run in report["runs"]]
    assert sorted(seen) == sorted(shapes)
    assert len(seen) == len(set(seen))
    assert sum(report["states"].values()) == report["run_count"]


def test_repository_report_is_internally_consistent() -> None:
    """The committed raw layer may or may not be on this machine, but the
    report must always describe itself."""

    report = build_adoption_backlog(REPO_ROOT / "datasets")
    assert report["run_count"] == len(report["runs"])
    assert sum(report["states"].values()) == report["run_count"]
    assert report["run_metadata_count"] + report["no_run_metadata_count"] == (
        report["run_count"]
    )
    for run in report["runs"]:
        assert run["state"] in report["states"]
        assert run["reason"]
