"""`compound_rare` stays intentionally empty until collection-grade evidence arrives.

Contract sources: ``ISS-20261015-TAX-027`` (OPEN),
``metadata/taxonomy/compound-taxonomy.skos.jsonld`` (the ``compound_rare`` scopeNote),
``docs/provenance/compound-taxonomy.md`` (the TAX-027 decision record),
``metadata/taxonomy/iptc-mapping.yaml`` (``compound-rare`` is ``not_applicable``),
``docs/data-dictionary.md`` section 6.4 (the taxonomy mirror).

The rule: SKOS category membership (a compound concept with ``skos:broader``
pointing at ``compound_rare``) requires collection-grade repository evidence -- a
raw run, a registered query, or a research/regulatory-status record naming the
compound, plus a documented route/origin placement.  A passing mention (a COA
analyte panel, a generic cannabinoid list, or the scopeNote's own CBDP/THCP
examples) is not membership evidence.  In particular the repository must not
invent ``compound_cbdp`` / ``compound_thcp`` concepts, Japanese labels,
ChEBI/Wikidata exactMatches, or IPTC subject mappings just to fill the category.

Adding a rare member later is allowed, but it must update every layer together
(taxonomy, the IPTC declaration, the data-dictionary mirror, the query registry
where collection demand exists, and the provenance ledger), which is why this
test names the current empty state explicitly: a silent single-file addition
fails here first.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_DIR = REPO_ROOT / "metadata/taxonomy"
COMPOUND_TAXONOMY = TAXONOMY_DIR / "compound-taxonomy.skos.jsonld"
IPTC_MAPPING = TAXONOMY_DIR / "iptc-mapping.yaml"
QUERY_REGISTRY = REPO_ROOT / "metadata/queries/query-registry.json"
DATA_DICTIONARY = REPO_ROOT / "docs/data-dictionary.md"
PROVENANCE_LEDGER = REPO_ROOT / "docs/provenance/compound-taxonomy.md"

RARE_CATEGORY_ID = "jptr:compound-rare"

# Candidate notations named by TAX-027.  Listed explicitly so that inventing
# either concept without meeting the evidence gate fails loudly here.
CANDIDATE_NOTATIONS = ("compound_cbdp", "compound_thcp")
CANDIDATE_IDS = ("jptr:compound-cbdp", "jptr:compound-thcp")


def _concepts() -> list[dict]:
    document = json.loads(COMPOUND_TAXONOMY.read_text(encoding="utf-8"))
    return [n for n in document["@graph"] if n.get("@type") == "skos:Concept"]


def _scope_note_value(node: dict) -> str:
    note = node.get("skos:scopeNote")
    if isinstance(note, dict):
        return note.get("@value", "")
    if isinstance(note, list):
        return " ".join(item.get("@value", "") for item in note if isinstance(item, dict))
    return ""


def test_rare_category_is_empty_and_explained() -> None:
    """The decided TAX-027 state: no members, with the reason written down."""
    by_id = {n["@id"]: n for n in _concepts()}
    rare = by_id[RARE_CATEGORY_ID]
    assert rare.get("skos:narrower", []) == []
    assert "INTENTIONALLY EMPTY" in _scope_note_value(rare)


def test_no_invented_rare_member_concepts() -> None:
    """CBDP/THCP concepts must not appear without the evidence gate."""
    nodes = _concepts()
    notations = {n.get("skos:notation") for n in nodes}
    ids = {n["@id"] for n in nodes}
    for notation in CANDIDATE_NOTATIONS:
        assert notation not in notations, notation
    for concept_id in CANDIDATE_IDS:
        assert concept_id not in ids, concept_id
    children = [n["@id"] for n in nodes if n.get("skos:broader") == RARE_CATEGORY_ID]
    assert children == []


def test_no_rare_member_queries() -> None:
    """Every registered compound resolves to the taxonomy; no rare orphans."""
    registry = json.loads(QUERY_REGISTRY.read_text(encoding="utf-8"))
    compound_ids = {q["compound_id"] for q in registry["queries"]}
    notations = {n["skos:notation"] for n in _concepts() if "skos:notation" in n}
    assert compound_ids <= notations
    for notation in CANDIDATE_NOTATIONS:
        assert notation not in compound_ids, notation


def test_rare_category_stays_out_of_iptc_subjects() -> None:
    """``compound-rare`` is declared out of scope; candidates gain no mapping."""
    text = IPTC_MAPPING.read_text(encoding="utf-8")
    assert "\n  not_applicable:" in text
    chunk = text.split("\n  not_applicable:", 1)[1]
    chunk = chunk.split("\nlimitations:", 1)[0]
    assert f'"{RARE_CATEGORY_ID}"' in chunk
    for concept_id in (RARE_CATEGORY_ID, *CANDIDATE_IDS):
        assert f'- skos_id: "{concept_id}"' not in text, concept_id
    for concept_id in CANDIDATE_IDS:
        assert f'"{concept_id}"' not in text, concept_id


def test_data_dictionary_rare_row_stays_empty() -> None:
    """Section 6.4 mirrors the taxonomy, so its rare row must be empty too."""
    text = DATA_DICTIONARY.read_text(encoding="utf-8")
    marker = "### 6.4 "
    assert marker in text
    section = text.split(marker, 1)[1]
    section = section.split("\n## ", 1)[0]
    row = re.compile(r"^\|\s*`compound_rare`\s*\|([^|]*)\|([^|]*)\|\s*$", re.M)
    match = row.search(section)
    assert match is not None, "no compound_rare row in section 6.4"
    assert re.findall(r"`(compound_[a-z_0-9]+)`", match.group(2)) == []


def test_provenance_records_the_keep_empty_decision() -> None:
    """The 'record the reason' completion criterion is machine-checked."""
    text = PROVENANCE_LEDGER.read_text(encoding="utf-8")
    assert "TAX-027" in text
    assert "compound_rare" in text
    assert "compound_cbdp" in text
