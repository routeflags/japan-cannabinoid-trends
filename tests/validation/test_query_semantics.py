"""Contract tests for G2 query semantics (b.md §5 / §8 / §9 / §13).

Covers:

- the registry consistency checks behind ``validate-registries``
  (duplicate IDs/texts: G2-T02; taxonomy references: G2-T01; variant bundle
  checks: G2-T04);
- Stage-1 classification (b.md §8), including the recorded Durban CBD noise
  example and the CBD-vs-CBDリキッド intent separation (G2-T09/T11/T12);
- definition-level comparability (Q1-Q5 subset) and its consistency with the
  L2 C1 run gate;
- the real repository registry / variants / taxonomy and the b.md §13 audit
  snapshot (regenerate with ``python -m validation.cli audit-queries`` from
  the repository root after any registry or rule change).
"""

import json
from pathlib import Path

import pytest

from validation.comparability import compare_runs
from validation.core import validate_document
from validation.integrity import sha256_file
from validation.query_semantics import (
    EXCLUSION_RULES,
    build_query_inventory,
    check_query_registry,
    check_query_variants,
    classify_query_text,
    compare_query_definitions,
    extract_query_strings,
    load_compound_vocabulary,
    normalize_query_text,
    resolve_query_text,
)
from validation.schema_registry import get_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "metadata" / "queries" / "query-registry.json"
VARIANTS_PATH = REPO_ROOT / "metadata" / "queries" / "query-variants.json"
TAXONOMY_PATH = REPO_ROOT / "metadata" / "taxonomy" / "compound-taxonomy.skos.jsonld"
AUDIT_PATH = REPO_ROOT / "docs" / "audits" / "g2-query-inventory.json"
FIXTURES = Path(__file__).parent / "fixtures"


def _load(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _registry() -> dict:
    return _load(REGISTRY_PATH)


def _variants() -> dict:
    return _load(VARIANTS_PATH)


def _vocabulary():
    return load_compound_vocabulary(TAXONOMY_PATH)


def _codes(issues) -> list:
    return [issue.code for issue in issues]


def _find_query(query_id: str) -> dict:
    return next(q for q in _registry()["queries"] if q["query_id"] == query_id)


def _classify(text):
    return classify_query_text(
        text,
        query_registry={"queries": _registry()["queries"]},
        variant_registry=_variants(),
        vocabulary=_vocabulary(),
    )


# ---------------------------------------------------------------------------
# normalization / resolution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("CBD リキッド", "cbd リキッド"),
        ("cbd リキッド", "cbd リキッド"),
        ("ＣＢＤリキッド", "cbdリキッド"),
        ("  CBX\tリキッド ", "cbx リキッド"),
        ("THC-O リキッド", "thc-o リキッド"),
    ],
)
def test_normalization_absorbs_case_and_width(raw, expected):
    assert normalize_query_text(raw) == expected


def test_resolution_distinguishes_canonical_and_variant():
    registries = {"queries": _registry()["queries"]}
    variants = _variants()
    canonical = resolve_query_text(
        "CBD リキッド", query_registry=registries, variant_registry=variants
    )
    assert canonical["match"] == "canonical"
    assert canonical["query_id"] == "cbd-liquid-ja"
    variant = resolve_query_text(
        "CBDリキッド", query_registry=registries, variant_registry=variants
    )
    assert variant["match"] == "variant"
    assert variant["variant_id"] == "cbd-liquid-nospace"
    assert (
        resolve_query_text(
            "Durban CBD", query_registry=registries, variant_registry=variants
        )
        is None
    )


# ---------------------------------------------------------------------------
# Stage 1 classification (b.md §8)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,classification,query_id,variant_id,rule_id",
    [
        ("CBD", "relevant", "cbd-general-ja", None, None),
        ("CBD リキッド", "relevant", "cbd-liquid-ja", None, None),
        ("CBDリキッド", "relevant", "cbd-liquid-ja", "cbd-liquid-nospace", None),
        ("ＣＢＤ", "relevant", "cbd-general-ja", None, None),
        ("Durban CBD", "irrelevant", None, None, "non-compound-durban-cbd"),
        ("CBD ペン", "ambiguous", None, None, None),
        ("THC リキッド", "relevant", "thc-liquid-ja", None, None),
        ("天気", "unknown", None, None, None),
    ],
)
def test_stage1_classification(text, classification, query_id, variant_id, rule_id):
    result = _classify(text)
    assert result["classification"] == classification
    assert result["query_id"] == query_id
    assert result["variant_id"] == variant_id
    assert result["rule_id"] == rule_id


def test_cbd_and_cbd_liquid_are_separate_concepts():
    """b.md §1 / P1: 'CBD' and 'CBD リキッド' must never be a single query
    (their observations must not be summed as one)."""
    general = _classify("CBD")
    liquid = _classify("CBD リキッド")
    assert general["query_id"] == "cbd-general-ja"
    assert liquid["query_id"] == "cbd-liquid-ja"
    assert general["query_id"] != liquid["query_id"]


def test_every_exclusion_rule_records_rationale_and_evidence():
    """Nothing is excluded without a recorded reason; rules are phrases
    matched on the normalized text (b.md §8.3)."""
    assert EXCLUSION_RULES
    for rule in EXCLUSION_RULES:
        assert rule.rule_id and rule.rationale and rule.evidence
        assert rule.phrase == normalize_query_text(rule.phrase)


def test_classification_without_vocabulary_preserves_uncertainty():
    """With no compound vocabulary loaded, token detection cannot run; such
    texts fall through to 'unknown' - never 'relevant'."""
    result = classify_query_text(
        "CBD ペン",
        query_registry={"queries": _registry()["queries"]},
        variant_registry=_variants(),
        vocabulary=None,
    )
    assert result["classification"] == "unknown"


# ---------------------------------------------------------------------------
# registry consistency checks (G2-T01 / G2-T02 / G2-T04)
# ---------------------------------------------------------------------------


def test_registry_accepts_the_real_files_semantically():
    assert check_query_registry(_registry(), vocabulary=_vocabulary()) == []
    assert (
        check_query_variants(
            _variants(), query_registry=_registry(), vocabulary=_vocabulary()
        )
        == []
    )


def test_duplicate_query_id_fails_g2_t02():
    document = _registry()
    clone = dict(document["queries"][0])
    clone["canonical_text"] = "CBX ダミー"
    document["queries"].append(clone)
    assert "QUERY_DUPLICATE_ID" in _codes(check_query_registry(document))


def test_duplicate_query_text_fails():
    document = _registry()
    clone = dict(document["queries"][0])
    clone["query_id"] = "cbx-general-ja-copy"
    document["queries"].append(clone)
    assert "QUERY_DUPLICATE_TEXT" in _codes(check_query_registry(document))


def test_unregistered_compound_fails_when_the_taxonomy_is_loaded_g2_t01():
    document = _registry()
    document["queries"][0]["compound_id"] = "compound_unknown"
    codes = _codes(check_query_registry(document, vocabulary=_vocabulary()))
    assert "QUERY_COMPOUND_UNREGISTERED" in codes
    # Without the taxonomy the cross-check is disabled (the missing-registry
    # convention), never converted into a false failure.
    assert "QUERY_COMPOUND_UNREGISTERED" not in _codes(
        check_query_registry(document)
    )


def test_registered_text_matching_an_exclusion_rule_fails():
    document = _registry()
    document["queries"][0]["canonical_text"] = "Durban CBD"
    assert "QUERY_TEXT_EXCLUDED" in _codes(check_query_registry(document))


def test_variant_bundle_checks_g2_t04():
    registry = _registry()
    variants = _variants()

    broken = json.loads(json.dumps(variants))
    broken["variant_sets"][0]["variants"].append(
        {"variant_id": "cbd-general-primary", "text": "CBD2", "status": "alternative"}
    )
    assert "VARIANT_DUPLICATE_ID" in _codes(
        check_query_variants(broken, query_registry=registry)
    )

    broken = json.loads(json.dumps(variants))
    broken["variant_sets"][0]["query_id"] = "no-such-query"
    assert "VARIANT_QUERY_UNREGISTERED" in _codes(
        check_query_variants(broken, query_registry=registry)
    )

    broken = json.loads(json.dumps(variants))
    broken["variant_sets"][0]["variants"][0]["text"] = "CBX リキッド"
    assert "VARIANT_PRIMARY_MISMATCH" in _codes(
        check_query_variants(broken, query_registry=registry)
    )

    broken = json.loads(json.dumps(variants))
    broken["variant_sets"][0]["variants"][0]["status"] = "alternative"
    assert "VARIANT_PRIMARY_COUNT" in _codes(
        check_query_variants(broken, query_registry=registry)
    )

    # a variant text duplicating another set's variant (after normalization)
    broken = json.loads(json.dumps(variants))
    broken["variant_sets"][0]["variants"].append(
        {"variant_id": "cbx-dup", "text": "CBDリキッド", "status": "alternative"}
    )
    assert "VARIANT_DUPLICATE_TEXT" in _codes(
        check_query_variants(broken, query_registry=registry)
    )

    # an alternative text duplicating a registered canonical text
    broken = json.loads(json.dumps(variants))
    broken["variant_sets"][1]["variants"].append(
        {"variant_id": "cbd-conflict", "text": "CBD オイル", "status": "alternative"}
    )
    assert "VARIANT_TEXT_CONFLICTS_CANONICAL" in _codes(
        check_query_variants(broken, query_registry=registry)
    )


def test_variant_sets_require_exactly_one_primary_per_query():
    variants = json.loads(json.dumps(_variants()))
    variants["variant_sets"][0]["variants"].append(
        {"variant_id": "second-primary", "text": "CBX2", "status": "primary"}
    )
    assert "VARIANT_PRIMARY_COUNT" in _codes(
        check_query_variants(variants, query_registry=_registry())
    )


# ---------------------------------------------------------------------------
# definition comparability (Q1-Q5 subset) - must not contradict C1
# ---------------------------------------------------------------------------


def test_same_query_definition_is_conditional_at_best():
    result = compare_query_definitions(
        _find_query("cbd-general-ja"), _find_query("cbd-general-ja")
    )
    assert result.status == "conditional"
    assert "q5_platform_syntax_review_required" in result.reasons
    assert "q6_semantic_filter_absent" in result.reasons


def test_different_query_ids_are_not_comparable_g2_t09():
    result = compare_query_definitions(
        _find_query("cbd-general-ja"), _find_query("cbd-liquid-ja")
    )
    assert result.status == "not_comparable"
    assert "q2_intent_mismatch" in result.reasons
    assert "q3_text_mismatch" in result.reasons


def test_cbd_liquid_vs_cbd_oil_is_not_comparable_g2_t10():
    result = compare_query_definitions(
        _find_query("cbd-liquid-ja"), _find_query("cbd-oil-ja")
    )
    assert result.status == "not_comparable"
    assert "q2_intent_mismatch" in result.reasons


def test_submitted_text_difference_is_not_comparable_like_c1():
    result = compare_query_definitions(
        _find_query("cbd-general-ja"),
        _find_query("cbd-general-ja"),
        submitted_a="CBD",
        submitted_b="Cannabidiol",
    )
    assert result.status == "not_comparable"
    assert result.reasons == ["q5_submitted_query_mismatch"]


def test_definition_gate_never_contradicts_c1():
    """Where the definition gate refuses a pair, the L2 C1 gate refuses it
    too; where the gate allows a conditional review, C1 reports no query
    mismatch (G1 §12 consistency requirement)."""
    document = _load(FIXTURES / "collection_run_valid.json")
    a = json.loads(json.dumps(document))
    a["query_provenance"] = {
        "query_id": "cbd-general-ja",
        "submitted_query": "CBD",
        "compound_id": "compound_cbd",
    }
    b = json.loads(json.dumps(document))
    b["query_provenance"] = {
        "query_id": "cbd-liquid-ja",
        "submitted_query": "CBD リキッド",
        "compound_id": "compound_cbd",
    }
    definition = compare_query_definitions(
        _find_query("cbd-general-ja"), _find_query("cbd-liquid-ja")
    )
    run_level = compare_runs(a, b)
    assert definition.status == "not_comparable"
    assert run_level.status == "not_comparable"
    assert "c1_query_mismatch" in run_level.reasons

    same = compare_query_definitions(
        _find_query("cbd-general-ja"),
        _find_query("cbd-general-ja"),
        submitted_a="CBD",
        submitted_b="CBD",
    )
    assert same.status == "conditional"
    assert "c1_query_mismatch" not in compare_runs(a, json.loads(json.dumps(a))).reasons


# ---------------------------------------------------------------------------
# real repository artifacts
# ---------------------------------------------------------------------------


def test_real_taxonomy_supplies_the_registry_compound_ids():
    vocabulary = _vocabulary()
    assert {"compound_cbx", "compound_cbd"} <= set(vocabulary.notations)
    assert {"cbx", "cbd", "thc"} <= set(vocabulary.tokens)


def test_real_registry_files_are_structurally_valid():
    assert validate_document(_registry(), get_schema("query-registry-v1")).valid
    assert validate_document(
        _variants(), get_schema("query-variants-registry-v1")
    ).valid


def test_extraction_covers_legacy_shapes_and_deduplicates():
    document = {
        "queries": [{"term": "CBD", "terms": ["CBD", "CBX リキッド"]}],
        "terms": ["CBX リキッド"],
        "keyword": "CRDH",
        "compounds_collected": ["CBD"],
    }
    extracted = extract_query_strings(document)
    assert [entry["text"] for entry in extracted] == ["CBD", "CBX リキッド", "CRDH"]
    by_text = {entry["text"]: entry for entry in extracted}
    assert by_text["CBD"]["source_fields"] == [
        "queries[0].term",
        "queries[0].terms[0]",
        "compounds_collected[0]",
    ]
    assert by_text["CBX リキッド"]["source_fields"] == [
        "queries[0].terms[1]",
        "terms[0]",
    ]


def _real_run_entries():
    entries = []
    datasets_root = REPO_ROOT / "datasets"
    for path in sorted(datasets_root.rglob("run_metadata.json")):
        before = sha256_file(path)
        document = json.loads(path.read_text(encoding="utf-8"))
        after = sha256_file(path)
        entries.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "document": document,
                "sha256": before,
                "sha256_after": after,
                "unchanged": before == after,
            }
        )
    return entries


def test_audit_snapshot_matches_the_real_inventory():
    """The tracked audit is the deterministic b.md §13 snapshot (regenerate
    with ``python -m validation.cli audit-queries`` from the repository root
    after any registry or rule change)."""
    stored = _load(AUDIT_PATH)
    recomputed = build_query_inventory(
        _real_run_entries(),
        query_registry=_registry(),
        variant_registry=_variants(),
        vocabulary=_vocabulary(),
    )
    assert recomputed == stored
    assert stored["raw_modified"] is False
    assert stored["count"] == len(
        list((REPO_ROOT / "datasets").rglob("run_metadata.json"))
    )


def test_audit_snapshot_records_the_legacy_examples():
    stored = _load(AUDIT_PATH)
    states = {
        entry["text"]: entry["state"]
        for run in stored["runs"]
        for entry in run["queries"]
    }
    assert states["CBD"] == "exact_match"
    assert states["CBDリキッド"] == "variant_match"
    assert states["CBD オイル"] == "exact_match"
    # Registered in the 2026-10-13 G2 increment (14 queries): previously
    # ``ambiguous``, now ``exact_match`` (recomputed audit: exact 41 -> 73).
    assert states["THC リキッド"] == "exact_match"
    assert states["THC"] == "exact_match"
    assert states["CBG"] == "exact_match"
    assert states["CBG リキッド"] == "exact_match"
    assert states["CBN"] == "exact_match"
    assert states["CBN リキッド"] == "exact_match"
    # Assert the partition shape (the five states cover the corpus) rather
    # than a fixed partition: a future run may legitimately record an
    # ambiguous or unmapped string, and turning that into a failure would
    # contradict the point of recording review states.  The
    # ``recomputed == stored`` test above already forces a human-reviewed
    # snapshot regeneration on any data or classifier change.
    assert sum(stored["summary"].values()) == stored["query_count"]
    assert sum(stored["summary"].values()) == stored["query_count"]
