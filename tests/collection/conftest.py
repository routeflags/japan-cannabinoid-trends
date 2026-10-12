"""Shared helpers for the collection core contract tests (G1 §15).

All tests are offline: the Google Trends adapter runs on the synthetic
replay fixtures under ``fixtures/google_trends`` and no live collection is
ever executed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures" / "google_trends"
REPO_CONFIG = REPO_ROOT / "config"
REPO_METADATA = REPO_ROOT / "metadata"

FIXTURE_12M = FIXTURES / "interest_over_time_cbx_rikiddo_12m.json"
FIXTURE_5Y = FIXTURES / "interest_over_time_cbx_rikiddo_5y.json"

#: The real recorded series file (tracked in git, read-only in tests).
RECORDED_CBD_5Y = (
    REPO_ROOT
    / "datasets"
    / "cannabinoid-multi-trends"
    / "data"
    / "raw"
    / "google_trends"
    / "20261012T064246Z-google-trends-ja-rikiddo-5y-main5"
    / "records_cbd-rikiddo-5y.json"
)

STUDY_ID = "cbx-search-trends"


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def make_plan(
    *,
    term: str = "CBX リキッド",
    timeframe: str = "today 12-m",
    geo: str = "JP",
    start: str = "2025-10-12T00:00:00Z",
    end_exclusive: str = "2026-10-12T00:00:00Z",
    window_id: str = "2025-10-12_2026-10-12",
    granularity: str = "week",
    week_start: str = "sunday",
    required_capabilities=("geo_filter", "relative_date_range"),
    collector_id: str | None = "google-trends-mcp",
    source_id: str = "google-trends",
    study_id: str = STUDY_ID,
    query_id: str = "cbx-rikiddo-ja",
    compound_id: str = "CBX",
    purpose: str = "G1 collection contract test (synthetic replay)",
) -> dict:
    plan = {
        "plan_id": "plan-test-001",
        "study_id": study_id,
        "source_id": source_id,
        "query_id": query_id,
        "query": {
            "text": term,
            "geo": geo,
            "timeframe": timeframe,
            "compound_id": compound_id,
        },
        "required_capabilities": list(required_capabilities),
        "window": {
            "window_id": window_id,
            "start": start,
            "end_exclusive": end_exclusive,
            "granularity": granularity,
            "week_start": week_start,
            "timezone": "Asia/Tokyo",
        },
        "purpose": purpose,
    }
    if collector_id is not None:
        plan["collector_id"] = collector_id
    return plan


def make_workspace(tmp_path: Path, *, studies=(STUDY_ID,)) -> Path:
    """A scratch workspace with a datasets root for the catalog."""
    root = tmp_path / "workspace"
    for study_id in studies:
        (root / "datasets" / study_id).mkdir(parents=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def registries():
    """The real repository registries (config/ + metadata/)."""
    from collection.core.registry import load_registries

    return load_registries(REPO_CONFIG, REPO_METADATA)


def capabilities_of(registries, collector_id: str) -> dict:
    for collector in registries.collectors:
        if collector.get("collector_id") == collector_id:
            return collector.get("capabilities")
    raise AssertionError(f"collector not in registry: {collector_id}")


def build_replay_adapter(registries, fixture, collector_id: str = "google-trends-mcp"):
    from collection.adapters import get_adapter_factory

    factory = get_adapter_factory("google-trends")
    return factory(fixture=fixture, capabilities=capabilities_of(registries, collector_id))
