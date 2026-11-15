"""`compound_rare` stays intentionally empty; owner-named identity-unverified terms
live in an administrative category instead.

Contract sources: ``ISS-20261015-TAX-027`` (the 2026-10-15 decision, still in force
for ``compound_rare`` itself), ``ISS-20261111-TAX-040`` (the owner-directed decision
that supersedes TAX-027's *non-registration* decision and registers the batch),
``metadata/taxonomy/compound-taxonomy.skos.jsonld``, ``docs/provenance/compound-taxonomy.md``,
``metadata/taxonomy/iptc-mapping.yaml``, ``docs/data-dictionary.md`` section 6.4.

The rule, in two parts, because the two categories answer different questions:

1. ``compound_rare`` (route/origin dimension) is still INTENTIONALLY EMPTY. A rare
   member may only be added with collection-grade evidence -- a raw run, a
   registered query, or a research/regulatory-status record naming the compound,
   plus a documented route/origin placement -- and it must update every layer
   together. In particular ``compound_cbdp`` stays unregistered: the owner named no
   such term and the repository has no evidence for it.

2. The owner-named batch terms whose identities remain unresolved are registered
   in ``compound_identity_unverified``, an ADMINISTRATIVE registration-state
   category. That placement states no route/origin, natural occurrence, chemical
   class, structure, synonym or regulatory claim, carries no external identifier,
   and is never a substitute for a route category. ``compound_thcp`` exists because
   the owner directed it; TAX-027's prior non-registration decision is superseded by
   the dated record, not silently dropped. ``CBE``, ``CBL`` and ``CBGa`` left this
   category on 2026-11-11 when the owner confirmed them as cannabielsoin,
   cannabicyclol and cannabigerolic acid; they are now in ``compound_minor``
   with verified identifiers.

On 2026-11-11 the owner also split the generic THCA and THCB readings into six
specific search topics (``ISS-20261111-TAX-041``). Those six strings joined the
same administrative category without an identifier; the generic ``compound_thca``
and ``compound_thcb`` concepts remain separate literal-string registrations.

Both decisions are pinned explicitly: removing a member, moving one into
``compound_rare``, inventing an identifier, or dropping the supersession record
fails here first.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_DIR = REPO_ROOT / "metadata/taxonomy"
COMPOUND_TAXONOMY = TAXONOMY_DIR / "compound-taxonomy.skos.jsonld"
IPTC_MAPPING = TAXONOMY_DIR / "iptc-mapping.yaml"
DATA_DICTIONARY = REPO_ROOT / "docs/data-dictionary.md"
PROVENANCE_LEDGER = REPO_ROOT / "docs/provenance/compound-taxonomy.md"

RARE_CATEGORY_ID = "jptr:compound-rare"
ADMIN_CATEGORY_ID = "jptr:compound-identity-unverified"
ADMIN_CATEGORY_NOTATION = "compound_identity_unverified"

# The owner's terms exactly as written (2026-11-11 direction), with the notation
# the repository convention derives.  CBGa keeps its lowercase 'a'; 10-OH-HHC
# keeps its hyphens.  Pinned so a silent rename fails here.
BATCH = (
    ("THCB", "compound_thcb"),
    ("THCP", "compound_thcp"),
    ("THCJD", "compound_thcjd"),
    ("THCPO", "compound_thcpo"),
    ("CBE", "compound_cbe"),
    ("HHCPO", "compound_hhcpo"),
    ("CBND", "compound_cbnd"),
    ("CBL", "compound_cbl"),
    ("CBGa", "compound_cbga"),
    ("CBP", "compound_cbp"),
    ("10-OH-HHC", "compound_10_oh_hhc"),
    ("THXE", "compound_thxe"),
    ("THCA", "compound_thca"),
)
BATCH_NOTATIONS = tuple(notation for _, notation in BATCH)
BATCH_IDS = tuple(
    "jptr:compound-" + notation[len("compound_"):].replace("_", "-")
    for notation in BATCH_NOTATIONS
)
# CBE, CBL and CBGa were registered with this batch but identified the same day.
CBE = ("CBE", "compound_cbe")
CBL = ("CBL", "compound_cbl")
CBGA = ("CBGa", "compound_cbga")
CONFIRMED = {CBE[0], CBL[0], CBGA[0]}
# The THCA / THCB search-topic concepts registered on 2026-11-11
# (ISS-20261111-TAX-041) joined the same administrative category: six specific
# strings whose single-substance identity was not established by the owner's
# confirmation.  Delta signs and hyphens are kept exactly.
THCA_THCB_TOPICS = (
    ("Δ9-THCA-A", "compound_delta9_thca_a"),
    ("THCA-B", "compound_thca_b"),
    ("Δ8-THCA", "compound_delta8_thca"),
    ("Δ8-THCB", "compound_delta8_thcb"),
    ("Δ9-THCB", "compound_delta9_thcb"),
    ("THCB-O-acetate", "compound_thcb_o_acetate"),
)
TOPIC_NOTATIONS = tuple(notation for _, notation in THCA_THCB_TOPICS)
TOPIC_IDS = tuple(
    "jptr:compound-" + notation[len("compound_"):].replace("_", "-")
    for notation in TOPIC_NOTATIONS
)
ADMIN_BATCH = (
    tuple(item for item in BATCH if item[0] not in CONFIRMED) + THCA_THCB_TOPICS
)
# The 27 forms the owner registered on 2026-11-15 from the study README's
# candidate-form table (ISS-20261115-TAX-045).  They join the same
# administrative registration-state category: each is a registered search topic
# whose single-substance identity this repository has not established, and the
# category asserts no route, structure, synonym or regulatory claim.
FORM_BATCH = (
    ("Δ8-THCP", "compound_delta8_thcp"),
    ("Δ9-THCP", "compound_delta9_thcp"),
    ("Δ8-THCJD", "compound_delta8_thcjd"),
    ("Δ9-THCJD", "compound_delta9_thcjd"),
    ("Δ8-THCP-O-acetate", "compound_delta8_thcp_o_acetate"),
    ("Δ9-THCP-O-acetate", "compound_delta9_thcp_o_acetate"),
    ("Δ8-THCB-O-acetate", "compound_delta8_thcb_o_acetate"),
    ("Δ9-THCB-O-acetate", "compound_delta9_thcb_o_acetate"),
    ("Δ8-THC", "compound_delta8_thc"),
    ("Δ6a(10a)-THC", "compound_delta6a_10a_thc"),
    ("Δ6a(7)-THC", "compound_delta6a_7_thc"),
    ("Δ7-THC", "compound_delta7_thc"),
    ("Δ10-THC", "compound_delta10_thc"),
    ("Δ9(11)-THC", "compound_delta9_11_thc"),
    ("Δ9-THCV", "compound_delta9_thcv"),
    ("Δ8-THCV", "compound_delta8_thcv"),
    ("THCJD-O-acetate", "compound_thcjd_o_acetate"),
    ("Δ8-THCH", "compound_delta8_thch"),
    ("Δ9-THCH", "compound_delta9_thch"),
    ("9(R)-HHC", "compound_9_r_hhc"),
    ("9(S)-HHC", "compound_9_s_hhc"),
    ("(6aS,9S,10aS)-HHC", "compound_6as_9s_10as_hhc"),
    ("(6aS,9R,10aS)-HHC", "compound_6as_9r_10as_hhc"),
    ("(6aS,9S,10aR)-HHC", "compound_6as_9s_10ar_hhc"),
    ("(6aS,9R,10aR)-HHC", "compound_6as_9r_10ar_hhc"),
    ("(6aR,9S,10aS)-HHC", "compound_6ar_9s_10as_hhc"),
    ("(6aR,9R,10aS)-HHC", "compound_6ar_9r_10as_hhc"),
)
ADMIN_BATCH_NOTATIONS = tuple(
    notation for _, notation in ADMIN_BATCH + FORM_BATCH
)
ADMIN_BATCH_IDS = tuple(
    "jptr:compound-" + notation[len("compound_"):].replace("_", "-")
    for notation in ADMIN_BATCH_NOTATIONS
)
# Named by the 2026-10-15 decision as *not* to be invented; CBDP stays that way.
STILL_UNREGISTERED = ("compound_cbdp", "jptr:compound-cbdp")


def _concepts() -> list[dict]:
    document = json.loads(COMPOUND_TAXONOMY.read_text(encoding="utf-8"))
    return [n for n in document["@graph"] if n.get("@type") == "skos:Concept"]


def _by_id() -> dict[str, dict]:
    return {node["@id"]: node for node in _concepts()}


def _by_notation() -> dict[str, dict]:
    return {node["skos:notation"]: node for node in _concepts()}


def _label_values(node: dict, key: str) -> list[str]:
    value = node.get(key)
    items = value if isinstance(value, list) else [value] if value else []
    return [item["@value"] for item in items if isinstance(item, dict) and "@value" in item]


def _scope_note_value(node: dict) -> str:
    return " ".join(_label_values(node, "skos:scopeNote"))


def _iptc_coverage() -> dict[str, set[str]]:
    """Read the IPTC coverage declaration textually (no YAML dependency)."""

    text = IPTC_MAPPING.read_text(encoding="utf-8")
    body = text.split("\ncoverage:", 1)[1]
    deliberately = body.split("\n  deliberately_unmapped:", 1)[1]
    deliberately = deliberately.split("\n  not_applicable:", 1)[0]
    not_applicable = body.split("\n  not_applicable:", 1)[1]
    not_applicable = not_applicable.split("\nlimitations:", 1)[0]
    return {
        "mapped": set(re.findall(r'skos_id:\s*"([^"]+)"', text)),
        "deliberately_unmapped": set(re.findall(r'"(jptr:[^"]+)"', deliberately)),
        "not_applicable": set(re.findall(r'"(jptr:[^"]+)"', not_applicable)),
    }


# ---------------------------------------------------------------------------
# compound_rare: the 2026-10-15 decision still holds
# ---------------------------------------------------------------------------


def test_rare_category_is_empty_and_explained() -> None:
    """The decided TAX-027 state: no members, with the reason written down."""

    rare = _by_id()[RARE_CATEGORY_ID]
    assert rare.get("skos:narrower", []) == []
    assert "INTENTIONALLY EMPTY" in _scope_note_value(rare)
    assert [n["@id"] for n in _concepts() if n.get("skos:broader") == RARE_CATEGORY_ID] == []


def test_cbdp_is_still_not_invented() -> None:
    """The owner named no CBDP term; the taxonomy must not invent one for it."""

    nodes = _concepts()
    assert STILL_UNREGISTERED[0] not in {n.get("skos:notation") for n in nodes}
    assert STILL_UNREGISTERED[1] not in {n["@id"] for n in nodes}


# ---------------------------------------------------------------------------
# compound_identity_unverified: the owner-directed administrative category
# ---------------------------------------------------------------------------


def test_the_batch_is_registered_in_the_administrative_category() -> None:
    """Every owner term resolves to exactly one concept, under the new category."""

    notations = _by_notation()
    for term, notation in ADMIN_BATCH:
        concept = notations[notation]
        assert concept.get("skos:broader") == ADMIN_CATEGORY_ID, notation
        assert _label_values(concept, "skos:prefLabel") == [term, term], notation
        assert concept.get("skos:exactMatch") is None, notation

    category = _by_id()[ADMIN_CATEGORY_ID]
    assert category["skos:notation"] == ADMIN_CATEGORY_NOTATION
    assert sorted(category["skos:narrower"]) == sorted(ADMIN_BATCH_IDS)
    assert category.get("skos:topConceptOf") == "jptr:compound-taxonomy"
    assert category.get("skos:broader") is None


def test_the_administrative_category_makes_no_chemical_or_route_claim() -> None:
    """The category must say, in both languages, what it does not claim."""

    note = _scope_note_value(_by_id()[ADMIN_CATEGORY_ID])
    assert "ADMINISTRATIVE" in note
    for domain in (
        "route",
        "natural occurrence",
        "chemical class",
        "structure",
        "synonym",
        "regulatory",
    ):
        assert domain in note, domain
    assert "管理上の登録状態" in note
    assert "UNCONFIRMED" in note
    assert "ISS-20261111-TAX-040" in note


def test_members_carry_no_identifier_or_chemical_class_link() -> None:
    """An unverified identity gains no external identifier and no class link."""

    chemclass_ids = {
        node["@id"]
        for path in (TAXONOMY_DIR / "chemical-class-taxonomy.skos.jsonld",)
        for node in json.loads(path.read_text(encoding="utf-8"))["@graph"]
        if node.get("@type") == "skos:Concept"
    }
    for node in _by_id().values():
        if node.get("skos:broader") != ADMIN_CATEGORY_ID:
            continue
        # Only registration fields are allowed: an identifier key (exactMatch /
        # CAS / PubChem / chemical class) cannot appear without failing here.
        assert set(node) <= {
            "@id",
            "@type",
            "skos:inScheme",
            "skos:broader",
            "skos:prefLabel",
            "skos:altLabel",
            "skos:notation",
            "skos:scopeNote",
            "skos:related",
        }, node["@id"]
        assert "skos:exactMatch" not in node, node["@id"]
        for target in node.get("skos:related", []) or []:
            assert target not in chemclass_ids, (node["@id"], target)
        note = _scope_note_value(node)
        assert "UNCONFIRMED" in note, node["@id"]
        # Each member records the decision that placed it: the 2026-11-11
        # registration batch, the same-day THCA / THCB topic split, or the
        # 2026-11-15 candidate-form registration.
        assert (
            "ISS-20261111-TAX-040" in note
            or "ISS-20261111-TAX-041" in note
            or "ISS-20261115-TAX-045" in note
        ), node["@id"]


def test_cbl_and_cbga_left_the_administrative_category_for_a_source_backed_placement() -> None:
    """The move condition was met for CBL and CBGa; both are documented identities."""

    notations = _by_notation()
    admin_members = _by_id()[ADMIN_CATEGORY_ID]["skos:narrower"]
    for term, notation in (CBL, CBGA):
        concept = notations[notation]
        assert concept.get("skos:broader") == "jptr:compound-minor", term
        assert concept["@id"] not in admin_members, term
    cbl = notations[CBL[1]]
    assert cbl["skos:exactMatch"] == "wikidata:Q907909"
    assert _label_values(cbl, "skos:prefLabel") == [
        "Cannabicyclol (CBL)",
        "カンナビシクロール (CBL)",
    ]
    assert "skos:related" not in cbl
    cbl_note = _scope_note_value(cbl)
    assert "cannabicyclol" in cbl_note.lower()
    assert "21366-63-2" in cbl_note and "67920-00-7" in cbl_note
    assert "literal" in cbl_note and "ISS-20261111-TAX-040" in cbl_note
    cbga = notations[CBGA[1]]
    assert set(cbga["skos:exactMatch"]) == {
        "chebi:67081",
        "wikidata:Q27135612",
        "https://identifiers.org/unii:80I4ZM847Y",
    }
    assert _label_values(cbga, "skos:prefLabel") == [
        "Cannabigerolic acid (CBGA)",
        "カンナビゲロール酸 (CBGA)",
    ]
    # CBGA is distinct from CBG; the precursor relation is prose only.
    assert "skos:related" not in cbga
    cbga_note = _scope_note_value(cbga)
    assert "cannabigerolic acid" in cbga_note.lower()
    assert "compound_cbg" in cbga_note
    assert "literal" in cbga_note and "ISS-20261111-TAX-040" in cbga_note


def test_cbe_left_the_administrative_category_for_a_source_backed_placement() -> None:
    """The move condition was met; CBE is not an unverified registration anymore."""

    cbe = _by_notation()[CBE[1]]
    assert cbe.get("skos:broader") == "jptr:compound-minor"
    assert "jptr:compound-cbe" not in _by_id()[ADMIN_CATEGORY_ID]["skos:narrower"]
    assert set(cbe["skos:exactMatch"]) == {
        "wikidata:Q22668702",
        "https://identifiers.org/unii:2ERD6V6652",
    }
    labels = _label_values(cbe, "skos:prefLabel")
    assert "Cannabielsoin (CBE)" in labels
    note = _scope_note_value(cbe)
    assert "cannabielsoin" in note.lower()
    assert "literal" in note
    assert "ISS-20261111-TAX-040" in note


def test_thcp_records_the_superseding_decision() -> None:
    """THCP exists by owner direction, not by silent reversal of TAX-027."""

    thcp = _by_notation()["compound_thcp"]
    assert thcp.get("skos:broader") == ADMIN_CATEGORY_ID
    note = _scope_note_value(thcp)
    assert "ISS-20261015-TAX-027" in note
    assert "supersedes" in note
    assert "ISS-20261111-TAX-040" in note
    assert "ISS-20261015-TAX-027" in _scope_note_value(_by_id()[ADMIN_CATEGORY_ID])


# ---------------------------------------------------------------------------
# the declarations outside the taxonomy that the decision also touches
# ---------------------------------------------------------------------------


def test_batch_members_are_declared_outside_iptc_subjects() -> None:
    """No IPTC subject is guessed, with or without an identifier."""

    coverage = _iptc_coverage()
    assert ADMIN_CATEGORY_ID in coverage["not_applicable"]
    assert ADMIN_CATEGORY_ID not in coverage["mapped"]
    for concept_id in (*BATCH_IDS, *TOPIC_IDS):
        assert concept_id in coverage["deliberately_unmapped"], concept_id
        assert concept_id not in coverage["mapped"], concept_id
    text = IPTC_MAPPING.read_text(encoding="utf-8")
    for concept_id in (ADMIN_CATEGORY_ID, *BATCH_IDS, *TOPIC_IDS):
        assert f'- skos_id: "{concept_id}"' not in text, concept_id


def test_data_dictionary_mirrors_both_categories() -> None:
    """Section 6.4 is a copy of the taxonomy: rare empty, batch listed."""

    text = DATA_DICTIONARY.read_text(encoding="utf-8")
    marker = "### 6.4 "
    assert marker in text
    section = text.split(marker, 1)[1]
    section = section.split("\n## ", 1)[0]
    row = re.compile(r"^\|\s*`(compound_[a-z_]+)`\s*\|([^|]*)\|([^|]*)\|\s*$", re.M)
    rows = {match.group(1): match.group(3) for match in row.finditer(section)}
    assert re.findall(r"`(compound_[a-z_0-9]+)`", rows["compound_rare"]) == []
    assert sorted(re.findall(r"`(compound_[a-z_0-9]+)`", rows[ADMIN_CATEGORY_NOTATION])) == sorted(
        ADMIN_BATCH_NOTATIONS
    )
    minor_members = re.findall(r"`(compound_[a-z_0-9]+)`", rows["compound_minor"])
    for confirmed in ("compound_cbe", "compound_cbl", "compound_cbga"):
        assert confirmed in minor_members, confirmed


def test_provenance_records_the_superseding_decision() -> None:
    """'Record the decision' is machine-checked, including the supersession."""

    text = PROVENANCE_LEDGER.read_text(encoding="utf-8")
    assert "TAX-027" in text
    assert "compound_cbdp" in text
    assert "ISS-20261111-TAX-040" in text
    assert "compound_thcp" in text
    assert "置換" in text
    assert "compound_identity_unverified" in text
