"""Integrity of the compound taxonomy document (SKOS JSON-LD).

Multiple development lines add concepts to
``metadata/taxonomy/compound-taxonomy.skos.jsonld`` (G2 query registration
references its notations, the regulatory knowledge graph relates to it, and
the compound categories are published in the data package).  An asymmetric
``skos:broader``/``skos:narrower`` pair or a duplicate notation is therefore a
structural defect, not a cosmetic one: ``compound-crdh`` had a ``broader``
without a matching ``narrower`` entry until 2026-10-13.
"""

import json
from pathlib import Path

TAXONOMY_PATH = (
    Path(__file__).resolve().parents[2]
    / "metadata"
    / "taxonomy"
    / "compound-taxonomy.skos.jsonld"
)


def _graph():
    return json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))["@graph"]


def test_the_document_parses_and_has_unique_ids():
    graph = _graph()
    ids = [node["@id"] for node in graph]
    assert len(ids) == len(set(ids)), f"duplicate @id: {ids}"
    notations = [node["skos:notation"] for node in graph if "skos:notation" in node]
    assert len(notations) == len(set(notations)), f"duplicate notation: {notations}"


def test_broader_and_narrower_are_symmetric():
    """A parent must list every child, and a child must point back."""
    graph = _graph()
    by_id = {node["@id"]: node for node in graph}
    asymmetric = []

    for node in graph:
        parent = node.get("skos:broader")
        if parent is not None and node["@id"] not in (by_id.get(parent, {}).get("skos:narrower") or []):
            asymmetric.append(f"{node['@id']}.broader -> {parent} (parent does not list it)")
        for child in node.get("skos:narrower") or []:
            if by_id.get(child, {}).get("skos:broader") != node["@id"]:
                asymmetric.append(
                    f"{node['@id']}.narrower -> {child} "
                    f"(child.broader = {by_id.get(child, {}).get('skos:broader')})"
                )

    assert asymmetric == [], asymmetric


def test_every_compound_concept_belongs_to_a_category():
    """Each compound concept is either a top concept or has a broader category."""
    graph = _graph()
    orphans = [
        node["@id"]
        for node in graph
        if "skos:notation" in node
        and node["skos:notation"].startswith("compound_")
        and node.get("skos:topConceptOf") is None
        and node.get("skos:broader") is None
    ]
    assert orphans == [], f"compound concepts without a category: {orphans}"
