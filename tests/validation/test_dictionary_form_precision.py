"""The study dictionary keeps form, search term, and coverage apart.

Contract sources: the owner's 2026-11-15 precision baseline
(``ISS-20261115-TAX-044``), ``metadata/queries/query-registry.json`` as the
authority for registered search topics, and the form-level evidence reviews
``ISS-20261111-TAX-042`` / ``ISS-20261115-TAX-043``.

The rule: a registered string is not a structural form.  A form the evidence
supports but the owner has not enumerated as a search topic is an unregistered,
uncollected candidate -- it must not appear as a registry query, as a taxonomy
label, or as a covered series.  Generic, family and market-language terms stay
distinct from individual forms, and a coverage state is not an identity state.

The owner's 2026-11-15 follow-up direction moved the forms that were previously
only named in an exclusion note into the candidate table: the other five THC
positional isomers, the two THCH forms, and the HHC stereoisomers.  The HHC
stereochemistry and registry records are checked against the WHO 47th ECDD
(2024) review and PubChem; the table must still keep statutory structure-group
evidence apart from product analytical identification.

These tests read the reader-facing README rather than re-deriving its prose:
the table structure is the contract.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "datasets/cannabinoid-raw-collection/README.md"
REGISTRY = REPO_ROOT / "metadata/queries/query-registry.json"
TAXONOMY = REPO_ROOT / "metadata/taxonomy/compound-taxonomy.skos.jsonld"

FORM_HEADING = "#### 構造形式辞書"
CROSSWALK_HEADING = "#### 検索語 → 構造形式の crosswalk"
CANDIDATE_HEADING = "#### 未登録・未収集の候補形式"
BATCH_HEADING = "#### 2026-11-15 登録バッチ"
MAP_HEADING = "### 登録済みキーワードと収集状態"

#: Crosswalk display labels that include a recorded alias but keep the canonical
#: registered search term as their base string.
DISPLAY_LABEL_BASES = {"THCNM（別名 THA）": "THCNM"}

#: Terms whose registered string names one form (verified or owner-named).
INDIVIDUAL_FORM_TERMS = (
    "CBD",
    "CBDV",
    "CBC",
    "CBE",
    "CBG",
    "CBGa",
    "CBL",
    "CBN",
    "THCA-B",
    "Δ8-THCA",
    "Δ8-THCB",
    "Δ9-THCA-A",
    "Δ9-THCB",
)
#: Terms that leave the positional isomer (or stereochemistry) unspecified.
FAMILY_TERMS = ("THCB-O-acetate", "THCJD", "THCP", "THCPO", "THCV", "THCH")
#: First-code key of every candidate row the README inventories, exactly once.
CANDIDATE_FORMS = (
    "Δ8-THCP",
    "Δ9-THCP",
    "Δ8-THCJD",
    "Δ9-THCJD",
    "Δ8-THCP-O-acetate",
    "Δ9-THCP-O-acetate",
    "Δ8-THCB-O-acetate",
    "Δ9-THCB-O-acetate",
    "Δ8-THC",
    "Δ6a(10a)-THC",
    "Δ6a(7)-THC",
    "Δ7-THC",
    "Δ10-THC",
    "Δ9(11)-THC",
    "Δ9-THCV",
    "Δ8-THCV",
    "THCJD-O-acetate",
    "Δ8-THCH",
    "Δ9-THCH",
    "9(R)-HHC",
    "9(S)-HHC",
    "(6aS,9S,10aS)-HHC",
    "(6aS,9R,10aS)-HHC",
    "(6aS,9S,10aR)-HHC",
    "(6aS,9R,10aR)-HHC",
    "(6aR,9S,10aS)-HHC",
    "(6aR,9R,10aS)-HHC",
)
#: HHC configurations the WHO review shows beyond the two C-9 epimers.
HHC_OTHER_CONFIGURATIONS = (
    "(6aS,9S,10aS)",
    "(6aS,9R,10aS)",
    "(6aS,9S,10aR)",
    "(6aS,9R,10aR)",
    "(6aR,9S,10aS)",
    "(6aR,9R,10aS)",
)
#: Candidate row key for each of those configurations.
HHC_OTHER_FORMS = tuple(
    f"{configuration}-HHC" for configuration in HHC_OTHER_CONFIGURATIONS
)
#: Terms whose chemical expansion is undefined or market-supplied.
UNRESOLVED_TERMS = (
    "THC",
    "THCA",
    "THCB",
    "CBX",
    "CRDH",
    "CRDP",
    "H4CBH",
    "HHBD",
    "HHC",
    "HHCH",
    "THCNM",
    "THC-O",
    "10-OH-HHC",
    "CBND",
    "CBP",
    "HHCPO",
    "THXE",
)


def _text() -> str:
    return README.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Return the body under ``heading`` up to the next heading of any level."""

    start = text.index(heading)
    body = text[start + len(heading) :]
    kept: list[str] = []
    for line in body.splitlines():
        if re.match(r"^#{1,4} ", line):
            break
        kept.append(line)
    return "\n".join(kept)


def _rows(section: str) -> list[list[str]]:
    """Parse the first Markdown table in ``section``; header excluded."""

    rows: list[list[str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        rows.append(cells)
    return rows[1:]


def _first_code(cell: str) -> str:
    match = re.search(r"`([^`]+)`", cell)
    return match.group(1) if match else cell


def _registry() -> list[dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["queries"]


def _pref_labels() -> set[str]:
    document = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    labels: set[str] = set()
    for concept in document["@graph"]:
        for label in concept.get("skos:prefLabel", []):
            labels.add(label["@value"])
    return labels


def _by_term() -> dict[str, list[str]]:
    rows = _rows(_section(_text(), CROSSWALK_HEADING))
    return {cells[0].strip("`"): cells for cells in rows}


def test_crosswalk_covers_every_registered_concept_once() -> None:
    queries = _registry()
    general: dict[str, list[str]] = {}
    for query in queries:
        if query["intent_id"] == "compound_general":
            general.setdefault(query["compound_id"], []).append(
                query["canonical_text"]
            )

    rows = _rows(_section(_text(), CROSSWALK_HEADING))
    assert len(rows) == len(general) == 63

    seen: dict[str, str] = {}
    for cells in rows:
        term, concept = cells[0].strip("`"), cells[1].strip("`")
        assert concept not in seen, concept
        seen[concept] = term
    assert set(seen) == set(general)
    for concept, term in seen.items():
        canonical_term = DISPLAY_LABEL_BASES.get(term, term)
        assert canonical_term in general[concept], (concept, term)


def test_crosswalk_does_not_claim_a_form_for_generic_or_family_terms() -> None:
    section = _section(_text(), CROSSWALK_HEADING)
    # Coverage lives in the map; an identity table must not imply adopted runs.
    assert "✅" not in section
    assert "adopted" not in section

    rows = _by_term()

    for term in INDIVIDUAL_FORM_TERMS:
        assert not rows[term][4].startswith("未解決"), term
    for term in FAMILY_TERMS:
        assert "未指定" in rows[term][4], term
    for term in UNRESOLVED_TERMS:
        assert rows[term][4].startswith("未解決"), term


def test_form_dictionary_marks_the_unverified_forms() -> None:
    rows = _rows(_section(_text(), FORM_HEADING))
    # 14 rows before the 2026-11-15 batch, plus the 26 determinate forms it registered
    # (THCJD-O-acetate is isomer-unspecified, so it has no form-dictionary row).
    assert len(rows) == 40

    states = {_first_code(cells[0]): cells[4] for cells in rows}
    for term in ("Δ9-THCA-A", "THCA-B", "Δ8-THCA", "Δ8-THCB", "Δ9-THCB"):
        assert "未確認" in states[term], term
    for term in ("Δ9-THC", "CBD", "CBG", "CBGA", "CBN", "CBC", "CBE", "CBL"):
        assert "検証済み" in states[term] or "owner 確認" in states[term], term


def test_the_batch_section_separates_registration_from_collection_status() -> None:
    """The batch records registration separately from its later coverage."""

    section = _section(_text(), BATCH_HEADING)
    assert "登録時点" in section
    assert "19 adopted" in section
    assert "8 `NO_VIDEOS`" in section
    assert "NO_DATA" in section
    assert "27" in section

    registered = {query["canonical_text"] for query in _registry()}
    labels = _pref_labels()
    query_id = re.compile(r"`[a-z0-9-]+-(?:general|liquid)-ja`")
    for form in CANDIDATE_FORMS:
        assert form in registered, form
        assert form in labels, form
    # The section must not re-introduce per-form run references.
    assert query_id.search(section) is None


def test_registered_forms_stay_distinct_from_the_form_dictionary_rows() -> None:
    candidate_forms = set(CANDIDATE_FORMS)
    registered_forms = {
        _first_code(cells[0]) for cells in _rows(_section(_text(), FORM_HEADING))
    }

    # The isomer-unspecified acetate has no determinate form, so it has no row.
    assert candidate_forms - registered_forms == {"THCJD-O-acetate"}
    assert registered_forms - candidate_forms == {
        "Δ9-THC",
        "CBD",
        "CBG",
        "CBGA",
        "CBN",
        "CBC",
        "CBE",
        "CBL",
        "CBDV",
        "Δ9-THCA-A",
        "THCA-B",
        "Δ8-THCA",
        "Δ8-THCB",
        "Δ9-THCB",
    } | {"CBDV"}
    # The generic THC query is not a positional isomer; the form dictionary's
    # Delta-9 row and the registered Delta-8 row stay in their own views.
    assert "Δ9-THC" in registered_forms
    assert "Δ9-THC" not in candidate_forms
    assert "Δ8-THC" in candidate_forms


def test_form_rows_label_evidence_type_and_limits() -> None:
    rows = {
        _first_code(cells[0]): cells for cells in _rows(_section(_text(), FORM_HEADING))
    }

    for form in ("Δ8-THCP-O-acetate", "Δ8-THCB-O-acetate", "Δ9-THCB-O-acetate"):
        evidence = rows[form][6]
        assert "法令（構造グループ）" in evidence, form
        assert "製品分析" in evidence and "未確認" in evidence, form
    assert "製品から同定" in rows["Δ9-THCP-O-acetate"][6]
    assert "Δ9-THCB-O-butanoate" in rows["Δ9-THCB-O-acetate"][6]

    for form in ("Δ8-THCH", "Δ9-THCH"):
        evidence = rows[form][6]
        assert "法令（構造グループ）" in evidence, form
        assert "製品分析" in evidence and "未確認" in evidence, form

    for form in ("9(R)-HHC", "9(S)-HHC"):
        evidence = rows[form][6]
        assert "WHO 47th ECDD" in evidence, form
        assert "特定製品の同定ではない" in evidence, form

    for form in HHC_OTHER_FORMS:
        evidence = rows[form][6]
        assert "WHO 47th ECDD (2024) §2C" in evidence, form
        assert "8 立体異性体" in evidence, form
        assert "配置" in evidence, form
        assert "個別に選択していない" in evidence, form
        assert "製品分析" in evidence and "確認していない" in evidence, form
        assert form.removesuffix("-HHC") in evidence, form

    # The six remaining WHO configurations are individual rows, not a group.
    assert "(6aS,9S,10aS)" not in rows


def test_coverage_map_keeps_coverage_separate_from_identity() -> None:
    section = _section(_text(), MAP_HEADING)
    assert "skos:broader" not in section

    by_concept: dict[tuple[str, str], list[str]] = {}
    for query in _registry():
        key = (query["compound_id"], query["intent_id"])
        by_concept.setdefault(key, []).append(query["query_id"])

    rows = _rows(section)
    assert len(rows) == 63
    for cells in rows:
        assert len(cells) == 5, cells
        concept = cells[1].strip("`")
        for query_id in by_concept[(concept, "compound_general")]:
            assert f"`{query_id}`" in cells[2], (concept, query_id)
        for query_id in by_concept[(concept, "product_liquid")]:
            assert f"`{query_id}`" in cells[3], (concept, query_id)
