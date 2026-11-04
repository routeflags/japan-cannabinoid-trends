"""Common-scale comparison declaration, gates and audit (ISS-20261105-GT-030).

The scenarios below are the acceptance cases for the rule: a valid CBD+THC
common-scale plan, each missing anchor, an anchor outside the same
``compare_terms`` request, a mismatched window / geo / timeframe / locale, a
single-series plan that stays allowed but is marked non-comparable, and an
adopted comparison artifact that is missing an anchor.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from validation.cli import main as validation_main
from validation.comparison_scale import (
    build_comparison_scale_audit,
    check_comparison_design,
    check_plan_comparison,
    check_run_comparison,
)
from validation.gates import pre_collection_gate
from validation.semantic import Registries

from collection.adapters import get_adapter_factory
from collection.core.contracts import CollectionResult
from collection.core.pipeline import run_collection
from collection.core.provenance import build_run_metadata
from collection.core.registry import load_registries

STUDY_ID = "cannabinoid-raw-collection"
POLICY_ID = "gt-5y-common-scale-cbd-thc"
WINDOW_ID = "2021-10-17_2026-10-18"

QUERIES = [
    {
        "query_id": "cbd-general-ja",
        "compound_id": "compound_cbd",
        "intent_id": "compound_general",
        "language": "ja",
        "canonical_text": "CBD",
        "status": "active",
    },
    {
        "query_id": "thc-general-ja",
        "compound_id": "compound_thc",
        "intent_id": "compound_general",
        "language": "ja",
        "canonical_text": "THC",
        "status": "active",
    },
    {
        "query_id": "thcnm-general-ja",
        "compound_id": "compound_thcnm",
        "intent_id": "compound_general",
        "language": "ja",
        "canonical_text": "THCNM",
        "status": "active",
    },
    {
        "query_id": "cbg-general-ja",
        "compound_id": "compound_cbg",
        "intent_id": "compound_general",
        "language": "ja",
        "canonical_text": "CBG",
        "status": "active",
    },
    {
        "query_id": "cbx-general-ja",
        "compound_id": "compound_cbx",
        "intent_id": "compound_general",
        "language": "ja",
        "canonical_text": "CBX",
        "status": "active",
    },
    {
        "query_id": "cbd-oil-en",
        "compound_id": "compound_cbd",
        "intent_id": "product_oil",
        "language": "en",
        "canonical_text": "CBD oil",
        "status": "active",
    },
    {
        "query_id": "comparison-5y-setA",
        "compound_id": "compound_cbd",
        "intent_id": "other",
        "language": "ja",
        "canonical_text": "CBD vs THC vs CBG",
        "status": "active",
    },
    {
        "query_id": "comparison-thcnm-anchored",
        "compound_id": "compound_thcnm",
        "intent_id": "other",
        "language": "ja",
        "canonical_text": "CBD vs THC vs THCNM",
        "status": "active",
    },
]

WINDOWS = [
    {
        "temporal_contract_version": "1.0.0",
        "window_id": WINDOW_ID,
        "timezone": "Asia/Tokyo",
        "start": "2021-10-17T00:00:00Z",
        "end_exclusive": "2026-10-18T00:00:00Z",
        "granularity": "week",
        "week_start": "sunday",
        "calendar": "gregorian",
    }
]


def _policy(**overrides) -> dict:
    policy = {
        "scale_id": POLICY_ID,
        "source_id": "google-trends",
        "comparison_scale": "common_scale",
        "anchor_query_ids": ["cbd-general-ja", "thc-general-ja"],
        "anchor_terms": ["CBD", "THC"],
        "request": {
            "tool": "compare_terms",
            "geo": "JP",
            "locale": "ja",
            "timeframe": "today 5-y",
            "window_id": WINDOW_ID,
        },
        "compound_set": {
            "authority": "query registry compound_general queries",
            "excluded_compound_ids": [
                {"compound_id": "compound_cbx", "reason": "CBX raw is in the CBX study"}
            ],
        },
        "rationale": "single-term series are peak-normalized",
        "decided": "2026-11-05",
        "decided_by": "owner",
    }
    policy.update(overrides)
    return policy


def _design(policies=None) -> dict:
    return {
        "schema_version": "1.0.0",
        "study_id": STUDY_ID,
        "query_designs": [],
        "comparison_scales": policies if policies is not None else [_policy()],
    }


def _plan(**overrides) -> dict:
    plan = {
        "plan_id": "gt-5y-common-scale-thcnm",
        "study_id": STUDY_ID,
        "source_id": "google-trends",
        "collector_id": "google-trends-mcp",
        "query_id": "comparison-thcnm-anchored",
        "query": {
            "terms": ["CBD", "THC", "THCNM"],
            "geo": "JP",
            "timeframe": "today 5-y",
            "compound_id": "compound_thcnm",
            "text": "CBD vs THC vs THCNM",
        },
        "comparison": {
            "comparison_scale": "common_scale",
            "policy_id": POLICY_ID,
            "anchor_query_ids": ["cbd-general-ja", "thc-general-ja"],
            "anchor_terms": ["CBD", "THC"],
            "locale": "ja",
        },
        "required_capabilities": ["geo_filter", "relative_date_range"],
        "window": {
            "window_id": WINDOW_ID,
            "start": "2021-10-17T00:00:00Z",
            "end_exclusive": "2026-10-18T00:00:00Z",
            "granularity": "week",
            "week_start": "sunday",
            "timezone": "Asia/Tokyo",
        },
        "purpose": "test plan",
    }
    plan.update(overrides)
    return plan


def _registries() -> Registries:
    return Registries.from_documents(
        source_registry={"sources": [{"source_id": "google-trends"}]},
        collector_registry={
            "collectors": [
                {
                    "collector_id": "google-trends-mcp",
                    "source_id": "google-trends",
                    "adapter_id": "google-trends-mcp@1",
                    "status": "active",
                    "capabilities": {
                        "geo_filter": "supported",
                        "relative_date_range": "supported",
                    },
                }
            ]
        },
        query_registry={"schema_version": "1.0.0", "queries": QUERIES},
    )


def _codes(issues) -> list[str]:
    return [issue.code for issue in issues]


def _errors(issues) -> list[str]:
    return [issue.code for issue in issues if issue.severity == "error"]


# ---------------------------------------------------------------------------
# Pre-collection plan checks
# ---------------------------------------------------------------------------


def test_valid_cbd_thc_common_scale_plan_is_accepted():
    issues = check_plan_comparison(
        _plan(), policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert _errors(issues) == []

    gate = pre_collection_gate(_plan(), registries=_registries())
    assert gate.passed is True
    assert gate.action == "proceed"


def test_missing_cbd_anchor_is_refused():
    plan = _plan()
    plan["query"]["terms"] = ["THC", "THCNM"]
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_ANCHOR_NOT_IN_REQUEST" in _codes(issues)

    gate = pre_collection_gate(plan, registries=_registries())
    assert gate.passed is False
    assert gate.action == "stop"


def test_missing_thc_anchor_is_refused():
    plan = _plan()
    plan["query"]["terms"] = ["CBD", "THCNM"]
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_ANCHOR_NOT_IN_REQUEST" in _codes(issues)


def test_anchor_declared_outside_the_same_compare_terms_request_is_refused():
    plan = _plan()
    plan["query"]["terms"] = ["CBD", "CBG", "THCNM"]
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_ANCHOR_NOT_IN_REQUEST" in _codes(issues)


def test_anchor_query_whose_canonical_text_is_not_declared_is_refused():
    plan = _plan()
    plan["comparison"]["anchor_query_ids"] = ["cbd-general-ja", "thc-general-ja"]
    plan["comparison"]["anchor_terms"] = ["CBD"]
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_ANCHOR_TERM_UNDECLARED" in _codes(issues)
    assert "COMPARISON_ANCHOR_SET_INCOMPLETE" in _codes(issues)


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (
            lambda plan: plan["window"].update({"window_id": "2021-10-10_2026-10-12"}),
            "COMPARISON_WINDOW_MISMATCH",
        ),
        (lambda plan: plan["query"].update({"geo": "US"}), "COMPARISON_GEO_MISMATCH"),
        (
            lambda plan: plan["query"].update({"timeframe": "today 12-m"}),
            "COMPARISON_TIMEFRAME_MISMATCH",
        ),
        (
            lambda plan: plan["comparison"].update({"locale": "en"}),
            "COMPARISON_LOCALE_MISMATCH",
        ),
        (
            lambda plan: plan["query"]["terms"].append("CBD oil"),
            "COMPARISON_LOCALE_MISMATCH",
        ),
    ],
)
def test_mismatched_request_conditions_are_refused(mutate, expected):
    plan = _plan()
    mutate(plan)
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert expected in _codes(issues)


def test_multi_term_plan_without_a_declaration_is_refused():
    plan = _plan()
    del plan["comparison"]
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_SCALE_UNDECLARED" in _codes(issues)

    gate = pre_collection_gate(plan, registries=_registries())
    assert gate.passed is False


def test_single_series_plan_is_allowed_but_marked_non_comparable():
    plan = _plan(
        query_id="thcnm-general-ja",
        query={
            "text": "THCNM",
            "geo": "JP",
            "timeframe": "today 5-y",
            "compound_id": "compound_thcnm",
        },
        comparison={"comparison_scale": "single_series"},
    )
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert _errors(issues) == []
    assert "COMPARISON_NOT_COMPARABLE" in _codes(issues)
    assert all(issue.severity == "info" for issue in issues)

    gate = pre_collection_gate(plan, registries=_registries())
    assert gate.passed is True

    document = _run_metadata(plan)
    assert document["comparison"]["comparison_scale"] == "single_series"
    assert document["comparison"]["cross_compound_comparable"] is False


def test_single_series_plan_cannot_request_multiple_terms():
    plan = _plan()
    plan["comparison"] = {"comparison_scale": "single_series"}
    issues = check_plan_comparison(
        plan, policies=[_policy()], queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_SINGLE_SERIES_MULTI_TERM" in _codes(issues)


# ---------------------------------------------------------------------------
# Run metadata / adoption checks
# ---------------------------------------------------------------------------


def _run_metadata(plan: dict) -> dict:
    collector_entry = {
        "collector_id": "google-trends-mcp",
        "adapter_id": "google-trends-mcp@1",
        "version": "0.1.1",
    }
    result = CollectionResult(
        raw=None,
        status="success",
        returned_count=3,
        errors=[],
        pagination_exhausted=True,
        completeness="complete",
        submitted_parameters={
            "tool": "compare_terms" if plan["query"].get("terms") else "interest_over_time",
            **{key: plan["query"].get(key) for key in ("terms", "geo", "timeframe")},
        },
        temporal={"granularity": "week", "week_start": "sunday"},
    )

    class _Adapter:
        adapter_id = "google-trends-mcp@1"
        version = "0.1.1"

    from datetime import datetime, timezone

    return build_run_metadata(
        plan=plan,
        collector_entry=collector_entry,
        adapter=_Adapter(),
        result=result,
        run_id="20261105T000000Z-google-trends-test",
        started_at=datetime(2026, 11, 5, tzinfo=timezone.utc),
        finished_at=datetime(2026, 11, 5, tzinfo=timezone.utc),
        artifact_manifest_name="artifact-manifest.json",
        window_id=plan["window"]["window_id"],
    )


def _comparison_run(tmp_path: Path, *, artifact_terms, request_terms, window_id=WINDOW_ID):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    artifact = {
        "terms": list(artifact_terms),
        "geo": "JP",
        "timeframe": "today 5-y",
        "data": [
            {"date": "2021-10-17", **{term: 1 for term in artifact_terms}}
        ],
    }
    (run_dir / "comparison_cbd-thc-thcnm.json").write_text(
        json.dumps(artifact), encoding="utf-8"
    )
    manifest = {
        "schema_version": "1.0.0",
        "run_id": "20261105T000000Z-google-trends-test",
        "artifacts": [
            {
                "artifact_id": "artifact-comparison",
                "path": "comparison_cbd-thc-thcnm.json",
                "artifact_type": "comparison",
                "format": "json",
                "schema_id": "google-trends-comparison-v1",
                "byte_length": 1,
                "sha256": "0" * 64,
                "layer": "raw",
                "completeness": "complete",
            }
        ],
    }
    document = {
        "run_id": "20261105T000000Z-google-trends-test",
        "study_id": STUDY_ID,
        "source_id": "google-trends",
        "comparison": {
            "comparison_scale": "common_scale",
            "cross_compound_comparable": True,
            "policy_id": POLICY_ID,
            "anchor_query_ids": ["cbd-general-ja", "thc-general-ja"],
            "anchor_terms": ["CBD", "THC"],
            "locale": "ja",
            "geo": "JP",
            "timeframe": "today 5-y",
        },
        "temporal_provenance": {
            "window_id": window_id,
            "submitted_parameters": {
                "tool": "compare_terms",
                "terms": list(request_terms),
                "geo": "JP",
                "timeframe": "today 5-y",
            },
        },
    }
    return run_dir, document, manifest


def test_adopted_comparison_artifact_missing_anchor_is_refused(tmp_path):
    run_dir, document, manifest = _comparison_run(
        tmp_path, artifact_terms=["CBD", "THCNM"], request_terms=["CBD", "THCNM"]
    )
    issues = check_run_comparison(
        document,
        policies=[_policy()],
        queries=QUERIES,
        windows=WINDOWS,
        base_dir=run_dir,
        manifest=manifest,
    )
    assert "COMPARISON_ARTIFACT_ANCHOR_MISSING" in _codes(issues)
    assert "COMPARISON_ANCHOR_NOT_IN_REQUEST" not in _codes(issues)


def test_adopted_comparison_artifact_with_anchors_is_accepted(tmp_path):
    run_dir, document, manifest = _comparison_run(
        tmp_path,
        artifact_terms=["CBD", "THC", "THCNM"],
        request_terms=["CBD", "THC", "THCNM"],
    )
    issues = check_run_comparison(
        document,
        policies=[_policy()],
        queries=QUERIES,
        windows=WINDOWS,
        base_dir=run_dir,
        manifest=manifest,
    )
    assert _errors(issues) == []


def test_adopted_comparison_artifact_with_mismatched_window_is_refused(tmp_path):
    run_dir, document, manifest = _comparison_run(
        tmp_path,
        artifact_terms=["CBD", "THC", "THCNM"],
        request_terms=["CBD", "THC", "THCNM"],
        window_id="2021-10-10_2026-10-12",
    )
    issues = check_run_comparison(
        document,
        policies=[_policy()],
        queries=QUERIES,
        windows=WINDOWS,
        base_dir=run_dir,
        manifest=manifest,
    )
    assert "COMPARISON_WINDOW_MISMATCH" in _codes(issues)


def test_undeclared_comparison_run_is_a_legacy_warning_not_an_error(tmp_path):
    run_dir, document, manifest = _comparison_run(
        tmp_path,
        artifact_terms=["CBD", "THC", "CBG"],
        request_terms=["CBD", "THC", "CBG"],
    )
    del document["comparison"]
    issues = check_run_comparison(
        document,
        policies=[_policy()],
        queries=QUERIES,
        windows=WINDOWS,
        base_dir=run_dir,
        manifest=manifest,
    )
    assert _codes(issues) == ["COMPARISON_LEGACY_UNDECLARED"]
    assert all(issue.severity == "warning" for issue in issues)


# ---------------------------------------------------------------------------
# Design validation and audit
# ---------------------------------------------------------------------------


def test_comparison_design_is_valid():
    issues = check_comparison_design(
        _design(), queries=QUERIES, windows=WINDOWS
    )
    assert issues == []


def test_comparison_design_rejects_duplicate_policy_ids():
    issues = check_comparison_design(
        _design([_policy(), _policy()]), queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_POLICY_ID_DUPLICATE" in _codes(issues)


def test_comparison_design_rejects_unregistered_anchor_and_window():
    policy = _policy(anchor_query_ids=["cbd-general-ja", "ghost-anchor"])
    policy["request"] = dict(policy["request"], window_id="2099-01-01_2099-01-08")
    issues = check_comparison_design(
        _design([policy]), queries=QUERIES, windows=WINDOWS
    )
    assert "COMPARISON_ANCHOR_QUERY_UNREGISTERED" in _codes(issues)
    assert "COMPARISON_WINDOW_UNREGISTERED" in _codes(issues)


def _write_study(tmp_path: Path) -> tuple[Path, Path, Path]:
    datasets_root = tmp_path / "datasets"
    metadata_dir = datasets_root / STUDY_ID / "metadata"
    metadata_dir.mkdir(parents=True)
    design_path = metadata_dir / "query-design.json"
    design_path.write_text(json.dumps(_design(), indent=2), encoding="utf-8")
    registry_path = tmp_path / "query-registry.json"
    registry_path.write_text(
        json.dumps({"schema_version": "1.0.0", "queries": QUERIES}, indent=2),
        encoding="utf-8",
    )
    return datasets_root, design_path, registry_path


def _write_legacy_run(
    datasets_root: Path, run_id: str, terms: list[str], *, window_id: str = WINDOW_ID
) -> None:
    run_dir = datasets_root / STUDY_ID / "data" / "raw" / "google_trends" / run_id
    run_dir.mkdir(parents=True)
    document = {
        "run_id": run_id,
        "study_id": STUDY_ID,
        "source_id": "google-trends",
        "temporal_provenance": {
            "window_id": window_id,
            "submitted_parameters": {
                "tool": "compare_terms",
                "terms": terms,
                "geo": "JP",
                "timeframe": "today 5-y",
            },
        },
    }
    (run_dir / "run_metadata.json").write_text(
        json.dumps(document, indent=2), encoding="utf-8"
    )
    if len(terms) > 1:
        artifact = {
            "terms": terms,
            "geo": "JP",
            "timeframe": "today 5-y",
            "data": [{"date": "2021-10-17", **{term: 1 for term in terms}}],
        }
        (run_dir / "comparison_legacy.json").write_text(
            json.dumps(artifact, indent=2), encoding="utf-8"
        )


def test_audit_reports_missing_compound_and_legacy_coverage(tmp_path):
    datasets_root, design_path, registry_path = _write_study(tmp_path)
    _write_legacy_run(datasets_root, "20261023T171700Z-google-trends-legacy-setA", ["CBD", "THC", "CBG"])
    _write_legacy_run(datasets_root, "20261023T171709Z-google-trends-legacy-setB", ["CBD", "THC", "THCNM"])
    _write_legacy_run(datasets_root, "20261023T171717Z-google-trends-legacy-single", ["CBD"])

    report = build_comparison_scale_audit(
        STUDY_ID,
        query_design_path=design_path,
        query_registry_path=registry_path,
        datasets_root=datasets_root,
    )
    assert report["valid"] is True
    policy = report["policies"][0]
    assert policy["run_count"] == 3
    assert policy["legacy_comparison_run_count"] == 2
    assert policy["single_series_run_count"] == 1
    assert [item["query_id"] for item in policy["missing_compounds"]] == []
    assert [item["query_id"] for item in policy["legacy_covered_compounds"]] == [
        "cbd-general-ja",
        "cbg-general-ja",
        "thc-general-ja",
        "thcnm-general-ja",
    ]
    assert report["missing_compound_count"] == 0

    # The CBX compound is excluded by the declaration, not silently missing.
    assert policy["excluded_compound_queries"] == [
        {
            "compound_id": "compound_cbx",
            "reason": "CBX raw is in the CBX study",
        }
    ]


def test_audit_reports_thcnm_missing_when_only_other_compounds_are_covered(tmp_path):
    datasets_root, design_path, registry_path = _write_study(tmp_path)
    _write_legacy_run(datasets_root, "20261023T171700Z-google-trends-legacy-setA", ["CBD", "THC", "CBG"])

    report = build_comparison_scale_audit(
        STUDY_ID,
        query_design_path=design_path,
        query_registry_path=registry_path,
        datasets_root=datasets_root,
    )
    missing = [item["query_id"] for item in report["missing_compounds"]]
    assert "thcnm-general-ja" in missing
    assert "cbd-general-ja" not in missing
    assert report["failure_count"] >= 1


def test_audit_reports_legacy_missing_anchor_sets(tmp_path):
    datasets_root, design_path, registry_path = _write_study(tmp_path)
    _write_legacy_run(datasets_root, "20261005T100000Z-google-trends-legacy-no-anchor", ["CBG", "CBN"])

    report = build_comparison_scale_audit(
        STUDY_ID,
        query_design_path=design_path,
        query_registry_path=registry_path,
        datasets_root=datasets_root,
    )
    policy = report["policies"][0]
    assert policy["legacy_missing_anchor_run_count"] == 1
    assert policy["legacy_missing_anchor_sets"][0]["missing_anchor_terms"] == ["CBD", "THC"]
    assert report["legacy_missing_anchor_set_count"] == 1


def test_audit_separates_out_of_scope_from_non_comparable_runs(tmp_path):
    """Another window is out of scope; missing anchors are not comparable."""

    datasets_root, design_path, registry_path = _write_study(tmp_path)
    _write_legacy_run(
        datasets_root, "20261023T171700Z-legacy-anchored", ["CBD", "THC", "CBG"]
    )
    _write_legacy_run(
        datasets_root,
        "20261023T171709Z-legacy-other-window",
        ["CBD", "THC", "CBG"],
        window_id="2021-10-10_2026-10-12",
    )
    _write_legacy_run(
        datasets_root, "20261023T171717Z-legacy-no-anchor", ["CBG", "CBN"]
    )

    report = build_comparison_scale_audit(
        STUDY_ID,
        query_design_path=design_path,
        query_registry_path=registry_path,
        datasets_root=datasets_root,
    )
    policy = report["policies"][0]

    # Comparable but undeclared: anchors are present and the conditions match.
    assert [item["run_id"] for item in policy["legacy_undeclared_runs"]] == [
        "20261023T171700Z-legacy-anchored"
    ]
    # A different window is outside the policy, not "not comparable".
    assert [item["run_id"] for item in policy["out_of_scope_runs"]] == [
        "20261023T171709Z-legacy-other-window"
    ]
    assert policy["out_of_scope_runs"][0]["window_id"] == "2021-10-10_2026-10-12"
    # Missing anchors inside the policy conditions cannot be compared.
    assert [item["run_id"] for item in policy["not_comparable_runs"]] == [
        "20261023T171717Z-legacy-no-anchor"
    ]
    assert report["out_of_scope_run_count"] == 1
    assert report["legacy_undeclared_run_count"] == 1
    assert report["not_comparable_run_count"] == 1


def test_audit_design_only_accepts_the_repository_declaration():
    report = build_comparison_scale_audit(
        STUDY_ID,
        query_design_path=(
            "datasets/cannabinoid-raw-collection/metadata/query-design.json"
        ),
        query_registry_path="metadata/queries/query-registry.json",
        query_variants_path="metadata/queries/query-variants.json",
        windows_dir="metadata/windows",
        datasets_root="datasets",
        design_only=True,
    )
    assert report["valid"] is True
    assert report["policy_count"] == 3
    assert [policy["scale_id"] for policy in report["policies"]] == [
        "gt-5y-common-scale-cbd-thc",
        "gt-12m-common-scale-cbd-thc",
        "gt-3m-common-scale-cbd-thc",
    ]
    for policy in report["policies"]:
        assert policy["anchor_terms"] == ["CBD", "THC"]


def test_pipeline_adopts_a_declared_comparison_run_and_the_audit_marks_it_compliant(
    tmp_path,
):
    """End-to-end: plan -> gate -> replay collect -> L1 -> audit (offline)."""

    repo_root = Path(__file__).resolve().parents[2]
    datasets_root = tmp_path / "datasets"
    study_dir = datasets_root / STUDY_ID
    (study_dir / "metadata").mkdir(parents=True)
    design_document = json.loads(
        (
            repo_root
            / "datasets"
            / STUDY_ID
            / "metadata"
            / "query-design.json"
        ).read_text(encoding="utf-8")
    )
    (study_dir / "metadata" / "query-design.json").write_text(
        json.dumps(design_document, indent=2),
        encoding="utf-8",
    )

    # The plan must use the window the repository declaration pins, so this
    # end-to-end test follows the study's current comparison window instead of
    # duplicating it as a constant.
    declared_window_id = design_document["comparison_scales"][0]["request"][
        "window_id"
    ]
    declared_window = json.loads(
        (repo_root / "metadata" / "windows" / f"{declared_window_id}.json").read_text(
            encoding="utf-8"
        )
    )
    plan = _plan(
        window={
            "window_id": declared_window_id,
            "start": declared_window["start"],
            "end_exclusive": declared_window["end_exclusive"],
            "granularity": declared_window.get("granularity", "week"),
            "week_start": declared_window.get("week_start", "sunday"),
            "timezone": declared_window.get("timezone", "Asia/Tokyo"),
        }
    )

    fixture = tmp_path / "comparison_fixture.json"
    text = (
        "Comparison: CBD vs THC vs THCNM\n"
        "Geo: JP | Timeframe: today 5-y\n\n"
        "Average interest scores (0-100):\n"
        "  CBD: 33 <-- highest\n"
        "  THC: 5\n"
        "  THCNM: 0\n\n"
        "Date\tCBD\tTHC\tTHCNM\n"
        "Nov 1 – Nov 7, 2021\t33\t5\t0\n"
    )
    fixture.write_text(
        json.dumps(
            {
                "request": {
                    "tool": "compare_terms",
                    "params": {
                        "terms": ["CBD", "THC", "THCNM"],
                        "geo": "JP",
                        "timeframe": "today 5-y",
                    },
                },
                "response": {"content": [{"type": "text", "text": text}]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    registries = load_registries(repo_root / "config", repo_root / "metadata")
    collector = next(
        item
        for item in registries.collectors
        if item.get("collector_id") == "google-trends-mcp"
    )
    adapter = get_adapter_factory("google-trends")(
        fixture=fixture, capabilities=collector["capabilities"]
    )

    from datetime import datetime, timedelta, timezone

    window_end = datetime.fromisoformat(
        declared_window["end_exclusive"].replace("Z", "+00:00")
    )
    result = run_collection(
        plan,
        adapter=adapter,
        workspace_root=tmp_path / "workspace",
        datasets_root=datasets_root,
        registries=registries,
        run_id="20261105T000000Z-google-trends-comparison-e2e",
        now=window_end - timedelta(days=3),
    )
    assert result.adopted is True, [issue.to_dict() for issue in result.issues]

    run_dir = (
        datasets_root
        / STUDY_ID
        / "data"
        / "raw"
        / "google_trends"
        / "20261105T000000Z-google-trends-comparison-e2e"
    )
    document = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert document["comparison"]["comparison_scale"] == "common_scale"
    assert document["comparison"]["cross_compound_comparable"] is True
    assert document["comparison"]["anchor_terms"] == ["CBD", "THC"]
    assert document["comparison"]["policy_id"] == POLICY_ID
    artifact = json.loads(
        (run_dir / "comparison_cbd-thc-thcnm.json").read_text(encoding="utf-8")
    )
    assert artifact["terms"] == ["CBD", "THC", "THCNM"]

    report = build_comparison_scale_audit(
        STUDY_ID,
        query_design_path=study_dir / "metadata" / "query-design.json",
        query_registry_path=repo_root / "metadata" / "queries" / "query-registry.json",
        query_variants_path=(
            repo_root / "metadata" / "queries" / "query-variants.json"
        ),
        windows_dir=repo_root / "metadata" / "windows",
        datasets_root=datasets_root,
    )
    assert report["valid"] is True
    policy = report["policies"][0]
    assert policy["compliant_run_count"] == 1
    thcnm = next(
        item
        for item in policy["compound_coverage"]
        if item["query_id"] == "thcnm-general-ja"
    )
    assert thcnm["state"] == "complete"
    assert thcnm["run_ids"] == ["20261105T000000Z-google-trends-comparison-e2e"]


def test_cli_audit_comparison_scale_design_only_exits_zero(capsys):
    code = validation_main(["audit-comparison-scale", "--design-only"])
    assert code == 0
    captured = capsys.readouterr()
    assert "comparison-design" in captured.err
