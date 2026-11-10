"""The owner-directed registration batch: canonical queries, preserved strings, declared
not-collected state.

Contract sources: ``ISS-20261111-TAX-040`` (the owner's enumerated scope decision and
the dated supersession of ``ISS-20261015-TAX-027`` for THCP), ``ISS-20261110-TAX-039``
(the earlier hold and the 17-vs-15 count discrepancy),
``datasets/cannabinoid-raw-collection/metadata/query-design.json`` and
``metadata/queries/query-registry.json``.

The rule: a registered term is a search string, not a chemical identity. Every term
the owner enumerated gets the same query set the study's design declares (bare term
for ``compound_general``, ``<term> リキッド`` for ``product_liquid``), exactly once,
``active``, with no variant, and no run. CBC and CBDV are included in the batch
counts without changing their existing identity or classification. The instruction
said 17 substances while listing 15, so the enumerated 15 are registered and the
discrepancy stays an open question -- no term is invented to reach 17.
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
ISSUE = (
    REPO_ROOT
    / "docs/issues/active/50-taxonomy-standards"
    / "20261111_p1_compound-registration-state-batch.md"
)

# Every compound the study now declares as registered but not collected: the two
# existing concepts plus the 13 new ones.  Exact owner strings.
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


# ---------------------------------------------------------------------------
# canonical queries: the exact strings the follow-up collector will send
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


def test_no_variant_is_pre_created_for_an_uncollected_term() -> None:
    """Variants record observed spellings; a term with no run has none."""

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


# ---------------------------------------------------------------------------
# the study declares the full batch as registered but not collected
# ---------------------------------------------------------------------------


def test_design_declares_every_batch_compound_not_collected() -> None:
    declared = _design()["compound_set"]["declared_not_yet_collected"]
    by_id = {item["compound_id"]: item for item in declared}
    assert sorted(by_id) == sorted(compound_id for _, compound_id, _ in BATCH)
    for _, compound_id, slug in BATCH:
        item = by_id[compound_id]
        assert item["state"] == "not_collected"
        assert item["decided"] in {"2026-11-10", "2026-11-11"}
        assert item["decided_by"] == "owner"
        assert item["query_ids"] == [f"{slug}-liquid-ja"]
        assert item["reason"].strip()


def test_design_does_not_exclude_the_batch() -> None:
    """Not collecting is not an exclusion decision."""

    document = json.loads(DESIGN.read_text(encoding="utf-8"))
    batch_ids = {compound_id for _, compound_id, _ in BATCH}
    for scale in document["comparison_scales"]:
        excluded = {
            item["compound_id"]
            for item in scale["compound_set"].get("excluded_compound_ids", [])
        }
        assert not (excluded & batch_ids), scale["scale_id"]


# ---------------------------------------------------------------------------
# the count discrepancy and the strings that must survive into prose
# ---------------------------------------------------------------------------


def test_the_enumerated_batch_is_15_and_the_17_discrepancy_is_recorded() -> None:
    """17 was stated, 15 were enumerated: register 15, invent none, say so."""

    assert len(BATCH) == 15
    text = ISSUE.read_text(encoding="utf-8")
    assert "17" in text and "15" in text
    assert "推測で補わない" in text or "invent" in text


def test_owner_strings_survive_into_the_study_documents() -> None:
    for path in (README, METHODOLOGY):
        text = path.read_text(encoding="utf-8")
        for term in ("CBGa", "10-OH-HHC", "THCJD", "THCPO", "CBND", "THXE"):
            assert term in text, (path.name, term)
        assert "compound_identity_unverified" in text, path.name
