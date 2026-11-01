"""Primary liquid coverage versus retained compound-term runs.

Why this needs its own tests: the dangerous state is a retained bare-term run
being counted as if it completed liquid coverage.  The inventory has to keep
the two sets separate, count one run per query, and still report coverage gaps
without treating a retained run as a failure.
"""

from __future__ import annotations

import json
from pathlib import Path

from validation.youtube_scope import build_youtube_scope


def _write_json(path: Path, document) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _registry(path: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "1.0.0",
            "queries": [
                {
                    "query_id": "cbd-liquid-ja",
                    "compound_id": "compound_cbd",
                    "intent_id": "product_liquid",
                    "language": "ja",
                    "canonical_text": "CBD リキッド",
                    "status": "active",
                },
                {
                    "query_id": "cbn-liquid-ja",
                    "compound_id": "compound_cbn",
                    "intent_id": "product_liquid",
                    "language": "ja",
                    "canonical_text": "CBN リキッド",
                    "status": "active",
                },
                {
                    "query_id": "hhc-general-ja",
                    "compound_id": "compound_hhc",
                    "intent_id": "compound_general",
                    "language": "ja",
                    "canonical_text": "HHC",
                    "status": "active",
                },
                {
                    "query_id": "cbg-research-ja",
                    "compound_id": "compound_cbg",
                    "intent_id": "research",
                    "language": "ja",
                    "canonical_text": "CBG 研究",
                    "status": "active",
                },
            ],
        },
    )


def _design(path: Path) -> None:
    _write_json(
        path,
        {
            "schema_version": "1.0.0",
            "study_id": "probe",
            "query_designs": [
                {
                    "design_id": "liquid-only",
                    "source_id": "youtube",
                    "primary_intent_id": "product_liquid",
                    "query_pattern": "<compound> リキッド",
                    "one_query_per_run": True,
                    "out_of_primary_intent_ids": [
                        "compound_general",
                        "product_oil",
                        "product_other",
                        "other",
                    ],
                }
            ],
        },
    )


def _declaration(path: Path, runs: list[tuple[str, str]]) -> None:
    _write_json(
        path,
        {
            "declaration_version": "staging-declaration-v1",
            "runs": [
                {
                    "run_id": run_id,
                    "study_id": "probe",
                    "source_id": "youtube",
                    "query": {"keyword": keyword, "query_id": query_id},
                    "execution": {"returned_count": 3},
                    "window": {
                        "start": "2026-01-01T00:00:00Z",
                        "end_exclusive": "2026-01-02T00:00:00Z",
                    },
                }
                for run_id, query_id in runs
                for keyword in [query_id]
            ],
        },
    )


def _scope(root: Path, **kwargs):
    return build_youtube_scope(
        "probe",
        query_design_path=root / "query-design.json",
        query_registry_path=root / "query-registry.json",
        declarations_dir=root / "declarations",
        catalog_path=root / "data-catalog.json",
        datasets_root=root / "datasets",
        **kwargs,
    )


def _base(root: Path) -> None:
    _registry(root / "query-registry.json")
    _design(root / "query-design.json")
    _write_json(
        root / "data-catalog.json",
        {
            "catalog_version": "1.0.0",
            "entries": [
                {
                    "run_id": "20260101T000000Z-probe-cbd",
                    "study_id": "probe",
                    "source_id": "youtube",
                    "query_id": "cbd-liquid-ja",
                    "record_count": 3,
                }
            ],
        },
    )
    _declaration(
        root / "declarations" / "d.json",
        [
            ("20260101T000000Z-probe-cbd", "cbd-liquid-ja"),
            ("20260101T000000Z-probe-hhc", "hhc-general-ja"),
        ],
    )


def test_liquid_runs_are_primary_and_bare_terms_are_retained(tmp_path: Path) -> None:
    root = tmp_path
    _base(root)

    report = _scope(root)

    assert report["primary_run_count"] == 1
    assert report["retained_out_of_scope_run_count"] == 1
    assert report["primary_compound_count"] == 1
    assert report["covered_compounds"] == ["compound_cbd"]
    retained = report["retained_out_of_scope_runs"][0]
    assert retained["run_id"] == "20260101T000000Z-probe-hhc"
    assert retained["intent_id"] == "compound_general"
    assert retained["primary_coverage"] == "none"
    assert retained["retained_reason"]


def test_coverage_gap_is_reported_but_not_a_failure(tmp_path: Path) -> None:
    root = tmp_path
    _base(root)

    report = _scope(root)

    assert report["missing_compounds"] == ["compound_cbn"]
    assert report["failure_count"] == 0
    assert report["require_complete"] is False


def test_require_complete_turns_a_gap_into_a_failure(tmp_path: Path) -> None:
    root = tmp_path
    _base(root)

    report = _scope(root, require_complete=True)

    assert report["failure_count"] == 1
    assert report["violations"][0]["reason"] == "primary_coverage_missing"


def test_catalog_only_run_is_included(tmp_path: Path) -> None:
    root = tmp_path
    _base(root)
    _declaration(root / "declarations" / "d.json", [("20260101T000000Z-probe-hhc", "hhc-general-ja")])

    report = _scope(root)

    assert report["primary_run_count"] == 1
    assert "catalog" in report["primary_runs"][0]["adopted_by"]


def test_unregistered_query_and_intent_outside_design_are_violations(tmp_path: Path) -> None:
    root = tmp_path
    _base(root)
    _declaration(
        root / "declarations" / "d.json",
        [
            ("20260101T000000Z-probe-cbd", "cbd-liquid-ja"),
            ("20260101T000000Z-probe-hhc", "hhc-general-ja"),
            ("20260101T000000Z-probe-unknown", "not-registered"),
            ("20260101T000000Z-probe-research", "cbg-research-ja"),
        ],
    )

    report = _scope(root)

    reasons = {entry["reason"] for entry in report["violations"]}
    assert "unregistered_query_id" in reasons
    assert "intent_outside_declared_design" in reasons
