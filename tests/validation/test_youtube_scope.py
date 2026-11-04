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


def _two_query_registry(path: Path) -> None:
    """One compound with two required liquid queries (THCNM / THA shape)."""

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
                    "query_id": "thcnm-liquid-ja",
                    "compound_id": "compound_thcnm",
                    "intent_id": "product_liquid",
                    "language": "ja",
                    "canonical_text": "THCNM リキッド",
                    "status": "active",
                },
                {
                    "query_id": "tha-liquid-ja",
                    "compound_id": "compound_thcnm",
                    "intent_id": "product_liquid",
                    "language": "ja",
                    "canonical_text": "THA リキッド",
                    "status": "active",
                },
            ],
        },
    )


def _two_query_base(root: Path, runs: list[tuple[str, str]]) -> None:
    _two_query_registry(root / "query-registry.json")
    _design(root / "query-design.json")
    _write_json(root / "data-catalog.json", {"catalog_version": "1.0.0", "entries": []})
    _declaration(root / "declarations" / "d.json", runs)


def _compound(report: dict, compound_id: str) -> dict:
    return next(
        item for item in report["compound_coverage"] if item["compound_id"] == compound_id
    )


def test_two_query_compound_with_no_run_is_missing(tmp_path: Path) -> None:
    root = tmp_path
    _two_query_base(root, [("20260101T000000Z-probe-cbd", "cbd-liquid-ja")])

    report = _scope(root)

    thcnm = _compound(report, "compound_thcnm")
    assert thcnm["state"] == "missing"
    assert thcnm["covered_query_count"] == 0
    assert thcnm["required_query_count"] == 2
    assert thcnm["missing_query_ids"] == ["tha-liquid-ja", "thcnm-liquid-ja"]
    assert report["missing_compounds"] == ["compound_thcnm"]
    assert report["partial_compounds"] == []


def test_one_of_two_queries_is_partial_not_complete(tmp_path: Path) -> None:
    root = tmp_path
    _two_query_base(
        root,
        [
            ("20260101T000000Z-probe-cbd", "cbd-liquid-ja"),
            ("20260101T000000Z-probe-thcnm", "thcnm-liquid-ja"),
        ],
    )

    report = _scope(root)

    thcnm = _compound(report, "compound_thcnm")
    assert thcnm["state"] == "partial"
    assert thcnm["covered_query_count"] == 1
    assert thcnm["missing_query_ids"] == ["tha-liquid-ja"]
    # a half-covered compound is not counted as complete, and the single-query
    # compound is unaffected
    assert report["covered_compounds"] == ["compound_cbd"]
    assert report["partial_compounds"] == ["compound_thcnm"]
    assert report["missing_compounds"] == []
    assert report["primary_compound_count"] == 1
    assert report["primary_query_count"] == 3
    assert report["primary_query_covered_count"] == 2
    assert report["failure_count"] == 0


def test_a_run_never_covers_its_sibling_query(tmp_path: Path) -> None:
    root = tmp_path
    _two_query_base(root, [("20260101T000000Z-probe-tha", "tha-liquid-ja")])

    report = _scope(root)

    coverage = {item["query_id"]: item for item in report["coverage"]}
    assert coverage["tha-liquid-ja"]["covered"] is True
    assert coverage["thcnm-liquid-ja"]["covered"] is False
    assert _compound(report, "compound_thcnm")["state"] == "partial"


def test_two_queries_both_adopted_complete_the_compound(tmp_path: Path) -> None:
    root = tmp_path
    _two_query_base(
        root,
        [
            ("20260101T000000Z-probe-tha", "tha-liquid-ja"),
            ("20260101T000000Z-probe-thcnm", "thcnm-liquid-ja"),
        ],
    )

    report = _scope(root)

    thcnm = _compound(report, "compound_thcnm")
    assert thcnm["state"] == "complete"
    assert thcnm["run_ids"] == [
        "20260101T000000Z-probe-tha",
        "20260101T000000Z-probe-thcnm",
    ]
    assert report["covered_compounds"] == ["compound_thcnm"]
    assert report["primary_run_count"] == 2


def test_require_complete_distinguishes_partial_from_missing(tmp_path: Path) -> None:
    root = tmp_path
    _two_query_base(
        root,
        [
            ("20260101T000000Z-probe-cbd", "cbd-liquid-ja"),
            ("20260101T000000Z-probe-thcnm", "thcnm-liquid-ja"),
        ],
    )

    report = _scope(root, require_complete=True)

    partial = [
        entry for entry in report["violations"] if entry["reason"] == "primary_coverage_partial"
    ]
    assert partial == [
        {
            "reason": "primary_coverage_partial",
            "compound_id": "compound_thcnm",
            "missing_query_ids": ["tha-liquid-ja"],
        }
    ]
    assert report["failure_count"] == 1
