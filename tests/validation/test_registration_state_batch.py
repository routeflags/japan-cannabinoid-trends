"""The owner-directed registration batch: canonical queries, preserved strings,
and the design/coverage boundary.

Contract sources: ``ISS-20261111-TAX-040`` (the owner's enumerated scope decision and
the dated supersession of ``ISS-20261015-TAX-027`` for THCP), ``ISS-20261110-TAX-039``
(the earlier hold and the 17-vs-15 count discrepancy),
``datasets/cannabinoid-raw-collection/metadata/query-design.json`` and
``metadata/queries/query-registry.json``.

The rule: a registered term is a search string, not a chemical identity. Every term
the owner enumerated gets the same query set the study's design declares (bare term
for ``compound_general``, ``<term> リキッド`` for ``product_liquid``), exactly once,
``active``, with no pre-created variant. CBC and CBDV are included in the batch
counts without changing their existing identity or classification. The instruction
said 17 substances while listing 15, so the enumerated 15 are registered and the
discrepancy stays an open question -- no term is invented to reach 17.

The batch has since been collected. Current adopted coverage is an audit/README
fact, not a design fact: these tests assert the design no longer carries per-term
uncollected-run declarations, while the registry, taxonomy, and project mirror
still pin the owner's strings and the identity-unverified classification.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "metadata/queries/query-registry.json"
VARIANTS = REPO_ROOT / "metadata/queries/query-variants.json"
TAXONOMY = REPO_ROOT / "metadata/taxonomy/compound-taxonomy.skos.jsonld"
STUDY = REPO_ROOT / "datasets/cannabinoid-raw-collection"
DESIGN = STUDY / "metadata/query-design.json"
README = STUDY / "README.md"
METHODOLOGY = STUDY / "methodology.md"
PROJECT = REPO_ROOT / "project.json"
ISSUE = (
    REPO_ROOT
    / "docs/issues/active/50-taxonomy-standards"
    / "20261111_p1_compound-registration-state-batch.md"
)

# Every compound in the owner-directed batch: the two existing concepts plus the
# 13 new ones.  Exact owner strings.
EXISTING = (
    ("CBC", "compound_cbc", "cbc"),
    ("CBDV", "compound_cbdv", "cbdv"),
)
NEW_TERMS = (
    ("THCB", "compound_thcb", "thcb"),
    ("THCP", "compound_thcp", "thcp"),
    ("THCJD", "compound_thcjd", "thcjd"),
    ("THCPO", "compound_thcpo", "thcpo"),
    ("CBE", "compound_cbe", "cbe"),
    ("HHCPO", "compound_hhcpo", "hhcpo"),
    ("CBND", "compound_cbnd", "cbnd"),
    ("CBL", "compound_cbl", "cbl"),
    ("CBGa", "compound_cbga", "cbga"),
    ("CBP", "compound_cbp", "cbp"),
    ("10-OH-HHC", "compound_10_oh_hhc", "10-oh-hhc"),
    ("THXE", "compound_thxe", "thxe"),
    ("THCA", "compound_thca", "thca"),
)
BATCH = EXISTING + NEW_TERMS


def _registry() -> list[dict]:
    document = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return document["queries"]


def _design() -> dict:
    document = json.loads(DESIGN.read_text(encoding="utf-8"))
    designs = [d for d in document["query_designs"] if d.get("source_id") == "youtube"]
    assert len(designs) == 1
    return designs[0]


def _concepts() -> dict[str, dict]:
    document = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    return {
        node["@id"]: node
        for node in document["@graph"]
        if node.get("@type") == "skos:Concept"
    }


def _project() -> dict:
    return json.loads(PROJECT.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# canonical queries: the exact registered strings the batch sent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("term,compound_id,slug", BATCH, ids=[t[2] for t in BATCH])
def test_each_term_has_the_declared_query_set_exactly_once(
    term: str, compound_id: str, slug: str
) -> None:
    queries = [q for q in _registry() if q["query_id"] in {f"{slug}-general-ja", f"{slug}-liquid-ja"}]
    by_intent = {q["intent_id"]: q for q in queries}
    assert set(by_intent) == {"compound_general", "product_liquid"}
    general = by_intent["compound_general"]
    liquid = by_intent["product_liquid"]
    assert general["query_id"] == f"{slug}-general-ja"
    assert liquid["query_id"] == f"{slug}-liquid-ja"
    assert general["canonical_text"] == term
    assert liquid["canonical_text"] == term + " リキッド"
    for query in (general, liquid):
        assert query["compound_id"] == compound_id
        assert query["language"] == "ja"
        assert query["status"] == "active"


def test_no_term_is_registered_twice_and_no_text_is_shared() -> None:
    queries = _registry()
    texts = [q["canonical_text"] for q in queries if q["status"] != "deprecated"]
    assert len(texts) == len(set(texts))
    for term, _, _ in NEW_TERMS:
        assert texts.count(term) == 1, term
        assert texts.count(term + " リキッド") == 1, term


def test_no_variant_is_pre_created_for_the_registration_batch() -> None:
    """Variants record observed spellings; the batch did not pre-create any."""

    document = json.loads(VARIANTS.read_text(encoding="utf-8"))
    registered = {q["query_id"] for q in _registry()}
    for _, _, slug in BATCH:
        for query_id in (f"{slug}-general-ja", f"{slug}-liquid-ja"):
            assert query_id in registered
    used = {s["query_id"] for s in document["variant_sets"]}
    assert not {f"{slug}-liquid-ja" for _, _, slug in NEW_TERMS} & used
    assert not {f"{slug}-general-ja" for _, _, slug in NEW_TERMS} & used


# ---------------------------------------------------------------------------
# existing concepts are reused, not redefined
# ---------------------------------------------------------------------------


def test_cbc_and_cbdv_keep_their_existing_identity_and_classification() -> None:
    concepts = _concepts()
    for _, compound_id, _ in EXISTING:
        concept = concepts["jptr:compound-" + compound_id[len("compound_"):].replace("_", "-")]
        assert concept["skos:broader"] == "jptr:compound-minor"
        assert concept.get("skos:exactMatch"), compound_id
    assert concepts["jptr:compound-cbc"]["skos:exactMatch"] == "wikidata:Q422441"
    assert concepts["jptr:compound-cbdv"]["skos:exactMatch"] == "wikidata:Q422426"


def test_new_terms_stay_in_the_identity_unverified_category() -> None:
    """Registration is a search string; no chemical identity or synonym is inferred."""

    concepts = _concepts()
    for _, compound_id, _ in NEW_TERMS:
        concept = concepts[
            "jptr:compound-" + compound_id[len("compound_"):].replace("_", "-")
        ]
        assert concept["skos:broader"] == "jptr:compound-identity-unverified"
        assert "skos:exactMatch" not in concept, compound_id
        scope_note = " ".join(
            item["@value"] for item in concept.get("skos:scopeNote", [])
        )
        assert "UNCONFIRMED" in scope_note, compound_id
        assert "未確認" in scope_note, compound_id


# ---------------------------------------------------------------------------
# the design declares requirements, not a run-state snapshot
# ---------------------------------------------------------------------------


def test_design_no_longer_declares_uncollected_runs() -> None:
    """The batch was collected; the design must not keep a stale run-state list."""

    design = _design()
    compound_set = design["compound_set"]
    assert "declared_not_yet_collected" not in compound_set
    assert "coverage_state_note" not in compound_set
    text = json.dumps(design, ensure_ascii=False)
    for stale in (
        "declared_not_yet_collected",
        "not_collected",
        "No run exists",
        "run is 0",
    ):
        assert stale not in text, stale


def test_design_registration_basis_covers_the_batch() -> None:
    compound_set = _design()["compound_set"]
    basis = compound_set["registration_basis"]
    by_compound = {
        compound_id: item
        for item in basis
        for compound_id in item["compound_ids"]
    }
    assert sorted(by_compound) == sorted(
        compound_id for _, compound_id, _ in BATCH
    )
    for _, compound_id, _ in EXISTING:
        item = by_compound[compound_id]
        assert item["decided"] == "2026-11-10"
        assert item["decided_by"] == "owner"
        assert item["identity_state"] == "existing_canonical_concept_reused"
        assert "ISS-20261110-TAX-039" in item["reason"]
    for _, compound_id, _ in NEW_TERMS:
        item = by_compound[compound_id]
        assert item["decided"] == "2026-11-11"
        assert item["decided_by"] == "owner"
        assert item["identity_state"] == "compound_identity_unverified"
        assert "compound_identity_unverified" in item["reason"]
        assert "UNVERIFIED" in item["reason"]
        assert "ISS-20261111-TAX-040" in item["reason"]
    # THCP's supersession is recorded with the batch, not left implicit.
    assert "ISS-20261015-TAX-027" in by_compound["compound_thcp"]["reason"]
    # The registry, not the design, enumerates the required queries.
    assert "query-registry.json" in compound_set["authority"]
    assert "product_liquid" in compound_set["authority"]


def test_design_coverage_authority_is_external() -> None:
    """Coverage counts live in the audit and README, never in the design."""

    compound_set = _design()["compound_set"]
    authority = compound_set["coverage_authority"]
    assert "audit-youtube-coverage" in authority
    assert "cannabinoid-raw-collection/README.md" in authority
    assert "never converted to zero" in authority
    for key in (
        "run_count",
        "adopted_run_count",
        "covered_query_count",
        "primary_run_count",
    ):
        assert key not in compound_set, key


def test_design_does_not_exclude_the_batch() -> None:
    """Registration is not an exclusion decision."""

    document = json.loads(DESIGN.read_text(encoding="utf-8"))
    batch_ids = {compound_id for _, compound_id, _ in BATCH}
    for scale in document["comparison_scales"]:
        excluded = {
            item["compound_id"]
            for item in scale["compound_set"].get("excluded_compound_ids", [])
        }
        assert not (excluded & batch_ids), scale["scale_id"]


# ---------------------------------------------------------------------------
# the project mirror carries pointers, not stale per-source statuses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("term,compound_id,slug", BATCH, ids=[t[2] for t in BATCH])
def test_project_mirror_has_no_stale_uncollected_state(
    term: str, compound_id: str, slug: str
) -> None:
    entry = _project()["queryDesign"]["compounds"][term]
    assert "coverageStatus" not in entry
    note = entry["note"]
    for stale in ("run は 0", "未収集", "declared_not_yet_collected"):
        assert stale not in note, (term, stale)
    assert "datasets/cannabinoid-raw-collection/README.md" in note
    assert "audit-youtube-coverage" in note
    assert f"{slug}-general-ja" in note
    assert f"{slug}-liquid-ja" in note
    assert entry["queries"]["youtube"] == term + " リキッド"
    assert entry["queries"]["googleTrends"] == term
    assert entry["identityNote"].strip()
    if compound_id in {c for _, c, _ in NEW_TERMS}:
        assert "compound_identity_unverified" in entry["identityNote"]


def test_project_coverage_note_removes_the_obsolete_raw_count() -> None:
    coverage = _project()["dataCoverage"]
    note = coverage["auditNote"]
    assert "37 runs" not in note
    assert "cannabinoid-raw-collection/README.md" in note
    assert "audit-youtube-coverage" in note
    assert "not refreshed" in note


# ---------------------------------------------------------------------------
# the count discrepancy and the strings that must survive into prose
# ---------------------------------------------------------------------------


def test_the_enumerated_batch_is_15_and_the_17_discrepancy_is_recorded() -> None:
    """17 was stated, 15 were enumerated: register 15, invent none, say so."""

    assert len(BATCH) == 15
    text = ISSUE.read_text(encoding="utf-8")
    assert "17" in text and "15" in text
    assert "推測で補わない" in text or "invent" in text
    reason = _design()["compound_set"]["registration_basis"][1]["reason"]
    assert "17" in reason and "15" in reason
    assert "invent" in reason


def test_owner_strings_survive_into_the_study_documents() -> None:
    for path in (README, METHODOLOGY):
        text = path.read_text(encoding="utf-8")
        for term in ("CBGa", "10-OH-HHC", "THCJD", "THCPO", "CBND", "THXE"):
            assert term in text, (path.name, term)
        assert "compound_identity_unverified" in text, path.name
