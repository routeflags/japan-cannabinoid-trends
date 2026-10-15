"""The chemical class is a second taxonomy dimension, not a second name for route.

Contract sources: ``ISS-20261015-TAX-026`` (owner decision (a): hold chemical
class as the taxonomy's second dimension), ``metadata/taxonomy/``,
``docs/data-dictionary.md`` section 6.5.

The rule: route/origin stays the compound hierarchy (``skos:broader`` /
``skos:narrower`` inside ``jptr:compound-taxonomy``); chemical class lives in
``jptr:chemical-class-taxonomy`` and compounds join it only through symmetric
``skos:related`` links.  A compound therefore keeps exactly one route parent
while carrying at most one chemical-class value, and no ``broader`` /
``narrower`` edge ever crosses the two dimensions.  Coverage is intentionally
partial: only evidenced classes (hydrogenated, acetate) are formalized, and a
compound without a link has a class that is not formalized, not no chemistry.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_DIR = REPO_ROOT / "metadata/taxonomy"
COMPOUND_TAXONOMY = TAXONOMY_DIR / "compound-taxonomy.skos.jsonld"
CONTENT_TAXONOMY = TAXONOMY_DIR / "content-taxonomy.skos.jsonld"
CHEMCLASS_TAXONOMY = TAXONOMY_DIR / "chemical-class-taxonomy.skos.jsonld"
IPTC_MAPPING = TAXONOMY_DIR / "iptc-mapping.yaml"
DATA_DICTIONARY = REPO_ROOT / "docs/data-dictionary.md"

CHEMCLASS_SCHEME = "jptr:chemical-class-taxonomy"

# The formalized membership.  Both directions are checked: the chemical-class
# concept lists exactly these members, and no other compound links back.
EXPECTED_MEMBERSHIP = {
    "jptr:chemclass-hydrogenated": sorted(
        [
            "jptr:compound-hhc",
            "jptr:compound-hhch",
            "jptr:compound-h4cbh",
            "jptr:compound-hhbd",
        ]
    ),
    "jptr:chemclass-acetate": ["jptr:compound-thc-o"],
}

# Route parents of the linked compounds.  Adding a chemical-class link must
# never move a compound to another route category.
EXPECTED_ROUTE_PARENTS = {
    "jptr:compound-hhc": "jptr:compound-semisynthetic",
    "jptr:compound-hhch": "jptr:compound-synthetic",
    "jptr:compound-h4cbh": "jptr:compound-semisynthetic",
    "jptr:compound-hhbd": "jptr:compound-semisynthetic",
    "jptr:compound-thc-o": "jptr:compound-semisynthetic",
}


def _concepts(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return [n for n in document["@graph"] if n.get("@type") == "skos:Concept"]


def _schemes(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return [n for n in document["@graph"] if n.get("@type") == "skos:ConceptScheme"]


def _notation(node: dict) -> str:
    return node["skos:notation"]


def test_the_second_dimension_is_declared_as_its_own_scheme() -> None:
    schemes = _schemes(CHEMCLASS_TAXONOMY)
    assert [s["@id"] for s in schemes] == [CHEMCLASS_SCHEME]
    scheme = schemes[0]
    assert sorted(scheme["skos:hasTopConcept"]) == sorted(EXPECTED_MEMBERSHIP)
    titles = {t["@language"]: t["@value"] for t in scheme["dct:title"]}
    assert titles["en"] and titles["ja"]


def test_chemical_class_notations_are_stable_and_namespaced() -> None:
    by_file = {path: _concepts(path) for path in (COMPOUND_TAXONOMY, CONTENT_TAXONOMY, CHEMCLASS_TAXONOMY)}
    chemclass = by_file[CHEMCLASS_TAXONOMY]
    assert len(chemclass) == len(EXPECTED_MEMBERSHIP)
    notations = [_notation(n) for n in chemclass]
    assert all(n.startswith("chemclass_") for n in notations)
    others = [_notation(n) for path, nodes in by_file.items() if path is not CHEMCLASS_TAXONOMY for n in nodes]
    assert not (set(notations) & set(others)), "chemical-class notation collides with another dimension"
    ids = [n["@id"] for nodes in by_file.values() for n in nodes]
    assert len(ids) == len(set(ids)), "duplicate @id across taxonomy files"


def test_no_hierarchy_edge_crosses_the_two_dimensions() -> None:
    chemclass_ids = set(EXPECTED_MEMBERSHIP)
    for node in _concepts(CHEMCLASS_TAXONOMY):
        assert "skos:broader" not in node, node["@id"]
        assert "skos:narrower" not in node, node["@id"]
    by_id = {n["@id"]: n for n in _concepts(COMPOUND_TAXONOMY)}
    for node in by_id.values():
        assert node.get("skos:broader") not in chemclass_ids, node["@id"]
        for child in node.get("skos:narrower") or []:
            assert child not in chemclass_ids, (node["@id"], child)
    for compound, parent in EXPECTED_ROUTE_PARENTS.items():
        assert by_id[compound].get("skos:broader") == parent, compound


def test_membership_is_exact_and_symmetric() -> None:
    chemclass_by_id = {n["@id"]: n for n in _concepts(CHEMCLASS_TAXONOMY)}
    compound_by_id = {n["@id"]: n for n in _concepts(COMPOUND_TAXONOMY)}
    assert set(chemclass_by_id) == set(EXPECTED_MEMBERSHIP)
    for class_id, members in EXPECTED_MEMBERSHIP.items():
        assert sorted(chemclass_by_id[class_id].get("skos:related", [])) == members, class_id
        for member in members:
            assert class_id in compound_by_id[member].get("skos:related", []), (member, class_id)
    linked = {m for members in EXPECTED_MEMBERSHIP.values() for m in members}
    for node in compound_by_id.values():
        for target in node.get("skos:related", []):
            if target in chemclass_by_id:
                assert node["@id"] in linked, node["@id"]


def test_each_compound_carries_at_most_one_chemical_class() -> None:
    chemclass_ids = set(EXPECTED_MEMBERSHIP)
    for node in _concepts(COMPOUND_TAXONOMY):
        classes = [t for t in node.get("skos:related", []) if t in chemclass_ids]
        assert len(classes) <= 1, (node["@id"], classes)


def test_chemical_classes_are_declared_outside_the_iptc_mapping() -> None:
    """IPTC Media Topics is a news-topic vocabulary with no chemical-structure
    topic, so the honest record is an explicit non-mapping, not a guess."""
    text = IPTC_MAPPING.read_text(encoding="utf-8")
    mapped = set(re.findall(r'skos_id:\s*"([^"]+)"', text))
    for class_id in EXPECTED_MEMBERSHIP:
        assert class_id not in mapped, class_id
        assert f'"{class_id}"' in text, f"{class_id} is not declared in the coverage"


def test_data_dictionary_section_65_mirrors_the_dimension() -> None:
    text = DATA_DICTIONARY.read_text(encoding="utf-8")
    marker = "### 6.5 "
    assert marker in text, "the data dictionary no longer has a 6.5 section"
    section = text.split(marker, 1)[1]
    section = section.split("\n## ", 1)[0]
    rows = re.findall(r"^\|\s*`(chemclass_[a-z_]+)`\s*\|([^|]*)\|([^|]*)\|\s*$", section, re.M)
    assert rows, "no chemical-class rows parsed from section 6.5"
    mirrored = {
        notation: sorted(re.findall(r"`(compound_[a-z_0-9]+)`", members)) for notation, _, members in rows
    }
    by_id = {n["@id"]: n for n in _concepts(CHEMCLASS_TAXONOMY)}
    # Compare by compound @id through the compound file so a renamed notation
    # fails loudly instead of silently matching.
    compound_notation = {n["@id"]: n["skos:notation"] for n in _concepts(COMPOUND_TAXONOMY)}
    expected = {
        by_id[c]["skos:notation"]: sorted(compound_notation[m] for m in ms)
        for c, ms in EXPECTED_MEMBERSHIP.items()
    }
    assert mirrored == expected
