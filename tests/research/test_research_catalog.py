"""G7 research catalog / discovery tests (G7-T06/T07/T08/T09, P2/P4).

Contract sources: g.md \u00a75 (catalog), \u00a713 (API), \u00a717 tests.
"""

import json
from pathlib import Path

from research.catalog import (
    DISCOVERY_NOTE,
    build_catalog,
    find_artifacts,
    get_provenance,
)
from validation.reporting import dump_json

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "datasets"


def _catalog() -> dict:
    return build_catalog(DATASETS, repo_root=REPO_ROOT)


def test_catalog_builds_from_existing_runs_only():
    catalog = _catalog()
    assert catalog["entry_count"] == len(list(DATASETS.rglob("run_metadata.json")))
    assert catalog["errors"] == []


def test_g7_t06_catalog_rebuild_is_deterministic():
    first = dump_json(_catalog())
    second = dump_json(_catalog())
    assert first == second


def test_g7_t07_source_discovery_finds_both_slice_studies():
    result = find_artifacts(_catalog(), source_id="google-trends")
    studies = {e["study_id"] for e in result["entries"]}
    assert {"cbx-search-trends", "cannabinoid-multi-trends"} <= studies


def test_g7_t08_compound_discovery_spans_studies_without_moving_data():
    """P2: discovery returns pointers; datasets/ layout is untouched."""
    result = find_artifacts(_catalog(), compound_id="compound_cbx")
    studies = {e["study_id"] for e in result["entries"]}
    assert {"cbx-search-trends", "cannabinoid-multi-trends"} <= studies
    assert result["match_count"] >= 2


def test_g7_t09_period_discovery_matches_collection_timestamps_only():
    result = find_artifacts(
        _catalog(),
        source_id="google-trends",
        start="2026-10-01T00:00:00Z",
        end="2026-10-03T00:00:00Z",
    )
    assert result["match_count"] >= 2
    for entry in result["entries"]:
        assert "2026-10-01T00:00:00Z" <= entry["collection_timestamp"] <= "2026-10-03T00:00:00Z"


def test_discovery_responses_carry_the_p4_note():
    catalog = _catalog()
    assert catalog["discovery_note"] == DISCOVERY_NOTE
    assert find_artifacts(catalog)["discovery_note"] == DISCOVERY_NOTE


def test_unlinked_terms_are_not_guessed():
    """Terms without an exact registry match link to nothing (no inference)."""
    catalog = _catalog()
    unlinked = [e for e in catalog["entries"] if e["compound_link_rule"] == "no_match"]
    assert unlinked, "expected at least one run without exact term matches"
    for entry in unlinked:
        assert entry["compound_ids"] == []
        assert entry["query_ids"] == []
