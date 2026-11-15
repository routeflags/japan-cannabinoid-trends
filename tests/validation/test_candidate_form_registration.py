"""The 2026-11-15 registration of the candidate-form table (ISS-20261115-TAX-045).

Contract sources: the owner's 2026-11-15 instruction to register the 27 rows the
study README inventoried as unregistered, uncollected candidate forms;
``ISS-20261115-TAX-044`` (the inventory and its precision baseline);
``metadata/queries/query-registry.json`` as the authority for registered search
topics; and the study's ``metadata/query-design.json``.

The rule: registering a term fixes a search string. It does not establish a
chemical identity, does not collect anything, and never reassigns an existing
query or run. Every registered form here is uncollected -- not zero, not missing,
not a collection failure -- and the evidence types behind the rows (registry
record, statutory structural group, nomenclature standard, WHO configuration
review, product analysis) stay distinct.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "metadata/queries/query-registry.json"
VARIANTS = REPO_ROOT / "metadata/queries/query-variants.json"
TAXONOMY = REPO_ROOT / "metadata/taxonomy/compound-taxonomy.skos.jsonld"
STUDY = REPO_ROOT / "datasets/cannabinoid-raw-collection"
README = STUDY / "README.md"
DESIGN = STUDY / "metadata/query-design.json"
CATALOG = STUDY / "metadata/data-catalog.json"
PROJECT = REPO_ROOT / "project.json"
METHODOLOGY = STUDY / "methodology.md"
DATA_DICTIONARY = REPO_ROOT / "docs/data-dictionary.md"
ISSUE = REPO_ROOT / "docs/issues/active/50-taxonomy-standards/20261115_p2_candidate-form-registration.md"
IPTC = REPO_ROOT / "metadata/taxonomy/iptc-mapping.yaml"
IPTC_EXPORT = REPO_ROOT / "exports/taxonomy/iptc-mapping.yaml"
EVIDENCE = REPO_ROOT / "metadata/provenance/evidence-registry.json"
QUERY_INVENTORY = REPO_ROOT / "docs/provenance/query-inventory.md"
PROVENANCE = REPO_ROOT / "docs/provenance/compound-taxonomy.md"

#: The seven compounds the study declares as X-designed.  The 27 batch forms
#: (including the pre-existing Δ8-THC entry) must not carry an X declaration.
X_DESIGNED = {"CBD", "THC", "CBG", "HHC", "THCV", "THC-O", "THCH"}

#: Relation and identifier properties that would turn a registered string into
#: a claimed external identity.  None may be attached to a batch concept.
IDENTITY_PROPERTIES = {
    "skos:exactMatch",
    "skos:closeMatch",
    "skos:broadMatch",
    "skos:narrowMatch",
    "skos:relatedMatch",
    "skos:related",
}

#: Every term the owner enumerated, in the README candidate table's order:
#: (term, notation, slug). Owner spelling is preserved exactly.
BATCH = (
    ("Δ8-THCP", "compound_delta8_thcp", "delta8-thcp"),
    ("Δ9-THCP", "compound_delta9_thcp", "delta9-thcp"),
    ("Δ8-THCJD", "compound_delta8_thcjd", "delta8-thcjd"),
    ("Δ9-THCJD", "compound_delta9_thcjd", "delta9-thcjd"),
    ("Δ8-THCP-O-acetate", "compound_delta8_thcp_o_acetate", "delta8-thcp-o-acetate"),
    ("Δ9-THCP-O-acetate", "compound_delta9_thcp_o_acetate", "delta9-thcp-o-acetate"),
    ("Δ8-THCB-O-acetate", "compound_delta8_thcb_o_acetate", "delta8-thcb-o-acetate"),
    ("Δ9-THCB-O-acetate", "compound_delta9_thcb_o_acetate", "delta9-thcb-o-acetate"),
    ("Δ8-THC", "compound_delta8_thc", "delta8-thc"),
    ("Δ6a(10a)-THC", "compound_delta6a_10a_thc", "delta6a-10a-thc"),
    ("Δ6a(7)-THC", "compound_delta6a_7_thc", "delta6a-7-thc"),
    ("Δ7-THC", "compound_delta7_thc", "delta7-thc"),
    ("Δ10-THC", "compound_delta10_thc", "delta10-thc"),
    ("Δ9(11)-THC", "compound_delta9_11_thc", "delta9-11-thc"),
    ("Δ9-THCV", "compound_delta9_thcv", "delta9-thcv"),
    ("Δ8-THCV", "compound_delta8_thcv", "delta8-thcv"),
    ("THCJD-O-acetate", "compound_thcjd_o_acetate", "thcjd-o-acetate"),
    ("Δ8-THCH", "compound_delta8_thch", "delta8-thch"),
    ("Δ9-THCH", "compound_delta9_thch", "delta9-thch"),
    ("9(R)-HHC", "compound_9_r_hhc", "9r-hhc"),
    ("9(S)-HHC", "compound_9_s_hhc", "9s-hhc"),
    ("(6aS,9S,10aS)-HHC", "compound_6as_9s_10as_hhc", "6as-9s-10as-hhc"),
    ("(6aS,9R,10aS)-HHC", "compound_6as_9r_10as_hhc", "6as-9r-10as-hhc"),
    ("(6aS,9S,10aR)-HHC", "compound_6as_9s_10ar_hhc", "6as-9s-10ar-hhc"),
    ("(6aS,9R,10aR)-HHC", "compound_6as_9r_10ar_hhc", "6as-9r-10ar-hhc"),
    ("(6aR,9S,10aS)-HHC", "compound_6ar_9s_10as_hhc", "6ar-9s-10as-hhc"),
    ("(6aR,9R,10aS)-HHC", "compound_6ar_9r_10as_hhc", "6ar-9r-10as-hhc"),
)
#: The eight HHC stereochemical rows are individuals, not one group row.
HHC_FORMS = tuple(term for term, _, _ in BATCH if term.endswith("-HHC"))
#: The only term whose registered scope stays positional-isomer-unspecified.
ISOMER_UNSPECIFIED = "THCJD-O-acetate"

#: The 75 general+liquid canonical queries the study had before this batch.
PRE_EXISTING_GENERAL_LIQUID = 75
IDENTIFIER_PATTERNS = (
    "skos:exactMatch",
    "CAS ",
    "PubChem",
    "UNII",
    "ChEBI",
    "Wikidata",
    "IUPAC",
)


def _registry() -> list[dict]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["queries"]


def _concepts() -> dict[str, dict]:
    document = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    return {
        node["@id"]: node
        for node in document["@graph"]
        if node.get("@type") == "skos:Concept"
    }


def _notes(concept: dict) -> str:
    return " ".join(item["@value"] for item in concept.get("skos:scopeNote", []))


def _concept_id(notation: str) -> str:
    return "jptr:compound-" + notation[len("compound_"):].replace("_", "-")


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    body = text[start + len(heading):]
    kept: list[str] = []
    for line in body.splitlines():
        if re.match(r"^#{1,4} ", line):
            break
        kept.append(line)
    return "\n".join(kept)


def _rows(section: str) -> list[list[str]]:
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


# ---------------------------------------------------------------------------
# the registered strings and their queries
# ---------------------------------------------------------------------------


def test_the_batch_is_the_27_enumerated_terms() -> None:
    assert len(BATCH) == 27
    assert len({term for term, _, _ in BATCH}) == 27
    assert len({notation for _, notation, _ in BATCH}) == 27
    assert len(HHC_FORMS) == 8


def test_every_term_has_the_declared_query_set_once_and_active() -> None:
    queries = _registry()
    by_compound: dict[str, dict[str, dict]] = {}
    for query in queries:
        by_compound.setdefault(query["compound_id"], {})[query["intent_id"]] = query

    for term, notation, slug in BATCH:
        pair = by_compound[notation]
        assert set(pair) == {"compound_general", "product_liquid"}, notation
        general, liquid = pair["compound_general"], pair["product_liquid"]
        assert general["query_id"] == f"{slug}-general-ja"
        assert liquid["query_id"] == f"{slug}-liquid-ja"
        assert general["canonical_text"] == term
        assert liquid["canonical_text"] == term + " リキッド"
        for query in (general, liquid):
            assert query["language"] == "ja"
            assert query["status"] == "active"


def test_no_canonical_text_is_registered_twice() -> None:
    texts = [query["canonical_text"] for query in _registry()]
    for term, _, _ in BATCH:
        assert texts.count(term) == 1, term
        assert texts.count(term + " リキッド") == 1, term


def test_batch_terms_are_not_pre_created_as_variants() -> None:
    """A registered term needs a recorded basis for a variant; none exists yet."""

    document = json.loads(VARIANTS.read_text(encoding="utf-8"))
    blocks = document.get("variants") or document.get("query_variants") or []
    used: set[str] = set()
    for block in blocks:
        if isinstance(block, dict) and isinstance(block.get("query_id"), str):
            used.add(block["query_id"])
    registered = {query["query_id"] for query in _registry()}
    for _, _, slug in BATCH:
        for intent in ("general", "liquid"):
            query_id = f"{slug}-{intent}-ja"
            assert query_id in registered
            assert query_id not in used


# ---------------------------------------------------------------------------
# the concepts carry the form, not a tradeable identity
# ---------------------------------------------------------------------------


def test_every_new_concept_is_in_the_administrative_category() -> None:
    concepts = _concepts()
    category = concepts["jptr:compound-identity-unverified"]
    members = set(category["skos:narrower"])

    for term, notation, _ in BATCH:
        concept = concepts[_concept_id(notation)]
        assert concept["skos:broader"] == "jptr:compound-identity-unverified", notation
        assert concept["@id"] in members, notation
        assert concept["skos:notation"] == notation
        labels = {item["@language"]: item["@value"] for item in concept["skos:prefLabel"]}
        assert labels == {"en": term, "ja": term}, notation
        # The liquid product form is the only alternate label.
        assert [item["@value"] for item in concept["skos:altLabel"]] == [term + " リキッド"]


def test_no_new_concept_carries_an_identifier_or_a_relation() -> None:
    """The identifiers belong in the ledger until a single record is selected."""

    concepts = _concepts()
    for _, notation, _ in BATCH:
        concept = concepts[_concept_id(notation)]
        attached = set(concept) & IDENTITY_PROPERTIES
        assert attached == set(), (notation, attached)
        # No relation of any kind, including a chemical-class link, is attached.
        assert "jptr:chemclass-acetate" not in json.dumps(concept, ensure_ascii=False), notation


def test_scope_notes_mark_the_unconfirmed_identity_and_the_query_limit() -> None:
    concepts = _concepts()
    for term, notation, _ in BATCH:
        note = _notes(concepts[_concept_id(notation)])
        assert "UNCONFIRMED" in note, notation
        assert "未確認" in note, notation
        assert "2026-11-15" in note and "ISS-20261115-TAX-045" in note, notation
        assert "literal strings" in note and "文字列への一致" in note, notation
        assert "search string, not a substance identification" in note, notation
        assert "検索文字列の登録であり、物質の同定ではない" in note, notation
        assert term in note


def test_statutory_and_review_evidence_are_not_reported_as_product_detection() -> None:
    """A legal structural group and a WHO review are not run results."""

    concepts = _concepts()
    statutory = (
        "compound_delta8_thcp_o_acetate",
        "compound_delta8_thcb_o_acetate",
        "compound_delta9_thcb_o_acetate",
        "compound_delta8_thch",
        "compound_delta9_thch",
        "compound_thcjd_o_acetate",
    )
    for notation in statutory:
        note = _notes(concepts[_concept_id(notation)])
        assert "statutory" in note or "法令" in note, notation
        assert "not a product detection" in note or "製品検出ではない" in note, notation

    epimers = {"9(R)-HHC", "9(S)-HHC"}
    for term, notation, _ in BATCH:
        if not term.endswith("-HHC"):
            continue
        note = _notes(concepts[_concept_id(notation)])
        assert "WHO 47th ECDD (2024) §2C" in note, notation
        if term in epimers:
            # The two C-9 epimers are the ones WHO records in CBD-derived product.
            assert "main epimers" in note and "主要 2 エピマー" in note, notation
        else:
            # The other six are possible configurations only.
            assert "possible configurations" in note or "可能な配置" in note, notation


def test_the_unspecified_acetate_is_not_split_into_positional_isomers() -> None:
    concepts = _concepts()
    note = _notes(concepts["jptr:compound-thcjd-o-acetate"])
    assert "isomer-unspecified" in note and "異性体未指定" in note
    assert "single isomer" in note
    # No companion Δ8/Δ9 rows were invented for this term.
    notations = {concept.get("skos:notation") for concept in concepts.values()}
    assert "compound_delta8_thcjd_o_acetate" not in notations
    assert "compound_delta9_thcjd_o_acetate" not in notations


def test_the_category_states_the_new_cases() -> None:
    category = _concepts()["jptr:compound-identity-unverified"]
    note = " ".join(item["@value"] for item in category["skos:scopeNote"])
    assert "stereochemical configuration" in note
    assert "立体配置" in note
    assert "positional structures the repository does not enumerate" in note
    assert "列挙していない" in note


# ---------------------------------------------------------------------------
# nothing is collected, and nothing historical moved
# ---------------------------------------------------------------------------


def test_no_new_query_appears_in_a_run() -> None:
    """Registration is not collection: the catalog holds no run for them."""

    new_ids = {
        query_id
        for _, _, slug in BATCH
        for query_id in (f"{slug}-general-ja", f"{slug}-liquid-ja")
    }
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    referenced: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "query_id" and isinstance(value, str):
                    referenced.add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(catalog)
    assert new_ids & referenced == set()


def test_existing_general_and_liquid_queries_are_preserved() -> None:
    """The batch adds 54 queries; it deprecates and retargets none."""

    queries = _registry()
    general_liquid = [
        query for query in queries if query["intent_id"] in {"compound_general", "product_liquid"}
    ]
    assert len(general_liquid) == PRE_EXISTING_GENERAL_LIQUID + 54

    new_ids = {
        query_id
        for _, _, slug in BATCH
        for query_id in (f"{slug}-general-ja", f"{slug}-liquid-ja")
    }
    old = [query for query in general_liquid if query["query_id"] not in new_ids]
    assert len(old) == PRE_EXISTING_GENERAL_LIQUID
    assert all(query["status"] == "active" for query in old)

    # The generic THC term keeps its own query and is not relabelled.
    by_id = {query["query_id"]: query for query in queries}
    assert by_id["thc-general-ja"]["canonical_text"] == "THC"
    assert by_id["thc-liquid-ja"]["canonical_text"] == "THC リキッド"
    assert by_id["thc-general-ja"]["compound_id"] == "compound_thc"
    for generic in ("thca", "thcb", "thcv", "thch", "hhc", "thcp", "thcjd", "thcpo"):
        assert f"{generic}-general-ja" in by_id


def test_the_design_records_the_batch_without_run_state() -> None:
    document = json.loads(DESIGN.read_text(encoding="utf-8"))
    design = next(d for d in document["query_designs"] if d["source_id"] == "youtube")
    compound_set = design["compound_set"]
    ids = {notation for _, notation, _ in BATCH}
    matched = [
        group for group in compound_set["registration_basis"] if set(group["compound_ids"]) == ids
    ]
    assert len(matched) == 1
    group = matched[0]
    assert group["decided"] == "2026-11-15"
    assert group["decided_by"] == "owner"
    assert group["identity_state"] == "compound_identity_unverified"
    assert "no run" in group["reason"]

    # A declaration of requirements, never a run-state snapshot.
    flat = json.dumps(compound_set, ensure_ascii=False)
    for stale in ("declared_not_yet_collected", "run_count", "coverageState", "未収集"):
        assert stale not in flat, stale
    for scale in document["comparison_scales"]:
        excluded = {
            item["compound_id"]
            for item in scale["compound_set"].get("excluded_compound_ids", [])
        }
        assert not (excluded & ids), scale["scale_id"]


def test_the_project_mirror_carries_every_term_without_a_coverage_status() -> None:
    compounds = json.loads(PROJECT.read_text(encoding="utf-8"))["queryDesign"]["compounds"]
    for term, _, slug in BATCH:
        entry = compounds[term]
        assert entry["queries"]["youtube"] == term + " リキッド"
        assert entry["queries"]["googleTrends"] == term
        assert "coverageStatus" not in entry
        assert entry["identityNote"].strip()
        assert entry["note"].strip()
        assert f"{slug}-general-ja" in entry["note"]
        assert f"{slug}-liquid-ja" in entry["note"]
        for stale in ("run は 0", "declared_not_yet_collected"):
            assert stale not in entry["note"]


# ---------------------------------------------------------------------------
# the reader-facing tables
# ---------------------------------------------------------------------------


def test_readme_lists_each_registered_term_as_uncollected() -> None:
    map_rows = {
        cells[0]: cells
        for cells in _rows(_section(_readme(), "### 登録済みキーワードと収集状態"))
    }
    assert len(map_rows) == 63
    for term, notation, _ in BATCH:
        row = map_rows[term]
        assert row[1].strip("`") == notation
        assert "未収集" in row[4], term
        assert "✅" not in row[4], term


def test_readme_keeps_the_batch_out_of_the_identity_tables() -> None:
    """Form, term and coverage stay in their own tables."""

    text = _readme()
    batch = _section(text, "#### 2026-11-15 登録バッチ")
    assert "未収集" in batch
    assert "✅" not in batch
    assert "ixiv" not in batch  # no adopted marker smuggled in
    assert "登録は収集の許可ではない" in batch or "run を持たない" in batch

    form_rows = {
        cells[0].strip("`"): cells
        for cells in _rows(_section(text, "#### 構造形式辞書"))
    }
    for term, _, _ in BATCH:
        if term == ISOMER_UNSPECIFIED:
            assert term not in form_rows
        else:
            assert term in form_rows, term
            assert form_rows[term][3], term  # stereochemistry stated, even as 未確認

    crosswalk = {
        cells[0]: cells
        for cells in _rows(_section(text, "#### 検索語 → 構造形式の crosswalk"))
    }
    assert crosswalk[ISOMER_UNSPECIFIED][3] == "異性体未指定"
    for term, _, _ in BATCH:
        if term == ISOMER_UNSPECIFIED:
            continue
        assert crosswalk[term][3] == "個別形式", term


# ---------------------------------------------------------------------------
# current-state reconciliation (audit follow-up)
# ---------------------------------------------------------------------------


def test_batch_breakdown_names_thcv_in_every_current_record() -> None:
    """The middle group is 13 only when THCV's two registered forms are counted."""

    checks = (
        (
            README,
            "THCP・THCJD・THCPO・THCB-O-acetate・THCH・THCV の個別異性体と "
            "`THCJD-O-acetate`（異性体未指定）の 13 形式",
            1,
        ),
        (
            DATA_DICTIONARY,
            "THCB-O-acetate・THCH・THCV の個別異性体と "
            "`THCJD-O-acetate`（異性体未指定）の 13 形式",
            1,
        ),
        (
            ISSUE,
            "THCB-O-acetate / THCH / THCV の個別異性体と "
            "`THCJD-O-acetate`（異性体未指定）の 13 形式",
            1,
        ),
        (
            IPTC,
            "THCB-O-acetate・THCH・THCV の個別異性体と THCJD-O-acetate の 13 形式",
            1,
        ),
        (
            IPTC_EXPORT,
            "THCB-O-acetate・THCH・THCV の個別異性体と THCJD-O-acetate の 13 形式",
            1,
        ),
        (
            DESIGN,
            "THCP / THCJD / THCPO / THCB-O-acetate / THCH / THCV individual isomers "
            "plus the isomer-unspecified THCJD-O-acetate (13 terms)",
            1,
        ),
        (
            EVIDENCE,
            "thirteen THCP / THCJD / THCPO / THCB-O-acetate / THCH / THCV forms",
            1,
        ),
    )
    for path, snippet, expected in checks:
        text = path.read_text(encoding="utf-8")
        assert text.count(snippet) == expected, (path, text.count(snippet))

    for path in (README, DATA_DICTIONARY, ISSUE):
        assert "6 + 13 + 8 = 27" in path.read_text(encoding="utf-8"), path

    for path in (IPTC, IPTC_EXPORT):
        text = path.read_text(encoding="utf-8")
        assert "THCH・THCV の個別異性体と THCJD-O-acetate の計 13 形式" in text, path


def _methodology_topic_rows() -> list[list[str]]:
    text = METHODOLOGY.read_text(encoding="utf-8")
    start = text.index("| No. | キーワード | SKOS notation")
    block = text[start:].split("\n\n", 1)[0]
    rows: list[list[str]] = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        rows.append(cells)
    return rows[1:]


def test_methodology_current_table_has_all_63_topics_and_64_queries() -> None:
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    assert "現在の登録集合は **63 トピック**" in methodology
    assert "| **登録 63 語** | **29/63** | **21/63** |" in methodology

    rows = _methodology_topic_rows()
    assert len(rows) == 63
    by_notation = {cells[2].strip("`"): cells for cells in rows}
    assert len(by_notation) == 63

    for term, notation, _ in BATCH:
        cells = by_notation[notation]
        assert len(cells) == 9, cells
        assert cells[1] == term, cells
        assert cells[4] == f"`{term}`", cells
        assert cells[5] == f"`{term} リキッド`", cells
        assert cells[6] == "未収集", cells
        assert cells[7] == "未収集", cells
        assert cells[8] == "設計外", cells


def test_readme_current_counts_are_63_topics_and_64_primary_queries() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "残る 56 トピック" in readme
    assert "残る 29 トピック" not in readme
    assert "登録集合は 36 トピック" not in readme
    assert "required primary query 64 本" in readme
    assert "required primary query 37 本" not in readme
    assert "計 34 本" in readme

    inventory = QUERY_INVENTORY.read_text(encoding="utf-8")
    assert "登録 63 トピック" in inventory
    assert "登録 36 化合物" not in inventory

    audit_note = json.loads(PROJECT.read_text(encoding="utf-8"))["dataCoverage"]["auditNote"]
    assert "36-term coverage" not in audit_note
    assert "63 registered topics" in audit_note
    assert "CBX" in audit_note and "not silently repaired" in audit_note


def test_project_mirror_has_no_x_for_the_batch_and_keeps_the_seven() -> None:
    compounds = json.loads(PROJECT.read_text(encoding="utf-8"))["queryDesign"]["compounds"]
    for term, _, _ in BATCH:
        assert "x" not in compounds[term]["queries"], term
    for term in X_DESIGNED:
        assert "x" in compounds[term]["queries"], term

    # The batch's X absence is not a registry design: no X intent exists there.
    registry = _registry()
    assert not [query for query in registry if query.get("source_id") == "x"]
    assert not [query for query in registry if "x" in query["query_id"].split("-")]


def test_the_99_required_entries_are_cumulative_additions() -> None:
    readme = README.read_text(encoding="utf-8")
    assert "合計 99 件は、既存構成からの累積追加数" in readme
    assert "policy ごとの有効な general 化合物の総数ではない" in readme
    assert "18 + 81" in readme


def test_scope_notes_deny_identifier_properties_not_recorded_values() -> None:
    concepts = _concepts()
    for term, notation, _ in BATCH:
        note = _notes(concepts[_concept_id(notation)])
        assert "No identifier property and no `skos:exactMatch` are assigned" in note, notation
        assert "recorded evidence in `docs/provenance/compound-taxonomy.md`" in note, notation
        assert "識別子プロパティも `skos:exactMatch` も割り当てない" in note, notation
        assert "carries no skos:exactMatch and no CAS number" not in note, notation
        assert "CAS 番号・PubChem CID・UNII・ChEBI ID・Wikidata QID・IUPAC 名も記載しない" not in note, notation

    # The evidence values stay in the prose; only their property status changes.
    assert "ChEBI 755032" in _notes(concepts["jptr:compound-delta9-thcv"])
    assert "CAS 31262-37-0" in _notes(concepts["jptr:compound-delta9-thcv"])
    assert "PubChem CID 44307335" in _notes(concepts["jptr:compound-delta8-thcp"])

    category = concepts["jptr:compound-identity-unverified"]
    category_note = " ".join(item["@value"] for item in category["skos:scopeNote"])
    assert "Members carry no" not in category_note
    assert "No identifier property and no `skos:exactMatch` are assigned to a member's" in category_note
    assert "member の taxonomy 概念には識別子プロパティも" in category_note
    assert "識別子も持たない" not in category_note


def test_slug_normalization_prose_matches_the_stable_query_ids() -> None:
    examples = (
        "`Δ6a(10a)-THC` → `delta6a-10a-thc`",
        "`Δ6a(7)-THC` → `delta6a-7-thc`",
        "`Δ9(11)-THC` → `delta9-11-thc`",
    )
    for path in (ISSUE, PROVENANCE):
        text = path.read_text(encoding="utf-8")
        assert "括弧を除き" not in text, path
        for example in examples:
            assert example in text, (path, example)


def test_the_12_month_numerator_is_documented_as_pre_existing() -> None:
    assert "12ヶ月 21/63 の分子は既存の被覆記録を引き継ぐ" in README.read_text(encoding="utf-8")
    methodology = METHODOLOGY.read_text(encoding="utf-8")
    assert "12ヶ月の分子 21/63 は既存の被覆記録を引き継いだ**既存値**" in methodology
    assert "本変更で新たに照合した数ではない" in methodology
