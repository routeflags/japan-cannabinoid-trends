"""A compound's external identifiers must resolve to that compound.

The 2026-11-15 P0 correction (``ISS-20261115-TAX-043``) started from a live
registry check of the nine compound crosswalks that the identifier audit
flagged: every one of the old values pointed somewhere else. ``chebi:32927``
is nonadecane, ``chebi:33669`` is metallacycloalkanes, ``chebi:52384`` is
zymosteryl oleate, ``chebi:64901`` is mygalin, and the Wikidata items were a
Quebec city, a German municipality, an aid organisation, two disambiguation
pages, a mycotoxin class, potassium fluoride and two ids that do not exist.

Two rules are pinned here. First, each corrected ``skos:exactMatch`` names the
record that was verified for this concept, so a later edit cannot quietly
re-introduce a wrong id. Second, ``iptc-mapping.yaml`` mirrors the taxonomy's
compound identifiers, because it duplicated the same wrong values and nothing
compared the two files; the mirror is checked textually, since this repository
deliberately has no YAML dependency.

An unqualified concept is not forced onto a more specific record: ``compound_thcv``
stays unmapped because every verified record is the Δ9 isomer while the concept
names no positional isomer, and ``compound_cbdv`` matches the Wikidata item that
is explicitly a group of stereoisomers rather than the stereo-defined record.

The expected values below are the externally verified ones, not a snapshot of
the file. The evidence (record names, standard InChIKeys, P683 cross-references)
lives in ``docs/provenance/compound-taxonomy.md``.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = REPO_ROOT / "metadata/taxonomy/compound-taxonomy.skos.jsonld"
IPTC_MAPPING = REPO_ROOT / "metadata/taxonomy/iptc-mapping.yaml"
EXPORTS = REPO_ROOT / "exports/taxonomy"

#: notation -> exactMatch values verified on 2026-11-15. An empty set is a
#: decision: the concept is broader than every verified record.
EXPECTED = {
    "compound_cbd": {"chebi:69478", "wikidata:Q422917"},
    "compound_thc": {"chebi:66964", "wikidata:Q190067"},
    "compound_cbg": {"chebi:69477", "wikidata:Q412122"},
    "compound_cbn": {"chebi:3360", "wikidata:Q265831"},
    "compound_cbc": {"chebi:3357", "wikidata:Q410949"},
    "compound_thcv": set(),
    "compound_cbdv": {"wikidata:Q1104117"},
    "compound_anandamide": {"chebi:2700", "wikidata:Q410228"},
    "compound_2ag": {"chebi:52392", "wikidata:Q209320"},
}

#: The values the audit found, and what each one actually is. They must not
#: come back: `Q409339` / `Q295793` do not resolve at all.
REPLACED = {
    "chebi:33669": "metallacycloalkanes (compound_cbd)",
    "chebi:32927": "nonadecane (compound_cbg / compound_thc)",
    "chebi:52384": "zymosteryl oleate (compound_anandamide)",
    "chebi:64901": "mygalin (compound_2ag)",
    "wikidata:Q141452": "Disraeli, a city in Quebec (compound_cbd)",
    "wikidata:Q141629": "Reifenberg, a German municipality (compound_thc)",
    "wikidata:Q422432": "Aktion Regen, an aid organisation (compound_cbg)",
    "wikidata:Q415237": "a Wikimedia disambiguation page (compound_cbn)",
    "wikidata:Q422441": "a Wikimedia disambiguation page (compound_cbc)",
    "wikidata:Q422449": "mycotoxins (compound_thcv)",
    "wikidata:Q422426": "potassium fluoride (compound_cbdv)",
    "wikidata:Q409339": "no such Wikidata item (compound_anandamide)",
    "wikidata:Q295793": "no such Wikidata item (compound_2ag)",
}


def _concepts() -> dict[str, dict]:
    document = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    return {
        node["@id"]: node
        for node in document["@graph"]
        if node.get("@type") == "skos:Concept"
    }


def _values(raw) -> set[str]:
    if raw is None:
        return set()
    if isinstance(raw, str):
        return {raw}
    return set(raw)


def _scope_note(node: dict) -> str:
    note = node.get("skos:scopeNote")
    if note is None:
        return ""
    items = note if isinstance(note, list) else [note]
    return " ".join(item["@value"] for item in items)


def _iptc_identifier_blocks() -> dict[str, dict]:
    """``skos_id -> {chebi_id, wikidata_id}`` from ``compound_mapping``."""

    text = IPTC_MAPPING.read_text(encoding="utf-8")
    body = text.split("\ncompound_mapping:", 1)[1]
    body = body.split("\n# ====", 1)[0]
    out: dict[str, dict] = {}
    for block in body.split("- skos_id:")[1:]:
        skos_id = re.match(r'\s*"([^"]+)"', block)
        assert skos_id, block[:80]
        row = {}
        for key, pattern in (
            ("chebi_id", r'chebi_id:\s*"([^"]+)"'),
            ("chebi_uri", r'chebi_uri:\s*"([^"]+)"'),
            ("wikidata_id", r'wikidata_id:\s*"([^"]+)"'),
            ("wikidata_uri", r'wikidata_uri:\s*"([^"]+)"'),
        ):
            match = re.search(pattern, block)
            if match:
                row[key] = match.group(1)
        out[skos_id.group(1)] = row
    return out


# ---------------------------------------------------------------------------
# the corrected crosswalks
# ---------------------------------------------------------------------------


def test_each_concept_carries_the_verified_record_only() -> None:
    concepts = _concepts()
    for notation, expected in EXPECTED.items():
        concept = next(
            node
            for node in concepts.values()
            if node.get("skos:notation") == notation
        )
        assert _values(concept.get("skos:exactMatch")) == expected, notation


def test_the_replaced_identifiers_do_not_come_back() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    for identifier, what in REPLACED.items():
        assert f'"{identifier}"' not in text, f"{identifier} is {what}"
    # The same values are duplicated in the IPTC mapping and must stay correct.
    iptc = IPTC_MAPPING.read_text(encoding="utf-8")
    for identifier, what in REPLACED.items():
        local = identifier.split(":", 1)[1]
        assert local not in iptc, f"{local} is {what}"


def test_the_unmapped_concept_records_why() -> None:
    """An unmapped concept needs its scope decision on the concept itself."""

    concepts = _concepts()
    thcv = next(
        node
        for node in concepts.values()
        if node.get("skos:notation") == "compound_thcv"
    )
    assert "skos:exactMatch" not in thcv
    note = _scope_note(thcv)
    assert "ISS-20261115-TAX-043" in note
    assert "Δ8/Δ9" in note
    assert "stereochemistry" in note
    assert "立体化学" in note


def test_the_group_match_is_not_passed_off_as_a_single_stereoisomer() -> None:
    concepts = _concepts()
    cbdv = next(
        node
        for node in concepts.values()
        if node.get("skos:notation") == "compound_cbdv"
    )
    assert _values(cbdv.get("skos:exactMatch")) == {"wikidata:Q1104117"}
    note = _scope_note(cbdv)
    assert "group of stereoisomers" in note
    assert "CHEBI:182159" in note


# ---------------------------------------------------------------------------
# the duplicated copy
# ---------------------------------------------------------------------------


def test_iptc_mapping_mirrors_the_taxonomy_identifiers() -> None:
    """The crosswalk exists in two files; they may not drift apart."""

    concepts = _concepts()
    mirrored = _iptc_identifier_blocks()
    assert mirrored, "compound_mapping lost its identifier rows"
    for skos_id, row in mirrored.items():
        if "chebi_id" not in row and "wikidata_id" not in row:
            continue
        expected = {
            value
            for value in _values(concepts[skos_id].get("skos:exactMatch"))
            if value.startswith(("chebi:", "wikidata:"))
        }
        actual = set()
        if "chebi_id" in row:
            actual.add("chebi:" + row["chebi_id"])
            assert row["chebi_uri"].endswith("_" + row["chebi_id"]), skos_id
        if "wikidata_id" in row:
            actual.add("wikidata:" + row["wikidata_id"])
            assert row["wikidata_uri"].endswith("/" + row["wikidata_id"]), skos_id
        assert actual == expected, skos_id


def test_exports_carry_the_corrected_identifiers() -> None:
    """Exports are generated; a hand edit or a stale run must fail here."""

    turtle = (EXPORTS / "compound-taxonomy.ttl").read_text(encoding="utf-8")
    for value in (
        "http://purl.obolibrary.org/obo/chebi/69478",
        "http://purl.obolibrary.org/obo/chebi/66964",
        "http://www.wikidata.org/entity/Q422917",
        "http://www.wikidata.org/entity/Q190067",
        "http://www.wikidata.org/entity/Q410949",
        "http://www.wikidata.org/entity/Q1104117",
    ):
        assert value in turtle
    for value in (
        "http://purl.obolibrary.org/obo/chebi/33669",
        "http://purl.obolibrary.org/obo/chebi/32927",
        "http://www.wikidata.org/entity/Q141452",
        "http://www.wikidata.org/entity/Q141629",
        "http://www.wikidata.org/entity/Q422441",
        "http://www.wikidata.org/entity/Q422426",
    ):
        assert value not in turtle


def test_the_exported_mapping_is_the_source_copy() -> None:
    """The export script copies the mapping; a divergent copy is stale output."""

    exported = (EXPORTS / "iptc-mapping.yaml").read_text(encoding="utf-8")
    assert exported == IPTC_MAPPING.read_text(encoding="utf-8")
