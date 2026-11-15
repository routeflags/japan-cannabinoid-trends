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

THCP and THCJD stay in that classification. On 2026-11-11 the owner confirmed only
an isomer-unspecified C7 (tetrahydrocannabiphorol) / C8 (THC-JD, 3-octyl-THC)
homologue family for them, so each concept records a search-topic scope and carries
no exactMatch and no per-isomer identifier; the family is not a substance identity.
THCPO is a related case for THCP-O-acetate: the owner confirmed only that the
string means THCP-O-acetate and named no Δ8/Δ9 isomer, so the registration is
treated as an isomer-unspecified family -- a registration-level reading of the
answer, not a family the owner explicitly confirmed. The concept records that
scope, the 2024 MHLW structural-group coverage of both isomers under the
ordinance's narcotics exclusion, and the 2025 analytical identification of the
Δ9 acetate, while carrying no exactMatch and no per-isomer identifier. Category
membership establishes no synonym, and the concept's English altLabel has its own
recorded basis in the scopeNote.

A later 2026-11-11 decision (``ISS-20261111-TAX-041``) registered six specific
THCA / THCB search topics. They follow the same rule: bare term plus
``<term> リキッド``, active, no variant, no identifier, and the generic
``compound_thca`` / ``compound_thcb`` registrations keep their own queries and runs.
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
# The 2026-11-11 THCA / THCB split (ISS-20261111-TAX-041): three topics replace
# the generic THCA reading and three replace THCB.  Owner spellings, exact.
THCA_THCB_TOPICS = (
    ("Δ9-THCA-A", "compound_delta9_thca_a", "delta9-thca-a"),
    ("THCA-B", "compound_thca_b", "thca-b"),
    ("Δ8-THCA", "compound_delta8_thca", "delta8-thca"),
    ("Δ8-THCB", "compound_delta8_thcb", "delta8-thcb"),
    ("Δ9-THCB", "compound_delta9_thcb", "delta9-thcb"),
    ("THCB-O-acetate", "compound_thcb_o_acetate", "thcb-o-acetate"),
)
# CBE, CBL and CBGa were registered with the batch but their intended identities
# were documented the same day (owner confirmation, public registries); the other
# ten remain unresolved as substances. THCP and THCJD have a documented family
# scope only (see FAMILY_SCOPED), so they stay in the administrative category.
CONFIRMED_TERMS = {"CBE", "CBL", "CBGa"}
UNRESOLVED_NEW_TERMS = tuple(term for term in NEW_TERMS if term[0] not in CONFIRMED_TERMS)
CBE = ("CBE", "compound_cbe", "cbe")
CBL = ("CBL", "compound_cbl", "cbl")
CBGA = ("CBGa", "compound_cbga", "cbga")
# THCP and THCJD keep the identity-unverified placement: the owner confirmed only an
# isomer-unspecified homologue family (C7 / C8), which is a search-topic scope, not a
# substance identity.  Each isomer has its own record; the family has none.
FAMILY_SCOPED = (
    ("THCP", "compound_thcp", "thcp", "tetrahydrocannabiphorol", "C7"),
    ("THCJD", "compound_thcjd", "thcjd", "3-octyl-THC", "C8"),
)


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


@pytest.mark.parametrize(
    "term,compound_id,slug",
    BATCH + THCA_THCB_TOPICS,
    ids=[t[2] for t in BATCH + THCA_THCB_TOPICS],
)
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
    for term, _, _ in NEW_TERMS + THCA_THCB_TOPICS:
        assert texts.count(term) == 1, term
        assert texts.count(term + " リキッド") == 1, term


def test_no_variant_is_pre_created_for_the_registration_batch() -> None:
    """Variants record observed spellings; the batch did not pre-create any."""

    document = json.loads(VARIANTS.read_text(encoding="utf-8"))
    registered = {q["query_id"] for q in _registry()}
    for _, _, slug in BATCH + THCA_THCB_TOPICS:
        for query_id in (f"{slug}-general-ja", f"{slug}-liquid-ja"):
            assert query_id in registered
    used = {s["query_id"] for s in document["variant_sets"]}
    for _, _, slug in NEW_TERMS + THCA_THCB_TOPICS:
        assert f"{slug}-liquid-ja" not in used
        assert f"{slug}-general-ja" not in used


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


def test_unresolved_new_terms_stay_in_the_identity_unverified_category() -> None:
    """Registration is a search string; no chemical identity or synonym is infer
red.

    CBE, CBL and CBGa are excluded here because the owner confirmed their intended
    identities on the same day; their documented identities are checked separately
    below.
    """

    concepts = _concepts()
    for _, compound_id, _ in UNRESOLVED_NEW_TERMS:
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


PER_ISOMER_IDENTIFIERS_THCPO = (
    # Delta-9-THCP acetate / delta-8-THCP acetate / Wikidata's Δ9-keyed item.
    "2829292-82-0",
    "172677450",
    "172874392",
    "Q122689235",
    "OXMUZNKOOOITQD-NHCUHLMSSA-N",
    "FDKCGSRFVKINQD-NHCUHLMSSA-N",
)

PER_ISOMER_IDENTIFIERS = (
    # Delta-9-THCP / delta-8-THCP / THC-JD (delta-9, delta-8): never attached to the family.
    "54763-99-4",
    "6453074",
    "Q85806080",
    "WTK87HN3LG",
    "51768-60-6",
    "44307335",
    "Q141317106",
    "155318984",
    "102024084",
)


@pytest.mark.parametrize(
    "term,compound_id,slug,family,carbon",
    FAMILY_SCOPED,
    ids=[item[2] for item in FAMILY_SCOPED],
)
def test_thcp_and_thcjd_document_an_isomer_unspecified_family_without_a_mapping(
    term: str, compound_id: str, slug: str, family: str, carbon: str
) -> None:
    """The 2026-11-11 confirmation is a search-topic scope, not an isomer identity.

    The registered string is unchanged, no single substance is identified, and the
    per-isomer records are kept out of the concept so nothing can be read as the
    family's identifier.
    """

    concept = _concepts()[
        "jptr:compound-" + compound_id[len("compound_"):].replace("_", "-")
    ]
    assert concept["skos:broader"] == "jptr:compound-identity-unverified"
    assert "skos:exactMatch" not in concept
    labels = {item["@language"]: item["@value"] for item in concept["skos:prefLabel"]}
    assert labels == {"en": term, "ja": term}
    note = " ".join(item["@value"] for item in concept.get("skos:scopeNote", []))
    assert family in note
    assert carbon in note
    assert "Δ8/Δ9" in note and "未指定" in note
    assert "UNCONFIRMED" in note and "未確認" in note
    assert "literal" in note and "文字列一致" in note
    for identifier in PER_ISOMER_IDENTIFIERS:
        assert identifier not in note, (term, identifier)
    registry = {q["query_id"]: q for q in _registry()}
    assert registry[f"{slug}-general-ja"]["canonical_text"] == term
    assert registry[f"{slug}-liquid-ja"]["canonical_text"] == term + " リキッド"


def test_thcpo_documents_the_thcp_o_acetate_family_without_a_mapping() -> None:
    """THCPO is an isomer-unspecified THCP-O-acetate family, not a single record.

    The owner confirmed only the meaning and named no isomer, so the family scope
    is this repository's registration-level reading, not an owner-confirmed
    family. The 2024 MHLW structural groups cover both isomers subject to the
    ordinance's narcotics exclusion, and Tanaka et al. 2025 identified the Δ9
    acetate (plus a Δ8 C5 acetate that is not this family). Neither fact identifies
    the registered string with one substance or with the content of any result.
    Unsupported analogue claims are absent, and the per-isomer identifiers stay
    in the provenance ledger.
    """

    concept = _concepts()["jptr:compound-thcpo"]
    assert concept["skos:broader"] == "jptr:compound-identity-unverified"
    assert "skos:exactMatch" not in concept
    assert "skos:related" not in concept
    labels = {
        item["@language"]: item["@value"] for item in concept["skos:prefLabel"]
    }
    assert labels == {"en": "THCPO", "ja": "THCPO"}
    alt_labels = [item["@value"] for item in concept.get("skos:altLabel", [])]
    assert "THCP-O-acetate" in alt_labels
    assert "THCPO リキッド" in alt_labels
    note = " ".join(item["@value"] for item in concept.get("skos:scopeNote", []))
    assert "THCP-O-acetate" in note
    assert "no Δ8 or Δ9 isomer" in note and "Δ8 体・Δ9 体" in note
    assert "未指定" in note
    assert "UNCONFIRMED" in note and "未確認" in note
    assert "literal" in note and "文字列一致" in note
    # The owner's answer is recorded as an answer, and the family reading is ours.
    assert "confirmation question" in note and "`y`" in note
    assert "確認質問" in note
    assert "not a family the owner explicitly confirmed" in note
    assert "owner がファミリーを明示的に確認したものではない" in note
    # The altLabel is a concept-level record, not a synonym implied by the category.
    assert "skos:altLabel" in note
    assert "not a claim that the family is one chemical structure" in note
    assert "単一の化学構造であるという主張でもない" in note
    # Distinct terms are named neutrally, with no unsupported analogue claims.
    for distinct in ("compound_thc_o", "THCP-O-butanoate", "compound_hhcpo"):
        assert distinct in note, distinct
    for unsupported in ("exo-THCP", "hexahydro", "六水素", "structural isomer of THCP"):
        assert unsupported not in note, unsupported
    # The statutory coverage keeps the ordinance's narcotics exclusion.
    assert "令和6年厚生労働省令第81号" in note
    assert "麻薬を除く" in note
    assert "statutory structural fact" in note
    assert "not part of the owner's identity confirmation" in note
    # Tanaka 2025 identifies a Δ8 C5 acetate, not Δ8-THCP-O-acetate.
    assert "Δ8-THC-O" in note
    assert "which is not Δ8-THCP-O-acetate" in note
    assert "10.1002/dta.3883" in note
    for identifier in PER_ISOMER_IDENTIFIERS_THCPO:
        assert identifier not in note, identifier
    registry = {q["query_id"]: q for q in _registry()}
    assert registry["thcpo-general-ja"]["canonical_text"] == "THCPO"
    assert registry["thcpo-liquid-ja"]["canonical_text"] == "THCPO リキッド"


def test_administrative_category_states_the_isomer_unspecified_family_case() -> None:
    """The category explains why a family-scoped term stays in a registration state.

    It also states that membership never implies a synonym: a concept-level
    alternate label needs its own recorded basis in that concept's scopeNote.
    """

    category = _concepts()["jptr:compound-identity-unverified"]
    note = " ".join(item["@value"] for item in category["skos:scopeNote"])
    assert "isomer-unspecified homologue family" in note
    assert "異性体未指定の同族体ファミリー" in note
    assert "single-substance chemical identity" in note
    assert "Membership itself establishes no synonym relationship" in note
    assert "skos:altLabel is a concept-level record" in note
    assert "does not assert that the family denotes one chemical structure" in note
    assert "membership 自体は同義関係を確立しない" in note
    assert "概念レベルの記録" in note


def test_identity_unverified_alternate_labels_need_a_recorded_basis() -> None:
    """Category membership is not a synonym; each extra label is documented.

    A member's non-liquid ``skos:altLabel`` must be recorded in that concept's
    own scopeNote. Only THCPO currently carries one, and its note states that the
    owner-confirmed meaning is a search-scope label, not one chemical structure.
    """

    concepts = _concepts()
    category = concepts["jptr:compound-identity-unverified"]
    documented: dict[str, str] = {}
    for member in category["skos:narrower"]:
        concept = concepts[member]
        note = " ".join(item["@value"] for item in concept.get("skos:scopeNote", []))
        for item in concept.get("skos:altLabel", []):
            label = item["@value"]
            if label.endswith(" リキッド"):
                continue
            assert label in note, (member, label)
            documented[member] = label
    assert documented == {"jptr:compound-thcpo": "THCP-O-acetate"}


def test_cbe_is_identified_as_cannabielsoin_but_still_measures_a_literal_string() -> None:
    """The owner's CBE confirmation is documented; the query is not content-veri
fied."""

    concept = _concepts()["jptr:compound-cbe"]
    assert concept["skos:broader"] == "jptr:compound-minor"
    labels = {
        item["@language"]: item["@value"]
        for item in concept["skos:prefLabel"]
    }
    assert labels == {"en": "Cannabielsoin (CBE)", "ja": "カンナビエルソイン (CBE)"}
    assert set(concept["skos:exactMatch"]) == {
        "wikidata:Q22668702",
        "https://identifiers.org/unii:2ERD6V6652",
    }
    scope_note = " ".join(
        item["@value"] for item in concept.get("skos:scopeNote", [])
    )
    assert "cannabielsoin" in scope_note.lower()
    assert "UNII 2ERD6V6652" in scope_note
    assert "52025-76-0" in scope_note
    assert "literal strings" in scope_note
    # The query strings did not change with the identity.
    registry = {q["query_id"]: q for q in _registry()}
    assert registry["cbe-general-ja"]["canonical_text"] == "CBE"
    assert registry["cbe-liquid-ja"]["canonical_text"] == "CBE リキッド"


@pytest.mark.parametrize(
    "term,compound_id,slug,pref_label,exact_match,identifiers",
    [
        (
            CBL[0],
            CBL[1],
            CBL[2],
            "Cannabicyclol (CBL)",
            {"wikidata:Q907909"},
            ("Q907909", "MP5WZK8M5U", "30607", "59444380", "21366-63-2", "67920-00-7"),
        ),
        (
            CBGA[0],
            CBGA[1],
            CBGA[2],
            "Cannabigerolic acid (CBGA)",
            {
                "chebi:67081",
                "wikidata:Q27135612",
                "https://identifiers.org/unii:80I4ZM847Y",
            },
            ("67081", "Q27135612", "80I4ZM847Y", "6449999", "25555-57-1", "C22H32O4"),
        ),
    ],
    ids=[CBL[2], CBGA[2]],
)
def test_cbl_and_cbga_are_identified_but_still_measure_literal_strings(
    term: str,
    compound_id: str,
    slug: str,
    pref_label: str,
    exact_match: set[str],
    identifiers: tuple[str, ...],
) -> None:
    """The 2026-11-11 confirmations are documented; the queries stay strings.

    The taxonomy must carry the verified identifier without inventing a relation
    to ``compound_cbg`` or a chemical-class link.
    """

    concept = _concepts()[
        "jptr:compound-" + compound_id[len("compound_"):].replace("_", "-")
    ]
    assert concept["skos:broader"] == "jptr:compound-minor"
    labels = {item["@language"]: item["@value"] for item in concept["skos:prefLabel"]}
    assert labels["en"] == pref_label, compound_id
    exact = concept["skos:exactMatch"]
    assert set(exact if isinstance(exact, list) else [exact]) == exact_match, compound_id
    assert "skos:related" not in concept, compound_id
    note = " ".join(item["@value"] for item in concept.get("skos:scopeNote", []))
    for identifier in identifiers:
        assert identifier in note, (compound_id, identifier)
    assert "literal" in note and "文字列一致" in note, compound_id
    assert "ISS-20261111-TAX-040" in note, compound_id
    registry = {q["query_id"]: q for q in _registry()}
    assert registry[f"{slug}-general-ja"]["canonical_text"] == term
    assert registry[f"{slug}-liquid-ja"]["canonical_text"] == term + " リキッド"


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
        compound_id for _, compound_id, _ in BATCH + THCA_THCB_TOPICS
    )
    for _, compound_id, _ in EXISTING:
        item = by_compound[compound_id]
        assert item["decided"] == "2026-11-10"
        assert item["decided_by"] == "owner"
        assert item["identity_state"] == "existing_canonical_concept_reused"
        assert "ISS-20261110-TAX-039" in item["reason"]
    for _, compound_id, _ in UNRESOLVED_NEW_TERMS:
        item = by_compound[compound_id]
        assert item["decided"] == "2026-11-11"
        assert item["decided_by"] == "owner"
        assert item["identity_state"] == "compound_identity_unverified"
        assert "compound_identity_unverified" in item["reason"]
        assert "UNVERIFIED" in item["reason"]
        assert "ISS-20261111-TAX-040" in item["reason"]
    cbe = by_compound[CBE[1]]
    assert cbe["decided"] == "2026-11-11"
    assert cbe["decided_by"] == "owner"
    assert cbe["identity_state"] == "documented_identity_cannabielsoin"
    assert "cannabielsoin" in cbe["reason"].lower()
    assert "ISS-20261111-TAX-040" in cbe["reason"]
    for _, compound_id, _ in THCA_THCB_TOPICS:
        item = by_compound[compound_id]
        assert item["decided"] == "2026-11-11"
        assert item["decided_by"] == "owner"
        assert item["identity_state"] == "compound_identity_unverified"
        assert "ISS-20261111-TAX-041" in item["reason"]
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
    batch_ids = {
        compound_id for _, compound_id, _ in BATCH + THCA_THCB_TOPICS
    }
    for scale in document["comparison_scales"]:
        excluded = {
            item["compound_id"]
            for item in scale["compound_set"].get("excluded_compound_ids", [])
        }
        assert not (excluded & batch_ids), scale["scale_id"]


# ---------------------------------------------------------------------------
# the project mirror carries pointers, not stale per-source statuses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "term,compound_id,slug",
    BATCH + THCA_THCB_TOPICS,
    ids=[t[2] for t in BATCH + THCA_THCB_TOPICS],
)
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
    if compound_id in {
        c for _, c, _ in UNRESOLVED_NEW_TERMS + THCA_THCB_TOPICS
    }:
        assert "compound_identity_unverified" in entry["identityNote"]
    for confirmed_id, expected in (
        (CBE[1], "cannabielsoin"),
        (CBL[1], "cannabicyclol"),
        (CBGA[1], "cannabigerolic acid"),
    ):
        if compound_id == confirmed_id:
            assert expected in entry["identityNote"].lower()
            assert "compound_identity_unverified" not in entry["identityNote"]


def test_project_coverage_note_removes_the_obsolete_raw_count() -> None:
    coverage = _project()["dataCoverage"]
    note = coverage["auditNote"]
    assert "37 runs" not in note
    assert "cannabinoid-raw-collection/README.md" in note
    assert "audit-youtube-coverage" in note
    assert "not refreshed" in note


# ---------------------------------------------------------------------------
# the 2026-11-11 THCA / THCB search-topic split
# ---------------------------------------------------------------------------


def test_thca_thcb_topics_are_literal_registrations_without_a_mapping() -> None:
    """Six specific strings replace the generic reading; the generic terms stay.

    Owner confirmation fixes the query topic.  It does not select a single
    external record, so no concept carries an identifier or a skos:related link,
    and the isomer-unspecified acetate says so explicitly.
    """

    concepts = _concepts()
    for term, compound_id, _ in THCA_THCB_TOPICS:
        concept = concepts[
            "jptr:compound-" + compound_id[len("compound_"):].replace("_", "-")
        ]
        assert concept["skos:broader"] == "jptr:compound-identity-unverified"
        labels = {
            item["@language"]: item["@value"]
            for item in concept["skos:prefLabel"]
        }
        assert labels == {"en": term, "ja": term}
        alt_labels = [item["@value"] for item in concept.get("skos:altLabel", [])]
        assert alt_labels == [term + " リキッド"]
        assert "skos:exactMatch" not in concept
        assert "skos:related" not in concept
        note = " ".join(
            item["@value"] for item in concept.get("skos:scopeNote", [])
        )
        assert "ISS-20261111-TAX-041" in note
        assert "UNCONFIRMED" in note and "未確認" in note
        assert "literal" in note and "文字列" in note and "一致" in note
        assert "compound_thca" in note or "compound_thcb" in note
    acetate = " ".join(
        item["@value"]
        for item in concepts["jptr:compound-thcb-o-acetate"]["skos:scopeNote"]
    )
    assert "isomer-unspecified" in acetate and "異性体未指定" in acetate
    assert "令和6年厚生労働省令第81号" in acetate

    registry = {q["query_id"]: q for q in _registry()}
    for query_id, text in (
        ("thca-general-ja", "THCA"),
        ("thca-liquid-ja", "THCA リキッド"),
        ("thcb-general-ja", "THCB"),
        ("thcb-liquid-ja", "THCB リキッド"),
    ):
        assert registry[query_id]["canonical_text"] == text
        assert registry[query_id]["status"] == "active"
        assert registry[query_id]["compound_id"] in {
            "compound_thca",
            "compound_thcb",
        }


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


def test_study_readme_term_table_lists_every_registered_topic() -> None:
    """The detailed term table must list all 15 additions and the six topics.

    THCA-B was omitted once. The table is the reader's coverage map, so a missing
    row hides an uncollected registration instead of reporting its state.
    """

    text = README.read_text(encoding="utf-8")
    start = text.index("### 登録済みキーワードと収集状態")
    section = text[start:]
    next_heading = section.find("\n### ", 1)
    if next_heading != -1:
        section = section[:next_heading]
    for term, _, slug in NEW_TERMS + THCA_THCB_TOPICS:
        rows = [
            line
            for line in section.splitlines()
            if line.startswith(f"| {term} |") or line.startswith(f"| {term}（")
        ]
        assert rows, term
        row = "\n".join(rows)
        assert f"{slug}-general-ja" in row, term
        assert f"{slug}-liquid-ja" in row, term
    # The six active compound_general registrations add 18 design-only
    # required entries (3 common-scale policies x 6), not a collection failure.
    assert "計 18 件" in section and "設計上" in section


def test_design_caveat_names_the_supported_thca_thcb_topics() -> None:
    """The caveat must not imply that Δ8-THCA has a literature source.

    Δ9-THCA-A, THCA-B, Δ8-THCB and Δ9-THCB are the four named in the cited
    sources; Δ8-THCA is unsourced here and THCB-O-acetate is isomer-unspecified.
    """

    caveat = _design()["compound_set"]["identity_caveat"]
    assert "The first four" not in caveat
    for term in ("Δ9-THCA-A", "THCA-B", "Δ8-THCB", "Δ9-THCB"):
        assert term in caveat, term
    assert "Δ8-THCA has no structural or nomenclatural source verified" in caveat
    assert "THCB-O-acetate leaves the Δ8/Δ9 isomer unspecified" in caveat
