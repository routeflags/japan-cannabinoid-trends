"""The controlled vocabularies and the documents that describe them must agree.

Contract sources: AGENTS.md (technical standards: W3C SKOS for taxonomy, Concept IDs
for portable classification, mapping to external standards), ``docs/data-dictionary.md``,
``metadata/taxonomy/``.

Each check below closes a defect that was live in the repository:

- ``docs/data-dictionary.md`` section 6.4 listed 3 categories and 7 compounds while the
  taxonomy had 6 and 18, and invented its own category ids
  (``major_phytocannabinoid`` vs ``compound_major``);
- ``compound_rare`` was an empty category with no explanation, so it read as a gap
  rather than a reserved dimension;
- ``metadata/taxonomy/iptc-mapping.yaml`` covered 15 of 40 concepts and said nothing
  about the other 25 before the coverage declaration; the chemical-class dimension
  (TAX-026) adds its 2 concepts to the declared universe rather than leaving them
  silent.

The IPTC declaration is read textually because this repository deliberately has no
YAML dependency (see ``processing/rulespec.py`` for the same reasoning).  The reader
is strict: a structure it cannot follow is a failure, not a silent pass.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_DIR = REPO_ROOT / "metadata/taxonomy"
COMPOUND_TAXONOMY = TAXONOMY_DIR / "compound-taxonomy.skos.jsonld"
CONTENT_TAXONOMY = TAXONOMY_DIR / "content-taxonomy.skos.jsonld"
CHEMCLASS_TAXONOMY = TAXONOMY_DIR / "chemical-class-taxonomy.skos.jsonld"
IPTC_MAPPING = TAXONOMY_DIR / "iptc-mapping.yaml"
DATA_DICTIONARY = REPO_ROOT / "docs/data-dictionary.md"
EXPORTS = REPO_ROOT / "exports/taxonomy"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _concepts(path: Path) -> list[dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return [n for n in document["@graph"] if n.get("@type") == "skos:Concept"]


def _is_category(node: dict) -> bool:
    return any("topConceptOf" in key for key in node)


def _categories() -> dict[str, list[str]]:
    """``notation -> sorted [member notation]`` for the compound taxonomy.

    Sorted, because the check is about membership; the document is free to order a
    row's members differently from the taxonomy's ``skos:narrower`` order.
    """

    nodes = _concepts(COMPOUND_TAXONOMY)
    by_id = {n["@id"]: n for n in nodes}
    out: dict[str, list[str]] = {}
    for node in nodes:
        if not _is_category(node):
            continue
        out[node["skos:notation"]] = sorted(
            by_id[member]["skos:notation"]
            for member in node.get("skos:narrower", [])
            if member in by_id
        )
    return out


def _data_dictionary_categories() -> dict[str, list[str]]:
    """Parse section 6.4 of the data dictionary into the same shape."""

    text = DATA_DICTIONARY.read_text(encoding="utf-8")
    marker = "### 6.4 "
    assert marker in text, "the data dictionary no longer has a 6.4 section"
    section = text.split(marker, 1)[1]
    section = section.split("\n## ", 1)[0]

    out: dict[str, list[str]] = {}
    row = re.compile(r"^\|\s*`(compound_[a-z_]+)`\s*\|([^|]*)\|([^|]*)\|\s*$", re.M)
    for match in row.finditer(section):
        notation, _label, members = match.group(1), match.group(2), match.group(3)
        out[notation] = sorted(re.findall(r"`(compound_[a-z_0-9]+)`", members))
    assert out, "no category rows parsed from section 6.4"
    return out


def _all_concept_ids() -> set[str]:
    return {
        node["@id"]
        for path in (COMPOUND_TAXONOMY, CONTENT_TAXONOMY, CHEMCLASS_TAXONOMY)
        for node in _concepts(path)
    }


def _iptc_sections() -> dict[str, set[str]]:
    """Read the coverage declaration without a YAML library, strictly."""

    text = IPTC_MAPPING.read_text(encoding="utf-8")
    assert "\ncoverage:" in text, "iptc-mapping.yaml lost its coverage declaration"
    body = text.split("\ncoverage:", 1)[1]

    mapped = set(re.findall(r'skos_id:\s*"([^"]+)"', text))

    def section(name: str, *, stop: str | None) -> set[str]:
        assert f"\n  {name}:" in body, f"coverage lost its {name} section"
        chunk = body.split(f"\n  {name}:", 1)[1]
        if stop is not None:
            assert f"\n  {stop}:" in chunk, f"{name} is missing before {stop}"
            chunk = chunk.split(f"\n  {stop}:", 1)[0]
        else:
            chunk = chunk.split("\nlimitations:", 1)[0]
        return set(re.findall(r'"(jptr:[^"]+)"', chunk))

    return {
        "mapped": mapped,
        "deliberately_unmapped": section("deliberately_unmapped", stop="not_applicable"),
        "not_applicable": section("not_applicable", stop=None),
    }


# ---------------------------------------------------------------------------
# the checks
# ---------------------------------------------------------------------------


def test_data_dictionary_matches_the_taxonomy() -> None:
    assert _data_dictionary_categories() == _categories()


def test_every_category_is_populated_or_explained() -> None:
    """An empty category must say it is empty on purpose."""

    for node in _concepts(COMPOUND_TAXONOMY):
        if not _is_category(node):
            continue
        members = node.get("skos:narrower", [])
        note = node.get("skos:scopeNote")
        has_note = bool(note.get("@value") if isinstance(note, dict) else note)
        assert members or has_note, f"{node['skos:notation']}: empty with no scopeNote"


def test_every_concept_is_mapped_or_declared_unmapped() -> None:
    sections = _iptc_sections()
    covered = sections["mapped"] | sections["deliberately_unmapped"] | sections["not_applicable"]
    everything = _all_concept_ids()

    assert sections["mapped"] & sections["deliberately_unmapped"] == set()
    assert sections["mapped"] & sections["not_applicable"] == set()
    assert covered == everything, {
        "undeclared": sorted(everything - covered),
        "declared but unknown": sorted(covered - everything),
    }


def test_unmapped_concepts_each_carry_a_reason() -> None:
    """A declaration without a reason is not a declaration."""

    text = IPTC_MAPPING.read_text(encoding="utf-8")
    for section in ("deliberately_unmapped", "not_applicable"):
        assert f"\n  {section}:" in text, section
        chunk = text.split(f"\n  {section}:", 1)[1]
        chunk = chunk.split("\n  not_applicable:", 1)[0] if section == "deliberately_unmapped" else chunk
        chunk = chunk.split("\nlimitations:", 1)[0]
        groups = chunk.split("    - concepts:")[1:]
        assert groups, f"{section} declares no groups"
        for group in groups:
            assert "reason:" in group, f"{section} group without a reason: {group[:60]!r}"


def test_exports_carry_both_languages() -> None:
    """The regression that mattered: English labels reached no published export."""

    for stem, expected in (("compound-taxonomy", 24), ("content-taxonomy", 14), ("chemical-class-taxonomy", 2)):
        turtle = (EXPORTS / f"{stem}.ttl").read_text(encoding="utf-8")
        english = len(re.findall(r'prefLabel> "[^"]*"@en', turtle))
        japanese = len(re.findall(r'prefLabel> "[^"]*"@ja', turtle))
        assert english == japanese == expected, (stem, english, japanese)


def test_the_empty_category_is_documented_in_the_exports() -> None:
    """The one empty category must carry its explanation into the published export."""

    lines = (EXPORTS / "compound-taxonomy.ttl").read_text(encoding="utf-8").splitlines()
    index = next(
        i for i, line in enumerate(lines) if 'notation> "compound_rare"' in line
    )
    block = "\n".join(lines[index : index + 3])
    assert "INTENTIONALLY EMPTY" in block, block
