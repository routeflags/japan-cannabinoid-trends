"""G7 research view tests (G7-T18/T19/T20, P6/P8).

Contract sources: g.md \u00a710 (view), \u00a711 (long format), \u00a717.
"""

import csv
import json
from pathlib import Path

import pytest

from research.catalog import build_catalog
from research.views import build_view, validate_view_definition

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"
VIEW_DIR = REPO_ROOT / "research_views" / "cbd-rikiddo-gt-weekly-parallel"


def _definition() -> dict:
    return json.loads((VIEW_DIR / "view-definition.json").read_text(encoding="utf-8"))


def _series() -> list:
    return json.loads((VIEW_DIR / "view-series.json").read_text(encoding="utf-8"))["series"]


def test_g7_t18_view_definition_satisfies_research_view_v1():
    assert validate_view_definition(_definition()) == []


def test_view_builds_four_files_with_lineage(tmp_path):
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    summary = build_view(_definition(), _series(), catalog, repo_root=REPO_ROOT, out_dir=tmp_path)
    assert summary["series_count"] == 3
    assert summary["row_count"] > 0
    for name in ("view-definition.json", "dataset.csv", "comparability-report.json", "provenance.json"):
        assert (tmp_path / name).is_file()
    with (tmp_path / "dataset.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows, "dataset.csv must carry observed rows"
    for row in rows:
        assert row["artifact_ref"], "every row keeps its artifact lineage (\u00a711)"
        assert row["normalization_scale"], "every row keeps its scale (\u00a711)"
        assert row["measurement_id"] == "search_interest_index"
        assert row["unit"] == "relative_index_0_100"
        assert float(row["value"]) >= 0


def test_view_never_aggregates_across_scales(tmp_path):
    """P6 + aggregation ban: parallel display only, scales stay distinct."""
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    summary = build_view(_definition(), _series(), catalog, repo_root=REPO_ROOT, out_dir=tmp_path)
    report = json.loads((tmp_path / "comparability-report.json").read_text(encoding="utf-8"))
    assert report["aggregation_performed"] is False
    assert report["comparison_mode"] == "parallel_timeseries"
    assert summary["direct_comparison_blocked_pairs"] == 2
    with (tmp_path / "dataset.csv").open(encoding="utf-8") as handle:
        scales = {row["normalization_scale"] for row in csv.DictReader(handle)}
    assert len(scales) == 3, "each fetch keeps its own scale (no forced normalization)"


def test_view_records_gt_zero_ambiguity(tmp_path):
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    build_view(_definition(), _series(), catalog, repo_root=REPO_ROOT, out_dir=tmp_path)
    provenance = json.loads((tmp_path / "provenance.json").read_text(encoding="utf-8"))
    assert any("zero" in note for note in provenance["uncertainty_notes"])
    assert provenance["inputs_read_only"] is True
    assert len(provenance["lineage"]) == 3
    for item in provenance["lineage"]:
        assert len(item["artifact_sha256"]) == 64


def test_non_parallel_mode_is_rejected(tmp_path):
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    definition = dict(_definition(), comparison_mode="summed_total")
    with pytest.raises(ValueError):
        build_view(definition, _series(), catalog, repo_root=REPO_ROOT, out_dir=tmp_path)


def test_checked_in_view_outputs_match_rebuild(tmp_path):
    """P8: the checked-in view is reproducible from raw inputs."""
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    summary = build_view(_definition(), _series(), catalog, repo_root=REPO_ROOT, out_dir=tmp_path)
    assert summary["row_count"] == 159
    checked = (VIEW_DIR / "dataset.csv").read_text(encoding="utf-8")
    rebuilt = (tmp_path / "dataset.csv").read_text(encoding="utf-8")
    assert rebuilt == checked


def test_g7_t19_new_study_needs_no_catalog_restructure():
    catalog = build_catalog(DATASETS, repo_root=REPO_ROOT)
    entry = {
        "catalog_entry_id": "future-study:run-1",
        "study_id": "future-study",
        "run_id": "run-1",
        "source_id": "x",
        "compound_ids": ["compound_cbx"],
    }
    catalog["entries"].append(entry)
    from research.catalog import find_artifacts

    assert find_artifacts(catalog, study_id="future-study")["match_count"] == 1


def test_g7_t20_new_source_keeps_catalog_shape():
    from research.catalog import SOURCE_MEASUREMENTS

    assert "google-trends" in SOURCE_MEASUREMENTS
    assert "x" in SOURCE_MEASUREMENTS
