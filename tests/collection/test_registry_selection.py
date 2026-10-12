"""Registry + capability/selection gate tests (G1 §7 / §9 / §15).

Covers the a.md §15 contract table rows that are decided before collection:
unregistered source / collector, collector-source mismatch, missing
capability (refuse), unknown capability (never auto-selected), and the
fictional-source test (a new source is recognised from registry data alone).
"""

import json

from validation.core import validate_document
from validation.schema_registry import get_schema
from validation.semantic import Registries

from collection.core.registry import (
    collectors_for_source,
    find_collector,
    find_source,
    load_registries,
)
from collection.core.selection import select_collector

from conftest import REPO_CONFIG, make_plan


# ---------------------------------------------------------------------------
# The real repository registries
# ---------------------------------------------------------------------------


def test_repo_source_registry_is_structurally_valid():
    document = json.loads((REPO_CONFIG / "sources.json").read_text(encoding="utf-8"))
    assert validate_document(document, get_schema("source-registry-v1")).valid is True


def test_repo_collector_registry_is_structurally_valid():
    document = json.loads((REPO_CONFIG / "collectors.json").read_text(encoding="utf-8"))
    assert validate_document(document, get_schema("collector-registry-v1")).valid is True


def test_repo_registries_have_exactly_one_active_collector(registries):
    active = [
        collector
        for collector in registries.collectors
        if collector.get("status") == "active"
    ]
    assert [collector["collector_id"] for collector in active] == ["google-trends-mcp"]


def test_registry_helpers(registries):
    assert find_source(registries, "google-trends")["kind"] == "search"
    assert find_source(registries, "nope") is None
    assert find_collector(registries, "google-trends", "google-trends-mcp") is not None
    # A collector is never found under a different source (mis-wiring).
    assert find_collector(registries, "x", "google-trends-mcp") is None
    assert {c["collector_id"] for c in collectors_for_source(registries, "youtube")} == {
        "youtube-apify-scraper",
        "youtube-apify-search",
    }


# ---------------------------------------------------------------------------
# Selection gate (G1 §9)
# ---------------------------------------------------------------------------


def test_selects_the_google_trends_collector(registries):
    collector, issues = select_collector(make_plan(), registries)
    assert issues == []
    assert collector["collector_id"] == "google-trends-mcp"


def test_selects_the_collector_when_none_is_requested(registries):
    plan = make_plan(collector_id=None)
    collector, issues = select_collector(plan, registries)
    assert issues == []
    assert collector["collector_id"] == "google-trends-mcp"


def test_unknown_capability_is_never_auto_selected(registries):
    """a.md §15: Capability unknown -> no automatic selection (fail closed)."""
    plan = make_plan(required_capabilities=("geo_filter", "language_filter"))
    collector, issues = select_collector(plan, registries)
    assert collector is None
    codes = [issue.code for issue in issues]
    assert "GATE_CAPABILITY_UNKNOWN" in codes


def test_unknown_absolute_date_range_is_refused(registries):
    """The registry records absolute_date_range=unknown for google-trends-mcp;
    a plan needing it must stop (unknown is not unsupported, but neither is
    it support)."""
    plan = make_plan(required_capabilities=("geo_filter", "absolute_date_range"))
    collector, issues = select_collector(plan, registries)
    assert collector is None
    assert "GATE_CAPABILITY_UNKNOWN" in [issue.code for issue in issues]


def test_unsupported_capability_reports_unsupported():
    registries = Registries.from_documents(
        source_registry={"sources": [{"source_id": "s", "kind": "k"}]},
        collector_registry={
            "collectors": [
                {
                    "collector_id": "c",
                    "source_id": "s",
                    "adapter_id": "c@1",
                    "status": "active",
                    "capabilities": {"geo_filter": "unsupported"},
                }
            ]
        },
    )
    collector, issues = select_collector(
        {"source_id": "s", "collector_id": "c", "required_capabilities": ["geo_filter"]},
        registries,
    )
    assert collector is None
    assert [issue.code for issue in issues] == ["GATE_CAPABILITY_UNSUPPORTED"]


def test_unregistered_source_is_refused(registries):
    """google-search-console has no collector: fail closed."""
    plan = make_plan(source_id="google-search-console", collector_id=None)
    collector, issues = select_collector(plan, registries)
    assert collector is None
    assert "GATE_NO_COLLECTOR_FOR_SOURCE" in [issue.code for issue in issues]


def test_unregistered_source_id_is_refused(registries):
    plan = make_plan(source_id="no-such-source", collector_id=None)
    collector, issues = select_collector(plan, registries)
    assert collector is None
    assert "GATE_NO_COLLECTOR_FOR_SOURCE" in [issue.code for issue in issues]


def test_unregistered_collector_is_refused(registries):
    plan = make_plan(collector_id="ghost-collector")
    collector, issues = select_collector(plan, registries)
    assert collector is None
    assert "GATE_COLLECTOR_UNREGISTERED" in [issue.code for issue in issues]


def test_collector_source_mismatch_is_refused(registries):
    """a.md §15: Collector and source mismatch -> FAIL."""
    plan = make_plan(source_id="youtube", collector_id="google-trends-mcp")
    collector, issues = select_collector(plan, registries)
    assert collector is None
    assert "GATE_COLLECTOR_UNREGISTERED" in [issue.code for issue in issues]


def test_unverified_collector_is_refused(registries):
    """x-apify-twitter-search is registered but not active: no collection."""
    plan = make_plan(source_id="x", collector_id="x-apify-twitter-search")
    collector, issues = select_collector(plan, registries)
    assert collector is None
    assert "GATE_COLLECTOR_NOT_ACTIVE" in [issue.code for issue in issues]


def test_ambiguous_selection_requires_an_explicit_plan():
    registries = Registries.from_documents(
        collector_registry={
            "collectors": [
                {
                    "collector_id": f"c{index}",
                    "source_id": "s",
                    "adapter_id": f"c{index}@1",
                    "status": "active",
                    "capabilities": {"geo_filter": "supported"},
                }
                for index in (1, 2)
            ]
        }
    )
    collector, issues = select_collector(
        {"source_id": "s", "required_capabilities": ["geo_filter"]}, registries
    )
    assert collector is None
    assert [issue.code for issue in issues] == ["GATE_COLLECTOR_AMBIGUOUS"]


def test_non_mapping_plan_is_refused(registries):
    collector, issues = select_collector([], registries)
    assert collector is None
    assert [issue.code for issue in issues] == ["GATE_PLAN_INVALID"]


# ---------------------------------------------------------------------------
# Fictional source (a.md §15 item 1): registry data alone adds a source
# ---------------------------------------------------------------------------


def test_fictional_source_is_recognised_from_registry_data(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "sources.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "sources": [
                    {"source_id": "test-social-platform", "kind": "social"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (config / "collectors.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "collectors": [
                    {
                        "collector_id": "test-social-example",
                        "source_id": "test-social-platform",
                        "adapter_id": "test-social-example@1",
                        "status": "unverified",
                        "capabilities": {"absolute_date_range": "unknown"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert validate_document(
        json.loads((config / "sources.json").read_text(encoding="utf-8")),
        get_schema("source-registry-v1"),
    ).valid
    assert validate_document(
        json.loads((config / "collectors.json").read_text(encoding="utf-8")),
        get_schema("collector-registry-v1"),
    ).valid

    registries = load_registries(config, tmp_path / "metadata")
    plan = {
        "source_id": "test-social-platform",
        "collector_id": "test-social-example",
        "required_capabilities": ["absolute_date_range"],
    }
    collector, issues = select_collector(plan, registries)
    assert collector is None
    assert "GATE_COLLECTOR_NOT_ACTIVE" in [issue.code for issue in issues]

    # The same source becomes selectable once its capabilities are verified
    # and the entry is activated - no core change required.
    entry = registries.collectors[0]
    entry["status"] = "active"
    entry["capabilities"]["absolute_date_range"] = "supported"
    collector, issues = select_collector(plan, Registries.from_documents(
        collector_registry={"collectors": [entry]}
    ))
    assert issues == []
    assert collector["collector_id"] == "test-social-example"
